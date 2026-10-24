// src/core/distaff.ts: turns notes into drafts (GDD 9.6).
import type { NoteIndex, Phrase, Target } from "../content/types";
import type { Conductor } from "../audio/conductor";
import type { NoteVoice } from "../audio/note-voice";
import type { GameBus } from "./bus";
import type { DraftLibrary } from "./drafts";
import type { Spindle } from "./spindle";

export class Distaff {
  private notes: NoteIndex[] = [];
  private beats: number[] = [];
  /** Beats of silence that reset a half-played phrase. GDD 9.6 uses 2; Settings can relax it (D-007). */
  resetBeats = 2;
  enabled = true;

  constructor(
    private conductor: Conductor,
    private library: DraftLibrary, // this save's melodies, what is learned, notes owned
    private voice: NoteVoice,
    private bus: GameBus,
    private spindle: Spindle,
  ) {}

  playNote(n: NoteIndex, target: Target | null): void {
    if (!this.enabled) return;
    if (n >= this.library.ownedNotes) {
      this.voice.playCracked(n); // a dead click: that note is still lost
      this.bus.emit("note", { n, cracked: true, index: this.notes.length });
      return;
    }
    this.voice.playNow(n); // immediate; never quantize what the player hears
    const beat = this.conductor.inputBeats();
    const last = this.beats.at(-1);
    if (last !== undefined && beat - last > this.resetBeats) this.clear(); // a pause resets
    this.notes.push(n);
    this.beats.push(beat);
    this.bus.emit("note", { n, cracked: false, index: this.notes.length - 1 });
    if (this.notes.length === 4) this.resolve(target);
  }

  get pending(): readonly NoteIndex[] {
    return this.notes;
  }

  private resolve(target: Target | null): void {
    const phrase = this.notes as Phrase;
    const match = this.library.match(phrase); // { id, reversed } for learned drafts only
    if (!match) {
      this.bus.emit("phraseFailed", { phrase });
    } else {
      this.bus.emit("cast", { ...match, target, fromLoop: false }); // the effect lands now
      if (this.spindle.armed && target) {
        this.spindle.recordDraft(match.id, match.reversed, target, phrase, this.beats);
      }
    }
    this.clear();
  }

  clear(): void {
    if (this.notes.length) this.bus.emit("noteCleared", undefined);
    this.notes = [];
    this.beats = [];
  }
}
