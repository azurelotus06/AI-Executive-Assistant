import React, { useState } from 'react';
import { FiSend, FiRefreshCw, FiDownload, FiTrash2 } from 'react-icons/fi';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';

interface ControlPanelProps {
  onSendPrompt: (prompt: string) => void;
  onClearHistory: () => void;
  onExportConversation: () => void;
  onTestPipeline: () => void;
  isConnected: boolean;
  isLoading?: boolean;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({
  onSendPrompt,
  onClearHistory,
  onExportConversation,
  onTestPipeline,
  isConnected,
  isLoading = false,
}) => {
  const [prompt, setPrompt] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (prompt.trim() && !isLoading) {
      onSendPrompt(prompt.trim());
      setPrompt('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="bg-gray-900 rounded-lg p-4">
      <h3 className="text-lg font-semibold text-white mb-4">Manual Control</h3>

      {/* Manual Prompt Input */}
      <form onSubmit={handleSubmit} className="mb-4">
        <div className="relative">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask the AI assistant anything..."
            disabled={!isConnected || isLoading}
            className="w-full px-4 py-3 pr-12 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none disabled:opacity-50 disabled:cursor-not-allowed"
            rows={3}
          />
          <button
            type="submit"
            disabled={!isConnected || isLoading || !prompt.trim()}
            className="absolute bottom-3 right-3 p-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <FiSend className="w-4 h-4" />
          </button>
        </div>
      </form>

      {/* Quick Actions */}
      <div className="space-y-2">
        <h4 className="text-sm font-medium text-gray-400 mb-2">Quick Actions</h4>
        
        <button
          onClick={onTestPipeline}
          disabled={!isConnected || isLoading}
          className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <FiRefreshCw className="w-4 h-4" />
          <span>Test Pipeline</span>
        </button>

        <button
          onClick={onExportConversation}
          disabled={!isConnected}
          className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <FiDownload className="w-4 h-4" />
          <span>Export Conversation</span>
        </button>

        <button
          onClick={() => {
            if (window.confirm('Are you sure you want to clear the conversation history?')) {
              onClearHistory();
            }
          }}
          disabled={!isConnected}
          className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <FiTrash2 className="w-4 h-4" />
          <span>Clear History</span>
        </button>
      </div>

      {/* Status Indicator */}
      {isLoading && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-4 p-3 bg-primary-500/10 border border-primary-500/30 rounded-lg"
        >
          <div className="flex items-center space-x-2">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            >
              <FiRefreshCw className="w-4 h-4 text-primary-400" />
            </motion.div>
            <span className="text-sm text-primary-300">Processing...</span>
          </div>
        </motion.div>
      )}
    </div>
  );
};
