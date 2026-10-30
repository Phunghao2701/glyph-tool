import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "node:path";
import { fileURLToPath } from "node:url";

const frontendRoot = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(frontendRoot, "src")
    }
  },
  server: {
    proxy: {
      "/api": {
        target: process.env.VFK_API_ORIGIN || "http://127.0.0.1:8000",
        changeOrigin: true
      }
    }
  }
});
