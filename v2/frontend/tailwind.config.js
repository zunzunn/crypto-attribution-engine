/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        slate: {
          850: '#131b2e',
          950: '#0a0e17',
        },
        entity: {
          vasp: '#3b82f6',
          mixer: '#ef4444',
          bridge: '#f59e0b',
          scam: '#a855f7',
          unknown: '#64748b',
        }
      }
    },
  },
  plugins: [],
}
