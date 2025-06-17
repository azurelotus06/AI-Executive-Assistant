import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

interface AudioVisualizerProps {
  audioLevel: number;
  isActive: boolean;
}

export const AudioVisualizer: React.FC<AudioVisualizerProps> = ({
  audioLevel,
  isActive,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number | null>(null);

  useEffect(() => {
    if (!canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    canvas.width = canvas.offsetWidth * window.devicePixelRatio;
    canvas.height = canvas.offsetHeight * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    const bars = 40;
    const barWidth = canvas.offsetWidth / bars;
    const barGap = 2;

    const draw = () => {
      ctx.clearRect(0, 0, canvas.offsetWidth, canvas.offsetHeight);

      if (isActive) {
        for (let i = 0; i < bars; i++) {
          const barHeight = Math.random() * (audioLevel / 100) * canvas.offsetHeight * 0.8;
          const x = i * barWidth;
          const y = canvas.offsetHeight - barHeight;

          // Create gradient
          const gradient = ctx.createLinearGradient(0, y, 0, canvas.offsetHeight);
          gradient.addColorStop(0, '#3b82f6');
          gradient.addColorStop(1, '#1d4ed8');

          ctx.fillStyle = gradient;
          ctx.fillRect(x + barGap / 2, y, barWidth - barGap, barHeight);
        }
      }

      animationRef.current = window.requestAnimationFrame(draw);
    };

    draw();

    return () => {
      if (animationRef.current) {
        window.cancelAnimationFrame(animationRef.current);
      }
    };
  }, [audioLevel, isActive]);

  return (
    <div className="relative w-full h-32 bg-gray-900 rounded-lg overflow-hidden">
      <canvas
        ref={canvasRef}
        className="w-full h-full"
        style={{ imageRendering: 'crisp-edges' }}
      />
      {!isActive && (
        <div className="absolute inset-0 flex items-center justify-center">
          <p className="text-gray-500 text-sm">Audio visualizer inactive</p>
        </div>
      )}
      {isActive && (
        <motion.div
          className="absolute bottom-2 right-2 flex items-center space-x-2"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          <span className="text-xs text-gray-400">Live</span>
        </motion.div>
      )}
    </div>
  );
};
