// tools/recipes.ts: placeholder drawings. Rooms are blocked in with flat shapes in the room's palette
// (GDD 7.3); characters are silhouettes of the right height and frame count, labelled with their ID.
import { readFileSync } from "node:fs";
import { Img, mix } from "./pixel";

type Rect = [number, number, number, number];
interface Hs { id: string; rect: Rect }
const room = (id: string): { hotspots: Hs[]; width: number } => JSON.parse(readFileSync(new URL(`../content/rooms/${id}.json`, import.meta.url), "utf8"));
const rectOf = (r: string, h: string): Rect => {
  const x = room(r).hotspots.find((s) => s.id === h);
  if (!x) throw new Error(`${r}.${h}`);
  return x.rect;
};

// ---- the colour script (GDD 7.3) ----
const PAL = {
  night: ["#0b0820", "#1d1450", "#3b2a7a", "#6b5ab0", "#c8c4e8"],
  dawn: ["#5a5c78", "#8a8aa0", "#c8b8b0", "#e8d0a8"],
  park: ["#3e4a3a", "#56664e", "#7a8a68", "#a8b494"],
  stone: ["#3a3a44", "#55556a", "#7a7a8c", "#a4a4b4"],
  spire: ["#2a0f3a", "#6a1e6e", "#c03aa8", "#ff7ae0", "#66e0ff", "#e8e8f4"],
  factory: ["#140c08", "#3a1e10", "#6e3a1c", "#b0602a", "#ff9a3a", "#ffd090"],
  arena: ["#0c0a1e", "#2a1e5a", "#5a3aa0", "#a070ff", "#ff60c0"],
};

function label(img: Img, s: string, x: number, y: number, c = "#ffffff", a = 90): void {
  img.text(x, y, s, c, a);
}

function stars(img: Img, n: number, seed: number, h = img.h): void {
  img.speckle(0, 0, img.w, h, "#ffffff", n / (img.w * h), seed, 200);
  img.speckle(0, 0, img.w, h, "#c8c4e8", n / (img.w * h), seed + 7, 140);
}

function skyline(img: Img, base: number, color: string, seed: number, opts: { spireAt?: number; windows?: string; maxH?: number } = {}): void {
  let s = seed;
  const rnd = () => ((s = (s * 1103515245 + 12345) >>> 0) / 4294967296);
  let x = -10;
  while (x < img.w) {
    const w = 16 + Math.floor(rnd() * 34);
    const h = 30 + Math.floor(rnd() * (opts.maxH ?? 110));
    img.rect(x, base - h, w, h, color);
    if (rnd() < 0.3) img.rect(x + w / 2 - 1, base - h - 10, 2, 10, color);
    if (opts.windows) for (let wy = base - h + 6; wy < base - 4; wy += 7) for (let wx = x + 3; wx < x + w - 3; wx += 5) if (rnd() < 0.35) img.rect(wx, wy, 2, 3, opts.windows);
    x += w + Math.floor(rnd() * 4);
  }
  if (opts.spireAt !== undefined) {
    const sx = opts.spireAt;
    img.poly([[sx - 18, base], [sx - 10, base - 200], [sx, base - 250], [sx + 10, base - 200], [sx + 18, base]], color);
    img.rect(sx - 1, base - 280, 2, 30, color);
    img.circle(sx, base - 282, 3, "#ff7ae0");
  }
}

function floor(img: Img, y: number, top: string, bottom: string, w = img.w): void {
  img.gradient(0, y, w, img.h - y, top, bottom, 5);
}

function door(img: Img, [x, y, w, h]: Rect, c: string, frame: string, text?: string): void {
  img.rect(x, y, w, h, frame);
  img.rect(x + 3, y + 3, w - 6, h - 3, c);
  img.rect(x + w - 9, y + h / 2, 3, 3, frame);
  if (text) label(img, text, x + Math.max(2, (w - img.textWidth(text)) / 2), y - 8, "#ffffff", 160);
}

function speakerWall(img: Img, [x, y, w, h]: Rect, body: string, cone: string): void {
  img.rect(x, y, w, h, body);
  const cols = Math.max(1, Math.floor(w / 42));
  const rows = Math.max(1, Math.floor(h / 42));
  for (let r = 0; r < rows; r++)
    for (let c = 0; c < cols; c++) {
      const cx = x + (c + 0.5) * (w / cols);
      const cy = y + (r + 0.5) * (h / rows);
      const rad = Math.min(w / cols, h / rows) * 0.38;
      img.circle(cx, cy, rad, mix(body, "#000000", 0.4));
      img.circle(cx, cy, rad * 0.55, cone);
      img.circle(cx, cy, rad * 0.18, mix(cone, "#ffffff", 0.4));
    }
}

function mirrorPanel(img: Img, [x, y, w, h]: Rect, frame: string, glass: string): void {
  img.rect(x, y, w, h, frame);
  img.gradient(x + 3, y + 3, w - 6, h - 6, mix(glass, "#ffffff", 0.35), glass, 4);
  img.line(x + 8, y + h - 10, x + w * 0.4, y + 8, "#ffffff", 70);
  img.line(x + 14, y + h - 10, x + w * 0.5, y + 8, "#ffffff", 50);
}

function window_(img: Img, [x, y, w, h]: Rect, sky: string, city: string): void {
  img.rect(x - 3, y - 3, w + 6, h + 6, "#2a2a34");
  img.gradient(x, y, w, h, sky, mix(sky, "#ffffff", 0.3), 4);
  let s = x * 31 + y;
  for (let i = x; i < x + w; ) {
    const bw = 6 + (s = (s * 17 + 11) % 97) % 14;
    const bh = 10 + (s % 50);
    img.rect(i, y + h - bh, Math.min(bw, x + w - i), bh, city);
    i += bw + 1;
  }
  img.rect(x + w / 2 - 1, y, 2, h, "#2a2a34");
}

/** A soft dithered darkening along the floor's front edge: grounds the room without framing it. */
function vignette(img: Img, amount = 0.5): void {
  img.shade(0, img.h - 70, img.w, 16, "#000000", amount * 0.25);
  img.shade(0, img.h - 54, img.w, 54, "#000000", amount * 0.45);
}

// ---- rooms -----------------------------------------------------------------------------------

const ROOMS: Record<string, (img: Img) => void> = {
  bg_crossing_far(img) {
    img.gradient(0, 0, img.w, img.h, "#05041a", "#2a1e5a", 7);
    stars(img, 900, 11);
    img.circle(540, 300, 46, "#2a5aa8");
    img.circle(532, 292, 40, "#3a7ad0");
    img.ellipse(520, 280, 14, 8, "#5aa860");
    img.ellipse(552, 306, 10, 6, "#5aa860");
    img.shade(500, 254, 92, 92, "#05041a", 0.25);
  },
  bg_crossing(img) {
    for (const [x, y, rx, ry, c, a] of [[120, 80, 140, 50, "#6b3aa0", 0.35], [380, 60, 200, 40, "#3a6aa0", 0.3], [260, 140, 160, 36, "#a04a9a", 0.25], [520, 120, 120, 40, "#4a8aa0", 0.25]] as const) {
      const tmp = new Img(img.w, img.h);
      tmp.ellipse(x, y, rx, ry, c);
      for (let j = 0; j < img.h; j++) for (let i = 0; i < img.w; i++) if (tmp.get(i, j)[3] && a * 16 > ((i * 7 + j * 13) % 16)) img.px(i, j, tmp.get(i, j));
    }
    label(img, "THE CROSSING", 4, 350);
  },
  bg_pond_far(img) {
    img.gradient(0, 0, img.w, 230, "#6a6c8c", "#e8d0a8", 7);
    img.circle(470, 190, 22, "#f0dcb0");
    skyline(img, 218, "#8a8aa4", 3, { spireAt: 300, maxH: 90 });
    skyline(img, 222, "#70708c", 9, { maxH: 60 });
    for (const x of [20, 70, 560, 610]) {
      img.rect(x + 8, 170, 6, 60, "#3e3a34");
      img.ellipse(x + 11, 160, 30, 34, "#3e4a3a");
      img.ellipse(x + 4, 150, 18, 20, "#56664e");
    }
  },
  bg_pond(img) {
    floor(img, 230, "#56664e", "#3e4a3a");
    img.ellipse(385, 222, 240, 26, "#6a7c9a");
    img.ellipse(385, 220, 230, 20, "#8a9cb4");
    for (let i = 0; i < 12; i++) img.line(200 + i * 30, 214 + (i % 3) * 4, 220 + i * 30, 214 + (i % 3) * 4, "#c8d4e0", 120);
    img.poly([[600, 236], [640, 232], [640, 300], [560, 300]], "#a4a090");
    const b = rectOf("pond", "bench");
    img.rect(b[0], b[1] + 10, b[2], 6, "#6a4a30");
    img.rect(b[0], b[1], b[2], 4, "#6a4a30");
    img.rect(b[0] + 4, b[1] + 16, 4, 18, "#3a2a1c");
    img.rect(b[0] + b[2] - 8, b[1] + 16, 4, 18, "#3a2a1c");
    const l = rectOf("pond", "lamp");
    img.rect(l[0] + 6, l[1] + 10, 4, l[3] - 10, "#2a2a30");
    img.rect(l[0], l[1], 16, 12, "#2a2a30");
    img.rect(l[0] + 3, l[1] + 3, 10, 7, "#ffe0a0");
    for (let i = 0; i < 18; i++) img.line(206 + i * 3, 276, 204 + i * 3 + (i % 3), 258 - (i % 4) * 3, "#6a7a50");
    img.speckle(0, 240, 640, 60, "#7a8a68", 0.02, 5);
    vignette(img, 0.3);
    label(img, "CADENCE PARK", 4, 350);
  },
  bg_park_gate_far(img) {
    img.gradient(0, 0, img.w, 200, "#6a6c8c", "#e0c8a8", 6);
    skyline(img, 180, "#7a7a94", 21, { windows: "#d8c8a0", maxH: 120 });
  },
  bg_park_gate(img) {
    floor(img, 240, "#7a7a8c", "#4a4a58");
    const hd = rectOf("park_gate", "hedge");
    img.rect(hd[0], hd[1], hd[2], hd[3], "#3e4a3a");
    img.rect(hd[0], hd[1], hd[2], 4, "#56664e");
    img.speckle(hd[0], hd[1], hd[2], hd[3], "#56664e", 0.08, 3);
    const g = rectOf("park_gate", "gate");
    img.rect(g[0] - 14, g[1] - 10, 14, g[3] + 10, "#8a8a9a");
    img.rect(g[0] + g[2], g[1] - 10, 14, g[3] + 10, "#8a8a9a");
    img.rect(g[0] - 16, g[1] - 14, 18, 6, "#a4a4b4");
    img.rect(g[0] + g[2] - 2, g[1] - 14, 18, 6, "#a4a4b4");
    const s = rectOf("park_gate", "sign");
    img.rect(s[0], s[1], s[2], s[3], "#e8e4d8");
    img.text(s[0] + 3, s[1] + 4, "PARK", "#3a3a44");
    img.text(s[0] + 3, s[1] + 12, "CLOSED", "#3a3a44");
    img.text(s[0] + 3, s[1] + 20, "DUSK-DAWN", "#3a3a44");
    const k = rectOf("park_gate", "keypad");
    img.rect(k[0], k[1], k[2], k[3], "#2a2a34");
    img.speckle(k[0] + 2, k[1] + 2, k[2] - 4, k[3] - 4, "#66e0ff", 0.3, 9);
    vignette(img, 0.3);
  },
  bg_street_sky(img) {
    img.gradient(0, 0, img.w, 260, "#5a5c80", "#e8c8a8", 7);
    img.ellipse(160, 60, 70, 10, "#c8b8c0", 160);
    img.ellipse(520, 40, 90, 12, "#c8b8c0", 140);
  },
  bg_street_mid(img) {
    skyline(img, 240, "#6a6a88", 41, { spireAt: 470, windows: "#ffd8a0", maxH: 150 });
    label(img, "STARLIGHT SPIRE", 420, 250, "#ffffff", 70);
  },
  bg_street(img) {
    floor(img, 248, "#8a8a98", "#4a4a58", img.w);
    img.rect(0, 244, img.w, 4, "#a4a4b4");
    for (let x = 0; x < img.w; x += 48) img.line(x, 260, x - 30, 300, "#6a6a7a");
    img.rect(0, 120, 300, 124, "#5a4a5a");
    for (let x = 10; x < 290; x += 26) for (let y = 130; y < 230; y += 26) img.rect(x, y, 14, 16, "#3a2e3a");
    const bb = rectOf("street", "billboard");
    img.rect(bb[0] - 4, bb[1] - 4, bb[2] + 8, bb[3] + 8, "#2a1a2a");
    img.gradient(bb[0], bb[1], bb[2], bb[3], "#ff7ae0", "#6a1e6e", 5);
    img.circle(bb[0] + 60, bb[1] + 50, 26, "#ffd0e8");
    img.ellipse(bb[0] + 60, bb[1] + 34, 30, 18, "#66e0ff");
    img.text(bb[0] + 110, bb[1] + 30, "AGAIN AGAIN", "#ffffff");
    img.text(bb[0] + 110, bb[1] + 42, "(OOH)", "#ffffff");
    img.text(bb[0] + 110, bb[1] + 60, "NO.1 AGAIN", "#66e0ff");
    img.rect(bb[0] + 40, bb[1] + bb[3] + 4, 6, 104, "#2a1a2a");
    img.rect(bb[0] + bb[2] - 46, bb[1] + bb[3] + 4, 6, 104, "#2a1a2a");
    const sp = rectOf("street", "speaker_pole");
    img.rect(sp[0] + 7, sp[1], 4, sp[3], "#3a3a44");
    for (let i = 0; i < 4; i++) img.rect(sp[0] + (i % 2 ? 10 : -4), sp[1] + 6 + i * 24, 12, 14, "#2a2a34");
    const st = rectOf("street", "stairs");
    img.rect(st[0] - 20, st[1] - 80, st[2] + 40, 80, "#c8b8d8");
    img.rect(st[0] - 20, st[1] - 84, st[2] + 40, 6, "#ff7ae0");
    for (let i = 0; i < 8; i++) img.rect(st[0] - i * 2, st[1] + i * 12, st[2] + i * 4, 12, i % 2 ? "#b0a8b8" : "#c8c0d0");
    label(img, "TO THE SPIRE", st[0] + 20, st[1] - 70, "#ffffff", 180);
    const ar = rectOf("street", "arena");
    img.ellipse(ar[0] + ar[2] / 2 + 20, ar[1] + 60, 90, 70, "#3a2a6a");
    img.rect(ar[0] - 20, ar[1] + 60, ar[2] + 40, ar[3] - 60, "#2a1e5a");
    img.text(ar[0] + 10, ar[1] + 30, "MEGA-DOME", "#ff60c0");
    door(img, [ar[0] + 30, ar[1] + 80, 50, 60], "#140c2a", "#5a3aa0");
    img.rect(0, 160, 40, 136, "#3e4a3a");
    vignette(img, 0.2);
  },
  bg_spire_lobby_far(img) {
    img.gradient(0, 0, img.w, 250, "#2a0f3a", "#c03aa8", 6);
    for (let x = 0; x < img.w; x += 64) img.rect(x, 0, 2, 250, "#ff7ae0", 90);
    img.rect(0, 30, img.w, 3, "#66e0ff", 140);
  },
  bg_spire_lobby(img) {
    floor(img, 248, "#e8e8f4", "#8a7a9a");
    for (let x = 0; x < img.w; x += 40) img.line(x, 248, x - 60, 300, "#c8c0d8");
    mirrorPanel(img, rectOf("spire_lobby", "mirrors"), "#e8e8f4", "#8a6aa8");
    const s = rectOf("spire_lobby", "sign");
    img.text(s[0] + 2, s[1] + 4, "WHERE EVERY STAR", "#ffffff");
    img.text(s[0] + 2, s[1] + 14, "IS BORN READY", "#66e0ff");
    door(img, rectOf("spire_lobby", "elevator"), "#c8c8d8", "#e8e8f4", "ELEVATOR");
    const h = rectOf("spire_lobby", "hologram");
    img.ellipse(h[0] + h[2] / 2, h[1] + h[3] - 2, 24, 6, "#66e0ff", 160);
    img.rect(0, 150, 36, 146, "#2a0f3a");
    vignette(img, 0.25);
  },
  bg_spire_lobby_front(img) {
    // the desk stands in front of the receptionist
    const d = rectOf("spire_lobby", "desk");
    img.ellipse(d[0] + d[2] / 2, d[1] + 6, d[2] / 2, 16, "#e8e8f4");
    img.rect(d[0], d[1] + 6, d[2], d[3] - 6, "#e8e8f4");
    img.rect(d[0] + 10, d[1] + 18, d[2] - 20, 3, "#ff7ae0");
    img.shade(d[0], d[1] + d[3] - 8, d[2], 8, "#8a7a9a", 0.5);
  },
  bg_floor40_far(img) {
    img.gradient(0, 0, img.w, 250, "#3a1550", "#a03090", 5);
    img.rect(0, 40, img.w, 2, "#66e0ff", 120);
  },
  bg_floor40(img) {
    floor(img, 250, "#d8d0e8", "#7a6a8a");
    door(img, rectOf("floor40", "door_mixing"), "#2a1a3a", "#e8e8f4", "CONTROL B");
    door(img, rectOf("floor40", "door_fitting"), "#2a1a3a", "#e8e8f4", "FITTING");
    door(img, rectOf("floor40", "door_corridor"), "#c8b8e8", "#e8e8f4", "MIRRORS");
    door(img, rectOf("floor40", "elevator"), "#c8c8d8", "#e8e8f4");
    const p = rectOf("floor40", "poster");
    img.rect(p[0], p[1], p[2], p[3], "#ff7ae0");
    img.text(p[0] + 4, p[1] + 6, "BE", "#ffffff");
    img.text(p[0] + 4, p[1] + 14, "YOURSELF", "#ffffff");
    for (let i = 0; i < 4; i++) img.rect(p[0] + 4, p[1] + 26 + i * 6, p[2] - 8, 2, "#ffffff", 140);
    const pl = rectOf("floor40", "plant");
    img.rect(pl[0] + 6, pl[1] + 30, 14, 16, "#e8e8f4");
    img.ellipse(pl[0] + 13, pl[1] + 18, 12, 16, "#40e080");
    const w = rectOf("floor40", "wardrobe");
    img.rect(w[0], w[1], w[2], 4, "#e8e8f4");
    for (let i = 0; i < 5; i++) {
      const fx = w[0] + 10 + i * 18;
      img.line(fx, w[1] + 4, fx, w[1] + 18, "#e8e8f4");
      img.ellipse(fx, w[1] + 30, 8, 11, ["#ffd0e8", "#d0e8ff", "#ffe8b0", "#e0d0ff", "#c8ffd8"][i]);
      img.rect(fx - 3, w[1] + 28, 2, 2, "#2a1a3a");
      img.rect(fx + 1, w[1] + 28, 2, 2, "#2a1a3a");
      img.line(fx - 3, w[1] + 35, fx + 3, w[1] + 35, "#2a1a3a");
      img.rect(fx - 8, w[1] + 42, 16, 60, ["#ff7ae0", "#66e0ff", "#ffd090", "#a070ff", "#40e080"][i]);
    }
    label(img, "PERSONAS", w[0] + 24, w[1] - 8, "#ffffff", 170);
    vignette(img, 0.2);
  },
  bg_mixing_room_far(img) {
    img.gradient(0, 0, img.w, 250, "#140c24", "#2a1e4a", 4);
    for (let x = 0; x < img.w; x += 20) img.rect(x, 0, 10, 250, "#1a1230");
  },
  bg_mixing_room(img) {
    floor(img, 250, "#2a2440", "#140c24");
    window_(img, rectOf("mixing_room", "window"), "#c8a8d8", "#5a4a7a");
    const m = rectOf("mixing_room", "monitors");
    img.rect(m[0], m[1], m[2], m[3], "#0a0814");
    for (let i = 0; i < 24; i++) {
      const h = 8 + ((i * 37) % 40);
      img.rect(m[0] + 6 + i * 7.5, m[1] + m[3] - 6 - h, 5, h, ["#66e0ff", "#ff7ae0", "#ffd090", "#40e080"][i % 4]);
    }
    const d = rectOf("mixing_room", "desk");
    img.poly([[d[0], d[1] + d[3]], [d[0] + 12, d[1]], [d[0] + d[2] - 12, d[1]], [d[0] + d[2], d[1] + d[3]]], "#3a3450");
    for (let i = 0; i < 26; i++) {
      img.rect(d[0] + 16 + i * 7, d[1] + 6, 2, 22, "#1a1430");
      img.rect(d[0] + 15 + i * 7, d[1] + 8 + ((i * 13) % 16), 4, 4, "#e8e8f4");
      img.px(d[0] + 16 + i * 7, d[1] + 3, [255, 120, 220, 255]);
    }
    door(img, rectOf("mixing_room", "door"), "#1a1430", "#3a3450");
    vignette(img, 0.4);
  },
  bg_fitting_room_far(img) {
    img.gradient(0, 0, img.w, 250, "#4a2440", "#a0607a", 5);
    for (let x = 0; x < img.w; x += 32) img.rect(x, 0, 2, 250, "#ffd0e0", 60);
  },
  bg_fitting_room(img) {
    floor(img, 250, "#a07060", "#5a3a34");
    const m = rectOf("fitting_room", "mirror");
    img.rect(m[0] - 6, m[1] - 6, m[2] + 12, m[3] + 12, "#3a2030");
    for (let i = 0; i < 8; i++) {
      img.circle(m[0] - 3 + (i * (m[2] + 6)) / 7, m[1] - 3, 3, "#ffe8b0");
      img.circle(m[0] - 3 + (i * (m[2] + 6)) / 7, m[1] + m[3] + 3, 3, "#ffe8b0");
    }
    mirrorPanel(img, m, "#c0a0a8", "#806070");
    const p = rectOf("fitting_room", "piano");
    img.rect(p[0], p[1] - 20, p[2], p[3] + 20, "#2a1810");
    img.rect(p[0] + 4, p[1] + 10, p[2] - 8, 8, "#e8e4d8");
    for (let i = 0; i < 14; i++) img.rect(p[0] + 7 + i * 6, p[1] + 10, 2, 5, "#1a1010");
    img.rect(p[0] + 4, p[1] + p[3] - 4, 6, 4, "#1a1010");
    img.rect(p[0] + p[2] - 10, p[1] + p[3] - 4, 6, 4, "#1a1010");
    const mt = rectOf("fitting_room", "metronome");
    img.poly([[mt[0], mt[1] + mt[3]], [mt[0] + mt[2] / 2, mt[1]], [mt[0] + mt[2], mt[1] + mt[3]]], "#6a4a30");
    img.line(mt[0] + mt[2] / 2, mt[1] + mt[3] - 2, mt[0] + mt[2] - 2, mt[1] + 4, "#e8e4d8");
    door(img, rectOf("fitting_room", "door"), "#3a2030", "#a07080");
    vignette(img, 0.3);
  },
  bg_mirror_corridor_far(img) {
    img.gradient(0, 0, img.w, 250, "#50306a", "#c098d8", 5);
    for (let x = 0; x < img.w; x += 46) mirrorPanel(img, [x + 3, 30, 40, 210], "#e8e0f4", "#a080c0");
    for (let x = 23; x < img.w; x += 46) {
      img.ellipse(x, 168, 6, 7, "#3a3040", 110);
      img.poly([[x - 9, 230], [x - 6, 172], [x + 6, 172], [x + 9, 230]], "#3a3040", 110);
    }
  },
  bg_mirror_corridor(img) {
    floor(img, 246, "#e8e0f4", "#8a7aa0");
    const s = rectOf("mirror_corridor", "speakers");
    for (let i = 0; i < 4; i++) speakerWall(img, [s[0] + i * 62, s[1], 52, s[3]], "#2a2030", "#ff7ae0");
    door(img, rectOf("mirror_corridor", "door_back"), "#2a1a3a", "#e8e8f4");
    door(img, rectOf("mirror_corridor", "door_hall"), "#2a1a3a", "#e8e8f4", "HALL");
    vignette(img, 0.2);
  },
  bg_rehearsal_hall_far(img) {
    img.gradient(0, 0, img.w, 250, "#1a0a2a", "#6a1e6e", 6);
    for (let i = 0; i < 6; i++) img.poly([[100 + i * 90, 0], [110 + i * 90, 0], [180 + i * 70, 250], [150 + i * 70, 250]], "#ff7ae0", 30);
  },
  bg_rehearsal_hall(img) {
    floor(img, 250, "#3a2a4a", "#140c24");
    for (let x = 0; x < img.w; x += 32) img.line(x, 250, x, 300, "#4a3a5a");
    speakerWall(img, rectOf("rehearsal_hall", "hook_engine"), "#1a1424", "#ff4fd8");
    label(img, "HOOK ENGINE", 96, 40, "#ff7ae0", 200);
    const b = rectOf("rehearsal_hall", "booth");
    img.rect(b[0], b[1], b[2], b[3], "#c8e8ff", 70);
    img.rect(b[0], b[1], b[2], 3, "#e8e8f4");
    img.rect(b[0], b[1], 3, b[3], "#e8e8f4");
    img.rect(b[0] + b[2] - 3, b[1], 3, b[3], "#e8e8f4");
    img.line(b[0] + 10, b[1] + 60, b[0] + 40, b[1] + 10, "#ffffff", 120);
    door(img, rectOf("rehearsal_hall", "door"), "#1a1430", "#6a4a8a");
    const e = rectOf("rehearsal_hall", "elevator");
    door(img, e, "#c8c8d8", "#e8e8f4", "TALENT");
    vignette(img, 0.35);
  },
  bg_talent_elevator_far(img) {
    img.gradient(0, 0, img.w, 260, "#5a5a6a", "#c8c8d8", 4);
    for (let x = 0; x < img.w; x += 60) img.rect(x, 0, 3, 260, "#e8e8f4", 120);
  },
  bg_talent_elevator(img) {
    floor(img, 250, "#8a8a9a", "#3a3a44");
    const d = rectOf("talent_elevator", "doors");
    img.rect(d[0] - 6, d[1] - 6, d[2] + 12, d[3] + 6, "#e8e8f4");
    img.rect(d[0], d[1], d[2] / 2 - 1, d[3], "#a4a4b4");
    img.rect(d[0] + d[2] / 2 + 1, d[1], d[2] / 2 - 1, d[3], "#a4a4b4");
    img.text(d[0] + 20, d[1] - 14, "STAFF ONLY", "#ff4040");
    const p = rectOf("talent_elevator", "panel");
    img.rect(p[0], p[1], p[2], p[3], "#3a3a44");
    for (let i = 0; i < 8; i++) img.circle(p[0] + 12 + (i % 2) * 20, p[1] + 12 + Math.floor(i / 2) * 18, 5, "#e8e8f4");
    img.rect(0, 150, 40, 146, "#2a2a34");
    vignette(img, 0.3);
  },
  bg_factory_night_far(img) {
    img.gradient(0, 0, img.w, 250, "#0c0806", "#3a1e10", 5);
    for (let x = 30; x < img.w; x += 110) {
      img.rect(x, 0, 14, 250, "#1a100a");
      img.rect(x - 4, 60, 22, 8, "#2a160c");
    }
    for (let y = 20; y < 90; y += 18) img.rect(0, y, img.w, 6, "#22140c");
  },
  bg_factory_night(img) {
    floor(img, 252, "#3a2414", "#140c08");
    img.speckle(0, 252, img.w, 48, "#6e3a1c", 0.03, 8);
    const ps = rectOf("factory_night", "posters");
    img.rect(ps[0], ps[1], ps[2], ps[3], "#b0602a");
    img.text(ps[0] + 6, ps[1] + 10, "WE MAKE", "#140c08");
    img.text(ps[0] + 6, ps[1] + 20, "WHAT WORKED", "#140c08");
    img.text(ps[0] + 6, ps[1] + 50, "AND AGAIN", "#140c08", 160);
    const wb = rectOf("factory_night", "workbench");
    img.rect(wb[0], wb[1] + 16, wb[2], 8, "#6e3a1c");
    img.rect(wb[0] + 4, wb[1] + 24, 6, 26, "#3a1e10");
    img.rect(wb[0] + wb[2] - 10, wb[1] + 24, 6, 26, "#3a1e10");
    img.rect(wb[0] + 20, wb[1] + 6, 30, 10, "#ffd090");
    img.rect(wb[0] + 70, wb[1] + 8, 16, 8, "#e8e4d8");
    const pd = rectOf("factory_night", "pedal");
    img.rect(pd[0], pd[1] + 4, pd[2], pd[3] - 4, "#2a6a4a");
    img.circle(pd[0] + 10, pd[1] + 9, 3, "#7fe0a0");
    img.circle(pd[0] + 30, pd[1] + 9, 3, "#ff9a3a");
    const mp = rectOf("factory_night", "mute_pedal");
    img.rect(mp[0], mp[1] + 4, mp[2], mp[3] - 4, "#3a3a6a");
    img.circle(mp[0] + mp[2] / 2, mp[1] + 9, 3, "#ff4040");
    door(img, rectOf("factory_night", "elevator"), "#2a2a34", "#6e3a1c");
    door(img, rectOf("factory_night", "floor_door"), "#2a160c", "#b0602a", "FLOOR");
    vignette(img, 0.5);
  },
  bg_press_floor_far(img) {
    img.gradient(0, 0, img.w, 250, "#140c08", "#6e3a1c", 6);
    for (let x = 0; x < img.w; x += 80) img.rect(x, 0, 30, 250, "#22140c");
    for (let y = 30; y < 200; y += 50) img.rect(0, y, img.w, 6, "#3a1e10");
  },
  bg_press_floor(img) {
    floor(img, 254, "#4a2a16", "#140c08");
    const hm = rectOf("press_floor", "hook_mill");
    const cx = hm[0] + hm[2] / 2;
    const cy = hm[1] + hm[3] / 2;
    img.circle(cx, cy, 58, "#3a1e10");
    img.circle(cx, cy, 52, "#6e3a1c");
    for (let i = 0; i < 12; i++) {
      const a = (i / 12) * Math.PI * 2;
      img.poly([[cx + Math.cos(a) * 50, cy + Math.sin(a) * 50], [cx + Math.cos(a + 0.12) * 64, cy + Math.sin(a + 0.12) * 64], [cx + Math.cos(a + 0.25) * 50, cy + Math.sin(a + 0.25) * 50]], "#b0602a");
    }
    img.circle(cx, cy, 14, "#ffd090");
    label(img, "HOOK MILL", hm[0] + 40, hm[1] - 8, "#ffd090", 200);
    const cu = rectOf("press_floor", "conveyor_up");
    img.poly([[cu[0], cu[1] + cu[3]], [cu[0] + cu[2], cu[1]], [cu[0] + cu[2], cu[1] + 20], [cu[0] + 18, cu[1] + cu[3]]], "#3a1e10");
    img.text(cu[0] + 6, cu[1] + 10, "LOUNGE", "#ffd090");
    door(img, rectOf("press_floor", "back"), "#2a160c", "#6e3a1c");
    vignette(img, 0.5);
  },
  bg_focus_lounge_far(img) {
    img.gradient(0, 0, img.w, 250, "#6a5040", "#d8c0a0", 5);
    for (let x = 0; x < img.w; x += 80) img.rect(x + 30, 0, 20, 250, "#c8b090", 120);
  },
  bg_focus_lounge(img) {
    floor(img, 252, "#b49c88", "#6a5040");
    const s = rectOf("focus_lounge", "screen");
    img.rect(s[0], s[1], s[2], s[3], "#1a140e");
    img.rect(s[0] + 4, s[1] + 4, s[2] - 8, s[3] - 8, "#2a3a2a");
    img.text(s[0] + 40, s[1] + 30, "SEGMENT TESTED", "#40e080");
    img.text(s[0] + 52, s[1] + 46, "AWAITING PANEL", "#a0c0a0");
    door(img, rectOf("focus_lounge", "library_door"), "#3a2a20", "#e8d0b0", "PRESETS");
    const cd = rectOf("focus_lounge", "conveyor_down");
    img.poly([[cd[0], cd[1] + 30], [cd[0] + cd[2], cd[1] + 40], [cd[0] + cd[2], cd[1] + cd[3]], [cd[0], cd[1] + cd[3]]], "#6e3a1c");
    vignette(img, 0.2);
  },
  bg_floor3_far(img) {
    img.gradient(0, 0, img.w, 250, "#140c08", "#5a2e16", 5);
    for (let y = 120; y < 240; y += 30) img.rect(0, y, img.w, 3, "#3a1e10");
  },
  bg_floor3(img) {
    floor(img, 252, "#4a2a16", "#140c08");
    const sh = rectOf("floor3", "shelves");
    img.rect(sh[0], sh[1], sh[2], sh[3], "#3a1e10");
    for (let r = 0; r < 6; r++)
      for (let c = 0; c < 6; c++) {
        img.rect(sh[0] + 4 + c * 31, sh[1] + 4 + r * 25, 28, 21, "#6e3a1c");
        img.rect(sh[0] + 12 + c * 31, sh[1] + 12 + r * 25, 12, 3, "#ffd090");
      }
    img.text(sh[0] + 6, sh[1] - 10, "PRESET LIBRARY", "#ffd090");
    const sg = rectOf("floor3", "sign");
    img.rect(sg[0], sg[1], sg[2], sg[3], "#ffd090");
    img.text(sg[0] + 4, sg[1] + 6, "ALL DOORS", "#140c08");
    img.text(sg[0] + 4, sg[1] + 14, "SIDECHAINED", "#140c08");
    img.text(sg[0] + 4, sg[1] + 22, "FOR YOUR SAFETY", "#140c08");
    speakerWall(img, rectOf("floor3", "speakers"), "#1a100a", "#ff9a3a");
    const cr = rectOf("floor3", "crate");
    img.rect(cr[0], cr[1], cr[2], cr[3], "#8a6a3a");
    img.line(cr[0], cr[1], cr[0] + cr[2], cr[1] + cr[3], "#6a4a2a");
    img.text(cr[0] + 2, cr[1] + 4, "FRAGILE", "#2a160c");
    const g = rectOf("floor3", "gate");
    img.rect(g[0] - 8, g[1] - 8, g[2] + 16, 8, "#6e3a1c");
    img.rect(g[0] - 8, g[1], 8, g[3], "#6e3a1c");
    img.rect(g[0] + g[2], g[1], 8, g[3], "#6e3a1c");
    door(img, rectOf("floor3", "back"), "#2a160c", "#6e3a1c");
    vignette(img, 0.5);
  },
  bg_dominic_studio_far(img) {
    img.gradient(0, 0, img.w, 250, "#2a1810", "#6a4030", 5);
    for (let x = 0; x < img.w; x += 40) for (let y = 30; y < 200; y += 40) img.rect(x + 4, y + 4, 32, 32, (x + y) % 80 ? "#4a2c1e" : "#3a2018");
  },
  bg_dominic_studio(img) {
    floor(img, 252, "#5a3a2a", "#2a1810");
    const c = rectOf("dominic_studio", "console");
    img.poly([[c[0], c[1] + c[3]], [c[0] + 10, c[1]], [c[0] + c[2] - 10, c[1]], [c[0] + c[2], c[1] + c[3]]], "#2a1e18");
    for (let i = 0; i < 22; i++) img.rect(c[0] + 14 + i * 7.5, c[1] + 6 + ((i * 7) % 12), 4, 4, "#e8d0b0");
    const f = rectOf("dominic_studio", "fader");
    img.rect(f[0], f[1], f[2], f[3], "#ff4040");
    const r = rectOf("dominic_studio", "run_of_show");
    img.rect(r[0], r[1], r[2], r[3], "#e8e4d8");
    for (let i = 0; i < 7; i++) img.rect(r[0] + 4, r[1] + 6 + i * 7, r[2] - 8 - (i % 3) * 6, 2, "#3a2a20");
    door(img, rectOf("dominic_studio", "back"), "#2a1810", "#8a5a3a");
    door(img, rectOf("dominic_studio", "stage_door"), "#2a1810", "#8a5a3a", "STAGE");
    vignette(img, 0.4);
  },
  bg_arena_outside_far(img) {
    img.gradient(0, 0, img.w, 250, "#0c0a1e", "#3a2a6a", 6);
    stars(img, 80, 5, 120);
    img.ellipse(560, 210, 200, 150, "#2a1e5a");
    img.speckle(380, 70, 400, 150, "#a070ff", 0.01, 4);
  },
  bg_arena_outside(img) {
    floor(img, 250, "#3a3450", "#141020");
    const p = rectOf("arena_outside", "poster");
    img.rect(p[0], p[1], p[2], p[3], "#ff60c0");
    img.circle(p[0] + p[2] / 2, p[1] + 40, 20, "#ffd0e8");
    img.text(p[0] + 8, p[1] + 80, "LYRIX LIVE", "#ffffff");
    img.text(p[0] + 8, p[1] + 90, "(NOT LIVE)", "#2a1e5a");
    img.line(p[0] + 4, p[1] + 88, p[0] + 48, p[1] + 96, "#ffffff");
    const d = rectOf("arena_outside", "dome_doors");
    door(img, d, "#140c2a", "#a070ff", "MEGA-DOME");
    const b = rectOf("arena_outside", "basement");
    img.rect(b[0], b[1], b[2], b[3], "#1a1424");
    img.text(b[0] + 4, b[1] + 4, "STORAGE", "#a070ff");
    door(img, rectOf("arena_outside", "studio_door"), "#2a1e3a", "#5a3aa0", "STAGE");
    img.rect(0, 150, 36, 146, "#2a2440");
    vignette(img, 0.4);
  },
  bg_arena_basement_far(img) {
    img.gradient(0, 0, img.w, 250, "#1a1210", "#4a3a30", 4);
    for (let x = 0; x < img.w; x += 70) img.rect(x, 0, 12, 250, "#2a1e18");
  },
  bg_arena_basement(img) {
    floor(img, 252, "#3a2e26", "#1a1210");
    const bx = rectOf("arena_basement", "boxes");
    img.rect(bx[0], bx[1] + 20, 50, 46, "#8a6a4a");
    img.rect(bx[0] + 54, bx[1] + 30, 40, 36, "#7a5a3a");
    img.circle(bx[0] + 110, bx[1] + 10, 18, "#e8e0b0");
    img.circle(bx[0] + 116, bx[1] + 6, 14, "#3a2e26");
    img.text(bx[0] + 4, bx[1] + 6, "LOVE", "#ff60c0");
    const p = rectOf("arena_basement", "piano_old");
    img.rect(p[0], p[1] - 30, p[2], p[3] + 30, "#3a2414");
    img.rect(p[0] + 4, p[1] - 26, p[2] - 8, 20, "#4a301c");
    img.rect(p[0] + 6, p[1] + 14, p[2] - 12, 9, "#e8e4d8");
    for (let i = 0; i < 15; i++) img.rect(p[0] + 9 + i * 6, p[1] + 14, 2, 5, "#1a1010");
    img.rect(p[0] + 30, p[1] - 22, 44, 10, "#e8e4d8");
    img.text(p[0] + 32, p[1] - 20, "PLAINSONG", "#3a2414");
    door(img, rectOf("arena_basement", "stairs"), "#1a1210", "#4a3a30");
    vignette(img, 0.55);
  },
  bg_mega_dome_far(img) {
    img.gradient(0, 0, img.w, 260, "#05040e", "#2a1e5a", 6);
    for (let i = 0; i < 9; i++) img.poly([[60 + i * 70, 0], [72 + i * 70, 0], [140 + i * 50, 210], [110 + i * 50, 210]], i % 2 ? "#ff60c0" : "#a070ff", 40);
    img.speckle(0, 120, img.w, 100, "#ffffff", 0.004, 2);
  },
  bg_mega_dome(img) {
    img.rect(0, 210, img.w, 90, "#141020");
    const st = rectOf("mega_dome", "stage");
    img.rect(st[0] - 40, st[1] + 10, st[2] + 80, 40, "#2a2440");
    img.rect(st[0] - 40, st[1] + 10, st[2] + 80, 3, "#a070ff");
    speakerWall(img, rectOf("mega_dome", "pa"), "#141020", "#ff60c0");
    const b = rectOf("mega_dome", "booth");
    img.rect(b[0], b[1], b[2], b[3], "#1a1430");
    img.rect(b[0] + 6, b[1] + 6, b[2] - 12, 40, "#3a2e6a");
    img.text(b[0] + 10, b[1] + b[3] - 12, "PRODUCTION", "#a070ff");
    for (let x = -8; x < img.w; x += 14) {
      const h = 18 + ((x * 7) % 9);
      img.ellipse(x + 6, 300 - h, 6, 7, "#0a0814");
      img.rect(x, 300 - h + 4, 13, h, "#0a0814");
    }
    vignette(img, 0.4);
  },
};

// ---- characters ---------------------------------------------------------------------------------------

interface Fig {
  h: number;
  body: string;
  skin?: string;
  hair?: string;
  hood?: boolean;
  legs?: string;
  accent?: string;
  headphones?: boolean;
  wide?: number;
}

/** A standing person, feet at the bottom of the frame. step: -1..1 leg swing; arm: 0..1 raised. */
function person(img: Img, ox: number, fw: number, f: Fig, step = 0, arm = 0): void {
  const cx = ox + fw / 2;
  const bottom = img.h - 1;
  const top = bottom - f.h + 1;
  const head = Math.round(f.h * 0.15);
  const w = f.wide ?? Math.round(f.h * 0.28);
  const legH = Math.round(f.h * 0.38);
  const legs = f.legs ?? mix(f.body, "#000000", 0.4);
  img.rect(cx - w / 2 + 2 + step * 3, bottom - legH, 5, legH, legs);
  img.rect(cx + w / 2 - 7 - step * 3, bottom - legH, 5, legH, legs);
  img.poly([[cx - w / 2, bottom - legH + 4], [cx - w / 2 + 3, top + head + 2], [cx + w / 2 - 3, top + head + 2], [cx + w / 2, bottom - legH + 4]], f.body);
  img.shade(cx + 1, top + head + 2, w / 2, f.h - head - legH, "#000000", 0.25);
  const ay = top + head + 6 - arm * 14;
  img.line(cx - w / 2, top + head + 6, cx - w / 2 - 4, ay + 14, f.body);
  img.line(cx - w / 2 - 1, top + head + 6, cx - w / 2 - 5, ay + 14, f.body);
  img.line(cx + w / 2, top + head + 6, cx + w / 2 + 3 + arm * 4, ay + 14 - arm * 6, f.body);
  img.circle(cx, top + head / 2 + 1, head / 2 + 1, f.skin ?? "#e0b090");
  if (f.hair) img.ellipse(cx, top + head / 4, head / 2 + 2, head / 3 + 1, f.hair);
  if (f.hood) {
    img.poly([[cx - head / 2 - 4, top + head + 4], [cx - head / 2 - 2, top + 1], [cx, top - 2], [cx + head / 2 + 2, top + 1], [cx + head / 2 + 4, top + head + 4]], f.body);
    img.ellipse(cx, top + head / 2 + 2, head / 2 - 1, head / 2 - 1, "#120e18");
    img.px(cx - 2, top + head / 2 + 2, [200, 220, 255, 255]);
    img.px(cx + 2, top + head / 2 + 2, [200, 220, 255, 255]);
  } else {
    img.px(cx - 2, top + head / 2 + 1, [30, 20, 20, 255]);
    img.px(cx + 2, top + head / 2 + 1, [30, 20, 20, 255]);
  }
  if (f.headphones) {
    img.rect(cx - head / 2 - 2, top + head / 2 - 1, 3, 5, "#2a2a34");
    img.rect(cx + head / 2, top + head / 2 - 1, 3, 5, "#2a2a34");
    img.line(cx - head / 2 - 1, top + head / 2 - 1, cx, top - 1, "#2a2a34");
    img.line(cx, top - 1, cx + head / 2 + 1, top + head / 2 - 1, "#2a2a34");
  }
  if (f.accent) img.rect(cx - w / 2 + 2, top + head + 8, w - 4, 2, f.accent);
}

function swan(img: Img, x: number, y: number, s: number, wing: number, c = "#f4f4f8"): void {
  img.ellipse(x, y, 10 * s, 5 * s, c);
  img.line(x + 8 * s, y - 1, x + 12 * s, y - 7 * s, c);
  img.line(x + 9 * s, y - 1, x + 13 * s, y - 7 * s, c);
  img.circle(x + 13 * s, y - 8 * s, 2 * s, c);
  img.px(x + 15 * s, y - 8 * s, [255, 150, 60, 255]);
  const wy = wing > 0 ? -8 * s : 4 * s;
  img.poly([[x - 6 * s, y - 1], [x + 4 * s, y - 1], [x - 2 * s, y + wy]], mix(c, "#9090a8", 0.25));
}

function sheet(img: Img, frames: number, draw: (ox: number, fw: number, i: number) => void): void {
  const fw = img.w / frames;
  for (let i = 0; i < frames; i++) draw(i * fw, fw, i);
}

function tag(img: Img, id: string, frames: number): void {
  const fw = img.w / frames;
  const s = id.toUpperCase().slice(0, Math.floor((fw - 1) / 4));
  if (fw < 20 || img.h < 20) return;
  for (let i = 0; i < frames; i++) img.text(i * fw + 1, img.h - 6, s, "#ffffff", 70);
}

const CHARS: Record<string, (img: Img, frames: number) => void> = {
  bobbin(img, n) {
    sheet(img, n, (ox, fw, i) => {
      const step = i === 0 ? 0 : Math.sin(((i - 1) / 8) * Math.PI * 2);
      person(img, ox, fw, { h: 62, body: "#8a8a98", hood: true, legs: "#5a5a68", wide: 18 }, step);
      img.rect(ox + fw - 6, 6, 2, 56, "#b08a5a");
      img.circle(ox + fw - 5, 6, 2, "#c9b8ff");
      img.poly([[ox + 7, 62], [ox + 10 + step * 2, 40], [ox + fw - 10 - step * 2, 40], [ox + fw - 7, 62]], "#7a7a88");
    });
    img.outline("#1a1624");
  },
  bobbin_swan(img, n) {
    sheet(img, n, (ox, fw, i) => swan(img, ox + fw / 2 - 4, 20, 1.4, i % 2 ? 1 : -1, "#e8e8f0"));
    img.outline("#3a3650");
  },
  skein(img, n) {
    sheet(img, n, (ox, _fw, i) => {
      img.ellipse(ox + 8, 11 - (i % 2), 6, 4, "#b8b8c4");
      img.circle(ox + 12, 6 - (i % 2), 3, "#b8b8c4");
      img.px(ox + 14, 6 - (i % 2), [60, 60, 70, 255]);
      img.px(ox + 15, 7 - (i % 2), [200, 120, 60, 255]);
      img.rect(ox + 6 + (i % 2), 14, 1, 2, "#3a3a44");
      img.rect(ox + 9 - (i % 2), 14, 1, 2, "#3a3a44");
    });
    img.outline("#2a2634");
  },
  skein_sit(img, n) {
    sheet(img, n, (ox, _fw, i) => {
      img.ellipse(ox + 12, 15, 9, 4, "#9a9aa4");
      img.circle(ox + 18 - i, 12, 3, "#9a9aa4");
      img.px(ox + 19 - i, 11, [50, 50, 60, 255]);
    });
    img.outline("#2a2634");
  },
  flock_flight(img, n) {
    sheet(img, n, (ox, _fw, i) => {
      const pos = [[130, 14], [104, 26], [78, 38], [56, 48], [104, 46], [80, 56]];
      pos.forEach(([x, y], k) => swan(img, ox + x, y, 1, (i + k) % 2 ? 1 : -1));
    });
    img.outline("#3a3650");
  },
  lead_swan(img, n) {
    sheet(img, n, (ox, fw, i) => swan(img, ox + fw / 2 - 4, 20, 1.5, i % 2 ? 1 : -1, "#ffffff"));
    img.outline("#3a3650");
  },
  flock_rest(img, n) {
    sheet(img, n, (ox, _fw, i) => {
      for (let k = 0; k < 6; k++) swan(img, ox + 18 + k * 34, 28 + (k % 2) * 4 + ((i + k) % 2), 1, 1, "#f0f0f4");
    });
  },
  jogger(img, n) {
    sheet(img, n, (ox, fw, i) => {
      person(img, ox, fw, { h: 60, body: "#4a90c0", skin: "#c08060", hair: "#2a1a10", legs: "#2a2a34" }, Math.sin((i / n) * Math.PI * 2) * 1.4, 0.5);
      img.rect(ox + fw - 9, 26, 4, 6, "#ff7ae0");
    });
    img.outline("#141018");
    tag(img, "jogger", n);
  },
  marcus(img, n) {
    sheet(img, n, (ox, fw, i) => {
      const cx = ox + fw / 2;
      img.rect(cx - 9, 50, 18, 22, "#3a6aa0");
      img.rect(cx - 11, 48, 22, 3, "#5a8ac0");
      img.rect(cx - 26, 56, 14, 16, "#c08040");
      img.rect(cx + 12, 58, 13, 14, "#d0a050");
      person(img, ox, fw, { h: 50, body: "#a05a30", skin: "#7a4a30", hair: "#1a1010", legs: "#3a2a20" }, 0, (i % 2) * 0.8);
      img.line(cx - 14, 40 - (i % 2) * 8, cx - 20, 54, "#e8d0a0");
      img.line(cx + 14, 40 - ((i + 1) % 2) * 8, cx + 18, 56, "#e8d0a0");
    });
    img.outline("#141018");
    tag(img, "marcus", n);
  },
  commuter(img, n) {
    sheet(img, n, (ox, fw, i) => person(img, ox, fw, { h: i ? 68 : 64, body: "#5a6070", skin: "#d0a080", hair: "#3a2a1a", headphones: true, legs: "#2a2a34" }, 0, i ? 0.9 : 0));
    img.outline("#141018");
    tag(img, "commuter", n);
  },
  receptionist(img, n) {
    sheet(img, n, (ox, fw, i) => {
      person(img, ox, fw, { h: 56, body: "#ff7ae0", skin: "#f0c0a0", hair: "#ffe080", headphones: true });
      const cx = ox + fw / 2;
      img.line(cx - 3, 8, cx + 3, 8, "#a02060");
      if (i) img.rect(cx - 3, 5, 6, 1, "#f0c0a0");
    });
    img.outline("#2a0f3a");
    tag(img, "recept", n);
  },
  lyrix_holo(img, n) {
    sheet(img, n, (ox, fw, i) => {
      person(img, ox, fw, { h: 84, body: "#66e0ff", skin: "#c8f4ff", hair: "#ffffff", accent: "#ff7ae0" }, 0, (i % 2) * 0.5);
      for (let y = i; y < img.h; y += 4) img.rect(ox, y, fw, 1, "#ffffff", 40);
    });
    tag(img, "lyrix", n);
  },
  lyra(img, n) {
    sheet(img, n, (ox, fw, i) => person(img, ox, fw, { h: 62, body: "#c87a5a", skin: "#e0b090", hair: "#5a3020", legs: "#3a3a5a" }, 0, i * 0.3));
    img.outline("#141018");
    tag(img, "lyra", n);
  },
  engineer(img, n) {
    sheet(img, n, (ox, fw, i) => person(img, ox, fw, { h: 54, body: "#3a5a8a", skin: "#d0a080", hair: "#5a5a5a", headphones: true, legs: "#2a2a34" }, 0, i * 0.4));
    img.outline("#141018");
    tag(img, "engineer", n);
  },
  coach(img, n) {
    sheet(img, n, (ox, fw, i) => {
      person(img, ox, fw, { h: 66, body: "#a0507a", skin: "#e8c0a0", hair: "#2a1a1a", accent: "#ffd090" }, 0, i * 0.6);
      if (i) img.circle(ox + fw / 2, 10, 1, "#2a1010");
    });
    img.outline("#141018");
    tag(img, "coach", n);
  },
  dancers(img, n) {
    sheet(img, n, (ox, _fw, i) => {
      for (let k = 0; k < 3; k++) {
        const sub = new Img(36, img.h);
        person(sub, 0, 36, { h: 62, body: "#e8e8f4", skin: "#d8c0d0", hair: "#ff7ae0", accent: "#66e0ff", legs: "#c0c0d8" }, [-1, 1, 0.4, -0.4][i], [0, 1, 0.5, 0.2][i]);
        img.blit(sub, ox + 2 + k * 39, 0);
      }
    });
    img.outline("#2a0f3a");
    tag(img, "dancers", n);
  },
  choreographer(img, n) {
    sheet(img, n, (ox, fw, i) => person(img, ox, fw, { h: 64, body: "#2a2a34", skin: "#e0b090", hair: "#e8e8f4", accent: "#ff4040" }, 0, i));
    img.outline("#141018");
    tag(img, "choreo", n);
  },
  scanner(img, n) {
    sheet(img, n, (ox, fw, i) => {
      img.rect(ox + 2, 2, fw - 4, img.h - 4, "#3a3a44");
      img.circle(ox + fw / 2, 12, 6, "#141018");
      img.circle(ox + fw / 2, 12, 3, i ? "#40e080" : "#ff4040");
      img.rect(ox + 6, 22, fw - 12, 4, i ? "#40e080" : "#ff4040");
    });
  },
  juno(img, n) {
    sheet(img, n, (ox, fw, i) => person(img, ox, fw, { h: 60, body: "#2a6a4a", skin: "#a87050", hair: "#1a1010", headphones: true, accent: "#7fe0a0", legs: "#2a2a34" }, 0, i * 0.5));
    img.outline("#141018");
    tag(img, "juno", n);
  },
  beat_press(img, n) {
    sheet(img, n, (ox, fw, i) => {
      img.rect(ox + 4, 10, 10, img.h - 10, "#3a1e10");
      img.rect(ox + fw - 14, 10, 10, img.h - 10, "#3a1e10");
      img.rect(ox, 4, fw, 14, "#6e3a1c");
      const y = [30, 70, 96, 60][i];
      img.rect(ox + 16, 18, 6, y - 18, "#b0602a");
      img.rect(ox + fw - 22, 18, 6, y - 18, "#b0602a");
      img.rect(ox + 12, y, fw - 24, 22, "#b0602a");
      img.rect(ox + 12, y + 20, fw - 24, 4, "#ffd090");
      img.rect(ox + 8, img.h - 24, fw - 16, 24, "#4a2a16");
      img.text(ox + 20, 8, "BEAT PRESS", "#ffd090");
      if (i === 2) img.speckle(ox + 10, y + 24, fw - 20, 10, "#ffd090", 0.2, i);
    });
  },
  conveyor(img, n) {
    sheet(img, n, (ox, fw, i) => {
      img.rect(ox, 4, fw, 14, "#3a1e10");
      for (let x = -12 + i * 4; x < fw; x += 16) img.rect(ox + Math.max(0, x), 6, Math.min(10, fw - Math.max(0, x)), 10, "#6e3a1c");
      img.circle(ox + 8, 18, 5, "#b0602a");
      img.circle(ox + fw - 8, 18, 5, "#b0602a");
    });
  },
  panelists(img, n) {
    sheet(img, n, (ox, _fw, i) => {
      for (let k = 0; k < 3; k++) {
        const sub = new Img(40, img.h);
        sub.rect(4, 40, 32, 30, "#8a6a50");
        sub.rect(2, 30, 6, 40, "#6a4a30");
        person(sub, 0, 40, { h: 58, body: ["#c06040", "#4a80c0", "#6aa060"][k], skin: "#e0b090", hair: ["#2a1a10", "#a08060", "#1a1a1a"][k] }, 0, (i + k) % 2 ? 0.4 : 0);
        img.blit(sub, ox + 4 + k * 48, 0);
      }
    });
    img.outline("#2a1810");
    tag(img, "panel", n);
  },
  dial(img, n) {
    sheet(img, n, (ox, fw, i) => {
      img.rect(ox + fw / 2 - 1, 14, 2, 10, "#3a3a44");
      img.circle(ox + fw / 2, 8, 7, "#2a2a34");
      img.circle(ox + fw / 2, 8, 5, i ? "#40e080" : "#ff4040");
      img.line(ox + fw / 2, 8, ox + fw / 2 + (i ? 4 : -4), 4, "#ffffff");
    });
  },
  host(img, n) {
    sheet(img, n, (ox, fw, i) => {
      person(img, ox, fw, { h: 64, body: "#d0a060", skin: "#e8c0a0", hair: "#6a3a20", accent: "#ffffff" }, 0, 0.3 + i * 0.3);
      img.rect(ox + 4, 26, 8, 10, "#e8e4d8");
    });
    img.outline("#2a1810");
    tag(img, "host", n);
  },
  foreman(img, n) {
    sheet(img, n, (ox, fw, i) => {
      person(img, ox, fw, { h: 62, body: "#ff9040", skin: "#c08060", wide: 22, legs: "#3a3a44" }, i ? 1 : -1, 0.6);
      img.ellipse(ox + fw / 2, 5, 7, 4, "#ffd040");
    });
    img.outline("#140c08");
    tag(img, "foreman", n);
  },
  gate_park(img, n) {
    sheet(img, n, (ox, fw, i) => {
      if (i === 0) {
        img.rect(ox, 6, fw, 4, "#2a2a30");
        img.rect(ox, img.h - 8, fw, 4, "#2a2a30");
        for (let x = 4; x < fw; x += 9) {
          img.rect(ox + x, 0, 3, img.h, "#2a2a30");
          img.poly([[ox + x - 1, 4], [ox + x + 1.5, -2], [ox + x + 4, 4]], "#2a2a30");
        }
        img.rect(ox + fw / 2 - 5, img.h / 2 - 6, 10, 12, "#6a6a74");
      } else {
        for (const side of [0, 1]) for (let x = 0; x < 3; x++) img.rect(ox + (side ? fw - 6 - x * 4 : 2 + x * 4), 0, 3, img.h, "#2a2a30");
      }
    });
  },
  gate_factory(img, n) {
    sheet(img, n, (ox, fw, i) => {
      const gap = i ? fw / 2 - 6 : 0;
      img.rect(ox, 0, fw / 2 - gap, img.h, "#4a2a16");
      img.rect(ox + fw / 2 + gap, 0, fw / 2 - gap, img.h, "#4a2a16");
      for (let y = 10; y < img.h; y += 20) {
        img.rect(ox + 2, y, fw / 2 - gap - 4, 3, "#ffd090");
        img.rect(ox + fw / 2 + gap + 2, y, fw / 2 - gap - 4, 3, "#ffd090");
      }
    });
  },
  dominic(img, n) {
    sheet(img, n, (ox, fw, i) => person(img, ox, fw, { h: 64, body: "#7a6a5a", skin: "#e0b090", hair: "#9a9a9a", headphones: true, accent: "#ff9a3a", wide: 20 }, 0, i * 0.5));
    img.outline("#141018");
    tag(img, "dominic", n);
  },
  mic(img, n) {
    sheet(img, n, (ox, fw, i) => {
      img.rect(ox + fw / 2 - 1, 8, 2, img.h - 8, "#2a2a34");
      img.ellipse(ox + fw / 2, 5, 3, 5, "#6a6a74");
      img.circle(ox + fw / 2, 14, 2, i ? "#40e080" : "#ff4040");
      img.rect(ox + 1, img.h - 3, fw - 2, 3, "#2a2a34");
    });
  },
};

// ---- portraits 160x160 (GDD 7.1) ---------------------------------------------------------------------

const PORTRAITS: Record<string, { bg: [string, string]; fig: Fig | "swan" }> = {
  bobbin: { bg: ["#1d1450", "#6b5ab0"], fig: { h: 150, body: "#8a8a98", hood: true, wide: 64 } },
  skein: { bg: ["#5a5c78", "#c8b8b0"], fig: "swan" },
  receptionist: { bg: ["#6a1e6e", "#ff7ae0"], fig: { h: 150, body: "#ff7ae0", skin: "#f0c0a0", hair: "#ffe080", headphones: true, wide: 60 } },
  lyrix: { bg: ["#2a0f3a", "#66e0ff"], fig: { h: 150, body: "#66e0ff", skin: "#c8f4ff", hair: "#ffffff", wide: 56, accent: "#ff7ae0" } },
  lyra: { bg: ["#4a2a20", "#e8c890"], fig: { h: 150, body: "#c87a5a", skin: "#e0b090", hair: "#5a3020", wide: 58 } },
  engineer: { bg: ["#140c24", "#3a5a8a"], fig: { h: 150, body: "#3a5a8a", skin: "#d0a080", hair: "#5a5a5a", headphones: true, wide: 62 } },
  coach: { bg: ["#4a2440", "#a0607a"], fig: { h: 150, body: "#a0507a", skin: "#e8c0a0", hair: "#2a1a1a", wide: 58, accent: "#ffd090" } },
  marcus: { bg: ["#5a5c80", "#e8c8a8"], fig: { h: 150, body: "#a05a30", skin: "#7a4a30", hair: "#1a1010", wide: 66 } },
  commuter: { bg: ["#5a5c80", "#c8c0d0"], fig: { h: 150, body: "#5a6070", skin: "#d0a080", hair: "#3a2a1a", headphones: true, wide: 60 } },
  choreographer: { bg: ["#1a0a2a", "#6a1e6e"], fig: { h: 150, body: "#2a2a34", skin: "#e0b090", hair: "#e8e8f4", wide: 58, accent: "#ff4040" } },
  juno: { bg: ["#140c08", "#6e3a1c"], fig: { h: 150, body: "#2a6a4a", skin: "#a87050", hair: "#1a1010", headphones: true, wide: 58, accent: "#7fe0a0" } },
  host: { bg: ["#6a5040", "#d8c0a0"], fig: { h: 150, body: "#d0a060", skin: "#e8c0a0", hair: "#6a3a20", wide: 58 } },
  dominic: { bg: ["#2a1810", "#6a4030"], fig: { h: 150, body: "#7a6a5a", skin: "#e0b090", hair: "#9a9a9a", headphones: true, wide: 66, accent: "#ff9a3a" } },
};

function portrait(img: Img, id: string): void {
  const p = PORTRAITS[id];
  img.gradient(0, 0, 160, 160, p.bg[0], p.bg[1], 6);
  if (p.fig === "swan") {
    img.ellipse(70, 130, 60, 34, "#d8d8e0");
    img.rect(96, 50, 16, 80, "#d8d8e0");
    img.ellipse(112, 46, 22, 16, "#d8d8e0");
    img.poly([[128, 44], [150, 50], [128, 54]], "#e09040");
    img.circle(114, 42, 3, "#1a1a24");
  } else {
    const fig = new Img(160, 300);
    person(fig, 0, 160, { ...p.fig, h: 290 });
    for (let y = 0; y < 160; y++) for (let x = 0; x < 160; x++) {
      const c = fig.get(x, y + 4);
      if (c[3]) img.px(x, y, c);
    }
  }
  img.text(4, 152, id.toUpperCase(), "#ffffff", 90);
}

export function draw(recipe: string, w: number, h: number, frames: number): Img {
  const img = new Img(w, h);
  const [kind, id] = recipe.split(":");
  if (kind === "room") {
    const fn = ROOMS[id];
    if (!fn) throw new Error(`No room recipe ${id}`);
    fn(img);
  } else if (kind === "char") {
    const fn = CHARS[id];
    if (!fn) throw new Error(`No character recipe ${id}`);
    fn(img, frames);
  } else if (kind === "portrait") portrait(img, id);
  else throw new Error(`Unknown recipe ${recipe}`);
  return img;
}

export const PALETTES = PAL;
