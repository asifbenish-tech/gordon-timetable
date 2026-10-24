// src/world/flags.ts: story flags and the one condition grammar used by rooms, puzzles and dialogue.
// A condition is terms joined by "&"; a leading "!" negates one term.
//   flag:x  draft:tuning  puzzle:A1-4  note:f  tool:combing  spools:4  swan
import type { SaveData } from "../core/save";

export const NOTE_NAMES = ["c", "d", "e", "f", "g", "a", "b", "C'"];

export function noteCount(letter: string): number {
  const i = NOTE_NAMES.indexOf(letter);
  if (i < 0) throw new Error(`Unknown note ${letter}`);
  return i + 1;
}

export interface CondState {
  flags: Record<string, boolean>;
  learned: { has(id: string): boolean } | string[];
  solved: string[];
  ownedNotes: number;
  tools: string[];
  capacity: number;
}

export function fromSave(s: SaveData): CondState {
  return s;
}

function learnedHas(l: CondState["learned"], id: string): boolean {
  return Array.isArray(l) ? l.includes(id) : l.has(id);
}

export function term(state: CondState, t: string): boolean {
  const [kind, arg] = t.split(":", 2);
  switch (kind) {
    case "flag":
      return !!state.flags[arg];
    case "draft":
      return learnedHas(state.learned, arg);
    case "puzzle":
      return state.solved.includes(arg);
    case "note":
      return state.ownedNotes >= noteCount(arg);
    case "tool":
      return state.tools.includes(arg);
    case "spools":
      return state.capacity >= Number(arg);
    case "true":
      return true;
    default:
      throw new Error(`Unknown condition term ${t}`);
  }
}

export function check(state: CondState, cond: string | undefined): boolean {
  if (!cond) return true;
  return cond.split("&").every((raw) => {
    const t = raw.trim();
    return t.startsWith("!") ? !term(state, t.slice(1)) : term(state, t);
  });
}

/** Static check used by content validation: does every term parse? */
export function validCondition(cond: string): boolean {
  try {
    check({ flags: {}, learned: [], solved: [], ownedNotes: 8, tools: [], capacity: 4 }, cond);
    return true;
  } catch {
    return false;
  }
}
