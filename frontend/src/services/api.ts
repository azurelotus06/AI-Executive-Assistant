import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://bold-chow-trivially.ngrok-free.app';
const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'wss://bold-chow-trivially.ngrok-free.app';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'ngrok-skip-browser-warning': 'true'
  },
  withCredentials: true
});

// Audio API endpoints
export const audioAPI = {
  processChunk: async (audioData: string) => {
    const response = await api.post('/api/audio/process-chunk', { audio_data: audioData });
    return response.data;
  },
  
  uploadAudio: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/api/audio/upload-audio', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  
  startRecording: async () => {
    const response = await api.post('/api/audio/start-recording');
    return response.data;
  },
  
  stopRecording: async () => {
    const response = await api.post('/api/audio/stop-recording');
    return response.data;
  },
  
  mute: async () => {
    const response = await api.post('/api/audio/mute');
    return response.data;
  },
  
  unmute: async () => {
    const response = await api.post('/api/audio/unmute');
    return response.data;
  },
  
  clearBuffers: async () => {
    const response = await api.post('/api/audio/clear-buffers');
    return response.data;
  },
  
  getStatus: async () => {
    const response = await api.get('/api/audio/status');
    return response.data;
  },
};

// AI API endpoints
export const aiAPI = {
  analyze: async (transcript: string, speaker: string = 'Participant') => {
    const response = await api.post('/api/ai/analyze', { transcript, speaker });
    return response.data;
  },
  
  manualPrompt: async (prompt: string) => {
    const response = await api.post('/api/ai/manual-prompt', { prompt });
    return response.data;
  },
  
  pause: async () => {
    const response = await api.post('/api/ai/pause');
    return response.data;
  },
  
  resume: async () => {
    const response = await api.post('/api/ai/resume');
    return response.data;
  },
  
  getConversationSummary: async () => {
    const response = await api.get('/api/ai/conversation-summary');
    return response.data;
  },
  
  getConversationHistory: async () => {
    const response = await api.get('/api/ai/conversation-history');
    return response.data;
  },
  
  clearHistory: async () => {
    const response = await api.post('/api/ai/clear-history');
    return response.data;
  },
  
  getStatus: async () => {
    const response = await api.get('/api/ai/status');
    return response.data;
  },
  
  testAnalysis: async (testTranscript?: string) => {
    const response = await api.post('/api/ai/test-analysis', { test_transcript: testTranscript });
    return response.data;
  },
};

// Control API endpoints
export const controlAPI = {
  startSession: async () => {
    const response = await api.post('/api/control/start-session');
    return response.data;
  },
  
  stopSession: async () => {
    const response = await api.post('/api/control/stop-session');
    return response.data;
  },
  
  muteAll: async () => {
    const response = await api.post('/api/control/mute-all');
    return response.data;
  },
  
  unmuteAll: async () => {
    const response = await api.post('/api/control/unmute-all');
    return response.data;
  },
  
  emergencyStop: async () => {
    const response = await api.post('/api/control/emergency-stop');
    return response.data;
  },
  
  getSystemStatus: async () => {
    const response = await api.get('/api/control/system-status');
    return response.data;
  },
  
  testPipeline: async () => {
    const response = await api.post('/api/control/test-pipeline');
    return response.data;
  },
  
  resetSystem: async () => {
    const response = await api.post('/api/control/reset-system');
    return response.data;
  },
  
  getAvailableVoices: async () => {
    const response = await api.get('/api/control/available-voices');
    return response.data;
  },
  
  setVoice: async (voiceId: string) => {
    const response = await api.post('/api/control/set-voice', { voice_id: voiceId });
    return response.data;
  },
};

// WebSocket connection class
export class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectInterval: number = 5000;
  private reconnectTimer: number | null = null;
  private messageHandlers: Map<string, Function[]> = new Map();
  
  connect() {
    try {
      this.ws = new WebSocket(`${WS_BASE_URL}/ws`);
      
      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.clearReconnectTimer();
        this.emit('connected', null);
      };
      
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.emit(data.type, data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.emit('error', error);
      };
      
      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.emit('disconnected', null);
        this.scheduleReconnect();
      };
    } catch (error) {
      console.error('Error creating WebSocket:', error);
      this.scheduleReconnect();
    }
  }
  
  disconnect() {
    this.clearReconnectTimer();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
  
  send(type: string, data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, ...data }));
    } else {
      console.warn('WebSocket is not connected');
    }
  }
  
  sendAudioChunk(audioData: string, timestamp?: number) {
    this.send('audio_chunk', { data: audioData, timestamp });
  }
  
  sendControl(action: string) {
    this.send('control', { action });
  }
  
  on(event: string, handler: Function) {
    if (!this.messageHandlers.has(event)) {
      this.messageHandlers.set(event, []);
    }
    this.messageHandlers.get(event)!.push(handler);
  }
  
  off(event: string, handler: Function) {
    const handlers = this.messageHandlers.get(event);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }
  
  private emit(event: string, data: any) {
    const handlers = this.messageHandlers.get(event);
    if (handlers) {
      handlers.forEach(handler => handler(data));
    }
  }
  
  private scheduleReconnect() {
    if (!this.reconnectTimer) {
      this.reconnectTimer = window.setTimeout(() => {
        console.log('Attempting to reconnect WebSocket...');
        this.connect();
      }, this.reconnectInterval);
    }
  }
  
  private clearReconnectTimer() {
    if (this.reconnectTimer) {
      window.clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }
  
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

// Meeting API endpoints
export const meetingAPI = {
  join: async (meetingUrl: string, botName?: string) => {
    const response = await api.post('/api/meeting/join', { 
      meeting_url: meetingUrl,
      bot_name: botName 
    });
    return response.data;
  },
  
  leave: async (botId: string) => {
    const response = await api.post(`/api/meeting/leave/${botId}`);
    return response.data;
  },
  
  getActiveMeetings: async () => {
    const response = await api.get('/api/meeting/active');
    return response.data;
  },
  
  getTranscripts: async (botId: string) => {
    const response = await api.get(`/api/meeting/transcripts/${botId}`);
    return response.data;
  },
};

// Export meeting functions for component use
export const joinMeeting = meetingAPI.join;
export const leaveMeeting = meetingAPI.leave;

export const getMeetingStatus = async (botId?: string) => {
  const activeMeetings = await meetingAPI.getActiveMeetings();
  
  if (botId) {
    const bot = activeMeetings.find((m: any) => m.bot_id === botId);
    if (!bot) {
      return { success: false, message: 'Bot not found' };
    }
    
    return {
      success: true,
      bot_status: {
        status: bot.status,
        status_details: {
          code: bot.status,
          created_at: bot.created_at,
          start_time: bot.start_time
        },
        mp4_url: bot.mp4_url,
        speakers: bot.speakers || [],
        error_details: bot.error_details || null
      }
    };
  }

  return {
    success: true,
    bot_status: activeMeetings.map((m: any) => ({
      status: m.status,
      status_details: {
        code: m.status,
        created_at: m.created_at,
        start_time: m.start_time
      },
      mp4_url: m.mp4_url,
      speakers: m.speakers || [],
      error_details: m.error_details || null
    }))
  };
};

// Export a singleton instance
export const wsService = new WebSocketService();

export default api;
