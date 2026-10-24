// tools/make-normals.ts: a rough normal map from each image's brightness (GDD 7.9). Hand-painted
// normals for final hero sprites replace these files directly.
import { readFileSync, writeFileSync } from "node:fs";
import { inflateSync } from "node:zlib";
import type { Manifest } from "../src/content/types";
import { Img, readPng } from "./pixel";

const root = new URL("../", import.meta.url);
const manifest = JSON.parse(readFileSync(new URL("assets/manifest.json", root), "utf8")) as Manifest;
let n = 0;
for (const e of manifest.images) {
  if (!e.normal || e.status === "final") continue;
  const src = readPng(readFileSync(new URL(`assets/${e.path}`, root)), inflateSync);
  const lum = (x: number, y: number) => {
    const c = src.get(Math.max(0, Math.min(src.w - 1, x)), Math.max(0, Math.min(src.h - 1, y)));
    return c[3] ? (0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]) / 255 : 0;
  };
  const out = new Img(src.w, src.h);
  for (let y = 0; y < src.h; y++)
    for (let x = 0; x < src.w; x++) {
      const a = src.get(x, y)[3];
      if (!a) continue;
      const dx = (lum(x + 1, y) - lum(x - 1, y)) * 2;
      const dy = (lum(x, y + 1) - lum(x, y - 1)) * 2;
      const len = Math.hypot(dx, dy, 1);
      out.px(x, y, [Math.round(((-dx / len) * 0.5 + 0.5) * 255), Math.round(((dy / len) * 0.5 + 0.5) * 255), Math.round((1 / len) * 255), a]);
    }
  writeFileSync(new URL(`assets/${e.normal}`, root), out.png());
  n++;
}
console.log(`${n} normal maps written`);
