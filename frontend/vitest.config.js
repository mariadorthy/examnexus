import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],

  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.js"],
    include: ["src/test/**/*.test.{js,jsx}"],

    clearMocks: true,
    restoreMocks: true,
    mockReset: true,

    // Admin pages mount ~10 child components + fire 2–3 fetches;
    // jsdom is slow. 5s (default) is too tight.
    testTimeout: 15000,
    hookTimeout: 15000,
    // Keep per-file isolation so window.location.hash,
    // localStorage and mocks do not leak between test files.
    // Use vmThreads to share one jsdom per worker while
    // preserving isolation. (Previously created jsdom 9 times.)
    pool: "vmThreads",
    
    reporters: ["default"],
  },
});