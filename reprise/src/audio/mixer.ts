// src/audio/mixer.ts: buses into one limiter, mastered for -18 LUFS-ish, peaks at -1 dBTP (GDD 8.7).
import * as Tone from "tone";

export class Mixer {
  readonly limiter = new Tone.Limiter(-1).toDestination();
  readonly master = new Tone.Gain(0.8).connect(this.limiter);
  readonly music = new Tone.Gain(0.7).connect(this.master);
  readonly distaff = new Tone.Gain(0.9).connect(this.master);
  readonly sfx = new Tone.Gain(0.7).connect(this.master);
  readonly voices = new Tone.Gain(0.35).connect(this.master);

  setVolumes(music: number, effects: number): void {
    this.musicLevel = music;
    this.music.gain.rampTo(music, 0.1);
    this.sfx.gain.rampTo(effects, 0.1);
    this.voices.gain.rampTo(0.35 * effects, 0.1);
  }

  /** The Distaff bed (GDD 8.4), simplified: the score steps back while Bobbin plays. */
  duck(on: boolean): void {
    this.music.gain.rampTo(on ? this.musicLevel * 0.45 : this.musicLevel, on ? 0.05 : 0.8);
  }

  musicLevel = 0.7;
}
