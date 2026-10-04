/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eef5fb', 100: '#d6e6f4', 200: '#aecde9', 300: '#7aaed9', 400: '#4a8bc2',
          500: '#2a6fa8', 600: '#1e5a8c', 700: '#194a73', 800: '#173e5f', 900: '#14324d',
        },
      },
      fontFamily: {
        sans: ['system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
