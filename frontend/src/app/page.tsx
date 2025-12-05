'use client';

import { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Header from '@/components/Header';
import UploadZone from '@/components/UploadZone';
import AgeSelector from '@/components/AgeSelector';
import ScanningOverlay from '@/components/ScanningOverlay';
import ResultsPanel from '@/components/ResultsPanel';
import ComicDisplay from '@/components/ComicDisplay';
import ToothMascot from '@/components/ToothMascot';

type AppState = 'idle' | 'uploading' | 'scanning' | 'results' | 'comic';

interface DetectedItem {
  name: string;
  brand_guess: string | null;
  category: string;
  visible_clues: string;
  confidence: number;
}

interface ScoredItem {
  snack_id: string;
  name: string;
  category: string;
  dental_risk_score: number;
  confidence: number;
}

interface ComicData {
  comic_square_uri: string;
  comic_portrait_uri: string;
  reel_cover_uri: string | null;
}

export default function Home() {
  const [state, setState] = useState<AppState>('idle');
  const [age, setAge] = useState(7);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [photoId, setPhotoId] = useState<string | null>(null);
  const [detectedItems, setDetectedItems] = useState<DetectedItem[]>([]);
  const [scoredItems, setScoredItems] = useState<ScoredItem[]>([]);
  const [facts, setFacts] = useState<any[]>([]);
  const [swaps, setSwaps] = useState<any[]>([]);
  const [comicData, setComicData] = useState<ComicData | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const steps = [
    { label: 'Uploading', icon: '📤' },
    { label: 'Detecting snacks', icon: '🔍' },
    { label: 'Checking dental risk', icon: '🦷' },
    { label: 'Writing script', icon: '✍️' },
    { label: 'Drawing comic', icon: '🎨' },
  ];

  const handleFileSelect = useCallback(async (file: File) => {
    setError(null);
    setPreviewUrl(URL.createObjectURL(file));
    setState('uploading');
    setCurrentStep(0);

    try {
      // Step 1: Upload image
      const formData = new FormData();
      formData.append('file', file);

      const intakeRes = await fetch('/api/capture/intake', {
        method: 'POST',
        body: formData,
      });

      if (!intakeRes.ok) throw new Error('Failed to upload image');
      const intakeData = await intakeRes.json();
      setPhotoId(intakeData.photo_id);

      // Step 2: Vision detection
      setState('scanning');
      setCurrentStep(1);

      const visionRes = await fetch('/api/vision/detect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ photo_id: intakeData.photo_id }),
      });

      if (!visionRes.ok) throw new Error('Failed to detect snacks');
      const visionData = await visionRes.json();
      setDetectedItems(visionData.items);

      // Step 3: Score and retrieve facts
      setCurrentStep(2);

      const scoreRes = await fetch('/api/score/retrieve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          items: visionData.items,
          age: age,
          allergies: [],
        }),
      });

      if (!scoreRes.ok) throw new Error('Failed to calculate risk');
      const scoreData = await scoreRes.json();
      setScoredItems(scoreData.scored_items);
      setFacts(scoreData.facts);
      setSwaps(scoreData.swaps);

      // Step 4: Generate script
      setCurrentStep(3);

      const scriptRes = await fetch('/api/script/compose', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scored_items: scoreData.scored_items,
          facts: scoreData.facts,
          swaps: scoreData.swaps,
          style_id: 'default',
          age: age,
        }),
      });

      if (!scriptRes.ok) throw new Error('Failed to write script');
      const scriptData = await scriptRes.json();

      // Step 5: Render comic
      setCurrentStep(4);

      const renderRes = await fetch('/api/render/comic', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ script_id: scriptData.script_id }),
      });

      if (!renderRes.ok) throw new Error('Failed to render comic');
      const renderData = await renderRes.json();
      setComicData(renderData);

      setState('results');
    } catch (err: any) {
      setError(err.message || 'Something went wrong');
      setState('idle');
    }
  }, [age]);

  const handleReset = () => {
    setState('idle');
    setPreviewUrl(null);
    setPhotoId(null);
    setDetectedItems([]);
    setScoredItems([]);
    setFacts([]);
    setSwaps([]);
    setComicData(null);
    setCurrentStep(0);
    setError(null);
  };

  const viewComic = () => {
    setState('comic');
  };

  return (
    <main className="min-h-screen pb-20">
      <Header />

      <div className="container mx-auto px-4 max-w-2xl">
        {/* Mascot with speech bubble */}
        <div className="flex items-start gap-4 mb-8 mt-6">
          <ToothMascot state={state} />
          <motion.div
            className="speech-bubble flex-1"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            key={state}
          >
            <p className="font-comic text-lg">
              {state === 'idle' && "Hey there! Snap a pic of your snack and I'll turn it into a comic!"}
              {state === 'uploading' && "Ooh, let me take a look at that snack..."}
              {state === 'scanning' && "Using my super tooth vision to analyze this..."}
              {state === 'results' && "Wow! Check out what I found! Ready to see your comic?"}
              {state === 'comic' && "TA-DA! Your very own snack comic! Share it with friends!"}
            </p>
          </motion.div>
        </div>

        {/* Error display */}
        <AnimatePresence>
          {error && (
            <motion.div
              className="comic-border bg-comic-coral text-white p-4 mb-6"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
            >
              <p className="font-bold flex items-center gap-2">
                <span className="text-2xl">💥</span>
                OOPS! {error}
              </p>
              <button
                onClick={handleReset}
                className="mt-3 underline font-bold"
              >
                Try again
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main content based on state */}
        <AnimatePresence mode="wait">
          {(state === 'idle' || state === 'uploading') && (
            <motion.div
              key="upload"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <UploadZone
                onFileSelect={handleFileSelect}
                previewUrl={previewUrl}
                isUploading={state === 'uploading'}
              />

              <AgeSelector age={age} onAgeChange={setAge} />
            </motion.div>
          )}

          {state === 'scanning' && (
            <motion.div
              key="scanning"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
            >
              <ScanningOverlay
                previewUrl={previewUrl}
                currentStep={currentStep}
                steps={steps}
              />
            </motion.div>
          )}

          {state === 'results' && (
            <motion.div
              key="results"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <ResultsPanel
                scoredItems={scoredItems}
                facts={facts}
                swaps={swaps}
                onViewComic={viewComic}
                onReset={handleReset}
              />
            </motion.div>
          )}

          {state === 'comic' && comicData && (
            <motion.div
              key="comic"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
            >
              <ComicDisplay
                comicData={comicData}
                onReset={handleReset}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </main>
  );
}
