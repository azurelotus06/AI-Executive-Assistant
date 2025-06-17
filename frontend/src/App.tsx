import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Toaster, toast } from 'react-hot-toast';
import { v4 as uuidv4 } from 'uuid';

// Components
import { Header } from './components/Header';
import { AudioVisualizer } from './components/AudioVisualizer';
import { ConversationPanel } from './components/ConversationPanel';
import { ControlPanel } from './components/ControlPanel';
import { StatusPanel } from './components/StatusPanel';
import { MeetingPanel } from './components/MeetingPanel';

// Services and hooks
import { wsService, controlAPI, aiAPI, audioAPI } from './services/api';
import { useAudioRecorder } from './hooks/useAudioRecorder';

interface Message {
  id: string;
  speaker: string;
  text: string;
  timestamp: string;
  type: 'user' | 'ai' | 'transcript';
  confidence?: number;
}

interface SystemStatus {
  audio_processor: {
    healthy: boolean;
    muted: boolean;
    recording: boolean;
    sample_rate: number;
  };
  ai_service: {
    healthy: boolean;
    paused: boolean;
    conversation_length: number;
    last_response: string | null;
  };
  tts_service: {
    healthy: boolean;
    muted: boolean;
    voice_id: string;
  };
}

function App() {
  // State management
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting'>('disconnected');
  const [messages, setMessages] = useState<Message[]>([]);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [isMuted, setIsMuted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isAIThinking, setIsAIThinking] = useState(false);

  // Audio context for playing TTS
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioQueueRef = useRef<HTMLAudioElement[]>([]);

  // Audio recorder hook
  const handleAudioData = useCallback((audioData: string) => {
    if (isConnected && !isMuted) {
      wsService.sendAudioChunk(audioData, Date.now());
    }
  }, [isConnected, isMuted]);

  const {
    isRecording,
    audioLevel,
    startRecording,
    stopRecording,
    error: recordingError,
  } = useAudioRecorder(handleAudioData);

  // Initialize audio context
  useEffect(() => {
    audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
    return () => {
      audioContextRef.current?.close();
    };
  }, []);

  // WebSocket event handlers
  useEffect(() => {
    // Connection events
    wsService.on('connected', () => {
      setIsConnected(true);
      setConnectionStatus('connected');
      toast.success('Connected to AI Assistant');
      fetchSystemStatus();
    });

    wsService.on('disconnected', () => {
      setIsConnected(false);
      setConnectionStatus('disconnected');
      toast.error('Disconnected from AI Assistant');
      if (isRecording) {
        stopRecording();
      }
    });

    wsService.on('error', (error: any) => {
      console.error('WebSocket error:', error);
      toast.error('Connection error occurred');
    });

    // Message events
    wsService.on('transcript_update', (data: any) => {
      const message: Message = {
        id: uuidv4(),
        speaker: 'Participant',
        text: data.transcript,
        timestamp: new Date().toISOString(),
        type: 'transcript',
        confidence: data.confidence,
      };
      setMessages(prev => [...prev, message]);
    });

    wsService.on('ai_response', async (data: any) => {
      setIsAIThinking(false);
      
      // Add AI message
      const message: Message = {
        id: uuidv4(),
        speaker: 'AI Assistant',
        text: data.ai_text,
        timestamp: new Date().toISOString(),
        type: 'ai',
        confidence: data.confidence,
      };
      setMessages(prev => [...prev, message]);

      // Play TTS audio if available
      if (data.audio_data) {
        playAudioResponse(data.audio_data);
      }
    });

    wsService.on('status', (data: any) => {
      console.log('Status update:', data);
    });

    wsService.on('control_response', (data: any) => {
      if (data.status === 'success') {
        toast.success(`Action completed: ${data.action}`);
      }
    });

    return () => {
      // Cleanup listeners
      wsService.off('connected', () => {});
      wsService.off('disconnected', () => {});
      wsService.off('error', () => {});
      wsService.off('transcript_update', () => {});
      wsService.off('ai_response', () => {});
      wsService.off('status', () => {});
      wsService.off('control_response', () => {});
    };
  }, [isRecording, stopRecording]);

  // Play audio response
  const playAudioResponse = async (audioDataBase64: string) => {
    try {
      const audioData = atob(audioDataBase64);
      const arrayBuffer = new ArrayBuffer(audioData.length);
      const view = new Uint8Array(arrayBuffer);
      
      for (let i = 0; i < audioData.length; i++) {
        view[i] = audioData.charCodeAt(i);
      }

      const blob = new Blob([arrayBuffer], { type: 'audio/mpeg' });
      const audioUrl = URL.createObjectURL(blob);
      
      const audio = new Audio(audioUrl);
      audio.volume = 0.8;
      
      audioQueueRef.current.push(audio);
      
      audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
        audioQueueRef.current = audioQueueRef.current.filter(a => a !== audio);
      };
      
      await audio.play();
    } catch (error) {
      console.error('Error playing audio:', error);
      toast.error('Failed to play audio response');
    }
  };

  // Fetch system status
  const fetchSystemStatus = async () => {
    try {
      const response = await controlAPI.getSystemStatus();
      if (response.success) {
        setSystemStatus(response.system_status);
      }
    } catch (error) {
      console.error('Error fetching system status:', error);
    }
  };

  // Connection handlers
  const handleToggleConnection = async () => {
    if (isConnected) {
      // Disconnect
      try {
        await controlAPI.stopSession();
        wsService.disconnect();
        if (isRecording) {
          stopRecording();
        }
      } catch (error) {
        console.error('Error stopping session:', error);
        toast.error('Failed to stop session');
      }
    } else {
      // Connect
      setConnectionStatus('connecting');
      try {
        await controlAPI.startSession();
        wsService.connect();
        
        // Start recording after connection
        setTimeout(async () => {
          if (!isMuted) {
            try {
              await startRecording();
            } catch (err) {
              console.error('Failed to start recording:', err);
              toast.error('Failed to access microphone');
            }
          }
        }, 1000);
      } catch (error) {
        console.error('Error starting session:', error);
        toast.error('Failed to start session');
        setConnectionStatus('disconnected');
      }
    }
  };

  // Mute handlers
  const handleToggleMute = async () => {
    try {
      if (isMuted) {
        await audioAPI.unmute();
        setIsMuted(false);
        if (isConnected && !isRecording) {
          await startRecording();
        }
        toast.success('Unmuted');
      } else {
        await audioAPI.mute();
        setIsMuted(true);
        if (isRecording) {
          stopRecording();
        }
        toast.success('Muted');
      }
    } catch (error) {
      console.error('Error toggling mute:', error);
      toast.error('Failed to toggle mute');
    }
  };

  // Control panel handlers
  const handleSendPrompt = async (prompt: string) => {
    setIsLoading(true);
    try {
      const response = await aiAPI.manualPrompt(prompt);
      if (response.success && response.response) {
        const message: Message = {
          id: uuidv4(),
          speaker: 'You',
          text: prompt,
          timestamp: new Date().toISOString(),
          type: 'user',
        };
        setMessages(prev => [...prev, message]);

        const aiMessage: Message = {
          id: uuidv4(),
          speaker: 'AI Assistant',
          text: response.response,
          timestamp: new Date().toISOString(),
          type: 'ai',
        };
        setMessages(prev => [...prev, aiMessage]);
      }
    } catch (error) {
      console.error('Error sending prompt:', error);
      toast.error('Failed to send prompt');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearHistory = async () => {
    try {
      await aiAPI.clearHistory();
      setMessages([]);
      toast.success('Conversation history cleared');
    } catch (error) {
      console.error('Error clearing history:', error);
      toast.error('Failed to clear history');
    }
  };

  const handleExportConversation = async () => {
    try {
      const response = await aiAPI.getConversationHistory();
      if (response.success) {
        const dataStr = JSON.stringify(response.history, null, 2);
        const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
        
        const exportFileDefaultName = `conversation_${new Date().toISOString().split('T')[0]}.json`;
        
        const linkElement = document.createElement('a');
        linkElement.setAttribute('href', dataUri);
        linkElement.setAttribute('download', exportFileDefaultName);
        linkElement.click();
        
        toast.success('Conversation exported');
      }
    } catch (error) {
      console.error('Error exporting conversation:', error);
      toast.error('Failed to export conversation');
    }
  };

  const handleTestPipeline = async () => {
    setIsLoading(true);
    try {
      const response = await controlAPI.testPipeline();
      if (response.success) {
        toast.success('Pipeline test completed successfully');
        console.log('Pipeline test results:', response.test_results);
      }
    } catch (error) {
      console.error('Error testing pipeline:', error);
      toast.error('Pipeline test failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenSettings = () => {
    toast('Settings panel coming soon!', { icon: '⚙️' });
  };

  // Update system status periodically
  useEffect(() => {
    if (isConnected) {
      const interval = setInterval(fetchSystemStatus, 5000);
      return () => clearInterval(interval);
    }
  }, [isConnected]);

  // Handle recording errors
  useEffect(() => {
    if (recordingError) {
      toast.error(`Recording error: ${recordingError}`);
    }
  }, [recordingError]);

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col">
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#1f2937',
            color: '#e5e7eb',
            border: '1px solid #374151',
          },
        }}
      />

      <Header
        isConnected={isConnected}
        isRecording={isRecording}
        isMuted={isMuted}
        onToggleConnection={handleToggleConnection}
        onToggleMute={handleToggleMute}
        onOpenSettings={handleOpenSettings}
      />

      <main className="flex-1 container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
          {/* Left Column - Conversation */}
          <div className="lg:col-span-2 flex flex-col space-y-6">
            <AudioVisualizer
              audioLevel={audioLevel}
              isActive={isRecording && !isMuted}
            />
            <div className="flex-1 min-h-0">
              <ConversationPanel
                messages={messages}
                isLoading={isAIThinking}
              />
            </div>
          </div>

          {/* Right Column - Controls and Status */}
          <div className="flex flex-col space-y-6">
            <MeetingPanel />
            <ControlPanel
              onSendPrompt={handleSendPrompt}
              onClearHistory={handleClearHistory}
              onExportConversation={handleExportConversation}
              onTestPipeline={handleTestPipeline}
              isConnected={isConnected}
              isLoading={isLoading}
            />
            <StatusPanel
              systemStatus={systemStatus}
              connectionStatus={connectionStatus}
            />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
