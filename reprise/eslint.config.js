import js from "@eslint/js";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist", "dist-bot", "node_modules", "test-results", "playwright-report", "public/sw.js"] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    rules: {
      "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_", varsIgnorePattern: "^_" }],
      "no-restricted-globals": ["error", { name: "setInterval", message: "The AudioContext is the only clock (GDD 9.3)." }],
    },
  },
  {
    // the bot drives the page through window.__reprise, which has no static type on that side
    files: ["tests/e2e/**"],
    rules: { "@typescript-eslint/no-explicit-any": "off" },
  },
  {
    files: ["src/audio/**", "src/core/**"],
    rules: {
      "no-restricted-globals": ["error",
        { name: "setTimeout", message: "The AudioContext is the only clock (GDD 9.3)." },
        { name: "setInterval", message: "The AudioContext is the only clock (GDD 9.3)." }],
    },
  },
);
