import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "node:path";
import { fileURLToPath } from "node:url";

const frontendRoot = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, frontendRoot, ["VITE_", "VFK_"]);

  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        "@": path.resolve(frontendRoot, "src")
      }
    },
    server: {
      proxy: {
        "/api": {
          target: env.VFK_API_ORIGIN || "http://127.0.0.1:8000",
          changeOrigin: true
        }
      }
    }
  };
});
