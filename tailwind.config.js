/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: { extend: { colors: { navy: { 950: "#070d1a", 900: "#0b1426", 800: "#111d36", 700: "#1b2b4d" }, accent: "#2dd4bf" } } },
  plugins: [],
};
