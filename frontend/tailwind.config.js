/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter var', 'Inter', 'system-ui', 'sans-serif'],
        display: ['Inter var', 'Inter', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1rem' }],
        'sm': ['0.875rem', { lineHeight: '1.25rem' }],
        'base': ['1rem', { lineHeight: '1.5rem' }],
        'lg': ['1.125rem', { lineHeight: '1.75rem' }],
        'xl': ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
      },
      colors: {
        primary: {
          50: '#fef7f0',
          100: '#feeee0',
          200: '#fcd9c1',
          300: '#f9be96',
          400: '#f59765',
          500: '#f2753f',
          600: '#e35a24',
          700: '#bc451a',
          800: '#96391c',
          900: '#8B1538', // Gannon maroon
          950: '#701226',
        },
        gannon: {
          maroon: '#8B1538',
          gold: '#FFD700',
          gray: {
            light: '#f8fafc',
            dark: '#1e293b',
          }
        }
      },
      fontWeight: {
        'light': '300',
        'normal': '400',
        'medium': '500',
        'semibold': '600',
        'bold': '700',
        'extrabold': '800',
      },
      letterSpacing: {
        tighter: '-0.05em',
        tight: '-0.025em',
        normal: '0em',
        wide: '0.025em',
        wider: '0.05em',
      }
    },
  },
  plugins: [],
};