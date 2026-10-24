import type { Config } from "tailwindcss";

// Minimal Tailwind setup for the scaffold. TODO: port the mockup's palette,
// spacing, and typography into `theme.extend` once the visual design is final.
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Risk bands are the only semantic colours in the UI.
        risk: {
          high: "#b91c1c",
          elevated: "#c2410c",
          moderate: "#a16207",
          low: "#475569",
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
