'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';

interface ComicData {
  comic_portrait_uri: string;
  reel_cover_uri: string | null;
}

interface ComicDisplayProps {
  comicData: ComicData;
  onReset: () => void;
}

type FormatType = 'portrait' | 'reel';

export default function ComicDisplay({ comicData, onReset }: ComicDisplayProps) {
  const [selectedFormat, setSelectedFormat] = useState<FormatType>('reel');
  const [isDownloading, setIsDownloading] = useState(false);

  const formats: { key: FormatType; label: string; emoji: string; uri: string | null }[] = [
    { key: 'reel', label: 'Reel', emoji: '🎬', uri: comicData.reel_cover_uri },
    { key: 'portrait', label: 'Story', emoji: '📱', uri: comicData.comic_portrait_uri },
  ];

  const currentFormat = formats.find(f => f.key === selectedFormat);
  const imageUrl = currentFormat?.uri || null;

  const handleDownload = async () => {
    if (!imageUrl) return;

    setIsDownloading(true);
    try {
      const response = await fetch(imageUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `snackswap-comic-${selectedFormat}.png`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
    }
    setIsDownloading(false);
  };

  const handleShare = async () => {
    if (!imageUrl || !navigator.share) return;

    try {
      const response = await fetch(imageUrl);
      const blob = await response.blob();
      const file = new File([blob], 'snackswap-comic.png', { type: 'image/png' });

      await navigator.share({
        title: 'My SnackSwap Comic!',
        text: 'Check out my dental health comic!',
        files: [file],
      });
    } catch (error) {
      console.error('Share failed:', error);
    }
  };

  // Platform-specific share helper
  const shareToPlatform = async (url: string, text: string) => {
    if (!url || !navigator.share) return;
    try {
      const response = await fetch(url);
      const blob = await response.blob();
      const file = new File([blob], 'snackswap-comic.png', { type: 'image/png' });
      await navigator.share({
        title: 'My SnackSwap Comic!',
        text,
        files: [file],
      });
    } catch (error) {
      if ((error as Error).name !== 'AbortError') {
        console.error('Share failed:', error);
      }
    }
  };

  const handleInstagramShare = async () => {
    // Use portrait format for Instagram Stories
    const url = comicData.comic_portrait_uri;
    await shareToPlatform(url, 'Check out my dental health comic! 🦷✨ #DentalHealth #KidsHealth');
  };

  const handleTikTokShare = async () => {
    // Use reel format for TikTok
    const url = comicData.reel_cover_uri || comicData.comic_portrait_uri;
    await shareToPlatform(url, 'My SnackSwap dental health comic! 🦷🎬 #DentalHealth #KidsHealth #SnackSwap');
  };

  return (
    <div className="space-y-6">
      {/* TA-DA! Header */}
      <motion.div
        className="text-center"
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: 'spring', bounce: 0.5 }}
      >
        <motion.h2
          className="font-display text-5xl text-brand-orange action-word inline-block relative"
          style={{
            textShadow: `
              3px 3px 0 var(--brand-green),
              6px 6px 0 var(--brand-blue)
            `,
          }}
          animate={{ rotate: [-1, 1, -1] }}
          transition={{ duration: 0.6, repeat: 2 }}
        >
          TA-DA!
          {/* Sparkles */}
          <motion.span
            className="absolute -top-4 -left-4 text-3xl"
            animate={{ rotate: [0, 360], scale: [1, 1.2, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            ✨
          </motion.span>
          <motion.span
            className="absolute -top-2 -right-6 text-2xl"
            animate={{ rotate: [0, -360], scale: [1, 1.3, 1] }}
            transition={{ duration: 2.5, repeat: Infinity, delay: 0.3 }}
          >
            ⭐
          </motion.span>
        </motion.h2>
      </motion.div>

      {/* Format selector */}
      <motion.div
        className="flex justify-center gap-2"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        {formats.map((format) => (
          <motion.button
            key={format.key}
            onClick={() => setSelectedFormat(format.key)}
            disabled={!format.uri}
            className={`
              px-4 py-2 rounded-full font-comic text-sm border-3 border-brand-dark
              transition-all
              ${selectedFormat === format.key
                ? 'bg-brand-blue text-white shadow-comic'
                : 'bg-white hover:bg-brand-subtle'
              }
              ${!format.uri ? 'opacity-40 cursor-not-allowed' : ''}
            `}
            whileHover={format.uri ? { scale: 1.05 } : {}}
            whileTap={format.uri ? { scale: 0.95 } : {}}
          >
            {format.emoji} {format.label}
          </motion.button>
        ))}
      </motion.div>

      {/* Comic display with panel animation */}
      <motion.div
        className="comic-border bg-white p-4 overflow-hidden"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.4, type: 'spring' }}
      >
        {imageUrl ? (
          <motion.div
            className="relative"
            key={selectedFormat}
            initial={{ clipPath: 'inset(0 100% 0 0)' }}
            animate={{ clipPath: 'inset(0 0 0 0)' }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
          >
            <img
              src={imageUrl}
              alt="Your SnackSwap Comic"
              className="w-full rounded-lg"
            />

            {/* Corner decorations */}
            <div className="absolute top-2 left-2 text-xl">🦷</div>
            <div className="absolute top-2 right-2 text-xl">⭐</div>
            <div className="absolute bottom-2 left-2 text-xl">✨</div>
            <div className="absolute bottom-2 right-2 text-xl">🎨</div>
          </motion.div>
        ) : (
          <div className="h-64 flex items-center justify-center text-gray-400 font-comic">
            This format is not available
          </div>
        )}
      </motion.div>

      {/* Action buttons */}
      <motion.div
        className="space-y-3"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
      >
        {/* Download button */}
        <button
          onClick={handleDownload}
          disabled={!imageUrl || isDownloading}
          className="comic-btn w-full bg-brand-green text-white disabled:opacity-50"
        >
          <span className="flex items-center justify-center gap-2">
            <span>{isDownloading ? '⏳' : '📥'}</span>
            {isDownloading ? 'DOWNLOADING...' : 'DOWNLOAD COMIC'}
          </span>
        </button>

        {/* Social share buttons (if supported) */}
        {typeof navigator !== 'undefined' && navigator.share && (
          <div className="flex flex-col gap-2">
            <motion.button
              onClick={handleInstagramShare}
              disabled={!comicData.comic_portrait_uri}
              className="comic-btn w-full py-3 px-6 text-white font-bold disabled:opacity-50"
              style={{ background: 'linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888)' }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <span className="flex items-center justify-center gap-2">
                <span>📸</span> SHARE TO INSTAGRAM
              </span>
            </motion.button>
            <motion.button
              onClick={handleTikTokShare}
              disabled={!comicData.reel_cover_uri && !comicData.comic_portrait_uri}
              className="comic-btn w-full py-3 px-6 text-white font-bold bg-black disabled:opacity-50"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <span className="flex items-center justify-center gap-2">
                <span>🎵</span> SHARE TO TIKTOK
              </span>
            </motion.button>
          </div>
        )}

        {/* Try again button */}
        <button
          onClick={onReset}
          className="comic-btn w-full bg-white text-brand-dark"
        >
          <span className="flex items-center justify-center gap-2">
            <span>📸</span> MAKE ANOTHER COMIC
          </span>
        </button>
      </motion.div>

      {/* Fun footer message */}
      <motion.div
        className="text-center p-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
      >
        <p className="font-comic text-sm text-brand-mid">
          Remember to brush twice a day! 🦷✨
        </p>
      </motion.div>
    </div>
  );
}
