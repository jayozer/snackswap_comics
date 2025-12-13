'use client';

import { motion } from 'framer-motion';

interface ToothMascotProps {
  state: 'idle' | 'uploading' | 'scanning' | 'results' | 'comic';
}

export default function ToothMascot({ state }: ToothMascotProps) {
  // Determine which image to show based on state
  let imageSrc = '/images/Dr.Drip_chillin.png'; // Default idle state

  if (state === 'scanning' || state === 'uploading') {
    imageSrc = '/images/Dr.Drip_folded_hands.png'; // Thinking/analyzing
  } else if (state === 'results' || state === 'comic') {
    imageSrc = '/images/Dr.Drip_microphone.png'; // Announcing results
  }

  return (
    <div className="relative w-32 h-32 md:w-40 md:h-40 shrink-0">
      <motion.div
        key={imageSrc}
        className="w-full h-full relative"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0 }}
        transition={{ type: 'spring', bounce: 0.3 }}
      >
        {/* Glow effect */}
        <div className="absolute inset-0 bg-brand-green/20 rounded-full blur-xl" />

        <img
          src={imageSrc}
          alt="Dr. Drip Mascot"
          className="w-full h-full object-contain relative z-10 animate-float"
        />
      </motion.div>
    </div>
  );
}
