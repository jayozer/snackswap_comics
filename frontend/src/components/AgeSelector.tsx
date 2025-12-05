'use client';

import { motion } from 'framer-motion';

interface AgeSelectorProps {
  age: number;
  onAgeChange: (age: number) => void;
}

const ageGroups = [
  { min: 3, max: 5, emoji: '🧒', label: 'Little' },
  { min: 6, max: 8, emoji: '👦', label: 'Kid' },
  { min: 9, max: 12, emoji: '🧑', label: 'Tween' },
];

export default function AgeSelector({ age, onAgeChange }: AgeSelectorProps) {
  const currentGroup = ageGroups.find(g => age >= g.min && age <= g.max) || ageGroups[1];

  return (
    <motion.div
      className="comic-border bg-white p-5 mt-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
    >
      <div className="flex items-center gap-3 mb-4">
        <span className="text-3xl">{currentGroup.emoji}</span>
        <div>
          <h3 className="font-display text-xl text-comic-navy">
            HOW OLD ARE YOU?
          </h3>
          <p className="font-comic text-sm text-gray-500">
            We'll make the comic just right for you!
          </p>
        </div>
      </div>

      {/* Age slider */}
      <div className="relative mt-4">
        {/* Track background */}
        <div className="h-4 bg-gray-200 rounded-full border-2 border-comic-navy overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-comic-mint via-comic-yellow to-comic-coral"
            style={{ width: `${((age - 3) / 9) * 100}%` }}
            layout
          />
        </div>

        {/* Custom slider */}
        <input
          type="range"
          min="3"
          max="12"
          value={age}
          onChange={(e) => onAgeChange(Number(e.target.value))}
          className="absolute inset-0 w-full opacity-0 cursor-pointer"
        />

        {/* Thumb indicator */}
        <motion.div
          className="absolute top-1/2 -translate-y-1/2 w-10 h-10 bg-comic-yellow border-3 border-comic-navy rounded-full flex items-center justify-center font-display text-lg shadow-comic pointer-events-none"
          style={{ left: `calc(${((age - 3) / 9) * 100}% - 20px)` }}
          layout
          whileHover={{ scale: 1.1 }}
        >
          {age}
        </motion.div>
      </div>

      {/* Age labels */}
      <div className="flex justify-between mt-3 text-sm font-comic text-gray-500">
        <span>3</span>
        <span>6</span>
        <span>9</span>
        <span>12</span>
      </div>

      {/* Age group badges */}
      <div className="flex gap-2 mt-4 justify-center">
        {ageGroups.map((group) => {
          const isActive = age >= group.min && age <= group.max;
          return (
            <motion.button
              key={group.label}
              onClick={() => onAgeChange(Math.floor((group.min + group.max) / 2))}
              className={`
                px-4 py-2 rounded-full font-comic text-sm border-2 border-comic-navy
                transition-colors
                ${isActive
                  ? 'bg-comic-cyan text-comic-navy shadow-comic'
                  : 'bg-white text-gray-600 hover:bg-gray-100'
                }
              `}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              {group.emoji} {group.label} ({group.min}-{group.max})
            </motion.button>
          );
        })}
      </div>
    </motion.div>
  );
}
