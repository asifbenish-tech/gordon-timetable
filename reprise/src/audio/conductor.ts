// src/audio/conductor.ts: the musical clock. Tone.js reads the AudioContext.
import * as Tone from "tone";

export type BarListener = (bar: number, audioTime: number) => void;
export type StepListener = (step: number, audioTime: number) => void;

export const STEPS_PER_BAR = 16;

export class Conductor {
  readonly beatsPerBar = 4;
  calibrationSec = 0; // set by the latency calibration screen
  tempoScale = 1; // debug builds only: the solvability bot plays at speed
  bpm = 96;
  private listeners: BarListener[] = [];
  private stepListeners: StepListener[] = [];
  private bar = 0;
  private step = 0;
  private started = false;

  /** Call from the Begin button's click handler. */
  async start(bpm: number): Promise<void> {
    await Tone.start();
    if (this.started) return;
    this.started = true;
    this.bpm = bpm;
    const transport = Tone.getTransport();
    transport.bpm.value = bpm * this.tempoScale;
    transport.timeSignature = this.beatsPerBar;
    transport.scheduleRepeat((time) => {
      const bar = this.bar++;
      for (const fn of this.listeners) fn(bar, time);
    }, "1m", 0);
    transport.scheduleRepeat((time) => {
      const step = this.step++;
      for (const fn of this.stepListeners) fn(step, time);
    }, "16n", 0);
    transport.start("+0.05");
  }

  get running(): boolean {
    return this.started;
  }

  setBpm(bpm: number): void {
    this.bpm = bpm;
    if (this.started) Tone.getTransport().bpm.value = bpm * this.tempoScale;
  }

  onBar(fn: BarListener): () => void {
    this.listeners.push(fn);
    return () => (this.listeners = this.listeners.filter((f) => f !== fn));
  }

  onStep(fn: StepListener): () => void {
    this.stepListeners.push(fn);
    return () => (this.stepListeners = this.stepListeners.filter((f) => f !== fn));
  }

  /** Beats elapsed on the Transport at audio time `at`. */
  beatsAt(at: number): number {
    const transport = Tone.getTransport();
    return transport.getTicksAtTime(at) / transport.PPQ;
  }

  /** Where in the music the player pressed, corrected for measured latency. */
  inputBeats(): number {
    return this.beatsAt(Tone.immediate() - this.calibrationSec);
  }

  now(): number {
    return Tone.now();
  }

  beatSeconds(): number {
    return 60 / (this.bpm * this.tempoScale);
  }

  barSeconds(): number {
    return this.beatSeconds() * this.beatsPerBar;
  }

  currentBar(): number {
    return this.bar;
  }

  currentStep(): number {
    return this.step;
  }
}
