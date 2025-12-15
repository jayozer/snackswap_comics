'use client';

import { useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';

export default function HowToUse() {
  const [isOpen, setIsOpen] = useState(false);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!isOpen) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setIsOpen(false);
    };

    window.addEventListener('keydown', onKeyDown);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    return () => {
      window.removeEventListener('keydown', onKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    closeButtonRef.current?.focus();
  }, [isOpen]);

  return (
    <>
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          setIsOpen(true);
        }}
        className="
          absolute top-4 right-4 z-10
          w-10 h-10 rounded-full
          bg-white/90 backdrop-blur
          border-2 border-brand-subtle
          text-brand-dark
          flex items-center justify-center
          shadow-sm
          transition-transform
          hover:scale-105
          active:scale-95
        "
        aria-label="How to use Roast My Snack"
        title="How to use"
      >
        <span className="font-display text-xl leading-none select-none">ⓘ</span>
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            className="fixed inset-0 z-50 bg-brand-dark/50 backdrop-blur-sm flex items-center justify-center p-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setIsOpen(false)}
          >
            <motion.div
              className="
                w-full max-w-lg
                bg-white
                border-2 border-brand-subtle
                rounded-3xl
                shadow-2xl
                overflow-hidden
              "
              initial={{ scale: 0.96, y: 12, opacity: 0 }}
              animate={{ scale: 1, y: 0, opacity: 1 }}
              exit={{ scale: 0.98, y: 12, opacity: 0 }}
              transition={{ type: 'spring', bounce: 0.2, duration: 0.35 }}
              onClick={(e) => e.stopPropagation()}
              role="dialog"
              aria-modal="true"
              aria-labelledby="howto-title"
            >
              {/* Header */}
              <div className="p-6 border-b-2 border-brand-subtle bg-brand-light">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h2 id="howto-title" className="font-display text-2xl text-brand-dark">
                      HOW TO ROAST YOUR SNACK
                    </h2>
                    <p className="mt-2 font-comic text-brand-mid">
                      Dr. Hawley is your Gen‑Z tooth doc. He calls out snacks that can mess with your smile’s glow‑up.
                    </p>
                  </div>

                  <button
                    ref={closeButtonRef}
                    type="button"
                    onClick={() => setIsOpen(false)}
                    className="
                      shrink-0
                      w-10 h-10 rounded-full
                      border-2 border-brand-subtle
                      bg-white
                      text-brand-dark
                      font-display
                      flex items-center justify-center
                      hover:bg-brand-subtle/60
                      transition-colors
                    "
                    aria-label="Close"
                    title="Close"
                  >
                    ✕
                  </button>
                </div>
              </div>

              {/* Content */}
              <div className="p-6 max-h-[70vh] overflow-y-auto space-y-5">
                <div className="space-y-3">
                  {[
                    'Tap SNAP YOUR SNACK (or drag & drop a pic).',
                    'Pick your age: Tween = Spicy 🔥, Teen = Savage 💀.',
                    'Tap allergies so swap ideas avoid them.',
                    'Watch the scan: detect → score → facts → comic.',
                    'Check your risk score + tooth facts + swap ideas.',
                    'Open your comic, download Story/Reel, then share it.',
                  ].map((text, index) => (
                    <div key={text} className="flex items-start gap-3">
                      <div className="w-7 h-7 rounded-full bg-brand-blue/15 border-2 border-brand-blue text-brand-dark font-display flex items-center justify-center shrink-0">
                        {index + 1}
                      </div>
                      <p className="font-comic text-brand-dark leading-snug">{text}</p>
                    </div>
                  ))}
                </div>

                <div className="p-4 rounded-2xl border-2 border-brand-green bg-brand-green/10">
                  <p className="font-comic text-brand-dark">
                    <span className="font-bold">Important:</span> Dr. Hawley roasts the snack, not you. It’s jokes + glow‑up motivation, not shame.
                  </p>
                </div>

                <div className="p-4 rounded-2xl border-2 border-brand-orange bg-brand-orange/10">
                  <p className="font-comic text-brand-dark">
                    <span className="font-bold">Share challenge:</span> Post it to Stories/Reels or drop it in the group chat. See whose snack is most “cooked.”
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => setIsOpen(false)}
                  className="comic-btn w-full bg-brand-green text-white"
                >
                  GOT IT — LET’S GO
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

