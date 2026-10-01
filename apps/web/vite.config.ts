import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The Python control service serves the built bundle from apps/web/dist and the JSON API under /api.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://127.0.0.1:8765", changeOrigin: false },
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
    sourcemap: false,
  },
});
