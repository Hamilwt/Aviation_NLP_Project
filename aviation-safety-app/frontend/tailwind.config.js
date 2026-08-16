/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cream: {
          50: '#FFFDF9',
          100: '#FFF8F0',
          200: '#F5E6D3',
          300: '#ECD9BF',
          400: '#D9C5B2',
          500: '#C9B099',
        },
        brown: {
          50: '#F5F0EB',
          100: '#E8DDD4',
          200: '#D1B8A9',
          300: '#B9947E',
          400: '#A67C63',
          500: '#8B6B4D',
          600: '#73563E',
          700: '#5C4033',
          800: '#4A352A',
          900: '#3E2F1F',
        },
        teal: {
          50: '#F0FDFA',
          100: '#CCFBF1',
          200: '#99F6E4',
          300: '#5EEAD4',
          400: '#2DD4BF',
          500: '#14B8A6',
          600: '#0D9488',
          700: '#0F766E',
          800: '#115E59',
          900: '#134E4A',
        },
        risk: {
          critical: '#EF4444',
          high: '#F97316',
          medium: '#22C55E',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}