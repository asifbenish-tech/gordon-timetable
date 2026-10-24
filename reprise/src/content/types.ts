// src/content/types.ts: every JSON file under content/ matches one of these.
// Fields beyond GDD 9.5 are marked "ext" and logged in DECISIONS.md.

export type NoteIndex = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7; // c d e f g a b C'
export type Phrase = [NoteIndex, NoteIndex, NoteIndex, NoteIndex];

export interface DraftDef {
  id: string; // "opening"
  reverseId?: string; // "closing"; absent = not reversible
  highestNote: NoteIndex; // notes Bobbin owns when it is taught
  sung?: boolean; // sung in the story: stricter melodic rules
  fixed?: Phrase; // story-locked drafts only
}

export interface DraftsFile {
  drafts: DraftDef[];
  fallbackPool: Phrase[];
}

export type StemRole = "melody" | "rhythm" | "harmony";

export interface StemDef {
  id: string; // "kick"
  file: string; // "audio/stems/again_again/kick", no extension
  color: string; // thread colour in the Loom View
  masksGolden?: number; // 0..1
  sealed?: boolean; // copy or cast only
  knot?: string; // draft that unties it, e.g. "tuning"
  tether?: string; // hotspot this stem drives
  role?: StemRole; // for weaving recipes
  hitsFile?: string; // note-on beats from render-stems.py
  golden?: boolean; // this stem is the golden thread
  braid?: string; // ext: the knotted stem the golden thread is braided into, until the knot is untied
  label: string; // ext: string key for the thread's name
  instrument: string; // ext: placeholder synth used until a rendered stem exists
  when?: string; // ext: condition; the thread only exists while it holds
  level?: number; // ext: mix level, default 1
}

export interface SongDef {
  id: string;
  bpm: number;
  bars: number;
  stems: StemDef[];
  caption?: string; // ext: caption key describing the music (GDD 4.7)
}

export type Rect = [number, number, number, number];

export interface SpriteDef {
  image: string; // manifest id
  x: number; // feet position in room space
  y: number;
  fps?: number;
  depth?: number;
  lit?: boolean;
  frameWhen?: [number, string][]; // ext: show this frame while the condition holds
}

export interface ExitDef {
  to: string; // room id
  entry: string; // entry id in the target room
  when?: string; // condition; if false, `blocked` is said instead
  blocked?: string; // string key
  check?: string; // ext: script that decides at the door (returns true to pass)
}

export interface HotspotDef {
  id: string;
  rect: Rect; // x, y, w, h in room space
  look: string; // string key
  name: string; // ext: string key of the object's name
  songSource?: string; // can be combed
  weaveFrame?: { needs: StemRole[]; gives: string };
  drafts?: Record<string, string>; // "opening" or "opening_rev" -> action
  talk?: string; // ext: dialogue id (double-click talks instead of looking)
  listen?: string; // ext: script run on double-click instead of the look line
  person?: boolean; // ext
  stand?: [number, number]; // ext: where Bobbin stands to use it
  when?: string; // ext: condition for the hotspot to exist
  sprite?: SpriteDef; // ext
  exit?: ExitDef; // ext
}

export interface LightDef {
  x: number;
  y: number;
  radius: number;
  color: string;
  intensity: number;
}

export interface LayerDef {
  image: string; // manifest id
  scroll: number; // parallax factor, 1 = moves with the room
  lit?: boolean;
  front?: boolean; // ext: drawn in front of characters (a desk, a railing)
}

export interface RoomDef {
  id: string;
  act: "prologue" | "act1" | "act2";
  location: string; // colour-script key (GDD 7.3)
  width: number;
  layers: LayerDef[];
  walk: [number, number][]; // walkable polygon
  entries: Record<string, [number, number]>;
  hotspots: HotspotDef[];
  song: string;
  ambient?: string; // hex ambient light colour
  lights?: LightDef[];
  logic?: string; // ext: id of live room logic in src/world/scripts
  onEnter?: string; // ext: action run on every entry
  swan?: boolean; // ext: Bobbin is still a swan here
}

export interface PuzzleDef {
  id: string; // "A1-5"
  needs: string[]; // "draft:tuning", "puzzle:A1-4"
  gives: string[]; // "draft:unmasking", "note:f", "spools:4"
  solvedWhen: string; // a flag
  hints: [string, string, string]; // look, nudge, answer (string keys)
  bot: string[]; // steps for the solvability bot
  room: string; // ext: where the puzzle is solved (hint look target)
  focus?: string; // ext: hotspot Skein looks at for the first hint
  title: string; // ext: string key
}

export interface DialogueChoice {
  text: string;
  next: string;
  when?: string;
}

export interface DialogueNode {
  speaker: string;
  text: string;
  next?: string;
  when?: string; // skip this node unless the condition holds
  else?: string; // ext: where to go when `when` fails (default: next)
  effects?: string[]; // setFlag:x, learnDraft:x, giveNote:f, giveSpools:4, script:x
  choices?: DialogueChoice[];
}

export interface DialogueDef {
  id: string;
  start: string;
  nodes: Record<string, DialogueNode>;
}

export interface SpeakerDef {
  id: string;
  name: string; // string key or names key in braces
  portrait: string; // manifest id, or "" for voices with no face
  signature: [number, number]; // two-note instrumental signature (MIDI)
  instrument: string;
  color: string;
}

export interface NoteEvent {
  t: number; // beat
  m: number; // MIDI pitch; -1 when `k` refers to this save's draft
  d: number; // duration in beats
  v: number; // velocity 0..1
  k?: number; // index into the per-save draft phrase (GDD 8.9 step 6)
  o?: number; // octave shift for `k`
}

export interface StemNotesFile {
  bars: number;
  instrument: string;
  draft: string | null;
  notes: NoteEvent[];
}

export interface ImageAsset {
  id: string;
  path: string;
  w: number;
  h: number;
  frames: number;
  frameW?: number;
  normal?: string;
  status: "placeholder" | "generated" | "final";
  recipe: string;
}

export interface AudioAsset {
  id: string; // "again_again/kick"
  path: string; // no extension
  notes: string; // expanded notation for the placeholder synth
  hits: string;
  status: "placeholder" | "generated" | "final";
}

export interface Manifest {
  images: ImageAsset[];
  audio: AudioAsset[];
}

export type Target =
  | { kind: "hotspot"; id: string }
  | { kind: "thread"; song: string; stem: string }
  | { kind: "self" };

export function targetKey(t: Target | null): string {
  if (!t || t.kind === "self") return "self";
  if (t.kind === "hotspot") return `hotspot:${t.id}`;
  return `thread:${t.song}:${t.stem}`;
}
