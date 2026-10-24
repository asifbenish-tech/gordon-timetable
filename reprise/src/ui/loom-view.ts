// src/ui/loom-view.ts: the full-screen weave on dark cloth (GDD 4.3, 7.6). Threads braid left to right
// in time with the music; thickness follows live loudness. Knots are tangles, tethers taut lines
// leaving the frame, seals wax stamps, the golden thread a shimmering line that grows.
import * as Phaser from "phaser";
import * as Tone from "tone";
import type { StemDef } from "../content/types";
import type { Song } from "../audio/song";
import type { Game } from "../world/game";

export const LOOM_TOP = 34;
export const LOOM_BOTTOM = 286;

export interface ThreadRow {
  id: string; // stem id or "spool:N"
  stem: StemDef | null;
  y: number;
  color: number;
}

export function threadRows(g: Game, song: Song): ThreadRow[] {
  const stems = song.model.stems().filter((s) => !s.golden);
  const guests = song.guestSlots().filter(({ slot }) => !Object.values(song.model.mods.replaced).includes(slot));
  const n = stems.length + guests.length;
  const gap = (LOOM_BOTTOM - LOOM_TOP) / Math.max(1, n);
  const rows: ThreadRow[] = stems.map((s, i) => ({ id: s.id, stem: s, y: LOOM_TOP + gap * (i + 0.5), color: Phaser.Display.Color.HexStringToColor(s.color).color }));
  guests.forEach(({ slot, thread }, i) => {
    const src = g.model(thread.song).def.stems.find((s) => s.id === thread.stem);
    rows.push({ id: `spool:${slot}`, stem: src ?? null, y: LOOM_TOP + gap * (stems.length + i + 0.5), color: Phaser.Display.Color.HexStringToColor(src?.color ?? "#cccccc").color });
  });
  return rows;
}

export class LoomScene extends Phaser.Scene {
  private g!: Game;
  private song!: Song;
  private gfx!: Phaser.GameObjects.Graphics;
  selected: string | null = null;

  constructor() {
    super({ key: "loom" });
  }

  init(data: { game: Game; song: Song }): void {
    this.g = data.game;
    this.song = data.song;
    this.selected = null;
  }

  create(): void {
    this.gfx = this.add.graphics();
    this.input.on("pointerdown", (p: Phaser.Input.Pointer) => {
      if (p.y >= 300) return;
      const rows = threadRows(this.g, this.song);
      let best: ThreadRow | null = null;
      for (const r of rows) if (!best || Math.abs(r.y - p.y) < Math.abs(best.y - p.y)) best = r;
      if (best && Math.abs(best.y - p.y) < 24) this.g.hudSelectThread?.(best.id);
    });
  }

  override update(): void {
    const g = this.gfx;
    const now = Tone.now();
    const m = this.song.model;
    const beats = this.g.conductor.beatsAt(now);
    g.clear();
    // dark cloth with a faint warp
    g.fillStyle(0x15121c, 0.97).fillRect(0, 0, 640, 304);
    g.lineStyle(1, 0x221d2c, 1);
    for (let x = 6; x < 640; x += 12) g.lineBetween(x, 0, x, 304);
    // the bar grid (the warp moves with the music)
    const off = ((beats % 4) / 4) * 160;
    g.lineStyle(1, 0x3a3150, 1);
    for (let x = -off; x < 640; x += 160) g.lineBetween(Math.round(x + 160), 8, Math.round(x + 160), 296);

    const rows = threadRows(this.g, this.song);
    const golden = m.def.stems.find((s) => s.golden && m.stems().includes(s));
    for (const r of rows) {
      const isGuest = r.id.startsWith("spool:");
      const stemId = isGuest ? null : r.id;
      const silenced = stemId ? m.silenced(stemId, now) : false;
      const muted = stemId ? !m.audible(stemId, now) : m.isolated !== null && m.isolated !== r.id;
      const loud = this.song.loudness(r.id);
      const thick = silenced || muted ? 1 : 2 + Math.round(loud * 5);
      const alpha = silenced ? 0.35 : muted ? 0.45 : 1;
      const sag = stemId && m.pulled.has(stemId) ? 14 : 0;
      const phase = beats * Math.PI * 0.5 + r.y * 0.07;
      const pts: [number, number][] = [];
      for (let x = 0; x <= 640; x += 4) {
        const y = r.y + Math.sin(x * 0.035 + phase) * (3 + loud * 3) + sag * Math.sin((x / 640) * Math.PI);
        pts.push([x, Math.round(y)]);
      }
      g.lineStyle(thick, r.color, alpha);
      g.beginPath();
      g.moveTo(pts[0][0], pts[0][1]);
      for (const [x, y] of pts) g.lineTo(x, y);
      g.strokePath();
      if (this.selected === r.id) {
        g.lineStyle(1, 0xffffff, 0.8);
        g.strokeRect(4, r.y - 16, 632, 32);
      }
      const stem = stemId ? m.stem(stemId) : null;
      if (stem?.sealed) {
        // a wax stamp: PRESET, DO NOT EDIT
        g.fillStyle(0x8a1a22, 1).fillCircle(588, r.y, 9);
        g.fillStyle(0xb52a33, 1).fillCircle(588, r.y, 6);
      }
      if (stem?.knot && m.isTied(stem.id)) {
        // a tight grid-shaped tangle that pulses with the thread
        const k = 1 + loud * 2;
        g.lineStyle(2, 0xd8d8e8, 1);
        for (let i = -2; i <= 2; i++) {
          g.lineBetween(300 + i * 4 * k, r.y - 9, 300 + i * 4 * k, r.y + 9);
          g.lineBetween(290, r.y + i * 4, 310, r.y + i * 4);
        }
      }
      if (stem?.tether) {
        const state = m.tether(stem.id, now);
        g.lineStyle(state === "taut" ? 2 : 1, r.color, state === "taut" ? 0.9 : 0.4);
        if (state === "taut") g.lineBetween(560, r.y, 640, r.y - 18);
        else {
          g.beginPath();
          g.moveTo(560, r.y);
          for (let x = 560; x <= 640; x += 8) g.lineTo(x, r.y + Math.sin(((x - 560) / 80) * Math.PI) * 14);
          g.strokePath();
        }
      }
      if (stemId && m.replacedBy(stemId) !== null) {
        const slot = m.replacedBy(stemId)!;
        const src = this.g.spindle.spool(slot);
        if (src?.kind === "thread") {
          const s2 = this.g.model(src.thread.song).def.stems.find((s) => s.id === src.thread.stem);
          const c = Phaser.Display.Color.HexStringToColor(s2?.color ?? "#ffffff").color;
          g.lineStyle(2 + Math.round(this.song.loudness(`spool:${slot}`) * 5), c, 1);
          g.beginPath();
          g.moveTo(0, r.y + 4);
          for (let x = 0; x <= 640; x += 4) g.lineTo(x, Math.round(r.y + 4 + Math.cos(x * 0.03 + phase) * 4));
          g.strokePath();
        }
      }
    }

    if (golden) {
      const level = this.song.goldenCurve(m.goldenLevel(now));
      const a = rows.find((r) => r.stem?.masksGolden && r.stem.masksGolden >= 0.35 && r.stem.knot) ?? rows[Math.floor(rows.length / 2)];
      const y = a ? a.y + 10 : 160;
      const shimmer = (Math.sin(performance.now() / 120) + 1) / 2;
      if (level < 0.05) {
        // a glint where other threads overlap
        g.fillStyle(0xffe9a0, 0.3 + 0.5 * shimmer).fillCircle(320, y, 2);
      } else {
        const len = 640 * level;
        g.lineStyle(1 + Math.round(level * 3), 0xf3c64b, 0.4 + 0.6 * level);
        g.beginPath();
        g.moveTo(320 - len / 2, y);
        for (let x = 320 - len / 2; x <= 320 + len / 2; x += 4) g.lineTo(x, Math.round(y + Math.sin(x * 0.05 + beats * 2) * 3));
        g.strokePath();
        g.fillStyle(0xfff3c0, shimmer).fillCircle(320 + Math.sin(beats) * len * 0.45, y, 1 + level * 2);
      }
    }
  }
}
