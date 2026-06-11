/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#FAFAFA",
        foreground: "#0A0A0A",
        border: "#E5E7EB",
      },
      fontFamily: {
        sans: ["Inter", "Geist Sans", "sans-serif"],
      },
    },
  },
  plugins: [],
};
