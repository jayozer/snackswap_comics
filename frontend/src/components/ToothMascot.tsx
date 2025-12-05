'use client';

import { motion } from 'framer-motion';

interface ToothMascotProps {
  state: 'idle' | 'uploading' | 'scanning' | 'results' | 'comic';
}

export default function ToothMascot({ state }: ToothMascotProps) {
  const getExpression = () => {
    switch (state) {
      case 'idle':
        return { eyes: '◠ ◠', mouth: '◡', blush: true };
      case 'uploading':
        return { eyes: '◉ ◉', mouth: 'o', blush: false };
      case 'scanning':
        return { eyes: '⊙ ⊙', mouth: '〰', blush: false };
      case 'results':
        return { eyes: '★ ★', mouth: 'D', blush: true };
      case 'comic':
        return { eyes: '♥ ♥', mouth: 'D', blush: true };
      default:
        return { eyes: '◠ ◠', mouth: '◡', blush: true };
    }
  };

  const expression = getExpression();

  return (
    <motion.div
      className="relative flex-shrink-0"
      animate={{
        y: state === 'scanning' ? [0, -5, 0] : 0,
        rotate: state === 'results' || state === 'comic' ? [-3, 3, -3] : 0,
      }}
      transition={{
        duration: state === 'scanning' ? 0.5 : 1,
        repeat: Infinity,
        ease: 'easeInOut',
      }}
    >
      {/* Tooth body */}
      <svg
        width="80"
        height="100"
        viewBox="0 0 80 100"
        className="drop-shadow-lg"
      >
        {/* Cape (for superhero effect) */}
        <motion.path
          d="M 60 30 Q 75 50 70 80 L 55 70 Q 60 50 55 35 Z"
          fill="#FF3366"
          stroke="#1A1A2E"
          strokeWidth="2"
          animate={{
            d: state === 'comic'
              ? [
                  "M 60 30 Q 75 50 70 80 L 55 70 Q 60 50 55 35 Z",
                  "M 60 30 Q 80 45 75 80 L 55 70 Q 65 48 55 35 Z",
                  "M 60 30 Q 75 50 70 80 L 55 70 Q 60 50 55 35 Z",
                ]
              : undefined,
          }}
          transition={{ duration: 1, repeat: Infinity }}
        />

        {/* Main tooth shape */}
        <path
          d="M 40 10
             C 60 10 70 25 70 45
             C 70 60 60 70 55 90
             L 45 85
             L 40 95
             L 35 85
             L 25 90
             C 20 70 10 60 10 45
             C 10 25 20 10 40 10"
          fill="white"
          stroke="#1A1A2E"
          strokeWidth="3"
        />

        {/* Shine highlight */}
        <ellipse
          cx="25"
          cy="35"
          rx="8"
          ry="12"
          fill="rgba(255,255,255,0.6)"
        />

        {/* Eyes */}
        <text
          x="40"
          y="45"
          textAnchor="middle"
          fontSize="14"
          fontFamily="system-ui"
          fill="#1A1A2E"
        >
          {expression.eyes}
        </text>

        {/* Blush */}
        {expression.blush && (
          <>
            <ellipse cx="22" cy="52" rx="6" ry="4" fill="#FFB6C1" opacity="0.6" />
            <ellipse cx="58" cy="52" rx="6" ry="4" fill="#FFB6C1" opacity="0.6" />
          </>
        )}

        {/* Mouth */}
        <text
          x="40"
          y="62"
          textAnchor="middle"
          fontSize="16"
          fontFamily="system-ui"
          fill="#1A1A2E"
        >
          {expression.mouth}
        </text>
      </svg>

      {/* Sparkle effects for results/comic state */}
      {(state === 'results' || state === 'comic') && (
        <>
          <motion.span
            className="absolute -top-2 -right-2 text-xl"
            animate={{ scale: [0, 1, 0], rotate: [0, 180, 360] }}
            transition={{ duration: 1, repeat: Infinity, delay: 0 }}
          >
            ✨
          </motion.span>
          <motion.span
            className="absolute top-4 -left-3 text-lg"
            animate={{ scale: [0, 1, 0], rotate: [0, -180, -360] }}
            transition={{ duration: 1, repeat: Infinity, delay: 0.3 }}
          >
            ⭐
          </motion.span>
        </>
      )}

      {/* Scanning rays effect */}
      {state === 'scanning' && (
        <motion.div
          className="absolute inset-0 pointer-events-none"
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 0.5, repeat: Infinity }}
        >
          <div className="absolute top-8 left-6 w-2 h-8 bg-comic-cyan rounded-full blur-sm transform -rotate-12" />
          <div className="absolute top-8 right-6 w-2 h-8 bg-comic-cyan rounded-full blur-sm transform rotate-12" />
        </motion.div>
      )}
    </motion.div>
  );
}
