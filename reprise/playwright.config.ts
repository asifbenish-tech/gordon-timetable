import { defineConfig } from "@playwright/test";

const PORT = 4174;

export default defineConfig({
  testDir: "tests/e2e",
  timeout: 20 * 60_000,
  fullyParallel: true,
  // One page at a time: the bot plays at 4x tempo on the real AudioContext, and parallel
  // headless pages starve each other of audio time on small machines.
  workers: Number(process.env.BOT_WORKERS ?? 1),
  reporter: [["list"]],
  use: {
    baseURL: `http://localhost:${PORT}`,
    viewport: { width: 1280, height: 720 },
    launchOptions: { args: ["--autoplay-policy=no-user-gesture-required", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] },
  },
  webServer: {
    command: `npm run build:bot && npx vite preview --outDir dist-bot --port ${PORT} --strictPort`,
    port: PORT,
    reuseExistingServer: true,
    timeout: 180_000,
  },
});
