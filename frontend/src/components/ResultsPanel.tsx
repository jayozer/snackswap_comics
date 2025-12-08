'use client';

import { motion } from 'framer-motion';

type ComicMode = 'educate' | 'celebrate' | 'unknown';

interface ScoredItem {
  snack_id: string;
  name: string;
  category: string;
  dental_risk_score: number;
  confidence: number;
}

interface ResultsPanelProps {
  scoredItems: ScoredItem[];
  facts: any[];
  swaps: any[];
  mode: ComicMode;
  averageRisk: number;
  onViewComic: () => void;
  onReset: () => void;
}

export default function ResultsPanel({
  scoredItems,
  facts,
  swaps,
  mode,
  averageRisk,
  onViewComic,
  onReset,
}: ResultsPanelProps) {
  const getRiskLevel = (score: number) => {
    if (score >= 70) return { label: 'HIGH RISK', color: 'brand-orange', emoji: '🚨' };
    if (score >= 40) return { label: 'MEDIUM RISK', color: 'brand-blue', emoji: '⚠️' };
    if (score >= 30) return { label: 'MODERATE', color: 'brand-blue', emoji: '⚠️' };
    return { label: 'LOW RISK', color: 'brand-green', emoji: '✨' };
  };

  const getCelebrateLevel = () => {
    return { label: 'TOOTH HERO!', color: 'brand-green', emoji: '🏆' };
  };

  const getUnknownLevel = () => {
    return { label: 'DENTAL TIPS', color: 'brand-blue', emoji: '💡' };
  };

  // Use backend-provided average risk instead of calculating locally
  const avgRisk = averageRisk;

  // Get display based on mode
  const getDisplayLevel = () => {
    if (mode === 'celebrate') return getCelebrateLevel();
    if (mode === 'unknown') return getUnknownLevel();
    return getRiskLevel(avgRisk);
  };

  const displayLevel = getDisplayLevel();

  return (
    <div className="space-y-6">
      {/* POW! Header - Mode-aware display */}
      <motion.div
        className={`comic-border p-6 text-center relative overflow-hidden ${
          mode === 'celebrate' ? 'bg-green-50' : 'bg-white'
        }`}
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: 'spring', bounce: 0.5 }}
      >
        {/* Background burst effect */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0 bg-comic-burst" style={{ transform: 'scale(2)' }} />
        </div>

        <motion.div
          className="relative"
          initial={{ rotate: -10, scale: 0 }}
          animate={{ rotate: 0, scale: 1 }}
          transition={{ delay: 0.2, type: 'spring' }}
        >
          <span className="text-4xl mb-2 block">{displayLevel.emoji}</span>
          <h2 className={`font-display text-4xl text-${displayLevel.color} action-word mb-2`}>
            {displayLevel.label}
          </h2>
          {mode === 'celebrate' ? (
            <div className="font-comic text-lg text-brand-dark">
              Great choice! This snack is tooth-friendly! 🎉
            </div>
          ) : mode === 'unknown' ? (
            <div className="font-comic text-lg text-brand-dark">
              Here are some helpful dental health tips!
            </div>
          ) : (
            <div className="font-comic text-lg text-brand-dark">
              Dental Risk Score: <span className="font-bold">{Math.round(avgRisk)}/100</span>
            </div>
          )}
        </motion.div>

        {/* Risk/Health meter - only show for educate and celebrate modes */}
        {mode !== 'unknown' && (
          <div className="mt-4 risk-meter">
            <motion.div
              className={`risk-meter-fill ${mode === 'celebrate' ? 'bg-brand-green' : ''}`}
              initial={{ width: 0 }}
              animate={{ width: mode === 'celebrate' ? '100%' : `${100 - avgRisk}%` }}
              transition={{ delay: 0.5, duration: 0.8 }}
            />
          </div>
        )}
      </motion.div>

      {/* Detected snacks - only show if we have items and not in unknown mode */}
      {scoredItems.length > 0 && mode !== 'unknown' && (
        <motion.div
          className={`comic-border p-5 ${mode === 'celebrate' ? 'bg-green-50' : 'bg-white'}`}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
        >
          <h3 className="font-display text-xl text-brand-dark mb-4 flex items-center gap-2">
            {mode === 'celebrate' ? (
              <>
                <span>🌟</span> HEALTHY HEROES
              </>
            ) : (
              <>
                <span>🍿</span> DETECTED SNACKS
              </>
            )}
          </h3>

          <div className="space-y-3">
            {scoredItems.map((item, index) => {
              const itemRisk = mode === 'celebrate'
                ? { emoji: '⭐', color: 'brand-green' }
                : getRiskLevel(item.dental_risk_score);
              return (
                <motion.div
                  key={item.snack_id}
                  className={`flex items-center gap-3 p-3 rounded-xl border-2 ${
                    mode === 'celebrate'
                      ? 'bg-green-100/50 border-brand-green'
                      : 'bg-brand-subtle/50 border-brand-subtle'
                  }`}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 + index * 0.1 }}
                >
                  <span className="text-2xl">{itemRisk.emoji}</span>
                  <div className="flex-1">
                    <p className="font-bold text-brand-dark">{item.name}</p>
                    <p className="text-sm text-brand-mid font-comic">{item.category}</p>
                  </div>
                  {mode === 'celebrate' ? (
                    <div className="px-3 py-1 rounded-full bg-brand-green/20 border-2 border-brand-green">
                      <span className="font-display text-sm">GREAT!</span>
                    </div>
                  ) : (
                    <div className={`px-3 py-1 rounded-full bg-${itemRisk.color}/20 border-2 border-${itemRisk.color}`}>
                      <span className="font-display text-sm">{Math.round(item.dental_risk_score)}</span>
                    </div>
                  )}
                </motion.div>
              );
            })}
          </div>
        </motion.div>
      )}

      {/* Facts section - mode-aware header and styling */}
      {facts.length > 0 && (
        <motion.div
          className={`comic-border p-5 ${
            mode === 'celebrate' ? 'bg-green-100/50' : 'bg-brand-blue/10'
          }`}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5 }}
        >
          <h3 className="font-display text-xl text-brand-dark mb-4 flex items-center gap-2">
            {mode === 'celebrate' ? (
              <>
                <span>🎉</span> WHY IT'S AWESOME
              </>
            ) : mode === 'unknown' ? (
              <>
                <span>💡</span> DENTAL TIPS
              </>
            ) : (
              <>
                <span>🦷</span> TOOTH FACTS
              </>
            )}
          </h3>

          <div className="space-y-3">
            {facts.slice(0, 3).map((fact, index) => (
              <motion.div
                key={index}
                className={`speech-bubble text-sm font-comic ${
                  mode === 'celebrate' ? 'bg-green-50 border-brand-green' : ''
                }`}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.6 + index * 0.1 }}
              >
                {fact.text || fact.fact_text || 'An interesting dental fact!'}
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Swap suggestions - only show for educate mode */}
      {swaps.length > 0 && mode === 'educate' && (
        <motion.div
          className="comic-border bg-brand-green/10 p-5"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
        >
          <h3 className="font-display text-xl text-brand-dark mb-4 flex items-center gap-2">
            <span>🔄</span> SWAP IDEAS
          </h3>

          <div className="grid gap-3">
            {swaps.slice(0, 2).map((swap, index) => (
              <motion.div
                key={index}
                className="flex items-center gap-3 p-3 bg-white rounded-xl border-2 border-brand-green"
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.8 + index * 0.1 }}
              >
                <span className="text-2xl">✨</span>
                <div>
                  <p className="font-bold text-brand-dark">{swap.name || swap.swap_name}</p>
                  <p className="text-sm text-brand-mid font-comic">
                    {swap.reason || 'A tooth-friendly alternative!'}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Action buttons */}
      <motion.div
        className="flex flex-col gap-3"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.9 }}
      >
        <button
          onClick={onViewComic}
          className="comic-btn w-full bg-brand-green text-white"
        >
          <span className="flex items-center justify-center gap-2">
            <span>🎨</span> SEE MY COMIC!
          </span>
        </button>

        <button
          onClick={onReset}
          className="comic-btn w-full bg-white text-brand-dark"
        >
          <span className="flex items-center justify-center gap-2">
            <span>📸</span> TRY ANOTHER SNACK
          </span>
        </button>
      </motion.div>
    </div>
  );
}
