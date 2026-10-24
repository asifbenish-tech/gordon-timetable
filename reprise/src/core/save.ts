// src/core/save.ts: saves stay on the player's device (GDD 9.7). Every read and write is guarded:
// storage can be missing, full or blocked, and the game must still run.
import type { SongMods } from "./loom";
import type { SpoolSave } from "./spindle";

export type Difficulty = "practice" | "standard" | "expert";

export interface SaveData {
  v: 1;
  seed: number;
  difficulty: Difficulty;
  room: string;
  entry: string;
  flags: Record<string, boolean>;
  learned: string[];
  ownedNotes: number;
  tools: string[]; // "combing", "spindle", "weaving"
  capacity: number;
  spools: (SpoolSave | null)[];
  mods: Record<string, SongMods>;
  book: Record<string, (number | null)[]>; // notes the player wrote down (Standard, Expert)
  hints: Record<string, number>;
  solved: string[];
  playSeconds: number;
}

const KEY = "reprise.save.v1";
const SETTINGS_KEY = "reprise.settings.v1";

export function newSave(seed: number, difficulty: Difficulty, room: string, entry: string): SaveData {
  return {
    v: 1,
    seed,
    difficulty,
    room,
    entry,
    flags: {},
    learned: [],
    ownedNotes: 8,
    tools: [],
    capacity: 0,
    spools: [null, null, null, null],
    mods: {},
    book: {},
    hints: {},
    solved: [],
    playSeconds: 0,
  };
}

export function isSave(x: unknown): x is SaveData {
  const s = x as SaveData;
  return !!s && s.v === 1 && typeof s.seed === "number" && typeof s.room === "string" && Array.isArray(s.learned);
}

export function readSave(): SaveData | null {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return null;
    const s = JSON.parse(raw) as unknown;
    return isSave(s) ? s : null;
  } catch {
    return null;
  }
}

export function writeSave(s: SaveData): boolean {
  try {
    localStorage.setItem(KEY, JSON.stringify(s));
    return true;
  } catch {
    return false;
  }
}

export function clearSave(): void {
  try {
    localStorage.removeItem(KEY);
  } catch {
    // nothing to clear
  }
}

export interface Settings {
  calibrationSec: number;
  calibrated: boolean;
  textSize: "s" | "m" | "l";
  contrast: boolean;
  captions: boolean;
  music: number;
  effects: number;
  resetBeats: number; // 2 = GDD default; 4; 999 = never
  lowDetail: boolean;
  textSpeed: "auto" | "click";
  names: string;
}

export const DEFAULT_SETTINGS: Settings = {
  calibrationSec: 0,
  calibrated: false,
  textSize: "m",
  contrast: false,
  captions: true,
  music: 0.7,
  effects: 0.8,
  resetBeats: 2,
  lowDetail: false,
  textSpeed: "auto",
  names: "",
};

export function readSettings(): Settings {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (raw) return { ...DEFAULT_SETTINGS, ...(JSON.parse(raw) as Partial<Settings>) };
  } catch {
    // fall back to defaults
  }
  return { ...DEFAULT_SETTINGS };
}

export function writeSettings(s: Settings): void {
  try {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(s));
  } catch {
    // settings simply won't persist
  }
}
