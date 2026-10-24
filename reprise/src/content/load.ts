// src/content/load.ts: all content is bundled JSON; nothing is fetched at runtime but the game's own files.
import type {
  DialogueDef,
  DraftsFile,
  Manifest,
  PuzzleDef,
  RoomDef,
  SongDef,
  SpeakerDef,
  StemNotesFile,
} from "./types";
import draftsJson from "../../content/drafts.json";
import castJson from "../../content/cast.json";
import manifestJson from "../../assets/manifest.json";

function byId<T extends { id: string }>(mods: Record<string, unknown>): Map<string, T> {
  const out = new Map<string, T>();
  for (const m of Object.values(mods)) {
    const v = ((m as { default?: T }).default ?? m) as T;
    out.set(v.id, v);
  }
  return out;
}

export const drafts = draftsJson as DraftsFile;
export const manifest = manifestJson as Manifest;
export const rooms = byId<RoomDef>(import.meta.glob("../../content/rooms/*.json", { eager: true }));
export const songs = byId<SongDef>(import.meta.glob("../../content/songs/*.json", { eager: true }));
export const dialogues = byId<DialogueDef>(import.meta.glob("../../content/dialogue/*.json", { eager: true }));
export const puzzles = [...byId<PuzzleDef>(import.meta.glob("../../content/puzzles/*.json", { eager: true })).values()];
export const speakers = new Map((castJson as { speakers: SpeakerDef[] }).speakers.map((s) => [s.id, s]));

const stemFiles = import.meta.glob("../../assets/audio/stems/*/*.json", { eager: true, import: "default" }) as Record<string, unknown>;

export function stemNotes(song: string, stem: string): StemNotesFile {
  const f = stemFiles[`../../assets/audio/stems/${song}/${stem}.notes.json`];
  if (!f) throw new Error(`No notation for ${song}/${stem}`);
  return f as StemNotesFile;
}

export function stemHits(song: string, stem: string): number[] {
  const f = stemFiles[`../../assets/audio/stems/${song}/${stem}.hits.json`] as { hits: number[] } | undefined;
  return f?.hits ?? [];
}

/** Images are loaded only through the manifest (GDD 7.9): path -> bundled URL. */
const artUrls = import.meta.glob("../../assets/art/**/*.png", { eager: true, query: "?url", import: "default" }) as Record<string, string>;

export function artUrl(path: string): string {
  const u = artUrls[`../../assets/${path}`];
  if (!u) throw new Error(`Asset missing from build: ${path}`);
  return u;
}

/** Puzzle order is the map's order (P1..P6, A1-1.., A2-1..). */
const ORDER = (id: string) => {
  const m = /^(P|A(\d)-|F)(\d+)$/.exec(id);
  if (!m) return 999;
  const act = m[1] === "P" ? 0 : m[1] === "F" ? 9 : Number(m[2]);
  return act * 100 + Number(m[3]);
};
puzzles.sort((a, b) => ORDER(a.id) - ORDER(b.id));
