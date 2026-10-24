// src/world/puzzles.ts: the puzzle map as data (GDD 6.4). Needs use the condition grammar.
import type { PuzzleDef } from "../content/types";
import { check, type CondState } from "./flags";

export class PuzzleTracker {
  readonly defs: PuzzleDef[];
  private byId: Map<string, PuzzleDef>;

  constructor(defs: PuzzleDef[], private state: () => CondState) {
    this.defs = defs;
    this.byId = new Map(defs.map((d) => [d.id, d]));
  }

  get(id: string): PuzzleDef | undefined {
    return this.byId.get(id);
  }

  needsMet(p: PuzzleDef): boolean {
    return check(this.state(), p.needs.join("&"));
  }

  isSolved(id: string): boolean {
    return this.state().solved.includes(id);
  }

  open(): PuzzleDef[] {
    return this.defs.filter((p) => !this.isSolved(p.id) && this.needsMet(p));
  }

  /** Newly satisfied `solvedWhen` flags, in map order. A puzzle never counts before its needs. */
  newlySolved(): PuzzleDef[] {
    const s = this.state();
    return this.defs.filter((p) => !s.solved.includes(p.id) && !!s.flags[p.solvedWhen] && this.needsMet(p));
  }

  /** What Skein hints at: an open puzzle in this room first, then the earliest open one. */
  current(room: string): PuzzleDef | null {
    const open = this.open();
    return open.find((p) => p.room === room) ?? open[0] ?? null;
  }
}
