import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Build output goes to web/dist, which FastAPI serves in production.
// In dev, /api is proxied to the local uvicorn process so the frontend never
// needs to know the backend host (and never sees a secret).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: false,
  },
  // TODO: add a Vitest `test` block when component tests are written.
});
