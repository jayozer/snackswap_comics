'use client';

import { motion } from 'framer-motion';
import Image from 'next/image';

export default function Header() {
  return (
    <header className="sticky top-0 z-50 bg-white shadow-sm">
      <div className="container mx-auto px-4 max-w-5xl h-44 flex justify-center items-center">
        {/* App Logo - Centered (Primary branding) */}
        <motion.div
          className="flex items-center"
          whileHover={{ scale: 1.02 }}
        >
          <Image
            src="/images/roast_my_snack_logo.png"
            alt="Roast My Snack - Your Smile's Drip Starts Here"
            width={512}
            height={512}
            className="h-40 w-40"
            priority
          />
        </motion.div>
      </div>
    </header>
  );
}
