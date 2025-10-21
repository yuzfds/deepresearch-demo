import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import tailwindcss from "@tailwindcss/vite";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: "/app/",
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    proxy: {
      // Proxy API requests to the LangGraph server
      "/api": {
          target: "http://127.0.0.1:8123", // LangGraph server with custom FastAPI app
          changeOrigin: true,
        },
      // Proxy LangGraph API requests
      "/threads": {
          target: "http://127.0.0.1:8123", // LangGraph server
          changeOrigin: true,
        },
      "/assistants": {
          target: "http://127.0.0.1:8123", // LangGraph server
          changeOrigin: true,
        },
      "/runs": {
          target: "http://127.0.0.1:8123", // LangGraph server
          changeOrigin: true,
        },
      },
    },
  });

