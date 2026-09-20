import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const proxy = {
  "/api": "http://127.0.0.1:18000",
  "/health": "http://127.0.0.1:18000",
  "/ready": "http://127.0.0.1:18000",
};

export default defineConfig({
  plugins: [react()],
  server: { proxy },
  preview: {
    proxy,
    allowedHosts: ["ditzy-dares-evaporate.ngrok-free.dev"],
  },
});
