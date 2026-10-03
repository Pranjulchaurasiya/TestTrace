/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: "#f8fafc",
        card: "#ffffff",
        border: "#e2e8f0",
        slate: {
          900: "#0f172a",
          800: "#1e293b",
          700: "#334155",
          600: "#475569",
          500: "#64748b",
          200: "#e2e8f0",
          100: "#f1f5f9",
          50: "#f8fafc",
        },
        primary: {
          DEFAULT: "#4f46e5",
          hover: "#4338ca",
          light: "#eef2ff",
        },
        success: {
          DEFAULT: "#10b981",
          light: "#ecfdf5",
          border: "#a7f3d0",
        },
        warning: {
          DEFAULT: "#f59e0b",
          light: "#fffbeb",
          border: "#fde68a",
        },
        danger: {
          DEFAULT: "#ef4444",
          light: "#fef2f2",
          border: "#fecaca",
        },
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["JetBrains Mono", "SFMono-Regular", "Menlo", "Monaco", "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
};
