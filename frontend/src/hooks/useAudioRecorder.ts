import { useState, useRef, useCallback, useEffect } from 'react';

interface UseAudioRecorderOptions {
  sampleRate?: number;
  channelCount?: number;
  echoCancellation?: boolean;
  noiseSuppression?: boolean;
  autoGainControl?: boolean;
}

interface UseAudioRecorderReturn {
  isRecording: boolean;
  isPaused: boolean;
  audioLevel: number;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  pauseRecording: () => void;
  resumeRecording: () => void;
  error: string | null;
}

export const useAudioRecorder = (
  onAudioData: (audioData: string) => void,
  options: UseAudioRecorderOptions = {}
): UseAudioRecorderReturn => {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const {
    sampleRate = 16000,
    channelCount = 1,
    echoCancellation = true,
    noiseSuppression = true,
    autoGainControl = true,
  } = options;

  // Calculate audio level from analyser
  const calculateAudioLevel = useCallback(() => {
    if (!analyserRef.current) return;

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    analyserRef.current.getByteFrequencyData(dataArray);

    // Calculate average volume
    const average = dataArray.reduce((acc, val) => acc + val, 0) / dataArray.length;
    const normalizedLevel = Math.min(100, (average / 255) * 100);
    setAudioLevel(normalizedLevel);

    if (isRecording && !isPaused) {
      animationFrameRef.current = requestAnimationFrame(calculateAudioLevel);
    }
  }, [isRecording, isPaused]);

  // Convert audio blob to base64
  const blobToBase64 = (blob: Blob): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64 = reader.result as string;
        resolve(base64.split(',')[1]); // Remove data:audio/webm;base64, prefix
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  };

  const startRecording = async () => {
    try {
      setError(null);

      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate,
          channelCount,
          echoCancellation,
          noiseSuppression,
          autoGainControl,
        },
      });

      streamRef.current = stream;

      // Create audio context and analyser
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({
        sampleRate,
      });
      
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;
      
      sourceRef.current = audioContextRef.current.createMediaStreamSource(stream);
      sourceRef.current.connect(analyserRef.current);

      // Create media recorder
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm';

      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType,
        audioBitsPerSecond: 128000,
      });

      // Handle data available
      mediaRecorderRef.current.ondataavailable = async (event) => {
        if (event.data.size > 0 && !isPaused) {
          try {
            const base64Audio = await blobToBase64(event.data);
            onAudioData(base64Audio);
          } catch (err) {
            console.error('Error converting audio to base64:', err);
          }
        }
      };

      // Handle errors
      mediaRecorderRef.current.onerror = (event) => {
        console.error('MediaRecorder error:', event);
        setError('Recording error occurred');
        stopRecording();
      };

      // Start recording with 1 second chunks
      mediaRecorderRef.current.start(1000);
      setIsRecording(true);
      calculateAudioLevel();

    } catch (err) {
      console.error('Error starting recording:', err);
      setError(err instanceof Error ? err.message : 'Failed to start recording');
    }
  };

  const stopRecording = () => {
    // Stop media recorder
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }

    // Stop all tracks
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }

    // Close audio context
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close();
    }

    // Cancel animation frame
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }

    // Reset refs
    mediaRecorderRef.current = null;
    audioContextRef.current = null;
    analyserRef.current = null;
    sourceRef.current = null;
    streamRef.current = null;
    animationFrameRef.current = null;

    // Reset state
    setIsRecording(false);
    setIsPaused(false);
    setAudioLevel(0);
  };

  const pauseRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.pause();
      setIsPaused(true);
      
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    }
  };

  const resumeRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'paused') {
      mediaRecorderRef.current.resume();
      setIsPaused(false);
      calculateAudioLevel();
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopRecording();
    };
  }, []);

  return {
    isRecording,
    isPaused,
    audioLevel,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    error,
  };
};
