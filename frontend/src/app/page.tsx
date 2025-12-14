'use client';

import { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Header from '@/components/Header';
import UploadZone from '@/components/UploadZone';
import AgeSelector from '@/components/AgeSelector';
import AllergenSelector from '@/components/AllergenSelector';
import ScanningOverlay from '@/components/ScanningOverlay';
import ResultsPanel from '@/components/ResultsPanel';
import ComicDisplay from '@/components/ComicDisplay';
import ToothMascot from '@/components/ToothMascot';
import { usePreferences } from '@/hooks/usePreferences';

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
  comic_portrait_uri: string;
  reel_cover_uri: string | null;
}

export default function Home() {
  const [state, setState] = useState<AppState>('idle');
  const { age, allergens, mode: intensityMode, setAge, setAllergens, isLoaded } = usePreferences();
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [photoId, setPhotoId] = useState<string | null>(null);
  const [detectedItems, setDetectedItems] = useState<DetectedItem[]>([]);
  const [scoredItems, setScoredItems] = useState<ScoredItem[]>([]);
  const [facts, setFacts] = useState<any[]>([]);
  const [swaps, setSwaps] = useState<any[]>([]);
  const [comicData, setComicData] = useState<ComicData | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [comicMode, setComicMode] = useState<ComicMode>('educate');
  const [averageRisk, setAverageRisk] = useState(0);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const steps = [
    { label: 'Uploading', icon: '📤' },
    { label: 'Scanning snack', icon: '🔍' },
    { label: 'Checking aesthetic threat', icon: '💀' },
    { label: 'Writing vanity roast', icon: '🔥' },
    { label: 'Creating glow up comic', icon: '🎨' },
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

      // Step 3: Score and retrieve facts (now with allergens)
      setCurrentStep(2);

      const scoreRes = await fetch('/api/score/retrieve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          items: visionData.items,
          age: age,
          allergies: allergens,
        }),
      });

      if (!scoreRes.ok) throw new Error('Failed to calculate risk');
      const scoreData = await scoreRes.json();
      setScoredItems(scoreData.scored_items);
      setFacts(scoreData.facts);
      setSwaps(scoreData.swaps);
      setComicMode(scoreData.mode || 'educate');
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
          style_id: intensityMode === 'Savage' ? 'savage_teen' : 'spicy_tween',
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
  }, [age, allergens, intensityMode]);

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
    setComicMode('educate');
    setAverageRisk(0);
  };

  const viewComic = () => {
    setState('comic');
  };

  // Get DR. HAWLEY's message based on state and mode - VANITY FOCUSED
  const getDrHawleyMessage = () => {
    if (state === 'idle') {
      return intensityMode === 'Savage'
        ? "Yo. Dr. Hawley here. Show me your snack and I'll tell you if it's gonna cook your smile or give you that glow up."
        : "Hey! Dr. Hawley here. Drop your snack and let's see if it's aesthetic or gonna turn your teeth yellow!";
    }
    if (state === 'uploading') return "Uploading... hold up.";
    if (state === 'scanning') return "Scanning for aesthetic threats... 👀";
    if (state === 'results' && comicMode === 'celebrate') {
      return intensityMode === 'Savage'
        ? "Sheesh! This snack is a natural glow up. Your smile stays pristine. No filter needed."
        : "Yooo this snack keeps your teeth WHITE! Glow up approved!";
    }
    if (state === 'results' && comicMode === 'educate') {
      return intensityMode === 'Savage'
        ? "Bro... this snack is gonna cook your smile. Yellow teeth incoming. Not aesthetic."
        : "Hmm... this snack might stain your teeth. Let me show you why it's not aesthetic.";
    }
    if (state === 'results' && comicMode === 'unknown') {
      return "Couldn't ID that snack, but here's some glow up secrets for your smile.";
    }
    if (state === 'comic' && comicMode === 'celebrate') {
      return "Check out this glow up comic I made for you! 10/10 aura.";
    }
    if (state === 'comic') {
      return "Peep this comic I made. Your friends need to see why their smile is cooked.";
    }
    return "...";
  };

  // Don't render until preferences are loaded from localStorage
  if (!isLoaded) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-white">
        <div className="text-gray-800 text-xl font-comic">Loading...</div>
      </main>
    );
  }

  return (
    <main className="min-h-screen pb-20 bg-white">
      <Header />

      <div className="container mx-auto px-4 max-w-4xl pt-12">
        {/* Mascot & Greeting - Centered Hero */}
        <div className="flex flex-col md:flex-row items-center justify-center gap-8 mb-12">
          <ToothMascot state={state} />
          <motion.div
            className="speech-bubble max-w-xs md:max-w-md shadow-lg bg-white/95 backdrop-blur"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            key={state + comicMode}
          >
            <p className="font-bold text-lg text-gray-800">
              {getDrHawleyMessage()}
            </p>
            <p className="text-xs text-gray-500 mt-1 font-comic">
              {intensityMode} Mode {intensityMode === 'Savage' ? '💀' : '🔥'}
            </p>
          </motion.div>
        </div>

        {/* Error display */}
        <AnimatePresence>
          {error && (
            <motion.div
              className="bg-red-900/50 text-red-200 p-4 mb-6 rounded-2xl border-2 border-red-500/50 flex items-center gap-4 shadow-sm backdrop-blur"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <span className="text-2xl">💀</span>
              <div>
                <p className="font-bold">Bruh...</p>
                <p>{error}</p>
                <button
                  onClick={handleReset}
                  className="mt-1 underline font-bold hover:text-red-100"
                >
                  Try again
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main Content Card */}
        <div className="bg-white/95 backdrop-blur rounded-3xl p-6 md:p-10 relative overflow-hidden transition-all duration-300 shadow-2xl border-4 border-gray-800">
          <AnimatePresence mode="wait">
            {(state === 'idle' || state === 'uploading') && (
              <motion.div
                key="upload"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="space-y-6"
              >
                <UploadZone
                  onFileSelect={handleFileSelect}
                  previewUrl={previewUrl}
                  isUploading={state === 'uploading'}
                />

                <div className="flex flex-col items-center gap-2">
                  <AgeSelector age={age} onAgeChange={setAge} />
                  <AllergenSelector
                    selectedAllergens={allergens}
                    onAllergensChange={setAllergens}
                  />
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
                  mode={comicMode}
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

        <footer className="mt-8 flex flex-col items-center gap-4">
          <p className="text-center text-gray-500 text-sm font-body">
            Powered by DeepMind (Gemini & Nano Banana) & Qdrant & Freepik • Roast My Snack 2025 • Your Smile's Glow Up Starts Here
          </p>
          <a
            href="https://www.poppykidsdental.com"
            target="_blank"
            rel="noopener noreferrer"
            className="transition-transform hover:scale-105"
          >
            <img
              src="/images/poppykids_logo.png"
              alt="Poppy Kids Pediatric Dentistry"
              className="h-12 w-auto"
            />
          </a>
        </footer>
      </div>
    </main>
  );
}
