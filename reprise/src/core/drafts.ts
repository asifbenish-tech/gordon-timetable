// src/core/drafts.ts: seeded draft melodies (GDD 9.6) and the save's draft library.
import type { DraftDef, NoteIndex, Phrase } from "../content/types";

const MIN_DISTANCE = 2;
export const SEMITONES = [0, 2, 4, 5, 7, 9, 11, 12]; // c d e f g a b C'
const RESTFUL_ENDINGS = [0, 2, 4, 7]; // c e g C'

export function mulberry32(seed: number): () => number {
  return () => {
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export const reversed = (p: Phrase): Phrase => [p[3], p[2], p[1], p[0]];
export const distance = (a: Phrase, b: Phrase): number =>
  a.reduce<number>((d, n, i) => d + (n === b[i] ? 0 : 1), 0);

/** Section 5's melodic rules. */
export function singable(p: Phrase, strict: boolean): boolean {
  const st = p.map((n) => SEMITONES[n]);
  const leaps = st.slice(1).map((s, i) => Math.abs(s - st[i]));
  if (leaps.some((l) => l === 6 || l > 9)) return false; // no tritone, nothing wider than a major sixth
  if (new Set(p).size < 3) return false; // at least three different notes
  if (strict) {
    if (!RESTFUL_ENDINGS.includes(p[3])) return false;
    if (leaps.filter((l) => l > 4).length > 1) return false; // at most one leap above a major third
  }
  return true;
}

export function fits(p: Phrase, reversible: boolean, taken: Phrase[]): boolean {
  if (reversible && distance(p, reversed(p)) < MIN_DISTANCE) return false; // no palindromes
  const phrases = reversible ? [p, reversed(p)] : [p];
  return phrases.every((q) => taken.every((t) => distance(q, t) >= MIN_DISTANCE));
}

/**
 * GDD 9.6's generator, run again from the same random stream when an early
 * choice leaves no room for a later draft (about 2% of seeds with five c-e
 * drafts). Still a pure function of the seed. DECISIONS.md D-004.
 */
export function generateDrafts(defs: DraftDef[], seed: number, fallbackPool: Phrase[]): Map<string, Phrase> {
  const rand = mulberry32(seed);
  for (let attempt = 0; ; attempt++) {
    try {
      return generateOnce(defs, rand, fallbackPool);
    } catch (e) {
      if (attempt >= 20) throw e;
    }
  }
}

function generateOnce(defs: DraftDef[], rand: () => number, fallbackPool: Phrase[]): Map<string, Phrase> {
  const taken: Phrase[] = [];
  const out = new Map<string, Phrase>();
  for (const def of defs) {
    // in the order they are taught
    const reversible = def.reverseId !== undefined;
    let p = def.fixed;
    for (let tries = 0; !p && tries < 20000; tries++) {
      const c = Array.from({ length: 4 }, () => Math.floor(rand() * (def.highestNote + 1))) as Phrase;
      // GDD 9.6 passes `!!def.sung` as `strict`: sung drafts get the stricter rules.
      if (singable(c, !!def.sung) && fits(c, reversible, taken)) p = c;
    }
    p ??= fallbackPool.find((f) => Math.max(...f) <= def.highestNote && fits(f, reversible, taken));
    if (!p) throw new Error(`No room for draft ${def.id}`);
    out.set(def.id, p);
    taken.push(p);
    if (reversible) taken.push(reversed(p));
  }
  return out;
}

export interface DraftMatch {
  id: string;
  reversed: boolean;
}

/** This save's melodies, what is learned and how many notes the Distaff owns. */
export class DraftLibrary {
  readonly phrases: Map<string, Phrase>;
  readonly learned = new Set<string>();
  ownedNotes = 8;
  private defs: Map<string, DraftDef>;

  constructor(defs: DraftDef[], seed: number, fallbackPool: Phrase[]) {
    this.defs = new Map(defs.map((d) => [d.id, d]));
    this.phrases = generateDrafts(defs, seed, fallbackPool);
  }

  def(id: string): DraftDef | undefined {
    return this.defs.get(id);
  }

  phraseOf(id: string, rev = false): Phrase {
    const p = this.phrases.get(id);
    if (!p) throw new Error(`Unknown draft ${id}`);
    return rev ? reversed(p) : p;
  }

  /** Drafts are matched only once learned; the reverse needs a reversible draft. */
  match(phrase: Phrase): DraftMatch | null {
    for (const id of this.learned) {
      const p = this.phrases.get(id);
      if (!p) continue;
      if (distance(p, phrase) === 0) return { id, reversed: false };
      if (this.defs.get(id)?.reverseId !== undefined && distance(reversed(p), phrase) === 0) {
        return { id, reversed: true };
      }
    }
    return null;
  }

  /** Every phrase that is spoken for: used by the finale composer and tests. */
  allTaken(): Phrase[] {
    const out: Phrase[] = [];
    for (const [id, p] of this.phrases) {
      out.push(p);
      if (this.defs.get(id)?.reverseId !== undefined) out.push(reversed(p));
    }
    return out;
  }

  isOwned(n: NoteIndex): boolean {
    return n < this.ownedNotes;
  }
}
