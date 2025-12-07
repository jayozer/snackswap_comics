/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Anthropic Brand Colors
        'brand': {
          dark: '#141413',
          light: '#faf9f5',
          mid: '#b0aea5',
          subtle: '#e8e6dc',
          orange: '#d97757',
          blue: '#6a9bcc',
          green: '#788c5d',
        },
        // Legacy aliases for gradual migration
        'poppy': {
          DEFAULT: '#d97757',
          teal: '#6a9bcc',
          yellow: '#788c5d',
          navy: '#141413',
          cream: '#faf9f5',
        },
        'comic': {
          cyan: '#6a9bcc',
          magenta: '#d97757',
          yellow: '#788c5d',
          coral: '#d97757',
          mint: '#6a9bcc',
          navy: '#141413',
          cream: '#faf9f5',
        },
        'comic-bubble': '#FFFFFF',
      },
      fontFamily: {
        'display': ['Poppins', 'Arial', 'system-ui', 'sans-serif'],
        'body': ['Lora', 'Georgia', 'serif'],
        'comic': ['Comic Neue', 'Comic Sans MS', 'cursive'],
      },
      boxShadow: {
        'comic': '4px 4px 0px 0px #141413',
        'comic-lg': '6px 6px 0px 0px #141413',
        'comic-xl': '8px 8px 0px 0px #141413',
        'bubble': '3px 3px 0px 0px rgba(0,0,0,0.15)',
      },
      animation: {
        'pop': 'pop 0.3s ease-out',
        'float': 'float 3s ease-in-out infinite',
        'scan': 'scan 2s ease-in-out infinite',
      },
      keyframes: {
        pop: {
          '0%': { transform: 'scale(0)', opacity: '0' },
          '80%': { transform: 'scale(1.05)' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-6px)' },
        },
        scan: {
          '0%, 100%': { transform: 'translateY(0)', opacity: '1' },
          '50%': { transform: 'translateY(100%)', opacity: '0.5' },
        },
      },
      backgroundImage: {
        'halftone': 'radial-gradient(circle, #141413 1px, transparent 1px)',
        'dots': 'radial-gradient(circle, currentColor 2px, transparent 2px)',
        'comic-burst': 'conic-gradient(from 0deg, #788c5d 0deg, #d97757 60deg, #788c5d 120deg, #d97757 180deg, #788c5d 240deg, #d97757 300deg, #788c5d 360deg)',
      },
    },
  },
  plugins: [],
};
