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
type ComicMode = 'educate' | 'celebrate' | 'unknown';

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
  const [mode, setMode] = useState<ComicMode>('educate');
  const [averageRisk, setAverageRisk] = useState(0);

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
      setMode(scoreData.mode || 'educate');
      setAverageRisk(scoreData.average_risk_score || 0);

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
          mode: scoreData.mode || 'educate',
        }),
      });

      if (!scriptRes.ok) throw new Error('Failed to write script');
      const scriptData = await scriptRes.json();

      // Step 5: Render comic (call backend directly to avoid proxy timeout)
      setCurrentStep(4);

      const renderRes = await fetch('http://localhost:8000/api/render/comic', {
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
    setMode('educate');
    setAverageRisk(0);
  };

  const viewComic = () => {
    setState('comic');
  };

  return (
    <main className="min-h-screen pb-20 bg-gradient-to-br from-brand-light to-white">
      <Header />

      <div className="container mx-auto px-4 max-w-4xl pt-12">
        {/* Mascot & Greeting - Centered Hero */}
        <div className="flex flex-col md:flex-row items-center justify-center gap-8 mb-12">
          <ToothMascot state={state} />
          <motion.div
            className="speech-bubble max-w-xs md:max-w-md shadow-lg"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            key={state}
          >
            <p className="font-bold text-lg text-brand-dark">
              {state === 'idle' && "Hi! I'm Poppy Tooth! Show me your snack and I'll tell you if it's tooth-friendly!"}
              {state === 'uploading' && "Ooh, uploading! Hang tight..."}
              {state === 'scanning' && "Let me take a closer look with my super specs..."}
              {state === 'results' && mode === 'celebrate' && "WOW! You picked an AMAZING tooth-friendly snack! High five!"}
              {state === 'results' && mode === 'educate' && "Done! I've got the scoop on your snack!"}
              {state === 'results' && mode === 'unknown' && "Hmm, I couldn't quite figure that one out. Let me share some tips!"}
              {state === 'comic' && mode === 'celebrate' && "Check out this celebration comic I made just for you!"}
              {state === 'comic' && mode !== 'celebrate' && "Check out this comic I made just for you!"}
            </p>
          </motion.div>
        </div>

        {/* Error display */}
        <AnimatePresence>
          {error && (
            <motion.div
              className="bg-red-50 text-red-600 p-4 mb-6 rounded-2xl border-2 border-red-100 flex items-center gap-4 shadow-sm"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <span className="text-2xl">🙊</span>
              <div>
                <p className="font-bold">Oops!</p>
                <p>{error}</p>
                <button
                  onClick={handleReset}
                  className="mt-1 underline font-bold hover:text-red-800"
                >
                  Try again
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main Content Card */}
        <div className="poppy-card p-6 md:p-10 relative overflow-hidden transition-all duration-300">
          <AnimatePresence mode="wait">
            {(state === 'idle' || state === 'uploading') && (
              <motion.div
                key="upload"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="space-y-8"
              >
                <UploadZone
                  onFileSelect={handleFileSelect}
                  previewUrl={previewUrl}
                  isUploading={state === 'uploading'}
                />

                <div className="flex justify-center">
                  <AgeSelector age={age} onAgeChange={setAge} />
                </div>
              </motion.div>
            )}

            {state === 'scanning' && (
              <motion.div
                key="scanning"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
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
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <ResultsPanel
                  scoredItems={scoredItems}
                  facts={facts}
                  swaps={swaps}
                  mode={mode}
                  averageRisk={averageRisk}
                  onViewComic={viewComic}
                  onReset={handleReset}
                />
              </motion.div>
            )}

            {state === 'comic' && comicData && (
              <motion.div
                key="comic"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <ComicDisplay
                  comicData={comicData}
                  onReset={handleReset}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <p className="text-center text-brand-mid text-sm mt-8 font-body">
          Powered by Gemini Vision & Qdrant • © 2025 Poppy Kids Dental
        </p>
      </div>
    </main>
  );
}
