// tools/make-placeholders.ts: writes every manifest image at its exact size (GDD 7.9).
// Final art replaces one file and flips its status; this script never overwrites "final" or "generated".
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";
import type { Manifest } from "../src/content/types";
import { draw } from "./recipes";
import { Img } from "./pixel";

const root = new URL("../", import.meta.url);
const manifest = JSON.parse(readFileSync(new URL("assets/manifest.json", root), "utf8")) as Manifest;
let n = 0;
for (const img of manifest.images) {
  if (img.status !== "placeholder") continue;
  const out = draw(img.recipe, img.w, img.h, img.frames);
  const file = new URL(`assets/${img.path}`, root);
  mkdirSync(dirname(file.pathname), { recursive: true });
  writeFileSync(file, out.png());
  n++;
}
// the app icon for the web manifest (installable, GDD 9.9)
const icon = new Img(192, 192);
icon.gradient(0, 0, 192, 192, "#1d1450", "#6b5ab0", 6);
icon.circle(96, 96, 60, "#0d0b14");
icon.circle(96, 96, 54, "#c9b8ff");
icon.circle(96, 96, 46, "#1d1450");
for (let i = 0; i < 8; i++) icon.circle(96 + Math.cos((i / 8) * Math.PI * 2) * 30, 96 + Math.sin((i / 8) * Math.PI * 2) * 30, 6, ["#e05a4f", "#f08c3a", "#efc94c", "#6cc070", "#4fb3c8", "#5b7be0", "#9a6ad6", "#ece8f6"][i]);
icon.circle(96, 96, 10, "#f3c64b");
mkdirSync(new URL("public/", root).pathname, { recursive: true });
writeFileSync(new URL("public/icon.png", root), icon.png());
console.log(`${n} placeholder images written`);
