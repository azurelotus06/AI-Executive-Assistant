import React from 'react';
import { Check, X, Cpu, Mic, Volume2, RefreshCw } from 'lucide-react';
import { motion } from 'framer-motion';

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

interface StatusPanelProps {
  systemStatus: SystemStatus | null;
  connectionStatus: 'connected' | 'disconnected' | 'connecting';
}

export const StatusPanel: React.FC<StatusPanelProps> = ({
  systemStatus,
  connectionStatus,
}) => {
  const getStatusIcon = (healthy: boolean) => {
    return healthy ? (
      <Check className="w-4 h-4 text-green-500" />
    ) : (
      <X className="w-4 h-4 text-red-500" />
    );
  };

  const getConnectionColor = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'bg-green-500';
      case 'connecting':
        return 'bg-yellow-500';
      default:
        return 'bg-red-500';
    }
  };

  return (
    <div className="bg-gray-900 rounded-lg p-4">
      <h3 className="text-lg font-semibold text-white mb-4">System Status</h3>

      {/* Connection Status */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-400">WebSocket Connection</span>
          <div className="flex items-center space-x-2">
            <motion.div
              className={`w-2 h-2 rounded-full ${getConnectionColor()}`}
              animate={connectionStatus === 'connecting' ? { opacity: [1, 0.5, 1] } : {}}
              transition={{ duration: 1.5, repeat: Infinity }}
            />
            <span className="text-sm text-gray-300 capitalize">{connectionStatus}</span>
          </div>
        </div>
      </div>

      {systemStatus && (
        <>
          {/* Audio Processor Status */}
          <div className="mb-4">
            <div className="flex items-center space-x-2 mb-2">
              <Mic className="w-5 h-5 text-primary-400" />
              <span className="text-sm font-medium text-gray-300">Audio Processor</span>
              {getStatusIcon(systemStatus.audio_processor.healthy)}
            </div>
            <div className="ml-7 space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500">Recording</span>
                <span className={systemStatus.audio_processor.recording ? 'text-green-400' : 'text-gray-400'}>
                  {systemStatus.audio_processor.recording ? 'Active' : 'Inactive'}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500">Muted</span>
                <span className={systemStatus.audio_processor.muted ? 'text-red-400' : 'text-green-400'}>
                  {systemStatus.audio_processor.muted ? 'Yes' : 'No'}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500">Sample Rate</span>
                <span className="text-gray-400">{systemStatus.audio_processor.sample_rate} Hz</span>
              </div>
            </div>
          </div>

          {/* AI Service Status */}
          <div className="mb-4">
            <div className="flex items-center space-x-2 mb-2">
              <Cpu className="w-5 h-5 text-primary-400" />
              <span className="text-sm font-medium text-gray-300">AI Service</span>
              {getStatusIcon(systemStatus.ai_service.healthy)}
            </div>
            <div className="ml-7 space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500">Status</span>
                <span className={systemStatus.ai_service.paused ? 'text-yellow-400' : 'text-green-400'}>
                  {systemStatus.ai_service.paused ? 'Paused' : 'Active'}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500">Messages</span>
                <span className="text-gray-400">{systemStatus.ai_service.conversation_length}</span>
              </div>
              {systemStatus.ai_service.last_response && (
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-500">Last Response</span>
                  <span className="text-gray-400">
                    {new Date(systemStatus.ai_service.last_response).toLocaleTimeString()}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* TTS Service Status */}
          <div className="mb-4">
            <div className="flex items-center space-x-2 mb-2">
              <Volume2 className="w-5 h-5 text-primary-400" />
              <span className="text-sm font-medium text-gray-300">TTS Service</span>
              {getStatusIcon(systemStatus.tts_service.healthy)}
            </div>
            <div className="ml-7 space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500">Muted</span>
                <span className={systemStatus.tts_service.muted ? 'text-red-400' : 'text-green-400'}>
                  {systemStatus.tts_service.muted ? 'Yes' : 'No'}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500">Voice ID</span>
                <span className="text-gray-400 truncate max-w-[100px]" title={systemStatus.tts_service.voice_id}>
                  {systemStatus.tts_service.voice_id}
                </span>
              </div>
            </div>
          </div>
        </>
      )}

      {!systemStatus && connectionStatus === 'connected' && (
        <div className="text-center py-8">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            className="inline-block"
          >
            <RefreshCw className="w-6 h-6 text-gray-500" />
          </motion.div>
          <p className="text-sm text-gray-500 mt-2">Loading system status...</p>
        </div>
      )}

      {connectionStatus === 'disconnected' && (
        <div className="text-center py-8">
          <X className="w-8 h-8 text-red-500 mx-auto mb-2" />
          <p className="text-sm text-gray-500">System disconnected</p>
        </div>
      )}
    </div>
  );
};
