import React from 'react';
import { FiMic, FiMicOff, FiPower, FiSettings, FiActivity } from 'react-icons/fi';
import { motion } from 'framer-motion';

interface HeaderProps {
  isConnected: boolean;
  isRecording: boolean;
  isMuted: boolean;
  onToggleConnection: () => void;
  onToggleMute: () => void;
  onOpenSettings: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  isConnected,
  isRecording,
  isMuted,
  onToggleConnection,
  onToggleMute,
  onOpenSettings,
}) => {
  return (
    <header className="bg-gray-900 border-b border-gray-800 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-3">
            <div className="relative">
              <FiActivity className="w-8 h-8 text-primary-500" />
              {isConnected && (
                <motion.div
                  className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full"
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                />
              )}
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">AI Executive Assistant</h1>
              <p className="text-sm text-gray-400">
                {isConnected ? 'Connected to Zoom' : 'Not Connected'}
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {/* Connection Status */}
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-gray-800">
            <div
              className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-green-500' : 'bg-red-500'
              }`}
            />
            <span className="text-sm text-gray-300">
              {isConnected ? 'Online' : 'Offline'}
            </span>
          </div>

          {/* Mute Button */}
          <button
            onClick={onToggleMute}
            disabled={!isConnected}
            className={`p-3 rounded-lg transition-all ${
              isMuted
                ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
            data-tooltip={isMuted ? 'Unmute' : 'Mute'}
          >
            {isMuted ? <FiMicOff className="w-5 h-5" /> : <FiMic className="w-5 h-5" />}
          </button>

          {/* Settings Button */}
          <button
            onClick={onOpenSettings}
            className="p-3 rounded-lg bg-gray-800 text-gray-300 hover:bg-gray-700 transition-all"
            data-tooltip="Settings"
          >
            <FiSettings className="w-5 h-5" />
          </button>

          {/* Power Button */}
          <button
            onClick={onToggleConnection}
            className={`p-3 rounded-lg transition-all ${
              isConnected
                ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                : 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
            }`}
            data-tooltip={isConnected ? 'Disconnect' : 'Connect'}
          >
            <FiPower className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Recording Indicator */}
      {isRecording && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-3 flex items-center space-x-2"
        >
          <motion.div
            className="w-3 h-3 bg-red-500 rounded-full"
            animate={{ opacity: [1, 0.5, 1] }}
            transition={{ duration: 1.5, repeat: Infinity }}
          />
          <span className="text-sm text-gray-400">Recording audio...</span>
        </motion.div>
      )}
    </header>
  );
};
