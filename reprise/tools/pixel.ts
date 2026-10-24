// tools/pixel.ts: a tiny raster for placeholder art: flat shapes, ordered dithering, a 3x5 font, PNG out.
import { deflateSync } from "node:zlib";

export type RGBA = [number, number, number, number];

export function hex(c: string, a = 255): RGBA {
  const v = c.replace("#", "");
  const n = parseInt(v.length === 3 ? v.split("").map((x) => x + x).join("") : v, 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255, a];
}

export function mix(a: string, b: string, t: number): string {
  const x = hex(a);
  const y = hex(b);
  const c = x.slice(0, 3).map((v, i) => Math.round(v + (y[i] - v) * t));
  return "#" + c.map((v) => v.toString(16).padStart(2, "0")).join("");
}

const BAYER4 = [
  [0, 8, 2, 10],
  [12, 4, 14, 6],
  [3, 11, 1, 9],
  [15, 7, 13, 5],
];

const FONT: Record<string, string> = {
  A: "010101111101101", B: "110101110101110", C: "011100100100011", D: "110101101101110", E: "111100110100111",
  F: "111100110100100", G: "011100101101011", H: "101101111101101", I: "111010010010111", J: "001001001101010",
  K: "101101110101101", L: "100100100100111", M: "101111111101101", N: "110101101101101", O: "010101101101010",
  P: "110101110100100", Q: "010101101110011", R: "110101110101101", S: "011100010001110", T: "111010010010010",
  U: "101101101101111", V: "101101101101010", W: "101101111111101", X: "101101010101101", Y: "101101010010010",
  Z: "111001010100111", "0": "111101101101111", "1": "010110010010111", "2": "110001010100111", "3": "110001010001110",
  "4": "101101111001001", "5": "111100110001110", "6": "011100111101111", "7": "111001010010010", "8": "111101111101111",
  "9": "111101111001110", "_": "000000000000111", "-": "000000111000000", ".": "000000000000010", " ": "000000000000000",
  "!": "010010010000010", "?": "110001010000010", "'": "010010000000000", ":": "000010000010000", "/": "001001010100100",
  "&": "010101010101011", "(": "010100100100010", ")": "010001001001010", "+": "000010111010000", "#": "101111101111101",
};

export class Img {
  readonly data: Uint8Array;
  constructor(readonly w: number, readonly h: number) {
    this.data = new Uint8Array(w * h * 4);
  }

  px(x: number, y: number, c: RGBA): void {
    x = Math.floor(x);
    y = Math.floor(y);
    if (x < 0 || y < 0 || x >= this.w || y >= this.h) return;
    const i = (y * this.w + x) * 4;
    const a = c[3] / 255;
    if (a >= 1) {
      this.data[i] = c[0];
      this.data[i + 1] = c[1];
      this.data[i + 2] = c[2];
      this.data[i + 3] = 255;
      return;
    }
    const da = this.data[i + 3] / 255;
    const oa = a + da * (1 - a);
    if (oa <= 0) return;
    for (let k = 0; k < 3; k++) this.data[i + k] = Math.round((c[k] * a + this.data[i + k] * da * (1 - a)) / oa);
    this.data[i + 3] = Math.round(oa * 255);
  }

  get(x: number, y: number): RGBA {
    const i = (y * this.w + x) * 4;
    return [this.data[i], this.data[i + 1], this.data[i + 2], this.data[i + 3]];
  }

  rect(x: number, y: number, w: number, h: number, c: string, a = 255): this {
    const col = hex(c, a);
    for (let j = Math.max(0, Math.floor(y)); j < Math.min(this.h, Math.floor(y + h)); j++)
      for (let i = Math.max(0, Math.floor(x)); i < Math.min(this.w, Math.floor(x + w)); i++) this.px(i, j, col);
    return this;
  }

  fill(c: string): this {
    return this.rect(0, 0, this.w, this.h, c);
  }

  /** Vertical gradient in banded steps with 4x4 ordered dithering between them (GDD 7.2). */
  gradient(x: number, y: number, w: number, h: number, top: string, bottom: string, steps = 6): this {
    for (let j = 0; j < h; j++) {
      const t = (j / Math.max(1, h - 1)) * (steps - 1);
      const band = Math.floor(t);
      const frac = t - band;
      for (let i = 0; i < w; i++) {
        const k = band + (frac * 16 > BAYER4[(y + j) & 3][(x + i) & 3] ? 1 : 0);
        this.px(x + i, y + j, hex(mix(top, bottom, Math.min(1, k / (steps - 1)))));
      }
    }
    return this;
  }

  /** Dithered blend of a flat colour over whatever is there: shading without new colours. */
  shade(x: number, y: number, w: number, h: number, c: string, amount: number): this {
    const col = hex(c);
    for (let j = 0; j < h; j++)
      for (let i = 0; i < w; i++) if (amount * 16 > BAYER4[(y + j) & 3][(x + i) & 3]) this.px(x + i, y + j, col);
    return this;
  }

  circle(cx: number, cy: number, r: number, c: string, a = 255): this {
    return this.ellipse(cx, cy, r, r, c, a);
  }

  ellipse(cx: number, cy: number, rx: number, ry: number, c: string, a = 255): this {
    const col = hex(c, a);
    for (let j = Math.floor(cy - ry); j <= Math.ceil(cy + ry); j++)
      for (let i = Math.floor(cx - rx); i <= Math.ceil(cx + rx); i++) {
        const dx = (i + 0.5 - cx) / rx;
        const dy = (j + 0.5 - cy) / ry;
        if (dx * dx + dy * dy <= 1) this.px(i, j, col);
      }
    return this;
  }

  poly(pts: [number, number][], c: string, a = 255): this {
    const col = hex(c, a);
    const ys = pts.map((p) => p[1]);
    for (let y = Math.floor(Math.min(...ys)); y <= Math.ceil(Math.max(...ys)); y++) {
      const xs: number[] = [];
      for (let i = 0; i < pts.length; i++) {
        const [x0, y0] = pts[i];
        const [x1, y1] = pts[(i + 1) % pts.length];
        if (y0 <= y + 0.5 !== y1 <= y + 0.5) xs.push(x0 + ((y + 0.5 - y0) / (y1 - y0)) * (x1 - x0));
      }
      xs.sort((a2, b) => a2 - b);
      for (let k = 0; k + 1 < xs.length; k += 2) for (let x = Math.round(xs[k]); x < Math.round(xs[k + 1]); x++) this.px(x, y, col);
    }
    return this;
  }

  line(x0: number, y0: number, x1: number, y1: number, c: string, a = 255): this {
    const col = hex(c, a);
    const n = Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0), 1);
    for (let i = 0; i <= n; i++) this.px(Math.round(x0 + ((x1 - x0) * i) / n), Math.round(y0 + ((y1 - y0) * i) / n), col);
    return this;
  }

  /** Scattered pixels, seeded so placeholders are byte-identical between runs. */
  speckle(x: number, y: number, w: number, h: number, c: string, density: number, seed: number, a = 255): this {
    let s = seed >>> 0 || 1;
    const rnd = () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
    const n = Math.floor(w * h * density);
    for (let i = 0; i < n; i++) this.px(x + rnd() * w, y + rnd() * h, hex(c, a));
    return this;
  }

  text(x: number, y: number, s: string, c: string, a = 255): this {
    const col = hex(c, a);
    let cx = x;
    for (const ch of s.toUpperCase()) {
      const g = FONT[ch] ?? FONT["?"];
      for (let j = 0; j < 5; j++) for (let i = 0; i < 3; i++) if (g[j * 3 + i] === "1") this.px(cx + i, y + j, col);
      cx += 4;
    }
    return this;
  }

  textWidth(s: string): number {
    return s.length * 4 - 1;
  }

  blit(src: Img, x: number, y: number): this {
    for (let j = 0; j < src.h; j++)
      for (let i = 0; i < src.w; i++) {
        const c = src.get(i, j);
        if (c[3]) this.px(x + i, y + j, c);
      }
    return this;
  }

  /** One-pixel dark outline around opaque shapes: sprites read against busy backgrounds. */
  outline(c: string): this {
    const col = hex(c);
    const mask = new Uint8Array(this.w * this.h);
    for (let i = 0; i < this.w * this.h; i++) mask[i] = this.data[i * 4 + 3] > 0 ? 1 : 0;
    for (let y = 0; y < this.h; y++)
      for (let x = 0; x < this.w; x++) {
        if (mask[y * this.w + x]) continue;
        const near = [[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dx, dy]) => {
          const nx = x + dx;
          const ny = y + dy;
          return nx >= 0 && ny >= 0 && nx < this.w && ny < this.h && mask[ny * this.w + nx];
        });
        if (near) this.px(x, y, col);
      }
    return this;
  }

  png(): Buffer {
    const raw = Buffer.alloc((this.w * 4 + 1) * this.h);
    for (let y = 0; y < this.h; y++) {
      raw[y * (this.w * 4 + 1)] = 0;
      Buffer.from(this.data.buffer, this.data.byteOffset + y * this.w * 4, this.w * 4).copy(raw, y * (this.w * 4 + 1) + 1);
    }
    const chunk = (type: string, body: Buffer) => {
      const len = Buffer.alloc(4);
      len.writeUInt32BE(body.length);
      const td = Buffer.concat([Buffer.from(type), body]);
      const crc = Buffer.alloc(4);
      crc.writeUInt32BE(crc32(td));
      return Buffer.concat([len, td, crc]);
    };
    const ihdr = Buffer.alloc(13);
    ihdr.writeUInt32BE(this.w, 0);
    ihdr.writeUInt32BE(this.h, 4);
    ihdr[8] = 8;
    ihdr[9] = 6;
    return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk("IHDR", ihdr), chunk("IDAT", deflateSync(raw, { level: 9 })), chunk("IEND", Buffer.alloc(0))]);
  }
}

const CRC = new Uint32Array(256).map((_, n) => {
  let c = n;
  for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
  return c >>> 0;
});

function crc32(b: Buffer): number {
  let c = 0xffffffff;
  for (const x of b) c = CRC[(c ^ x) & 255] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

/** Reads back a PNG this module wrote (8-bit RGBA, no interlace). Used by make-normals.ts. */
export function readPng(buf: Buffer, inflate: (b: Buffer) => Buffer): Img {
  let p = 8;
  let w = 0;
  let h = 0;
  const idat: Buffer[] = [];
  while (p < buf.length) {
    const len = buf.readUInt32BE(p);
    const type = buf.toString("ascii", p + 4, p + 8);
    const body = buf.subarray(p + 8, p + 8 + len);
    if (type === "IHDR") {
      w = body.readUInt32BE(0);
      h = body.readUInt32BE(4);
    } else if (type === "IDAT") idat.push(body);
    p += 12 + len;
  }
  const raw = inflate(Buffer.concat(idat));
  const img = new Img(w, h);
  const stride = w * 4;
  const prev = new Uint8Array(stride);
  for (let y = 0; y < h; y++) {
    const f = raw[y * (stride + 1)];
    const line = raw.subarray(y * (stride + 1) + 1, (y + 1) * (stride + 1));
    const out = new Uint8Array(stride);
    for (let i = 0; i < stride; i++) {
      const a = i >= 4 ? out[i - 4] : 0;
      const b = prev[i];
      const c = i >= 4 ? prev[i - 4] : 0;
      const x = line[i];
      let v = x;
      if (f === 1) v = x + a;
      else if (f === 2) v = x + b;
      else if (f === 3) v = x + ((a + b) >> 1);
      else if (f === 4) {
        const pp = a + b - c;
        const pa = Math.abs(pp - a);
        const pb = Math.abs(pp - b);
        const pc = Math.abs(pp - c);
        v = x + (pa <= pb && pa <= pc ? a : pb <= pc ? b : c);
      }
      out[i] = v & 255;
    }
    img.data.set(out, y * stride);
    prev.set(out);
  }
  return img;
}
