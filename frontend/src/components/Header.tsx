'use client';

import { motion } from 'framer-motion';

export default function Header() {
  return (
    <header className="sticky top-0 z-50 bg-poppy-cream/80 backdrop-blur-md border-b-2 border-poppy-teal/20">
      <div className="container mx-auto px-4 max-w-5xl h-16 flex justify-between items-center">
        <motion.div
          className="flex items-center gap-3"
          whileHover={{ scale: 1.02 }}
        >
          <div className="w-10 h-10 bg-poppy-red rounded-full flex items-center justify-center text-white font-black text-xl shadow-md border-2 border-white">
            P
          </div>
          <h1 className="text-2xl font-black tracking-tight text-poppy-navy">
            SnackSwap <span className="text-poppy-red">Comics</span>
          </h1>
        </motion.div>

        <div className="hidden sm:flex items-center gap-6 font-bold text-sm text-poppy-navy/70">
          <a href="#" className="hover:text-poppy-red transition-colors">How it Works</a>
          <a href="https://www.poppykidsdental.com" target="_blank" className="hover:text-poppy-red transition-colors">Poppy Kids Dental</a>
        </div>
      </div>
    </header>
  );
}
