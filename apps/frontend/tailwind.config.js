/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html','./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        jp: ['\"Noto Sans JP\"', 'sans-serif'],
      },
    },
  },
  plugins: [],
};