// src/audio/song.ts: one song = stems locked to the Transport, each on its own gain.
// Until a stem is rendered (assets/manifest.json status), it is played from its notation
// by a placeholder synth; gameplay reads the hits data either way (GDD 9.3 rule 5).
import * as Tone from "tone";
import type { NoteEvent, SongDef, StemDef } from "../content/types";
import type { GameBus, ThreadRef } from "../core/bus";
import type { LoomModel } from "../core/loom";
import { STEPS_PER_BAR, type Conductor } from "./conductor";
import { makeInstrument, type Instrument } from "./instruments";
import type { Mixer } from "./mixer";

export interface StemData {
  notes: NoteEvent[];
  hits: number[];
  bars: number;
  instrument: string;
}

type Bucket = Map<number, { frac: number; ev: NoteEvent }[]>;

function bucket(notes: NoteEvent[]): Bucket {
  const b: Bucket = new Map();
  for (const ev of notes) {
    const pos = ev.t * 4;
    const step = Math.floor(pos + 1e-6);
    let list = b.get(step);
    if (!list) b.set(step, (list = []));
    list.push({ frac: pos - step, ev });
  }
  return b;
}

function hitBucket(hits: number[]): Set<number> {
  return new Set(hits.map((h) => Math.round(h * 4)));
}

interface Voice {
  inst: Instrument;
  gain: Tone.Gain;
  vibrato: Tone.Vibrato;
  shaper: Tone.Chebyshev | null;
  notes: Bucket;
  hits: Set<number>;
  len: number; // steps
  recent: { time: number; vel: number }[];
}

export class Song {
  private out: Tone.Gain;
  private voices = new Map<string, Voice>();
  private guests = new Map<number, Voice & { thread: ThreadRef }>();
  private startStep = -1;
  private unsub: (() => void) | null = null;
  goldenCurve = (level: number) => level;
  guestLevel = 0.45;

  constructor(
    readonly model: LoomModel,
    private data: (song: string, stem: string) => StemData,
    private conductor: Conductor,
    mixer: Mixer,
    private bus: GameBus,
  ) {
    this.out = new Tone.Gain(1).connect(mixer.music);
  }

  get def(): SongDef {
    return this.model.def;
  }

  private makeVoice(stem: StemDef | null, d: StemData): Voice {
    const inst = makeInstrument(d.instrument);
    const gain = new Tone.Gain(stem?.level ?? 1).connect(this.out);
    const vibrato = new Tone.Vibrato(7, 0.7).connect(gain);
    vibrato.wet.value = 0;
    let shaper: Tone.Chebyshev | null = null;
    if (stem?.knot) {
      shaper = new Tone.Chebyshev(31).connect(vibrato);
      shaper.wet.value = 0.45;
      inst.output.connect(shaper);
    } else inst.output.connect(vibrato);
    return { inst, gain, vibrato, shaper, notes: bucket(d.notes), hits: hitBucket(d.hits), len: d.bars * STEPS_PER_BAR, recent: [] };
  }

  start(): void {
    for (const stem of this.def.stems) this.voices.set(stem.id, this.makeVoice(stem, this.data(this.def.id, stem.id)));
    const now = this.conductor.currentStep();
    this.startStep = Math.ceil((now + 1) / STEPS_PER_BAR) * STEPS_PER_BAR;
    this.unsub = this.conductor.onStep((step, time) => this.onStep(step, time));
  }

  addGuest(slot: number, thread: ThreadRef): void {
    this.removeGuest(slot);
    const d = this.data(thread.song, thread.stem);
    const v = this.makeVoice(null, d);
    this.guests.set(slot, { ...v, thread });
  }

  removeGuest(slot: number): void {
    const g = this.guests.get(slot);
    if (!g) return;
    this.disposeVoice(g);
    this.guests.delete(slot);
  }

  /** Local position of the song, in steps; -1 before it starts. */
  localStep(): number {
    const s = this.conductor.currentStep();
    if (s < this.startStep) return -1;
    return (s - this.startStep) % (this.def.bars * STEPS_PER_BAR);
  }

  private onStep(step: number, time: number): void {
    if (step < this.startStep) return;
    const rel = step - this.startStep;
    const stepSec = this.conductor.beatSeconds() / 4;
    const m = this.model;
    for (const stem of m.stems()) {
      const v = this.voices.get(stem.id);
      if (!v) continue;
      const local = rel % v.len;
      const quick = m.state(stem.id, "quickening", time);
      const slow = m.state(stem.id, "quickening_rev", time);
      const sources: { src: number; offset: number; stretch: number }[] = quick
        ? [{ src: (local * 2) % v.len, offset: 0, stretch: 0.5 }, { src: (local * 2 + 1) % v.len, offset: 0.5, stretch: 0.5 }]
        : slow
          ? local % 2 === 0 ? [{ src: local / 2, offset: 0, stretch: 2 }] : []
          : [{ src: local, offset: 0, stretch: 1 }];
      const sounding = m.audible(stem.id, time) && !(stem.golden && m.goldenLevel(time) <= 0.01);
      for (const { src, offset, stretch } of sources) {
        if (sounding) {
          for (const { frac, ev } of v.notes.get(src) ?? []) {
            const t = time + (offset + frac * stretch) * stepSec;
            v.inst.play(ev.m, ev.d * this.conductor.beatSeconds() * stretch, t, ev.v);
            v.recent.push({ time: t, vel: ev.v });
          }
        }
        if (v.hits.has(src) && !m.silenced(stem.id, time)) {
          const t = time + offset * stepSec;
          Tone.getDraw().schedule(() => this.bus.emit("hit", { song: this.def.id, stem: stem.id, time: t }), t);
        }
      }
      if (v.recent.length > 12) v.recent.splice(0, v.recent.length - 12);
    }
    const isolated = m.isolated !== null;
    for (const [slot, g] of this.guests) {
      const local = rel % g.len;
      const replacing = Object.entries(m.mods.replaced).find(([, s]) => s === slot)?.[0];
      if (isolated && m.isolated !== `spool:${slot}`) continue;
      for (const { frac, ev } of g.notes.get(local) ?? []) {
        const t = time + frac * stepSec;
        g.inst.play(ev.m, ev.d * this.conductor.beatSeconds(), t, ev.v);
        g.recent.push({ time: t, vel: ev.v });
      }
      if (replacing && g.hits.has(local)) {
        Tone.getDraw().schedule(() => this.bus.emit("hit", { song: this.def.id, stem: `spool:${slot}`, time }), time);
      }
      if (g.recent.length > 12) g.recent.splice(0, g.recent.length - 12);
    }
  }

  /** Per frame: golden level, knots, detuning and swelling become gains and effect amounts. */
  update(): void {
    const now = Tone.now();
    const m = this.model;
    for (const stem of m.stems()) {
      const v = this.voices.get(stem.id);
      if (!v) continue;
      let level = stem.level ?? 1;
      if (stem.golden) level = this.goldenCurve(m.goldenLevel(now));
      else if (!m.audible(stem.id, now)) level = 0;
      if (m.state(stem.id, "swelling", now)) level *= 1.6;
      if (m.state(stem.id, "swelling_rev", now)) level *= 0.3;
      if (Math.abs(v.gain.gain.value - level) > 0.01) v.gain.gain.rampTo(level, 0.05);
      const detune = m.state(stem.id, "tuning_rev", now) ? 1 : 0;
      if (v.vibrato.wet.value !== detune) v.vibrato.wet.value = detune;
      if (v.shaper) {
        const wet = m.isTied(stem.id) ? 0.45 : 0;
        if (v.shaper.wet.value !== wet) v.shaper.wet.value = wet;
      }
    }
    const replacedSlots = new Set(Object.values(m.mods.replaced));
    for (const [slot, g] of this.guests) {
      const level = replacedSlots.has(slot) ? 1 : this.guestLevel;
      if (Math.abs(g.gain.gain.value - level) > 0.01) g.gain.gain.rampTo(level, 0.1);
    }
  }

  /** 0..1 loudness for drawing thread thickness (from the notation, not audio analysis). */
  loudness(stemId: string): number {
    const v = stemId.startsWith("spool:") ? this.guests.get(Number(stemId.slice(6))) : this.voices.get(stemId);
    if (!v) return 0;
    const now = Tone.now();
    let env = 0;
    for (const r of v.recent) {
      if (r.time > now) continue;
      env = Math.max(env, r.vel * Math.exp(-(now - r.time) / 0.22));
    }
    return env;
  }

  guestSlots(): { slot: number; thread: ThreadRef }[] {
    return [...this.guests].map(([slot, g]) => ({ slot, thread: g.thread }));
  }

  private disposeVoice(v: Voice): void {
    const g = v.gain;
    g.gain.rampTo(0, 0.08);
    const dispose = () => {
      v.inst.dispose();
      v.vibrato.dispose();
      v.shaper?.dispose();
      g.dispose();
    };
    Tone.getContext().setTimeout(dispose, 0.3);
  }

  dispose(): void {
    this.unsub?.();
    for (const v of this.voices.values()) this.disposeVoice(v);
    for (const g of this.guests.values()) this.disposeVoice(g);
    this.voices.clear();
    this.guests.clear();
    const out = this.out;
    Tone.getContext().setTimeout(() => out.dispose(), 0.4);
  }
}
