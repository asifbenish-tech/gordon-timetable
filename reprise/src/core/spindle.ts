// src/core/spindle.ts: Bobbin's looper (GDD 4.4, 9.6).
import * as Tone from "tone";
import type { NoteIndex, Phrase, Target } from "../content/types";
import type { Conductor } from "../audio/conductor";
import type { NoteVoice } from "../audio/note-voice";
import type { GameBus, ThreadRef } from "./bus";

export interface LoopEvent {
  beat: number; // position inside the bar, in beats, snapped to eighths
  note: NoteIndex;
}

type Spool =
  | { kind: "draft"; id: string; reversed: boolean; target: Target; events: LoopEvent[]; part: Tone.Part | null }
  | { kind: "thread"; thread: ThreadRef };

export type SpoolSave =
  | { kind: "draft"; id: string; reversed: boolean; target: Target; events: LoopEvent[] }
  | { kind: "thread"; thread: ThreadRef };

/** A recorded draft keeps the player's rhythm, snapped to eighth notes and folded into one bar. */
export function quantizeToBar(beats: number[]): number[] {
  const bar0 = Math.floor(beats[0] / 4) * 4;
  return beats.map((b) => (Math.round((b - bar0) * 2) / 2) % 4);
}

export class Spindle {
  armed = false;
  capacity = 2; // four from late Act II; the UI keeps `selected` below it
  selected = 0;
  readonly spools: (Spool | null)[] = [null, null, null, null];

  constructor(
    conductor: Conductor,
    private voice: NoteVoice,
    private bus: GameBus,
    private audio = true,
  ) {
    conductor.onBar((_bar, time) => {
      for (const s of this.spools) {
        if (s?.kind !== "draft") continue;
        const cast = () => this.bus.emit("cast", { id: s.id, reversed: s.reversed, target: s.target, fromLoop: true });
        if (this.audio) Tone.getDraw().schedule(cast, time);
        else cast();
      }
    });
  }

  recordDraft(id: string, reversed: boolean, target: Target, notes: Phrase, beats: number[]): void {
    const snapped = quantizeToBar(beats);
    const events = notes.map((note, i) => ({ beat: snapped[i], note }));
    this.setDraft(this.selected, id, reversed, target, events);
    this.armed = false;
    this.bus.emit("spoolsChanged", undefined);
  }

  private setDraft(slot: number, id: string, reversed: boolean, target: Target, events: LoopEvent[]): void {
    this.clear(slot, false);
    let part: Tone.Part | null = null;
    if (this.audio) {
      const toneEvents = events.map((e) => ({ time: `0:${Math.floor(e.beat)}:${(e.beat % 1) * 4}`, note: e.note }));
      part = new Tone.Part((time, ev: { note: NoteIndex }) => this.voice.playAt(ev.note, time, 0.45), toneEvents);
      part.loop = true;
      part.loopEnd = "1m";
      part.start("@1m"); // from the next bar line, sample-accurate
    }
    this.spools[slot] = { kind: "draft", id, reversed, target, events, part };
  }

  copyThread(thread: ThreadRef): void {
    this.clear(this.selected, false);
    this.spools[this.selected] = { kind: "thread", thread };
    this.bus.emit("spoolThreadAdded", { slot: this.selected, thread }); // the Song plays it in sync
    this.bus.emit("spoolsChanged", undefined);
  }

  clear(slot: number, notify = true): void {
    const s = this.spools[slot];
    if (s?.kind === "draft") s.part?.dispose();
    if (s?.kind === "thread") this.bus.emit("spoolThreadRemoved", { slot });
    this.spools[slot] = null;
    if (notify) this.bus.emit("spoolsChanged", undefined);
  }

  select(slot: number): void {
    if (slot >= 0 && slot < this.capacity) this.selected = slot;
    this.bus.emit("spoolsChanged", undefined);
  }

  setArmed(on: boolean): void {
    this.armed = on;
    this.bus.emit("spoolsChanged", undefined);
  }

  setCapacity(n: number): void {
    this.capacity = Math.max(this.capacity, Math.min(4, n));
    this.bus.emit("spoolsChanged", undefined);
  }

  /** Spools whose loop re-casts `draftKey` ("hushing" or "hushing_rev") on `target`. */
  loopsOn(targetKey: (t: Target) => string, key: string, draftId: string, reversed: boolean): number[] {
    const out: number[] = [];
    this.spools.forEach((s, i) => {
      if (s?.kind === "draft" && s.id === draftId && s.reversed === reversed && targetKey(s.target) === key) out.push(i);
    });
    return out;
  }

  threadSlots(): { slot: number; thread: ThreadRef }[] {
    const out: { slot: number; thread: ThreadRef }[] = [];
    this.spools.forEach((s, i) => {
      if (s?.kind === "thread") out.push({ slot: i, thread: s.thread });
    });
    return out;
  }

  spool(slot: number): SpoolSave | null {
    const s = this.spools[slot];
    if (!s) return null;
    if (s.kind === "thread") return { kind: "thread", thread: s.thread };
    return { kind: "draft", id: s.id, reversed: s.reversed, target: s.target, events: s.events };
  }

  save(): (SpoolSave | null)[] {
    return this.spools.map((_, i) => this.spool(i));
  }

  load(spools: (SpoolSave | null)[], capacity: number): void {
    for (let i = 0; i < 4; i++) this.clear(i, false);
    this.capacity = capacity;
    this.selected = Math.min(this.selected, capacity - 1);
    spools.forEach((s, i) => {
      if (!s) return;
      if (s.kind === "thread") {
        this.spools[i] = { kind: "thread", thread: s.thread };
        this.bus.emit("spoolThreadAdded", { slot: i, thread: s.thread });
      } else this.setDraft(i, s.id, s.reversed, s.target, s.events);
    });
    this.armed = false;
    this.bus.emit("spoolsChanged", undefined);
  }
}
