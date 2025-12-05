'use client';

import { motion } from 'framer-motion';

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
  onViewComic: () => void;
  onReset: () => void;
}

export default function ResultsPanel({
  scoredItems,
  facts,
  swaps,
  onViewComic,
  onReset,
}: ResultsPanelProps) {
  const getRiskLevel = (score: number) => {
    if (score >= 70) return { label: 'HIGH RISK', color: 'comic-coral', emoji: '🚨' };
    if (score >= 40) return { label: 'MEDIUM RISK', color: 'comic-yellow', emoji: '⚠️' };
    return { label: 'LOW RISK', color: 'comic-mint', emoji: '✨' };
  };

  const avgRisk = scoredItems.length > 0
    ? scoredItems.reduce((sum, item) => sum + item.dental_risk_score, 0) / scoredItems.length
    : 0;

  const riskLevel = getRiskLevel(avgRisk);

  return (
    <div className="space-y-6">
      {/* POW! Header with risk score */}
      <motion.div
        className="comic-border bg-white p-6 text-center relative overflow-hidden"
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
          <span className="text-4xl mb-2 block">{riskLevel.emoji}</span>
          <h2 className={`font-display text-4xl text-${riskLevel.color} action-word mb-2`}>
            {riskLevel.label}
          </h2>
          <div className="font-comic text-lg text-comic-navy">
            Dental Risk Score: <span className="font-bold">{Math.round(avgRisk)}/100</span>
          </div>
        </motion.div>

        {/* Risk meter */}
        <div className="mt-4 risk-meter">
          <motion.div
            className="risk-meter-fill"
            initial={{ width: 0 }}
            animate={{ width: `${100 - avgRisk}%` }}
            transition={{ delay: 0.5, duration: 0.8 }}
          />
        </div>
      </motion.div>

      {/* Detected snacks */}
      <motion.div
        className="comic-border bg-white p-5"
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.3 }}
      >
        <h3 className="font-display text-xl text-comic-navy mb-4 flex items-center gap-2">
          <span>🍿</span> DETECTED SNACKS
        </h3>

        <div className="space-y-3">
          {scoredItems.map((item, index) => {
            const itemRisk = getRiskLevel(item.dental_risk_score);
            return (
              <motion.div
                key={item.snack_id}
                className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl border-2 border-gray-200"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 + index * 0.1 }}
              >
                <span className="text-2xl">{itemRisk.emoji}</span>
                <div className="flex-1">
                  <p className="font-bold text-comic-navy">{item.name}</p>
                  <p className="text-sm text-gray-500 font-comic">{item.category}</p>
                </div>
                <div className={`px-3 py-1 rounded-full bg-${itemRisk.color}/20 border-2 border-${itemRisk.color}`}>
                  <span className="font-display text-sm">{Math.round(item.dental_risk_score)}</span>
                </div>
              </motion.div>
            );
          })}
        </div>
      </motion.div>

      {/* Dental facts */}
      {facts.length > 0 && (
        <motion.div
          className="comic-border bg-comic-cyan/10 p-5"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5 }}
        >
          <h3 className="font-display text-xl text-comic-navy mb-4 flex items-center gap-2">
            <span>🦷</span> TOOTH FACTS
          </h3>

          <div className="space-y-3">
            {facts.slice(0, 3).map((fact, index) => (
              <motion.div
                key={index}
                className="speech-bubble text-sm font-comic"
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

      {/* Swap suggestions */}
      {swaps.length > 0 && (
        <motion.div
          className="comic-border bg-comic-mint/10 p-5"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
        >
          <h3 className="font-display text-xl text-comic-navy mb-4 flex items-center gap-2">
            <span>🔄</span> SWAP IDEAS
          </h3>

          <div className="grid gap-3">
            {swaps.slice(0, 2).map((swap, index) => (
              <motion.div
                key={index}
                className="flex items-center gap-3 p-3 bg-white rounded-xl border-2 border-comic-mint"
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.8 + index * 0.1 }}
              >
                <span className="text-2xl">✨</span>
                <div>
                  <p className="font-bold text-comic-navy">{swap.name || swap.swap_name}</p>
                  <p className="text-sm text-gray-500 font-comic">
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
          className="comic-btn w-full bg-comic-yellow text-comic-navy"
        >
          <span className="flex items-center justify-center gap-2">
            <span>🎨</span> SEE MY COMIC!
          </span>
        </button>

        <button
          onClick={onReset}
          className="comic-btn w-full bg-white text-comic-navy"
        >
          <span className="flex items-center justify-center gap-2">
            <span>📸</span> TRY ANOTHER SNACK
          </span>
        </button>
      </motion.div>
    </div>
  );
}
