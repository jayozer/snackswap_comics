'use client';

import { motion } from 'framer-motion';

interface Step {
  label: string;
  icon: string;
}

interface ScanningOverlayProps {
  previewUrl: string | null;
  currentStep: number;
  steps: Step[];
}

export default function ScanningOverlay({ previewUrl, currentStep, steps }: ScanningOverlayProps) {
  return (
    <div className="comic-border bg-white overflow-hidden">
      {/* Image with scan effect */}
      <div className="relative">
        {previewUrl && (
          <img
            src={previewUrl}
            alt="Scanning..."
            className="w-full max-h-64 object-cover"
          />
        )}

        {/* Scan line effect */}
        <div className="scan-line" />

        {/* Corner brackets for "targeting" effect */}
        <div className="absolute inset-4 pointer-events-none">
          <div className="absolute top-0 left-0 w-8 h-8 border-t-4 border-l-4 border-brand-blue" />
          <div className="absolute top-0 right-0 w-8 h-8 border-t-4 border-r-4 border-brand-blue" />
          <div className="absolute bottom-0 left-0 w-8 h-8 border-b-4 border-l-4 border-brand-blue" />
          <div className="absolute bottom-0 right-0 w-8 h-8 border-b-4 border-r-4 border-brand-blue" />
        </div>

        {/* Animated grid overlay */}
        <motion.div
          className="absolute inset-0 pointer-events-none"
          style={{
            backgroundImage: `
              linear-gradient(to right, rgba(106, 155, 204, 0.1) 1px, transparent 1px),
              linear-gradient(to bottom, rgba(106, 155, 204, 0.1) 1px, transparent 1px)
            `,
            backgroundSize: '20px 20px',
          }}
          animate={{ opacity: [0.3, 0.7, 0.3] }}
          transition={{ duration: 1, repeat: Infinity }}
        />
      </div>

      {/* Progress steps */}
      <div className="p-6">
        <div className="flex items-center justify-center gap-2 mb-6">
          <motion.span
            className="font-display text-2xl text-brand-dark"
            animate={{ scale: [1, 1.05, 1] }}
            transition={{ duration: 0.8, repeat: Infinity }}
          >
            ANALYZING
          </motion.span>
          <div className="loading-dots flex gap-1">
            <span className="w-2 h-2 bg-brand-orange rounded-full" />
            <span className="w-2 h-2 bg-brand-green rounded-full" />
            <span className="w-2 h-2 bg-brand-blue rounded-full" />
          </div>
        </div>

        {/* Step indicators */}
        <div className="space-y-3">
          {steps.map((step, index) => {
            const isComplete = index < currentStep;
            const isActive = index === currentStep;

            return (
              <motion.div
                key={step.label}
                className={`
                  flex items-center gap-3 p-3 rounded-xl border-2
                  transition-colors duration-300
                  ${isComplete ? 'bg-white border-brand-green' : ''}
                  ${isActive ? 'bg-brand-blue/10 border-brand-blue' : ''}
                  ${!isComplete && !isActive ? 'bg-white border-brand-subtle' : ''}
                `}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                {/* Icon */}
                <motion.span
                  className="text-2xl"
                  animate={isActive ? { scale: [1, 1.15, 1], rotate: [0, 3, -3, 0] } : {}}
                  transition={{ duration: 0.6, repeat: isActive ? Infinity : 0 }}
                >
                  {isComplete ? '✅' : step.icon}
                </motion.span>

                {/* Label */}
                <span className={`
                  font-comic flex-1
                  ${isComplete ? 'text-brand-dark line-through opacity-70' : ''}
                  ${isActive ? 'text-brand-dark font-bold' : ''}
                  ${!isComplete && !isActive ? 'text-brand-mid' : ''}
                `}>
                  {step.label}
                </span>

                {/* Progress indicator for active step */}
                {isActive && (
                  <motion.div
                    className="w-6 h-6 border-3 border-brand-blue border-t-transparent rounded-full"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  />
                )}

                {/* Completed checkmark indicator */}
                {isComplete && (
                  <span className="text-brand-green font-bold">✓</span>
                )}
              </motion.div>
            );
          })}
        </div>

        {/* Fun fact while waiting */}
        <motion.div
          className="mt-6 p-4 bg-brand-orange/10 rounded-xl border-2 border-dashed border-brand-orange"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <p className="font-comic text-sm text-center text-brand-dark">
            <span className="font-bold text-brand-orange">Did you know?</span> Your tooth enamel is the hardest substance in your entire body!
          </p>
        </motion.div>
      </div>
    </div>
  );
}
