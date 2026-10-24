// src/audio/instruments.ts: placeholder synths. Every stem and teaching voice plays
// through one of these until a rendered stem exists (GDD 8.9, DECISIONS.md D-017).
import * as Tone from "tone";

export interface Instrument {
  play(midi: number, dur: number, time: number, vel: number): void;
  readonly output: Tone.ToneAudioNode;
  dispose(): void;
}

const hz = (m: number): number => 440 * Math.pow(2, (m - 69) / 12);

type Node = Tone.ToneAudioNode & { dispose(): unknown };

function build(nodes: Node[], output: Tone.ToneAudioNode, play: Instrument["play"]): Instrument {
  // Tone's monophonic voices and envelopes need start times in order; two callers scheduling the same
  // instrument a few milliseconds apart (a loop and a stinger, say) must never throw.
  let last = -1;
  return {
    play(m, d, t, v) {
      if (t <= last) t = last + 0.0005;
      last = t;
      play(m, d, t, v);
    },
    output,
    dispose: () => {
      for (const n of nodes) n.dispose();
    },
  };
}

// Tone's option types want every field; these placeholders set only what they need.
function poly(opts: object, maxPolyphony = 16): Tone.PolySynth<Tone.Synth> {
  const p = new Tone.PolySynth(Tone.Synth, opts as never);
  p.maxPolyphony = maxPolyphony;
  return p;
}

const makers: Record<string, () => Instrument> = {
  /** Bobbin's notes: a clarinet blended with a harp attack and a glass-harmonica sustain (GDD 8.5). */
  distaff() {
    const out = new Tone.Gain(1);
    const clarFilter = new Tone.Filter(1900, "lowpass").connect(out);
    const clar = poly({ oscillator: { type: "square" }, envelope: { attack: 0.025, decay: 0.2, sustain: 0.55, release: 0.35 } }, 16).connect(clarFilter);
    clar.volume.value = -14;
    const harp = new Tone.PluckSynth({ attackNoise: 1.2, dampening: 4200, resonance: 0.92 }).connect(out);
    harp.volume.value = -4;
    const glass = poly({ oscillator: { type: "sine" }, envelope: { attack: 0.12, decay: 0.3, sustain: 0.6, release: 1.4 } }, 16).connect(out);
    glass.volume.value = -16;
    return build([clar, clarFilter, harp, glass, out], out, (m, d, t, v) => {
      clar.triggerAttackRelease(hz(m), d, t, v);
      harp.triggerAttack(hz(m), t);
      glass.triggerAttackRelease(hz(m + 12), d * 1.4, t, v * 0.8);
    });
  },
  swan() {
    const out = new Tone.Gain(1);
    const f = new Tone.Filter(2400, "lowpass").connect(out);
    const s = new Tone.FMSynth({ harmonicity: 1.5, modulationIndex: 5, envelope: { attack: 0.02, decay: 0.2, sustain: 0.4, release: 0.3 } }).connect(f);
    s.volume.value = -10;
    return build([s, f, out], out, (m, d, t, v) => s.triggerAttackRelease(hz(m + 12), d, t, v));
  },
  bucket() {
    const out = new Tone.Gain(1);
    const mem = new Tone.MembraneSynth({ pitchDecay: 0.012, octaves: 1.6, envelope: { attack: 0.001, decay: 0.22, sustain: 0, release: 0.05 } }).connect(out);
    const noise = new Tone.NoiseSynth({ noise: { type: "pink" }, envelope: { attack: 0.001, decay: 0.06, sustain: 0 } } as never).connect(out);
    noise.volume.value = -16;
    return build([mem, noise, out], out, (m, d, t, v) => {
      mem.triggerAttackRelease(hz(m - 12), Math.min(d, 0.2), t, v);
      noise.triggerAttackRelease(0.05, t, v);
    });
  },
  snare() {
    const out = new Tone.Gain(1);
    const f = new Tone.Filter(1800, "bandpass").connect(out);
    const n = new Tone.NoiseSynth({ noise: { type: "white" }, envelope: { attack: 0.001, decay: 0.12, sustain: 0 } } as never).connect(f);
    const mem = new Tone.MembraneSynth({ pitchDecay: 0.01, octaves: 1, envelope: { attack: 0.001, decay: 0.08, sustain: 0 } }).connect(out);
    mem.volume.value = -8;
    return build([n, f, mem, out], out, (m, _d, t, v) => {
      n.triggerAttackRelease(0.1, t, v);
      mem.triggerAttackRelease(hz(m), 0.06, t, v);
    });
  },
  coach() {
    const out = new Tone.Gain(1);
    const vib = new Tone.Vibrato(5.2, 0.12).connect(out);
    const f = new Tone.Filter(1500, "lowpass").connect(vib);
    const s = poly({ oscillator: { type: "fatsawtooth", count: 2, spread: 12 } as never, envelope: { attack: 0.06, decay: 0.2, sustain: 0.7, release: 0.3 } }, 16).connect(f);
    s.volume.value = -14;
    return build([s, f, vib, out], out, (m, d, t, v) => s.triggerAttackRelease(hz(m + 12), d, t, v));
  },
  /** The teenage hum: slightly flat, a little breathy (GDD 6, puzzle 1). */
  hum() {
    const out = new Tone.Gain(1);
    const vib = new Tone.Vibrato(4.6, 0.08).connect(out);
    const s = poly({ oscillator: { type: "triangle" }, detune: -22, envelope: { attack: 0.09, decay: 0.2, sustain: 0.8, release: 0.4 } }, 16).connect(vib);
    s.volume.value = -6;
    return build([s, vib, out], out, (m, d, t, v) => s.triggerAttackRelease(hz(m + 12), d, t, v));
  },
  choir() {
    const out = new Tone.Gain(1);
    const f = new Tone.Filter(950, "lowpass").connect(out);
    const s = poly({ oscillator: { type: "fatsine", count: 3, spread: 18 } as never, envelope: { attack: 0.5, decay: 0.3, sustain: 0.8, release: 1.8 } }, 20).connect(f);
    s.volume.value = -12;
    return build([s, f, out], out, (m, d, t, v) => s.triggerAttackRelease(hz(m), d, t, v));
  },
  press() {
    const out = new Tone.Gain(1);
    const s = new Tone.FMSynth({ harmonicity: 3.01, modulationIndex: 12, envelope: { attack: 0.001, decay: 0.28, sustain: 0, release: 0.2 }, modulationEnvelope: { attack: 0.001, decay: 0.2, sustain: 0, release: 0.1 } }).connect(out);
    s.volume.value = -8;
    return build([s, out], out, (m, d, t, v) => s.triggerAttackRelease(hz(m), Math.min(d, 0.3), t, v));
  },
  pedal() {
    const out = new Tone.Gain(1);
    const s = new Tone.PluckSynth({ attackNoise: 5, dampening: 7000, resonance: 0.6 }).connect(out);
    return build([s, out], out, (m, _d, t) => s.triggerAttack(hz(m + 12), t));
  },
  piano() {
    const out = new Tone.Gain(1);
    const s = poly({ oscillator: { type: "triangle" }, envelope: { attack: 0.004, decay: 1.4, sustain: 0.08, release: 0.9 } }, 24).connect(out);
    s.volume.value = -8;
    return build([s, out], out, (m, d, t, v) => s.triggerAttackRelease(hz(m), d, t, v));
  },
  /** The grandmother's piano before Tuning: every string a little wrong. */
  piano_old() {
    const out = new Tone.Gain(1);
    const s = poly({ oscillator: { type: "triangle" }, envelope: { attack: 0.004, decay: 1.2, sustain: 0.06, release: 0.8 } }, 24).connect(out);
    s.volume.value = -8;
    return build([s, out], out, (m, d, t, v) => s.triggerAttackRelease(hz(m) * Math.pow(2, (((m * 37) % 11) - 5) / 140), d, t, v));
  },
  kick() {
    const out = new Tone.Gain(1);
    const s = new Tone.MembraneSynth({ pitchDecay: 0.045, octaves: 7, envelope: { attack: 0.001, decay: 0.35, sustain: 0, release: 0.1 } }).connect(out);
    s.volume.value = -2;
    return build([s, out], out, (_m, _d, t, v) => s.triggerAttackRelease(hz(33), 0.2, t, v));
  },
  clap() {
    const out = new Tone.Gain(1);
    const f = new Tone.Filter(1400, "bandpass").connect(out);
    const s = new Tone.NoiseSynth({ noise: { type: "pink" }, envelope: { attack: 0.002, decay: 0.13, sustain: 0 } } as never).connect(f);
    s.volume.value = 2;
    return build([s, f, out], out, (_m, _d, t, v) => s.triggerAttackRelease(0.1, t, v));
  },
  hat() {
    const out = new Tone.Gain(1);
    const f = new Tone.Filter(7500, "highpass").connect(out);
    const s = new Tone.NoiseSynth({ noise: { type: "white" }, envelope: { attack: 0.001, decay: 0.035, sustain: 0 } } as never).connect(f);
    s.volume.value = -10;
    return build([s, f, out], out, (_m, _d, t, v) => s.triggerAttackRelease(0.03, t, v));
  },
  click() {
    const out = new Tone.Gain(1);
    const s = new Tone.Synth({ oscillator: { type: "square" }, envelope: { attack: 0.001, decay: 0.02, sustain: 0, release: 0.01 } } as never).connect(out);
    s.volume.value = -18;
    return build([s, out], out, (m, _d, t, v) => s.triggerAttackRelease(hz(m), 0.02, t, v));
  },
  bass() {
    const out = new Tone.Gain(1);
    const s = new Tone.MonoSynth({ oscillator: { type: "sawtooth" }, filter: { Q: 2, type: "lowpass" }, envelope: { attack: 0.005, decay: 0.2, sustain: 0.5, release: 0.15 }, filterEnvelope: { attack: 0.005, decay: 0.15, sustain: 0.3, baseFrequency: 120, octaves: 3 } }).connect(out);
    s.volume.value = -10;
    return build([s, out], out, (m, d, t, v) => s.triggerAttackRelease(hz(m), d, t, v));
  },
  saw() {
    const out = new Tone.Gain(1);
    const f = new Tone.Filter(4200, "lowpass").connect(out);
    const s = poly({ oscillator: { type: "fatsawtooth", count: 3, spread: 38 } as never, envelope: { attack: 0.01, decay: 0.2, sustain: 0.6, release: 0.25 } }, 20).connect(f);
    s.volume.value = -20;
    return build([s, f, out], out, (m, d, t, v) => s.triggerAttackRelease(hz(m), d, t, v));
  },
  vocal() {
    const out = new Tone.Gain(1);
    const f = new Tone.Filter(2600, "lowpass").connect(out);
    const s = poly({ oscillator: { type: "fmsine", modulationIndex: 1.5, harmonicity: 2 } as never, envelope: { attack: 0.02, decay: 0.1, sustain: 0.8, release: 0.2 } }, 16).connect(f);
    s.volume.value = -10;
    return build([s, f, out], out, (m, d, t, v) => s.triggerAttackRelease(hz(m + 12), d, t, v));
  },
  arp() {
    const out = new Tone.Gain(1);
    const s = new Tone.Synth({ oscillator: { type: "square" }, envelope: { attack: 0.002, decay: 0.08, sustain: 0.1, release: 0.05 } } as never).connect(out);
    s.volume.value = -20;
    return build([s, out], out, (m, d, t, v) => s.triggerAttackRelease(hz(m), Math.min(d, 0.12), t, v));
  },
  pad() {
    const out = new Tone.Gain(1);
    const s = poly({ oscillator: { type: "triangle" }, envelope: { attack: 0.6, decay: 0.4, sustain: 0.7, release: 1.6 } }, 20).connect(out);
    s.volume.value = -16;
    return build([s, out], out, (m, d, t, v) => s.triggerAttackRelease(hz(m), d, t, v));
  },
  strings() {
    const out = new Tone.Gain(1);
    const f = new Tone.Filter(1700, "lowpass").connect(out);
    const s = poly({ oscillator: { type: "fatsawtooth", count: 3, spread: 14 } as never, envelope: { attack: 0.35, decay: 0.3, sustain: 0.7, release: 1.2 } }, 20).connect(f);
    s.volume.value = -22;
    return build([s, f, out], out, (m, d, t, v) => s.triggerAttackRelease(hz(m), d, t, v));
  },
  clarinet() {
    const out = new Tone.Gain(1);
    const f = new Tone.Filter(2100, "lowpass").connect(out);
    const s = new Tone.MonoSynth({ oscillator: { type: "square" }, portamento: 0.04, envelope: { attack: 0.03, decay: 0.2, sustain: 0.7, release: 0.3 }, filterEnvelope: { attack: 0.02, decay: 0.3, sustain: 0.7, baseFrequency: 900, octaves: 1.5 } }).connect(f);
    s.volume.value = -16;
    return build([s, f, out], out, (m, d, t, v) => s.triggerAttackRelease(hz(m), d, t, v));
  },
  harp() {
    const out = new Tone.Gain(1);
    const s = new Tone.PluckSynth({ attackNoise: 1, dampening: 3500, resonance: 0.95 }).connect(out);
    return build([s, out], out, (m, _d, t) => s.triggerAttack(hz(m), t));
  },
  riser() {
    const out = new Tone.Gain(1);
    const f = new Tone.AutoFilter(0.25, 800, 4).connect(out).start();
    const s = new Tone.NoiseSynth({ noise: { type: "white" }, envelope: { attack: 1.5, decay: 0.2, sustain: 0.4, release: 0.6 } } as never).connect(f);
    s.volume.value = -26;
    return build([s, f, out], out, (_m, d, t, v) => s.triggerAttackRelease(d, t, v));
  },
  jingle() {
    const out = new Tone.Gain(1);
    const s = new Tone.FMSynth({ harmonicity: 3.5, modulationIndex: 4, envelope: { attack: 0.002, decay: 0.7, sustain: 0, release: 0.6 } }).connect(out);
    s.volume.value = -14;
    return build([s, out], out, (m, d, t, v) => s.triggerAttackRelease(hz(m + 12), Math.min(d, 0.5), t, v));
  },
  chant() {
    const out = new Tone.Gain(1);
    const f = new Tone.Filter(1100, "lowpass").connect(out);
    const s = poly({ oscillator: { type: "fatsawtooth", count: 4, spread: 30 } as never, envelope: { attack: 0.08, decay: 0.2, sustain: 0.7, release: 0.3 } }, 24).connect(f);
    s.volume.value = -18;
    return build([s, f, out], out, (m, d, t, v) => s.triggerAttackRelease(hz(m), d, t, v));
  },
  hum_machine() {
    const out = new Tone.Gain(1);
    const f = new Tone.Filter(320, "lowpass").connect(out);
    const s = new Tone.MonoSynth({ oscillator: { type: "sawtooth" }, envelope: { attack: 0.2, decay: 0.2, sustain: 0.9, release: 0.4 }, filterEnvelope: { baseFrequency: 200, octaves: 1 } }).connect(f);
    s.volume.value = -16;
    return build([s, f, out], out, (m, d, t, v) => s.triggerAttackRelease(hz(m), d, t, v));
  },
  crowd() {
    const out = new Tone.Gain(1);
    const f = new Tone.Filter(600, "bandpass").connect(out);
    const s = new Tone.NoiseSynth({ noise: { type: "brown" }, envelope: { attack: 0.4, decay: 0.3, sustain: 0.6, release: 0.8 } } as never).connect(f);
    s.volume.value = -14;
    return build([s, f, out], out, (_m, d, t, v) => s.triggerAttackRelease(d, t, v));
  },
};

export function hasInstrument(name: string): boolean {
  return name in makers;
}

export function makeInstrument(name: string): Instrument {
  const make = makers[name];
  if (!make) throw new Error(`Unknown instrument ${name}`);
  return make();
}

export const INSTRUMENTS = Object.keys(makers);
