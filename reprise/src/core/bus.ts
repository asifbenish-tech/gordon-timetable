// src/core/bus.ts: the one event bus between the music systems and the adventure layer.
import type { NoteIndex, Phrase, Target } from "../content/types";

export interface CastEvent {
  id: string;
  reversed: boolean;
  target: Target | null;
  fromLoop: boolean;
}

export interface ThreadRef {
  song: string;
  stem: string;
  tuned?: boolean;
}

export interface BusEvents {
  cast: CastEvent;
  phraseFailed: { phrase: number[] };
  note: { n: NoteIndex; cracked: boolean; index: number };
  noteCleared: void;
  spoolThreadAdded: { slot: number; thread: ThreadRef };
  spoolThreadRemoved: { slot: number };
  spoolsChanged: void;
  flag: { name: string; value: unknown };
  learned: { id: string };
  teach: { phrase: Phrase; draftId: string | null };
  notesOwned: { count: number };
  hit: { song: string; stem: string; time: number };
  tether: { song: string; stem: string; slack: boolean };
  bar: { bar: number; time: number };
  roomEntered: { id: string };
  say: { speaker: string; text: string };
  caption: { text: string };
  solved: { id: string };
  settings: void;
}

type Handler<T> = (payload: T) => void;

export class GameBus {
  private handlers = new Map<keyof BusEvents, Set<Handler<never>>>();

  on<K extends keyof BusEvents>(name: K, fn: Handler<BusEvents[K]>): () => void {
    let set = this.handlers.get(name);
    if (!set) this.handlers.set(name, (set = new Set()));
    set.add(fn as Handler<never>);
    return () => set.delete(fn as Handler<never>);
  }

  emit<K extends keyof BusEvents>(name: K, payload: BusEvents[K]): void {
    const set = this.handlers.get(name);
    if (!set) return;
    for (const fn of [...set]) (fn as Handler<BusEvents[K]>)(payload);
  }
}
