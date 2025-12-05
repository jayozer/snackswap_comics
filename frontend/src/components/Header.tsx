'use client';

import { motion } from 'framer-motion';

export default function Header() {
  return (
    <header className="relative overflow-hidden">
      {/* Zigzag top border */}
      <div className="zigzag-divider" />

      {/* Main header */}
      <div className="bg-comic-navy py-6 px-4">
        <motion.div
          className="container mx-auto text-center"
          initial={{ y: -50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ type: 'spring', bounce: 0.5 }}
        >
          {/* Logo text with starburst effect */}
          <div className="relative inline-block">
            <motion.h1
              className="font-display text-5xl md:text-6xl text-comic-yellow action-word"
              style={{
                textShadow: `
                  3px 3px 0 var(--comic-coral),
                  6px 6px 0 var(--comic-magenta)
                `,
              }}
              animate={{
                rotate: [-1, 1, -1],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
            >
              SnackSwap
            </motion.h1>

            {/* Decorative sparkles */}
            <motion.span
              className="absolute -top-2 -right-4 text-2xl"
              animate={{ scale: [1, 1.2, 1], rotate: [0, 15, 0] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            >
              ✨
            </motion.span>
            <motion.span
              className="absolute -bottom-1 -left-4 text-xl"
              animate={{ scale: [1, 1.3, 1], rotate: [0, -15, 0] }}
              transition={{ duration: 1.8, repeat: Infinity, delay: 0.3 }}
            >
              ⭐
            </motion.span>
          </div>

          {/* Subtitle */}
          <motion.p
            className="font-comic text-comic-cream text-lg mt-2 opacity-90"
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.9 }}
            transition={{ delay: 0.3 }}
          >
            Turn snacks into dental health comics!
          </motion.p>
        </motion.div>
      </div>

      {/* Zigzag bottom border */}
      <div className="zigzag-divider transform rotate-180" />
    </header>
  );
}
