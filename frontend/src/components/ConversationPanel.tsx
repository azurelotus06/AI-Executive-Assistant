import React, { useEffect, useRef } from 'react';
import { format } from 'date-fns';
import { User, Cpu, Mic } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface Message {
  id: string;
  speaker: string;
  text: string;
  timestamp: string;
  type: 'user' | 'ai' | 'transcript';
  confidence?: number;
}

interface ConversationPanelProps {
  messages: Message[];
  isLoading?: boolean;
}

export const ConversationPanel: React.FC<ConversationPanelProps> = ({
  messages,
  isLoading = false,
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const getIcon = (type: string) => {
    switch (type) {
      case 'ai':
        return <Cpu className="w-5 h-5" />;
      case 'transcript':
        return <Mic className="w-4 h-4" />;
      default:
        return <User className="w-5 h-5" />;
    }
  };

  const getMessageStyle = (type: string) => {
    switch (type) {
      case 'ai':
        return 'bg-primary-500/10 border-primary-500/30 text-primary-100';
      case 'transcript':
        return 'bg-gray-800/50 border-gray-700/50 text-gray-300';
      default:
        return 'bg-gray-800 border-gray-700 text-gray-100';
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-900 rounded-lg">
      <div className="px-4 py-3 border-b border-gray-800">
        <h2 className="text-lg font-semibold text-white">Conversation</h2>
        <p className="text-sm text-gray-400">Real-time meeting transcript</p>
      </div>

      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 space-y-3 scrollbar-thin"
      >
        <AnimatePresence initial={false}>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className={`flex items-start space-x-3 p-3 rounded-lg border ${getMessageStyle(
                message.type
              )}`}
            >
              <div className="flex-shrink-0 mt-0.5">
                {getIcon(message.type)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium">
                    {message.speaker}
                  </span>
                  <span className="text-xs text-gray-500">
                    {format(new Date(message.timestamp), 'HH:mm:ss')}
                  </span>
                </div>
                <p className="text-sm break-words">{message.text}</p>
                {message.confidence !== undefined && (
                  <div className="mt-2 flex items-center space-x-2">
                    <div className="flex-1 h-1 bg-gray-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary-500 transition-all duration-300"
                        style={{ width: `${message.confidence * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-500">
                      {Math.round(message.confidence * 100)}%
                    </span>
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex items-center space-x-2 p-3 rounded-lg bg-gray-800/50"
          >
            <div className="flex space-x-1">
              <motion.div
                className="w-2 h-2 bg-primary-500 rounded-full"
                animate={{ y: [0, -5, 0] }}
                transition={{ duration: 0.6, repeat: Infinity, delay: 0 }}
              />
              <motion.div
                className="w-2 h-2 bg-primary-500 rounded-full"
                animate={{ y: [0, -5, 0] }}
                transition={{ duration: 0.6, repeat: Infinity, delay: 0.2 }}
              />
              <motion.div
                className="w-2 h-2 bg-primary-500 rounded-full"
                animate={{ y: [0, -5, 0] }}
                transition={{ duration: 0.6, repeat: Infinity, delay: 0.4 }}
              />
            </div>
            <span className="text-sm text-gray-400">AI is thinking...</span>
          </motion.div>
        )}

        {messages.length === 0 && !isLoading && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Mic className="w-12 h-12 text-gray-600 mb-3" />
            <p className="text-gray-500">No conversation yet</p>
            <p className="text-sm text-gray-600 mt-1">
              Start speaking to see the transcript
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
