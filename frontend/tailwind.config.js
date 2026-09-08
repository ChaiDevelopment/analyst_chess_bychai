/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Fraunces"', 'ui-serif', 'Georgia', 'serif'],
        sans: ['"Inter"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      colors: {
        // Deep slate/charcoal base, evoking a dim analysis room, not pure black.
        ink: {
          950: '#0D0F12',
          900: '#14171B',
          800: '#1B1F24',
          700: '#262B32',
          600: '#333A42',
          500: '#4A525C',
          400: '#6B7480',
          200: '#B8BFC7',
          100: '#DDE1E5',
          50: '#F1F3F5',
        },
        // Warm brass/gold accent - brass chess-clock and trophy tones,
        // deliberately not the terracotta/orange default.
        brass: {
          400: '#E3C878',
          500: '#C9A227',
          600: '#A9840F',
        },
        // Board tones for the review board itself.
        board: {
          light: '#EDE3CC',
          dark: '#6B5A45',
        },
        // Evaluation semantics
        good: '#5FA37A',
        bad: '#C4574A',
        brilliant: '#4FA8C9',
      },
      boxShadow: {
        panel: '0 1px 0 0 rgba(255,255,255,0.04) inset',
      },
    },
  },
  plugins: [],
}
