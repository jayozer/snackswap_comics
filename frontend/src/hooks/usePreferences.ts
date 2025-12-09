'use client';

import { useState, useEffect, useCallback } from 'react';

const STORAGE_KEY = 'roast-my-snack-preferences';

interface Preferences {
  age: number;
  allergens: string[];
}

const DEFAULT_PREFERENCES: Preferences = {
  age: 13, // Default to middle of teen range
  allergens: [],
};

export function usePreferences() {
  const [preferences, setPreferences] = useState<Preferences>(DEFAULT_PREFERENCES);
  const [isLoaded, setIsLoaded] = useState(false);

  // Load preferences from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored) as Partial<Preferences>;
        setPreferences({
          age: parsed.age ?? DEFAULT_PREFERENCES.age,
          allergens: parsed.allergens ?? DEFAULT_PREFERENCES.allergens,
        });
      }
    } catch (error) {
      console.warn('Failed to load preferences from localStorage:', error);
    }
    setIsLoaded(true);
  }, []);

  // Save preferences to localStorage whenever they change
  useEffect(() => {
    if (isLoaded) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences));
      } catch (error) {
        console.warn('Failed to save preferences to localStorage:', error);
      }
    }
  }, [preferences, isLoaded]);

  const setAge = useCallback((age: number) => {
    // Clamp age to valid range (9-17)
    const clampedAge = Math.min(17, Math.max(9, age));
    setPreferences((prev) => ({ ...prev, age: clampedAge }));
  }, []);

  const setAllergens = useCallback((allergens: string[]) => {
    setPreferences((prev) => ({ ...prev, allergens }));
  }, []);

  const toggleAllergen = useCallback((allergen: string) => {
    setPreferences((prev) => ({
      ...prev,
      allergens: prev.allergens.includes(allergen)
        ? prev.allergens.filter((a) => a !== allergen)
        : [...prev.allergens, allergen],
    }));
  }, []);

  const clearPreferences = useCallback(() => {
    setPreferences(DEFAULT_PREFERENCES);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (error) {
      console.warn('Failed to clear preferences from localStorage:', error);
    }
  }, []);

  // Derived values
  const ageBand = preferences.age <= 12 ? '9-12' : '13-17';
  const mode = preferences.age <= 12 ? 'Spicy' : 'Savage';

  return {
    age: preferences.age,
    allergens: preferences.allergens,
    ageBand,
    mode,
    isLoaded,
    setAge,
    setAllergens,
    toggleAllergen,
    clearPreferences,
  };
}
