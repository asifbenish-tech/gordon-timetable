// src/core/loom.ts: combing (taking a song apart) and weaving (joining threads), as data.
import type { SongDef, StemDef, StemRole } from "../content/types";
import type { Effects } from "./effects";

export interface SongMods {
  untied: string[];
  replaced: Record<string, number>; // stem id -> spool slot whose thread plays in its place
}

export type TetherState = "taut" | "slack" | "replaced";

/** 1 minus the masking of every thread that is still audible and not untied (GDD 9.6). */
export function goldenLevel(def: SongDef, audible: (id: string) => boolean, untied: (id: string) => boolean): number {
  const mask = def.stems
    .filter((s) => !s.golden && audible(s.id) && !untied(s.id))
    .reduce((sum, s) => sum + (s.masksGolden ?? 0), 0);
  return Math.min(1, Math.max(0, 1 - mask));
}

export class LoomModel {
  readonly pulled = new Set<string>();
  isolated: string | null = null;

  constructor(
    readonly def: SongDef,
    private effects: Effects,
    readonly mods: SongMods,
    private exists: (stem: StemDef) => boolean,
  ) {}

  key(stemId: string): string {
    return `thread:${this.def.id}:${stemId}`;
  }

  stem(id: string): StemDef | undefined {
    return this.def.stems.find((s) => s.id === id && this.exists(s));
  }

  stems(): StemDef[] {
    return this.def.stems.filter((s) => this.exists(s));
  }

  isTied(id: string): boolean {
    const s = this.stem(id);
    return !!s?.knot && !this.mods.untied.includes(id);
  }

  untie(id: string): void {
    if (!this.mods.untied.includes(id)) this.mods.untied.push(id);
  }

  state(id: string, draftKey: string, at: number): boolean {
    return this.effects.isActive(this.key(id), draftKey, at);
  }

  replacedBy(id: string): number | null {
    return this.mods.replaced[id] ?? null;
  }

  /** Its own sound is not playing: pulled, hushed or replaced by a spool. */
  silenced(id: string, at: number): boolean {
    return this.pulled.has(id) || this.state(id, "hushing", at) || this.replacedBy(id) !== null;
  }

  audible(id: string, at: number): boolean {
    if (!this.stem(id)) return false;
    if (this.silenced(id, at)) return false;
    return this.isolated === null || this.isolated === id;
  }

  goldenLevel(at: number): number {
    const golden = this.def.stems.find((s) => s.golden && this.exists(s));
    if (!golden) return 0;
    // Braided into a knotted thread, it goes wherever that thread goes until Tuning splits them (GDD 6, puzzle 1).
    if (golden.braid && this.isTied(golden.braid) && !this.audible(golden.braid, at)) return 0;
    return goldenLevel(
      this.def,
      (id) => this.audible(id, at),
      (id) => !!this.stem(id)?.knot && this.mods.untied.includes(id),
    );
  }

  tether(id: string, at: number): TetherState {
    if (this.replacedBy(id) !== null) return "replaced";
    return this.pulled.has(id) || this.state(id, "hushing", at) ? "slack" : "taut";
  }

  closeView(): void {
    this.pulled.clear();
    this.isolated = null;
  }
}

export interface WeaveResult {
  ok: boolean;
  missing: StemRole[];
  extra: number;
}

/** A frame's recipe names roles, never timing (GDD 4.5). */
export function checkWeave(needs: StemRole[], threads: { role?: StemRole }[]): WeaveResult {
  const have = threads.map((t) => t.role);
  const missing: StemRole[] = [];
  const pool = [...have];
  for (const r of needs) {
    const i = pool.indexOf(r);
    if (i < 0) missing.push(r);
    else pool.splice(i, 1);
  }
  return { ok: missing.length === 0 && threads.length <= 3, missing, extra: pool.length };
}
