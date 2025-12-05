/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Comic book palette
        'comic-cyan': '#00D4FF',
        'comic-magenta': '#FF3366',
        'comic-yellow': '#FFE135',
        'comic-coral': '#FF6B6B',
        'comic-mint': '#4ECDC4',
        'comic-navy': '#1A1A2E',
        'comic-cream': '#FFF8E7',
        'comic-bubble': '#FFFFFF',
      },
      fontFamily: {
        'display': ['Bangers', 'Impact', 'system-ui'],
        'body': ['Nunito', 'system-ui', 'sans-serif'],
        'comic': ['Comic Neue', 'Comic Sans MS', 'cursive'],
      },
      boxShadow: {
        'comic': '4px 4px 0px 0px #1A1A2E',
        'comic-lg': '6px 6px 0px 0px #1A1A2E',
        'comic-xl': '8px 8px 0px 0px #1A1A2E',
        'bubble': '3px 3px 0px 0px rgba(0,0,0,0.2)',
      },
      animation: {
        'bounce-slow': 'bounce 2s infinite',
        'wiggle': 'wiggle 0.5s ease-in-out infinite',
        'pop': 'pop 0.3s ease-out',
        'float': 'float 3s ease-in-out infinite',
        'scan': 'scan 2s ease-in-out infinite',
        'burst': 'burst 0.6s ease-out forwards',
      },
      keyframes: {
        wiggle: {
          '0%, 100%': { transform: 'rotate(-3deg)' },
          '50%': { transform: 'rotate(3deg)' },
        },
        pop: {
          '0%': { transform: 'scale(0)', opacity: '0' },
          '80%': { transform: 'scale(1.1)' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        scan: {
          '0%, 100%': { transform: 'translateY(0)', opacity: '1' },
          '50%': { transform: 'translateY(100%)', opacity: '0.5' },
        },
        burst: {
          '0%': { transform: 'scale(0) rotate(0deg)', opacity: '1' },
          '100%': { transform: 'scale(1.5) rotate(15deg)', opacity: '0' },
        },
      },
      backgroundImage: {
        'halftone': 'radial-gradient(circle, #1A1A2E 1px, transparent 1px)',
        'dots': 'radial-gradient(circle, currentColor 2px, transparent 2px)',
        'comic-burst': 'conic-gradient(from 0deg, #FFE135 0deg, #FF6B6B 60deg, #FFE135 120deg, #FF6B6B 180deg, #FFE135 240deg, #FF6B6B 300deg, #FFE135 360deg)',
      },
    },
  },
  plugins: [],
};
