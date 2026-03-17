/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'brand-gold': '#F59E0B',
        'brand-green': '#10B981',
        'brand-blue': '#3B82F6',
        'bg-dark': '#0B0E11',
        'card-dark': 'rgba(23, 27, 34, 0.8)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    },
  },
  plugins: [],
}
