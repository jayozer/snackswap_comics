'use client';

import { motion } from 'framer-motion';

interface AllergenSelectorProps {
  selectedAllergens: string[];
  onAllergensChange: (allergens: string[]) => void;
}

// Common 8 allergens (FDA major food allergens)
const ALLERGENS = [
  { id: 'dairy', label: 'Dairy', emoji: '🥛' },
  { id: 'eggs', label: 'Eggs', emoji: '🥚' },
  { id: 'peanuts', label: 'Peanuts', emoji: '🥜' },
  { id: 'nuts', label: 'Tree Nuts', emoji: '🌰' },
  { id: 'soy', label: 'Soy', emoji: '🫘' },
  { id: 'wheat', label: 'Wheat', emoji: '🌾' },
  { id: 'fish', label: 'Fish', emoji: '🐟' },
  { id: 'shellfish', label: 'Shellfish', emoji: '🦐' },
];

export default function AllergenSelector({
  selectedAllergens,
  onAllergensChange,
}: AllergenSelectorProps) {
  const toggleAllergen = (allergenId: string) => {
    if (selectedAllergens.includes(allergenId)) {
      onAllergensChange(selectedAllergens.filter((a) => a !== allergenId));
    } else {
      onAllergensChange([...selectedAllergens, allergenId]);
    }
  };

  return (
    <motion.div
      className="comic-border bg-white p-5 mt-4"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
    >
      <div className="flex items-center gap-3 mb-4">
        <span className="text-2xl">⚠️</span>
        <div>
          <h3 className="font-display text-lg text-brand-dark">
            ANY ALLERGIES?
          </h3>
          <p className="font-comic text-sm text-brand-mid">
            We'll skip swaps with these ingredients
          </p>
        </div>
      </div>

      {/* Allergen chips */}
      <div className="flex flex-wrap gap-2 mt-3">
        {ALLERGENS.map((allergen) => {
          const isSelected = selectedAllergens.includes(allergen.id);
          return (
            <motion.button
              key={allergen.id}
              onClick={() => toggleAllergen(allergen.id)}
              className={`
                px-3 py-1.5 rounded-full font-comic text-sm border-2
                transition-all flex items-center gap-1.5
                ${isSelected
                  ? 'bg-red-100 border-red-400 text-red-700'
                  : 'bg-white border-gray-300 text-gray-600 hover:border-gray-400'
                }
              `}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <span>{allergen.emoji}</span>
              <span>{allergen.label}</span>
              {isSelected && <span className="ml-1">✕</span>}
            </motion.button>
          );
        })}
      </div>

      {selectedAllergens.length > 0 && (
        <motion.p
          className="mt-3 text-xs text-brand-mid font-comic"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          {selectedAllergens.length} allergen{selectedAllergens.length > 1 ? 's' : ''} selected
          - swap suggestions will exclude these
        </motion.p>
      )}
    </motion.div>
  );
}
