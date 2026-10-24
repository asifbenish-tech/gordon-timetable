// src/audio/note-voice.ts: the Distaff's voice and the teaching voices (GDD 8.5, 8.8).
import * as Tone from "tone";
import type { NoteIndex, Phrase } from "../content/types";
import { SEMITONES } from "../core/drafts";
import { makeInstrument, type Instrument } from "./instruments";
import type { Mixer } from "./mixer";

export const DISTAFF_ROOT = 60; // c4

export function noteMidi(n: NoteIndex): number {
  return DISTAFF_ROOT + SEMITONES[n];
}

export class NoteVoice {
  private distaff: Instrument | null = null;
  private teachers = new Map<string, Instrument>();
  private crack: Tone.NoiseSynth | null = null;
  private stinger: Tone.PolySynth | null = null;

  constructor(private mixer: Mixer | null) {}

  private ensure(): Instrument | null {
    if (!this.mixer) return null;
    if (!this.distaff) {
      this.distaff = makeInstrument("distaff");
      this.distaff.output.connect(this.mixer.distaff);
    }
    return this.distaff;
  }

  /** Immediate: never quantize what the player hears. */
  playNow(n: NoteIndex): void {
    this.ensure()?.play(noteMidi(n), 0.45, Tone.immediate(), 0.85);
  }

  playAt(n: NoteIndex, time: number, vel = 0.7): void {
    this.ensure()?.play(noteMidi(n), 0.35, time, vel);
  }

  /** A dead click: that note is still lost. */
  playCracked(_n: NoteIndex): void {
    if (!this.mixer) return;
    if (!this.crack) {
      this.crack = new Tone.NoiseSynth({ noise: { type: "brown" }, envelope: { attack: 0.001, decay: 0.03, sustain: 0 } });
      this.crack.connect(this.mixer.sfx);
    }
    this.crack.triggerAttackRelease(0.03, Tone.immediate(), 0.6);
  }

  /** A teaching source performs a phrase from its eight single notes. Returns note times. */
  teach(voice: string, phrase: Phrase, start: number, beat: number): number[] {
    const times = phrase.map((_, i) => start + i * beat);
    const inst = this.teacher(voice);
    if (!inst) return times;
    phrase.forEach((n, i) => inst.play(noteMidi(n), beat * 0.9, times[i], 0.8));
    return times;
  }

  /** Each speaking character's two-note instrumental signature, played softly under their line (GDD 8.8). */
  signature(voice: string, midis: [number, number], start: number): void {
    const inst = this.teacher(voice);
    if (!inst) return;
    inst.play(midis[0], 0.18, start, 0.35);
    inst.play(midis[1], 0.3, start + 0.16, 0.3);
  }

  private teacher(voice: string): Instrument | null {
    if (!this.mixer) return null;
    let inst = this.teachers.get(voice);
    if (!inst) {
      inst = makeInstrument(voice);
      inst.output.connect(this.mixer.sfx);
      this.teachers.set(voice, inst);
    }
    return inst;
  }

  /** A successful draft fires a short phrase on the next beat; a failed one a soft unresolved chord. */
  stingerFor(success: boolean, time: number): void {
    if (!this.mixer) return;
    if (!this.stinger) {
      this.stinger = new Tone.PolySynth(Tone.Synth, { oscillator: { type: "sine" }, envelope: { attack: 0.05, decay: 0.4, sustain: 0.3, release: 1.2 } });
      this.stinger.volume.value = -18;
      this.stinger.connect(this.mixer.sfx);
    }
    const chord = success ? ["C5", "E5", "G5", "C6"] : ["D4", "F4", "B4"];
    if (success) chord.forEach((c, i) => this.stinger!.triggerAttackRelease(c, 0.6, time + i * 0.07, 0.5));
    else this.stinger.triggerAttackRelease(chord, 0.9, time, 0.35);
  }
}
