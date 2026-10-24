// tools/validate-content.ts: every JSON file under content/ against its JSON Schema, then the links
// between them: strings, rooms, songs, dialogues, puzzles, drafts, assets (GDD 0, definition of done 5).
import { existsSync, readdirSync, readFileSync } from "node:fs";
import Ajv, { type JSONSchemaType } from "ajv";
import type { DialogueDef, DraftsFile, Manifest, PuzzleDef, RoomDef, SongDef, SpeakerDef } from "../src/content/types";
import { validCondition } from "../src/world/flags";

const root = new URL("../", import.meta.url);
const read = <T>(p: string): T => JSON.parse(readFileSync(new URL(p, root), "utf8")) as T;
const dir = (p: string) => readdirSync(new URL(p, root)).filter((f) => f.endsWith(".json")).map((f) => `${p}/${f}`);
const errors: string[] = [];
const err = (m: string) => errors.push(m);

const ajv = new Ajv({ allErrors: true, strict: false });
const rect = { type: "array", items: { type: "number" }, minItems: 4, maxItems: 4 };
const pt = { type: "array", items: { type: "number" }, minItems: 2, maxItems: 2 };
const strMap = { type: "object", additionalProperties: { type: "string" } };
const schemas: Record<string, object> = {
  room: {
    type: "object",
    required: ["id", "act", "location", "width", "layers", "walk", "entries", "hotspots", "song"],
    additionalProperties: false,
    properties: {
      id: { type: "string" }, act: { enum: ["prologue", "act1", "act2"] }, location: { type: "string" }, width: { type: "number", minimum: 640, maximum: 1280 },
      layers: { type: "array", minItems: 1, items: { type: "object", required: ["image", "scroll"], additionalProperties: false, properties: { image: { type: "string" }, scroll: { type: "number" }, lit: { type: "boolean" }, front: { type: "boolean" } } } },
      walk: { type: "array", minItems: 3, items: pt }, entries: { type: "object", additionalProperties: pt }, song: { type: "string" },
      ambient: { type: "string" }, logic: { type: "string" }, onEnter: { type: "string" }, swan: { type: "boolean" },
      lights: { type: "array", items: { type: "object", required: ["x", "y", "radius", "color", "intensity"] } },
      hotspots: {
        type: "array",
        items: {
          type: "object",
          required: ["id", "rect", "look", "name"],
          additionalProperties: false,
          properties: {
            id: { type: "string" }, rect, look: { type: "string" }, name: { type: "string" }, songSource: { type: "string" }, drafts: strMap,
            talk: { type: "string" }, listen: { type: "string" }, person: { type: "boolean" }, stand: pt, when: { type: "string" },
            weaveFrame: { type: "object" },
            sprite: { type: "object", required: ["image", "x", "y"], properties: { image: { type: "string" }, x: { type: "number" }, y: { type: "number" }, fps: { type: "number" }, depth: { type: "number" }, lit: { type: "boolean" }, frameWhen: { type: "array" } }, additionalProperties: false },
            exit: { type: "object", required: ["to", "entry"], additionalProperties: false, properties: { to: { type: "string" }, entry: { type: "string" }, when: { type: "string" }, blocked: { type: "string" }, check: { type: "string" } } },
          },
        },
      },
    },
  },
  puzzle: {
    type: "object", additionalProperties: false,
    required: ["id", "needs", "gives", "solvedWhen", "hints", "bot", "room", "title"],
    properties: {
      id: { type: "string", pattern: "^(P\\d+|A\\d-\\d+|F\\d+)$" }, needs: { type: "array", items: { type: "string" } }, gives: { type: "array", items: { type: "string" } },
      solvedWhen: { type: "string" }, hints: { type: "array", items: { type: "string" }, minItems: 3, maxItems: 3 }, bot: { type: "array", minItems: 1, items: { type: "string" } },
      room: { type: "string" }, focus: { type: "string" }, title: { type: "string" },
    },
  },
  dialogue: {
    type: "object", required: ["id", "start", "nodes"], additionalProperties: false,
    properties: {
      id: { type: "string" }, start: { type: "string" },
      nodes: { type: "object", additionalProperties: { type: "object", required: ["speaker", "text"], additionalProperties: false, properties: {
        speaker: { type: "string" }, text: { type: "string" }, next: { type: "string" }, when: { type: "string" }, else: { type: "string" },
        effects: { type: "array", items: { type: "string" } }, choices: { type: "array", items: { type: "object", required: ["text", "next"] } } } } },
    },
  },
  song: {
    type: "object", required: ["id", "bpm", "bars", "stems"], additionalProperties: false,
    properties: {
      id: { type: "string" }, bpm: { type: "number", minimum: 40, maximum: 200 }, bars: { type: "integer", minimum: 1 }, caption: { type: "string" },
      stems: { type: "array", items: { type: "object", required: ["id", "file", "color", "label", "instrument"], additionalProperties: false, properties: {
        id: { type: "string" }, file: { type: "string" }, color: { type: "string", pattern: "^#[0-9a-f]{6}$" }, masksGolden: { type: "number", minimum: 0, maximum: 1 },
        sealed: { type: "boolean" }, knot: { type: "string" }, tether: { type: "string" }, role: { enum: ["melody", "rhythm", "harmony"] }, hitsFile: { type: "string" },
        golden: { type: "boolean" }, braid: { type: "string" }, label: { type: "string" }, instrument: { type: "string" }, when: { type: "string" }, level: { type: "number" } } } },
    },
  },
};
const checkSchema = (name: string, file: string, data: unknown) => {
  const v = ajv.compile(schemas[name] as JSONSchemaType<unknown>);
  if (!v(data)) for (const e of v.errors ?? []) err(`${file}: ${e.instancePath} ${e.message}`);
};

const strings = read<Record<string, string>>("content/strings/en.json");
const names = read<{ default: string; sets: Record<string, Record<string, string>> }>("content/names.json");
const drafts = read<DraftsFile>("content/drafts.json");
const cast = read<{ speakers: SpeakerDef[] }>("content/cast.json");
const manifest = read<Manifest>("assets/manifest.json");
const rooms = dir("content/rooms").map((f) => { const r = read<RoomDef>(f); checkSchema("room", f, r); return r; });
const songs = dir("content/songs").map((f) => { const s = read<SongDef>(f); checkSchema("song", f, s); return s; });
const dialogues = dir("content/dialogue").map((f) => { const d = read<DialogueDef>(f); checkSchema("dialogue", f, d); return d; });
const puzzles = dir("content/puzzles").map((f) => { const p = read<PuzzleDef>(f); checkSchema("puzzle", f, p); return p; });

const roomById = new Map(rooms.map((r) => [r.id, r]));
const songById = new Map(songs.map((s) => [s.id, s]));
const dlgById = new Map(dialogues.map((d) => [d.id, d]));
const puzzleIds = new Set(puzzles.map((p) => p.id));
const draftIds = new Set(drafts.drafts.map((d) => d.id));
const draftKeys = new Set(drafts.drafts.flatMap((d) => (d.reverseId ? [d.id, `${d.id}_rev`] : [d.id])));
const imageIds = new Set(manifest.images.map((i) => i.id));
const speakerIds = new Set(cast.speakers.map((s) => s.id));
const SCRIPTS = new Set<string>();
const LOGIC = new Set<string>();
for (const f of ["prologue", "act1", "act2"]) {
  const src = readFileSync(new URL(`src/world/scripts/${f}.ts`, root), "utf8");
  const scriptBlock = src.slice(src.indexOf("export const scripts"));
  for (const m of scriptBlock.matchAll(/^ {2}(?:async )?(\w+)\(/gm)) SCRIPTS.add(`${f}.${m[1]}`);
  const logicLine = src.match(/export const logic[^{]*\{([^}]*)\}/);
  for (const part of logicLine?.[1].split(",") ?? []) {
    const k = part.split(":")[0].trim();
    if (k) LOGIC.add(k);
  }
}

const key = (k: string | undefined, where: string) => {
  if (k && !(k in strings)) err(`${where}: missing string "${k}"`);
};
const cond = (c: string | undefined, where: string) => {
  if (c && !validCondition(c)) err(`${where}: bad condition "${c}"`);
};
const action = (a: string, where: string) => {
  for (const part of a.split(";").map((s) => s.trim()).filter(Boolean)) {
    const [kind, ...rest] = part.split(":");
    const arg = rest.join(":");
    if (kind === "say") key(arg, where);
    else if (kind === "script") { if (!SCRIPTS.has(arg.split(":").slice(0, 1).join(":"))) err(`${where}: unknown script ${arg}`); }
    else if (kind === "dialogue") { if (!dlgById.has(arg)) err(`${where}: unknown dialogue ${arg}`); }
    else if (kind !== "flag" && kind !== "unflag") err(`${where}: unknown action ${part}`);
  }
};

// ---- names and strings ----
const setKeys = Object.values(names.sets).map((s) => Object.keys(s).sort().join(","));
if (new Set(setKeys).size !== 1) err("names.json: name sets must define the same keys");
if (!(names.default in names.sets)) err("names.json: default set missing");
const nameKeys = new Set(Object.keys(Object.values(names.sets)[0]));
const VARS = new Set(["target", "thread", "draft", "note", "n", "i", "ms"]);
for (const [k, v] of Object.entries(strings)) {
  for (const m of v.matchAll(/\{(\w+)\}/g)) if (!nameKeys.has(m[1]) && !VARS.has(m[1])) err(`strings ${k}: unknown placeholder {${m[1]}}`);
  for (const set of Object.values(names.sets)) for (const n of Object.values(set)) if (n.length > 4 && v.includes(n) && !["Reprise"].includes(n)) err(`strings ${k}: franchise name "${n}" must come from names.json`);
  if (/\bLOOM\b|Threadbare|Guild of Weavers|Loom Island/.test(v)) err(`strings ${k}: franchise name written into a string`);
}

// ---- drafts ----
for (const d of drafts.drafts) {
  key(`draft.${d.id}`, "drafts");
  key(`draft.${d.id}.effect`, "drafts");
  if (d.reverseId) key(`draft.${d.id}_rev`, "drafts");
}

// ---- rooms ----
for (const r of rooms) {
  const w = `room ${r.id}`;
  if (!songById.has(r.song)) err(`${w}: unknown song ${r.song}`);
  for (const l of r.layers) if (!imageIds.has(l.image)) err(`${w}: unknown image ${l.image}`);
  if (r.logic && !LOGIC.has(r.logic)) err(`${w}: unknown logic ${r.logic}`);
  if (r.onEnter) action(r.onEnter, w);
  const ids = new Set<string>();
  for (const h of r.hotspots) {
    const hw = `${w}.${h.id}`;
    if (ids.has(h.id) && !h.when) err(`${hw}: duplicate id without a condition`);
    ids.add(h.id);
    key(h.look, hw);
    key(h.name, hw);
    cond(h.when, hw);
    if (h.songSource && !songById.has(h.songSource)) err(`${hw}: unknown song ${h.songSource}`);
    if (h.talk && !dlgById.has(h.talk)) err(`${hw}: unknown dialogue ${h.talk}`);
    if (h.listen) action(h.listen, hw);
    if (h.sprite && !imageIds.has(h.sprite.image)) err(`${hw}: unknown image ${h.sprite.image}`);
    for (const [, c] of h.sprite?.frameWhen ?? []) cond(c, hw);
    for (const [k, a] of Object.entries(h.drafts ?? {})) {
      if (!draftKeys.has(k)) err(`${hw}: unknown draft key ${k}`);
      action(a, hw);
    }
    if (h.exit) {
      const to = roomById.get(h.exit.to);
      if (!to) err(`${hw}: exit to unknown room ${h.exit.to}`);
      else if (!(h.exit.entry in to.entries)) err(`${hw}: room ${to.id} has no entry ${h.exit.entry}`);
      cond(h.exit.when, hw);
      key(h.exit.blocked, hw);
      if (h.exit.when && !h.exit.blocked) err(`${hw}: a conditional exit needs a blocked line`);
    }
  }
  for (const [e, p] of Object.entries(r.entries)) if (p[0] < 0 || p[0] > r.width) err(`${w}: entry ${e} outside the room`);
}

// ---- songs and stems ----
const audioIds = new Set(manifest.audio.map((a) => a.id));
for (const s of songs) {
  key(s.caption, `song ${s.id}`);
  const src = read<{ bpm: number; bars: number; tracks: Record<string, { instrument: string }> }>(`music/src/${s.id}.json`);
  if (src.bpm !== s.bpm || src.bars !== s.bars) err(`song ${s.id}: bpm/bars differ from music/src`);
  for (const st of s.stems) {
    const w = `song ${s.id}.${st.id}`;
    key(st.label, w);
    cond(st.when, w);
    if (!audioIds.has(`${s.id}/${st.id}`)) err(`${w}: not in assets/manifest.json audio`);
    if (!existsSync(new URL(`assets/${st.file}.notes.json`, root))) err(`${w}: run tools/render-stems.py`);
    if (st.knot && !draftIds.has(st.knot)) err(`${w}: knot names unknown draft ${st.knot}`);
    if (!src.tracks[st.id]) err(`${w}: no track in music/src`);
    else if (src.tracks[st.id].instrument !== st.instrument) err(`${w}: instrument differs from music/src`);
  }
  const mask = s.stems.reduce((a, st) => a + (st.masksGolden ?? 0), 0);
  if (s.stems.some((st) => st.golden) && Math.abs(mask - 1) > 0.001) err(`song ${s.id}: masking weights should sum to 1 (they sum to ${mask})`);
}

// ---- dialogue ----
for (const d of dialogues) {
  if (!d.nodes[d.start]) err(`dialogue ${d.id}: start node missing`);
  for (const [nid, n] of Object.entries(d.nodes)) {
    const w = `dialogue ${d.id}.${nid}`;
    if (!speakerIds.has(n.speaker)) err(`${w}: unknown speaker ${n.speaker}`);
    key(n.text, w);
    cond(n.when, w);
    for (const t of [n.next, n.else, ...(n.choices ?? []).map((c) => c.next)]) if (t && !d.nodes[t]) err(`${w}: no node ${t}`);
    for (const c of n.choices ?? []) { key(c.text, w); cond(c.when, w); }
    for (const e of n.effects ?? []) if (!/^(setFlag|learnDraft|giveNote|giveSpools|giveTool|script):/.test(e)) err(`${w}: unknown effect ${e}`);
  }
}
for (const s of cast.speakers) {
  key(s.name, `speaker ${s.id}`);
  if (s.portrait && !imageIds.has(s.portrait)) err(`speaker ${s.id}: unknown portrait ${s.portrait}`);
}

// ---- puzzles: the map's needs must be reachable (no dead ends, GDD 9.8) ----
const BOT = /^(walk|comb|pull|isolate|cast|spool|arm|copy|drop|clear|close|look|talk|listen|exit|wait|learn|flag|use)(:|$)/;
for (const p of puzzles) {
  const w = `puzzle ${p.id}`;
  key(p.title, w);
  for (const h of p.hints) key(h, w);
  if (!roomById.has(p.room)) err(`${w}: unknown room ${p.room}`);
  for (const n of p.needs) {
    cond(n, w);
    const [k, a] = n.split(":");
    if (k === "puzzle" && !puzzleIds.has(a)) err(`${w}: needs unknown puzzle ${a}`);
    if (k === "draft" && !draftIds.has(a)) err(`${w}: needs unknown draft ${a}`);
  }
  for (const g of p.gives) if (!/^(draft|note|spools|tool|flag):/.test(g)) err(`${w}: unknown gift ${g}`);
  for (const s of p.bot) if (!BOT.test(s)) err(`${w}: unknown bot step ${s}`);
}
{
  // Graph check: from nothing, repeatedly solve any puzzle whose needs are met by what earlier puzzles gave.
  const have = { flags: {} as Record<string, boolean>, learned: [] as string[], solved: [] as string[], ownedNotes: 3, tools: [] as string[], capacity: 0 };
  const left = new Set(puzzleIds);
  const met = (n: string) => {
    const [k, a] = n.split(":");
    if (k === "puzzle") return have.solved.includes(a);
    if (k === "draft") return have.learned.includes(a);
    if (k === "tool") return have.tools.includes(a);
    if (k === "note") return have.ownedNotes >= "cdefgab".indexOf(a) + 1;
    if (k === "spools") return have.capacity >= Number(a);
    return true;
  };
  for (let changed = true; changed; ) {
    changed = false;
    for (const p of puzzles) {
      if (!left.has(p.id) || !p.needs.every(met)) continue;
      left.delete(p.id);
      have.solved.push(p.id);
      for (const g of p.gives) {
        const [k, a] = g.split(":");
        if (k === "draft") have.learned.push(a);
        if (k === "tool") have.tools.push(a);
        if (k === "note") have.ownedNotes = Math.max(have.ownedNotes, "cdefgab".indexOf(a) + 1);
        if (k === "spools") have.capacity = Math.max(have.capacity, Number(a));
      }
      changed = true;
    }
  }
  for (const id of left) err(`puzzle ${id}: its needs can never be met (dead end)`);
}

// ---- assets ----
for (const i of manifest.images) {
  for (const p of [i.path, i.normal].filter(Boolean) as string[]) {
    const f = new URL(`assets/${p}`, root);
    if (!existsSync(f)) {
      err(`asset ${i.id}: missing file ${p} (run npm run placeholders)`);
      continue;
    }
    const b = readFileSync(f);
    const w = b.readUInt32BE(16);
    const h = b.readUInt32BE(20);
    if (w !== i.w || h !== i.h) err(`asset ${i.id}: ${p} is ${w}x${h}, manifest says ${i.w}x${i.h}`);
  }
  if (i.frames > 1 && (i.frameW ?? 0) * i.frames !== i.w) err(`asset ${i.id}: frameW x frames must equal w`);
  if (!["placeholder", "generated", "final"].includes(i.status)) err(`asset ${i.id}: bad status`);
}
for (const a of manifest.audio) if (!existsSync(new URL(`assets/${a.hits}`, root))) err(`audio ${a.id}: hits file missing`);

if (errors.length) {
  for (const e of errors) console.error("✗", e);
  console.error(`\n${errors.length} content error(s)`);
  process.exit(1);
}
console.log(`content ok: ${rooms.length} rooms, ${puzzles.length} puzzles, ${dialogues.length} dialogues, ${songs.length} songs, ${Object.keys(strings).length} strings, ${manifest.images.length} images, ${manifest.audio.length} stems`);
