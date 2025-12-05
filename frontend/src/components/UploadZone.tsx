'use client';

import { useState, useCallback, useRef } from 'react';
import { motion } from 'framer-motion';

interface UploadZoneProps {
  onFileSelect: (file: File) => void;
  previewUrl: string | null;
  isUploading: boolean;
}

export default function UploadZone({ onFileSelect, previewUrl, isUploading }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      onFileSelect(file);
    }
  }, [onFileSelect]);

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onFileSelect(file);
    }
  }, [onFileSelect]);

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <motion.div
      className={`
        comic-border bg-white p-6 cursor-pointer
        transition-all duration-200
        ${isDragging ? 'bg-comic-cyan/10 scale-[1.02]' : ''}
        ${isUploading ? 'pointer-events-none' : ''}
      `}
      onClick={handleClick}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      whileHover={{ scale: isUploading ? 1 : 1.01 }}
      whileTap={{ scale: isUploading ? 1 : 0.99 }}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        onChange={handleFileChange}
        className="hidden"
        disabled={isUploading}
      />

      {previewUrl ? (
        <div className="relative">
          <img
            src={previewUrl}
            alt="Snack preview"
            className="w-full max-h-64 object-contain rounded-lg"
          />
          {isUploading && (
            <motion.div
              className="absolute inset-0 bg-brand-dark/50 rounded-lg flex items-center justify-center"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              <div className="loading-dots flex gap-2">
                <span className="w-4 h-4 bg-brand-green rounded-full" />
                <span className="w-4 h-4 bg-brand-orange rounded-full" />
                <span className="w-4 h-4 bg-brand-blue rounded-full" />
              </div>
            </motion.div>
          )}
        </div>
      ) : (
        <div className="text-center py-8">
          {/* Camera icon with refined style */}
          <motion.div
            className="inline-block mb-4"
            animate={{ y: [0, -6, 0] }}
            transition={{ duration: 2.5, repeat: Infinity, ease: 'easeInOut' }}
          >
            <div className="relative">
              <div className="w-24 h-20 bg-brand-dark rounded-xl flex items-center justify-center">
                <div className="w-12 h-12 bg-brand-blue rounded-full border-4 border-white" />
              </div>
              {/* Flash */}
              <motion.div
                className="absolute -top-2 -right-2 w-6 h-6 bg-brand-green rounded-full"
                animate={{ scale: [1, 1.15, 1], opacity: [0.8, 1, 0.8] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              />
            </div>
          </motion.div>

          <h3 className="font-display text-2xl text-brand-dark mb-2">
            SNAP YOUR SNACK!
          </h3>
          <p className="font-comic text-brand-mid mb-4">
            Tap to take a photo or drag & drop an image
          </p>

          {/* Visual cue arrows */}
          <div className="flex justify-center gap-4 text-brand-orange opacity-60">
            <motion.span
              animate={{ y: [0, 4, 0] }}
              transition={{ duration: 1.2, repeat: Infinity, delay: 0 }}
            >
              ↓
            </motion.span>
            <motion.span
              animate={{ y: [0, 4, 0] }}
              transition={{ duration: 1.2, repeat: Infinity, delay: 0.2 }}
            >
              ↓
            </motion.span>
            <motion.span
              animate={{ y: [0, 4, 0] }}
              transition={{ duration: 1.2, repeat: Infinity, delay: 0.4 }}
            >
              ↓
            </motion.span>
          </div>
        </div>
      )}
    </motion.div>
  );
}
