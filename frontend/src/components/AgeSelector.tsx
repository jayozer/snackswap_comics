'use client';

import { motion } from 'framer-motion';

interface AgeSelectorProps {
  age: number;
  onAgeChange: (age: number) => void;
}

const ageGroups = [
  { min: 9, max: 12, emoji: '🔥', label: 'Tween', mode: 'Spicy' },
  { min: 13, max: 17, emoji: '💀', label: 'Teen', mode: 'Savage' },
];

export default function AgeSelector({ age, onAgeChange }: AgeSelectorProps) {
  const currentGroup = ageGroups.find(g => age >= g.min && age <= g.max) || ageGroups[0];

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
          <h3 className="font-display text-xl text-brand-dark">
            HOW OLD ARE YOU?
          </h3>
          <p className="font-comic text-sm text-brand-mid">
            {currentGroup.mode} mode: {age <= 12 ? 'lighter burns' : 'full destruction'}
          </p>
        </div>
      </div>

      {/* Age slider */}
      <div className="relative mt-4">
        {/* Track background */}
        <div className="h-4 bg-brand-subtle rounded-full border-2 border-brand-dark overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-orange-500 via-pink-500 to-purple-600"
            style={{ width: `${((age - 9) / 8) * 100}%` }}
            layout
          />
        </div>

        {/* Custom slider */}
        <input
          type="range"
          min="9"
          max="17"
          value={age}
          onChange={(e) => onAgeChange(Number(e.target.value))}
          className="absolute inset-0 w-full opacity-0 cursor-pointer"
        />

        {/* Thumb indicator */}
        <motion.div
          className="absolute top-1/2 -translate-y-1/2 w-10 h-10 bg-gradient-to-br from-pink-500 to-purple-600 border-3 border-brand-dark rounded-full flex items-center justify-center font-display text-lg text-white shadow-comic pointer-events-none"
          style={{ left: `calc(${((age - 9) / 8) * 100}% - 20px)` }}
          layout
          whileHover={{ scale: 1.1 }}
        >
          {age}
        </motion.div>
      </div>

      {/* Age labels */}
      <div className="flex justify-between mt-3 text-sm font-comic text-brand-mid">
        <span>9</span>
        <span>11</span>
        <span>13</span>
        <span>15</span>
        <span>17</span>
      </div>

      {/* Age group badges */}
      <div className="flex gap-3 mt-4 justify-center">
        {ageGroups.map((group) => {
          const isActive = age >= group.min && age <= group.max;
          return (
            <motion.button
              key={group.label}
              onClick={() => onAgeChange(Math.floor((group.min + group.max) / 2))}
              className={`
                px-5 py-2.5 rounded-full font-comic text-sm border-2 border-brand-dark
                transition-all
                ${isActive
                  ? 'bg-gradient-to-r from-pink-500 to-purple-600 text-white shadow-comic'
                  : 'bg-white text-brand-mid hover:bg-brand-subtle'
                }
              `}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              {group.emoji} {group.label} ({group.min}-{group.max})
              <span className="ml-1 text-xs opacity-75">• {group.mode}</span>
            </motion.button>
          );
        })}
      </div>
    </motion.div>
  );
}
