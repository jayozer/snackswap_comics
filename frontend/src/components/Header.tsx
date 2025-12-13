'use client';

import { motion } from 'framer-motion';
import Image from 'next/image';

export default function Header() {
  return (
    <header className="sticky top-0 z-50 bg-brand-light/80 backdrop-blur-md border-b-2 border-brand-blue/20">
      <div className="container mx-auto px-4 max-w-5xl h-20 flex justify-between items-center">
        {/* App Logo - Left */}
        <motion.div
          className="flex items-center"
          whileHover={{ scale: 1.02 }}
        >
          <Image
            src="/images/roast_my_snack_logo.png"
            alt="Roast My Snack - Your Smile's Drip Starts Here"
            width={96}
            height={160}
            className="h-16 w-auto"
            priority
          />
        </motion.div>

        {/* Poppy Kids Logo - Right (clickable) */}
        <motion.a
          href="https://www.poppykidsdental.com"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center"
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.98 }}
        >
          <Image
            src="/images/poppykids_logo.png"
            alt="Poppy Kids Pediatric Dentistry"
            width={286}
            height={160}
            className="h-14 w-auto"
            priority
          />
        </motion.a>
      </div>
    </header>
  );
}
