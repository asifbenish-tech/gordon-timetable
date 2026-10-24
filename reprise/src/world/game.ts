// src/world/game.ts: the adventure layer. Rooms, flags, saves and the receivers that turn casts into effects.
// It talks to the music systems only through draft receivers and flags (GDD 9.2).
import * as Tone from "tone";
import type { CastEvent } from "../core/bus";
import { GameBus } from "../core/bus";
import { Conductor } from "../audio/conductor";
import { Mixer } from "../audio/mixer";
import { NoteVoice, noteMidi } from "../audio/note-voice";
import { Song, type StemData } from "../audio/song";
import { DraftLibrary } from "../core/drafts";
import { Distaff } from "../core/distaff";
import { Spindle } from "../core/spindle";
import { Effects } from "../core/effects";
import { LoomModel } from "../core/loom";
import { newSave, writeSave, type Difficulty, type SaveData, type Settings } from "../core/save";
import type { HotspotDef, NoteIndex, Phrase, RoomDef, SpeakerDef, Target } from "../content/types";
import { targetKey } from "../content/types";
import { dialogues, drafts, puzzles as puzzleDefs, rooms, songs, speakers, stemHits, stemNotes } from "../content/load";
import { t, has } from "../content/strings";
import { check, noteCount, NOTE_NAMES, type CondState } from "./flags";
import { PuzzleTracker } from "./puzzles";
import { LOGIC, SCRIPTS } from "./scripts";

export const START_ROOM = "crossing";
export const STATE_DRAFTS = new Set([
  "hushing", "hushing_rev", "quickening", "quickening_rev", "swelling", "swelling_rev", "tuning_rev",
]);

export interface View {
  buildRoom(room: RoomDef, entry: string): void;
  walkTo(x: number, y: number, instant?: boolean): Promise<void>;
  bobbinPos(): [number, number];
  face(x: number): void;
  setSprite(id: string, s: { anim?: string; frame?: number; visible?: boolean; flipX?: boolean; alpha?: number }): void;
  moveSprite(id: string, x: number, y: number, seconds: number): Promise<void>;
  glint(hotspotId: string | null): void;
  skeinLook(x: number | null): void;
  flash(color: number, ms: number): void;
  refreshHotspots(): void;
  hotspotCenter(id: string): [number, number] | null;
  setSwan(swan: boolean): void;
  openLoom(song: Song): void;
  closeLoom(): void;
  setRestored(level: number): void;
  setFlockWhite(level: number): void;
}

export interface Hud {
  say(speaker: string, text: string): Promise<void>;
  dialogue(speaker: SpeakerDef, text: string, choices: string[] | null): Promise<number>;
  caption(text: string): void;
  toast(text: string): void;
  selection(label: string | null, target: Target | null): void;
  refresh(): void;
  teachNotes(phrase: Phrase, times: number[], draftId: string | null): void;
  loomOpened(): void;
  loomClosed(): void;
  episodeEnd(): Promise<void>;
  busy(on: boolean): void;
}

export interface RoomLogic {
  enter?(): void;
  leave?(): void;
  bar?(bar: number, time: number): void;
  hit?(stem: string, time: number): void;
  /** Return true to stop the default receivers. */
  cast?(e: CastEvent, key: string): boolean;
  update?(): void;
  exit?(hotspotId: string): Promise<boolean> | boolean;
  loomOpened?(): void;
  loomClosed?(): void;
}

export type ScriptFn = (g: Game, arg: string, quiet: boolean) => Promise<void> | void;
export type LogicFactory = (g: Game) => RoomLogic;

export class Game {
  readonly bus = new GameBus();
  readonly conductor = new Conductor();
  readonly effects = new Effects();
  mixer: Mixer | null = null;
  voice: NoteVoice;
  library!: DraftLibrary;
  distaff!: Distaff;
  spindle!: Spindle;
  save!: SaveData;
  puzzles!: PuzzleTracker;
  room!: RoomDef;
  song: Song | null = null;
  selection: Target | null = null;
  loom: { song: Song; hotspot: string } | null = null;
  logic: RoomLogic | null = null;
  view: View | null = null;
  hud: Hud | null = null;
  fast = false; // the solvability bot: lines don't wait for reading
  hudSelectThread: ((id: string) => void) | null = null;
  private busyDepth = 0;
  private models = new Map<string, LoomModel>();
  private unsubs: (() => void)[] = [];
  private lastSave = 0;

  constructor(public settings: Settings) {
    this.voice = new NoteVoice(null);
  }

  /** After Tone.start(): the mixer and voices need a running AudioContext. */
  audioReady(): void {
    if (this.mixer) return;
    this.mixer = new Mixer();
    this.mixer.setVolumes(this.settings.music, this.settings.effects);
    this.voice = new NoteVoice(this.mixer);
    this.conductor.calibrationSec = this.settings.calibrationSec;
  }

  get busy(): boolean {
    return this.busyDepth > 0;
  }

  async cutscene<T>(fn: () => Promise<T>): Promise<T> {
    this.busyDepth++;
    this.hud?.busy(true);
    try {
      return await fn();
    } finally {
      this.busyDepth--;
      if (!this.busyDepth) this.hud?.busy(false);
    }
  }

  cond(expr: string | undefined): boolean {
    if (!expr) return true;
    return check(this.condState(), expr);
  }

  condState(): CondState {
    const s = this.save;
    if (!s) return { flags: {}, learned: [], solved: [], ownedNotes: 8, tools: [], capacity: 0 }; // the title screen
    return { flags: s.flags, learned: this.library.learned, solved: s.solved, ownedNotes: this.library.ownedNotes, tools: s.tools, capacity: this.spindle.capacity };
  }

  // ---- starting and loading -------------------------------------------------------------

  newGame(seed: number, difficulty: Difficulty): void {
    this.load(newSave(seed, difficulty, START_ROOM, "start"));
  }

  load(save: SaveData): void {
    for (const u of this.unsubs) u();
    this.unsubs = [];
    this.save = save;
    this.effects.clearAll();
    this.models.clear();
    this.song?.dispose();
    this.song = null;
    this.library = new DraftLibrary(drafts.drafts, save.seed, drafts.fallbackPool);
    for (const id of save.learned) this.library.learned.add(id);
    this.library.ownedNotes = save.ownedNotes;
    this.spindle = new Spindle(this.conductor, this.voice, this.bus, !!this.mixer);
    this.distaff = new Distaff(this.conductor, this.library, this.voice, this.bus, this.spindle);
    this.distaff.resetBeats = this.settings.resetBeats;
    this.puzzles = new PuzzleTracker(puzzleDefs, () => this.condState());
    this.unsubs.push(
      this.bus.on("cast", (e) => this.onCast(e)),
      this.bus.on("phraseFailed", () => this.voice.stingerFor(false, Tone.now() + 0.05)),
      this.bus.on("spoolThreadAdded", ({ slot, thread }) => this.song?.addGuest(slot, thread)),
      this.bus.on("spoolThreadRemoved", ({ slot }) => {
        this.song?.removeGuest(slot);
        for (const m of Object.values(this.save.mods)) {
          for (const [stem, s] of Object.entries(m.replaced)) if (s === slot) delete m.replaced[stem];
        }
      }),
      this.bus.on("spoolsChanged", () => this.hud?.refresh()),
      this.bus.on("hit", (e) => this.logic?.hit?.(e.stem, e.time)),
      this.conductor.onBar((bar, time) => {
        Tone.getDraw().schedule(() => {
          this.bus.emit("bar", { bar, time });
          this.logic?.bar?.(bar, time);
        }, time);
      }),
    );
    this.spindle.load(save.spools, save.capacity);
    this.enterRoom(save.room, save.entry);
    this.hud?.refresh();
  }

  persist(force = false): void {
    if (!this.save) return;
    const now = performance.now();
    if (!force && now - this.lastSave < 500) return;
    this.lastSave = now;
    this.save.learned = [...this.library.learned];
    this.save.ownedNotes = this.library.ownedNotes;
    this.save.spools = this.spindle.save();
    this.save.capacity = this.spindle.capacity;
    writeSave(this.save);
  }

  // ---- rooms ---------------------------------------------------------------------------

  enterRoom(id: string, entry: string): void {
    const room = rooms.get(id);
    if (!room) throw new Error(`Unknown room ${id}`);
    this.logic?.leave?.();
    if (this.loom) this.closeLoom();
    this.room = room;
    this.save.room = id;
    this.save.entry = entry;
    this.select(null);
    this.playSong(room.song);
    this.logic = room.logic ? (LOGIC[room.logic]?.(this) ?? null) : null;
    this.view?.buildRoom(room, entry);
    this.view?.setSwan(!!room.swan && !this.save.flags.human);
    this.refreshLook();
    this.logic?.enter?.();
    this.persist(true);
    this.bus.emit("roomEntered", { id });
    if (room.onEnter) void this.run(room.onEnter);
  }

  /** Restoration and the flock's whiteness, from what has been restored so far (GDD 7.4). */
  refreshLook(): void {
    const restoredBy: Record<string, string> = { park: "note:f", spire: "note:f", factory: "note:g", arena: "note:g", crossing: "true", street: "note:g" };
    this.view?.setRestored(this.cond(restoredBy[this.room.location] ?? "false") ? 1 : 0);
    // The flock's whiteness is the progress bar: each note won back after the crack whitens it.
    const restored = this.save.flags.human ? Math.max(0, this.library.ownedNotes - 3) : 0;
    const white = this.save.flags.flock_grey ? restored / 5 : 1;
    this.view?.setFlockWhite(white);
  }

  model(songId: string): LoomModel {
    let m = this.models.get(songId);
    if (!m) {
      const def = songs.get(songId);
      if (!def) throw new Error(`Unknown song ${songId}`);
      const mods = this.save ? (this.save.mods[songId] ??= { untied: [], replaced: {} }) : { untied: [], replaced: {} };
      m = new LoomModel(def, this.effects, mods, (s) => this.cond(s.when));
      this.models.set(songId, m);
    }
    return m;
  }

  stemData = (song: string, stem: string): StemData => {
    const f = stemNotes(song, stem);
    const phrase = f.draft ? this.library.phraseOf(f.draft) : null;
    const notes = f.notes.map((n) => (n.m >= 0 || !phrase ? n : { ...n, m: noteMidi(phrase[n.k ?? 0]) + 12 * (n.o ?? 0) }));
    return { notes, hits: stemHits(song, stem), bars: f.bars, instrument: f.instrument };
  };

  playSong(id: string): void {
    const def = songs.get(id);
    if (!def) throw new Error(`Unknown song ${id}`);
    this.conductor.setBpm(def.bpm);
    if (this.song?.def.id === id) return;
    this.song?.dispose();
    this.song = null;
    if (!this.mixer) return;
    this.song = new Song(this.model(id), this.stemData, this.conductor, this.mixer, this.bus);
    if (this.save?.difficulty === "expert") this.song.goldenCurve = (l) => l * l * l;
    this.song.start();
    for (const { slot, thread } of this.spindle?.threadSlots() ?? []) this.song.addGuest(slot, thread);
    if (def.caption) this.caption(def.caption);
  }

  caption(key: string): void {
    if (this.settings.captions) this.hud?.caption(t(key));
  }

  hotspot(id: string): HotspotDef | undefined {
    return this.room.hotspots.find((h) => h.id === id && this.cond(h.when));
  }

  hotspots(): HotspotDef[] {
    return this.room.hotspots.filter((h) => this.cond(h.when));
  }

  select(target: Target | null): void {
    this.selection = target;
    let label: string | null = null;
    if (target?.kind === "hotspot") label = t(this.hotspot(target.id)?.name ?? target.id);
    if (target?.kind === "thread") {
      const stem = this.model(target.song).stem(target.stem);
      label = stem ? t(stem.label) : null;
    }
    this.hud?.selection(label, target);
  }

  // ---- player verbs -----------------------------------------------------------------------

  async clickHotspot(id: string, double: boolean): Promise<void> {
    if (this.busy) return;
    const h = this.hotspot(id);
    if (!h) return;
    if (h.exit) {
      if (!double) await this.walkToHotspot(h);
      await this.useExit(h);
      return;
    }
    this.select({ kind: "hotspot", id });
    if (double) {
      const c = this.view?.hotspotCenter(id);
      if (c) this.view?.face(c[0]);
      await this.examine(h);
    } else await this.walkToHotspot(h);
  }

  async walkToHotspot(h: HotspotDef): Promise<void> {
    const [x, y, w, hh] = h.rect;
    const stand = h.stand ?? [x + w / 2, y + hh + 6];
    await this.view?.walkTo(stand[0], stand[1]);
    this.view?.face(x + w / 2);
  }

  async examine(h: HotspotDef): Promise<void> {
    if (h.talk) await this.dialogue(h.talk);
    else if (h.listen) await this.run(h.listen);
    else await this.say("bobbin", h.look);
  }

  async useExit(h: HotspotDef): Promise<void> {
    const ex = h.exit!;
    if (!this.cond(ex.when)) {
      if (ex.blocked) await this.say("bobbin", ex.blocked);
      return;
    }
    if (ex.check) {
      const ok = await this.logic?.exit?.(h.id);
      if (!ok) return;
    }
    this.enterRoom(ex.to, ex.entry);
  }

  clickFloor(x: number, y: number, double: boolean): void {
    if (this.busy) return;
    this.select(null);
    void this.view?.walkTo(x, y, double);
  }

  playNote(n: NoteIndex): void {
    if (this.busy && !this.save.flags.allow_notes_in_cutscene) return;
    this.mixer?.duck(true);
    this.distaff.playNote(n, this.selection);
  }

  // ---- receivers: where every cast lands --------------------------------------------------

  onCast(e: CastEvent): void {
    const key = e.reversed ? `${e.id}_rev` : e.id;
    const now = Tone.now();
    if (!e.fromLoop) {
      this.voice.stingerFor(true, now + 0.08);
      this.mixer?.duck(false);
    }
    const dur = this.conductor.barSeconds() + 0.06;
    if (STATE_DRAFTS.has(key)) this.effects.apply(targetKey(e.target), key, now, dur);
    if (this.logic?.cast?.(e, key)) return;
    const tg = e.target;
    if (tg?.kind === "thread") return this.castOnThread(tg, key, e);
    const quiet = e.fromLoop;
    if (tg?.kind === "hotspot") {
      const h = this.hotspot(tg.id);
      if (!h) return;
      const action = h.drafts?.[key];
      if (action) void this.run(action, quiet);
      else if (!quiet) void this.say("bobbin", this.defaultLine(key), { target: t(h.name) });
      return;
    }
    const action = this.room.hotspots.find((h) => h.id === "_self")?.drafts?.[key];
    if (action) void this.run(action, quiet);
    else if (!quiet) void this.say("bobbin", has(`self.${key}`) ? `self.${key}` : "self.default");
  }

  defaultLine(key: string): string {
    return has(`draft.default.${key}`) ? `draft.default.${key}` : "draft.default.any";
  }

  castOnThread(tg: { song: string; stem: string }, key: string, e: CastEvent): void {
    const m = this.model(tg.song);
    const stem = m.stem(tg.stem);
    if (!stem) return;
    if (stem.knot && stem.knot === key) {
      if (m.isTied(stem.id)) {
        m.untie(stem.id);
        this.bus.emit("flag", { name: `untied:${tg.song}:${stem.id}`, value: true });
        void this.say("bobbin", "thread.untied", { thread: t(stem.label) });
        this.persist(true);
        this.checkPuzzles();
      }
      return;
    }
    if (e.fromLoop || STATE_DRAFTS.has(key)) return;
    const k = has(`thread.default.${key}`) ? `thread.default.${key}` : "thread.default.any";
    void this.say("bobbin", k, { thread: t(stem.label) });
  }

  // ---- actions and scripts --------------------------------------------------------------------

  /** "say:key", "flag:x", "unflag:x", "script:name:arg", "dialogue:id", several joined by ";". */
  async run(actions: string, quiet = false): Promise<void> {
    for (const a of actions.split(";").map((s) => s.trim()).filter(Boolean)) {
      const [kind, ...rest] = a.split(":");
      const arg = rest.join(":");
      if (kind === "say") {
        if (!quiet) await this.say("bobbin", arg);
      } else if (kind === "flag") this.setFlag(arg);
      else if (kind === "unflag") this.setFlag(arg, false);
      else if (kind === "dialogue") await this.dialogue(arg);
      else if (kind === "script") {
        const [name, ...sargs] = arg.split(":");
        const fn = SCRIPTS[name];
        if (!fn) throw new Error(`Unknown script ${name}`);
        await fn(this, sargs.join(":"), quiet);
      } else throw new Error(`Unknown action ${a}`);
    }
  }

  async say(speaker: string, key: string, vars: Record<string, string> = {}): Promise<void> {
    const text = t(key, vars);
    this.bus.emit("say", { speaker, text });
    const sp = speakers.get(speaker);
    if (sp && speaker !== "bobbin") this.speakerSignature(sp);
    if (!this.hud) return;
    await this.hud.say(speaker, text);
  }

  async dialogue(id: string): Promise<void> {
    const d = dialogues.get(id);
    if (!d) throw new Error(`Unknown dialogue ${id}`);
    await this.cutscene(async () => {
      let nodeId: string | undefined = d.start;
      let guard = 0;
      while (nodeId && guard++ < 200) {
        const node: (typeof d.nodes)[string] | undefined = d.nodes[nodeId];
        if (!node) throw new Error(`Dialogue ${id}: missing node ${nodeId}`);
        if (node.when && !this.cond(node.when)) {
          nodeId = node.else ?? node.next;
          continue;
        }
        const sp = speakers.get(node.speaker);
        if (!sp) throw new Error(`Unknown speaker ${node.speaker}`);
        const choices = node.choices?.filter((c) => this.cond(c.when)) ?? null;
        this.speakerSignature(sp);
        this.bus.emit("say", { speaker: sp.id, text: t(node.text) });
        const pick = this.hud ? await this.hud.dialogue(sp, t(node.text), choices?.map((c) => t(c.text)) ?? null) : 0;
        for (const eff of node.effects ?? []) await this.effect(eff);
        nodeId = choices?.length ? choices[pick]?.next : node.next;
      }
    });
  }

  private speakerSignature(sp: SpeakerDef): void {
    if (!this.mixer || this.fast) return;
    this.voice.signature(sp.instrument, sp.signature, Tone.now() + 0.02);
  }

  async effect(eff: string): Promise<void> {
    const [kind, ...rest] = eff.split(":");
    const arg = rest.join(":");
    if (kind === "setFlag") this.setFlag(arg);
    else if (kind === "learnDraft") this.learn(arg);
    else if (kind === "giveNote") this.giveNote(arg);
    else if (kind === "giveSpools") this.giveSpools(Number(arg));
    else if (kind === "giveTool") this.giveTool(arg);
    else if (kind === "script") await this.run(`script:${arg}`);
    else throw new Error(`Unknown effect ${eff}`);
  }

  setFlag(name: string, value = true): void {
    if (!!this.save.flags[name] === value) return;
    if (value) this.save.flags[name] = true;
    else delete this.save.flags[name];
    this.bus.emit("flag", { name, value });
    this.view?.refreshHotspots();
    this.checkPuzzles();
  }

  flag(name: string): boolean {
    return !!this.save.flags[name];
  }

  learn(id: string): void {
    if (this.library.learned.has(id)) return;
    this.library.learned.add(id);
    this.save.flags[`learned_${id}`] = true;
    if (this.save.difficulty === "practice") this.save.book[id] = [...this.library.phraseOf(id)];
    this.bus.emit("learned", { id });
    this.hud?.toast(t("toast.learned", { draft: t(`draft.${id}`) }));
    this.hud?.refresh();
    this.persist(true);
    this.checkPuzzles();
  }

  giveNote(letter: string): void {
    const count = noteCount(letter);
    if (this.library.ownedNotes >= count) return;
    this.library.ownedNotes = count;
    this.bus.emit("notesOwned", { count });
    this.hud?.toast(t("toast.note", { note: NOTE_NAMES[count - 1] }));
    this.hud?.refresh();
    this.refreshLook();
    this.persist(true);
    this.checkPuzzles();
  }

  /** The Distaff cracks: only c, d and e remain (P3). */
  crackDistaff(): void {
    this.library.ownedNotes = 3;
    this.distaff.clear();
    this.bus.emit("notesOwned", { count: 3 });
    this.hud?.refresh();
    this.refreshLook();
    this.persist(true);
  }

  giveSpools(n: number): void {
    this.spindle.setCapacity(n);
    if (!this.save.tools.includes("spindle")) this.save.tools.push("spindle");
    this.hud?.toast(t("toast.spools", { n }));
    this.hud?.refresh();
    this.persist(true);
    this.checkPuzzles();
  }

  giveTool(tool: string): void {
    if (this.save.tools.includes(tool)) return;
    this.save.tools.push(tool);
    this.hud?.toast(t(`toast.tool.${tool}`));
    this.hud?.refresh();
    this.persist(true);
    this.checkPuzzles();
  }

  checkPuzzles(): void {
    if (!this.puzzles) return;
    for (let guard = 0; guard < 20; guard++) {
      const solved = this.puzzles.newlySolved();
      if (!solved.length) return;
      for (const p of solved) {
        this.save.solved.push(p.id);
        for (const g of p.gives) {
          const [kind, arg] = g.split(":");
          if (kind === "draft") this.learn(arg);
          else if (kind === "note") this.giveNote(arg);
          else if (kind === "spools") this.giveSpools(Number(arg));
          else if (kind === "tool") this.giveTool(arg);
          else if (kind === "flag") this.setFlag(arg);
        }
        this.bus.emit("solved", { id: p.id });
      }
      this.persist(true);
    }
  }

  /** A teaching source performs a draft; the Distaff shows it; then it is in the Book of Patterns. */
  async teach(voice: string, draftId: string, opts: { learn?: boolean; reversed?: boolean } = {}): Promise<void> {
    const phrase = this.library.phraseOf(draftId, opts.reversed);
    const beat = this.conductor.beatSeconds();
    const start = Tone.now() + 0.15;
    const times = this.voice.teach(voice, phrase, start, beat);
    this.hud?.teachNotes(phrase, times, draftId);
    this.bus.emit("teach", { phrase, draftId });
    await this.waitSeconds(beat * 4 + 0.3);
    if (opts.learn !== false) this.learn(draftId);
  }

  /** Waits measured on the AudioContext clock (GDD 9.3 rule 1). */
  waitSeconds(s: number): Promise<void> {
    if (this.fast) s = Math.min(s, 0.05);
    if (!this.mixer) return Promise.resolve();
    return new Promise((res) => Tone.getContext().setTimeout(res, s));
  }

  waitBars(n: number): Promise<void> {
    return new Promise((res) => {
      let left = n;
      const off = this.conductor.onBar((_b, time) => {
        if (--left <= 0) {
          off();
          Tone.getDraw().schedule(res, time);
        }
      });
    });
  }

  // ---- the Loom View -----------------------------------------------------------------------

  comb(): boolean {
    const sel = this.selection;
    if (!this.save.tools.includes("combing") || sel?.kind !== "hotspot") return false;
    const h = this.hotspot(sel.id);
    if (!h?.songSource) {
      void this.say("bobbin", "comb.nothing", { target: h ? t(h.name) : "" });
      return false;
    }
    if (h.songSource !== this.song?.def.id) this.playSong(h.songSource);
    if (!this.song) return false;
    this.loom = { song: this.song, hotspot: h.id };
    this.view?.openLoom(this.song);
    this.hud?.loomOpened();
    this.logic?.loomOpened?.();
    return true;
  }

  closeLoom(): void {
    if (!this.loom) return;
    this.loom.song.model.closeView();
    this.loom = null;
    this.view?.closeLoom();
    this.hud?.loomClosed();
    this.select(null);
    this.logic?.loomClosed?.();
    if (this.song && this.song.def.id !== this.room.song) this.playSong(this.room.song);
  }

  pull(stemId: string): boolean {
    const m = this.loom?.song.model;
    const stem = m?.stem(stemId);
    if (!m || !stem) return false;
    if (stem.sealed) {
      void this.say("bobbin", "loom.sealed");
      return false;
    }
    if (m.pulled.has(stemId)) m.pulled.delete(stemId);
    else m.pulled.add(stemId);
    this.logic?.update?.(); // a pull lands now, not on the next frame
    this.checkPuzzles();
    return true;
  }

  isolate(stemId: string | null): void {
    const m = this.loom?.song.model;
    if (!m) return;
    m.isolated = stemId;
    if (stemId) this.logic?.cast?.({ id: "_isolate", reversed: false, target: { kind: "thread", song: m.def.id, stem: stemId }, fromLoop: false }, "_isolate");
  }

  copyToSpool(stemId: string): boolean {
    const m = this.loom?.song.model;
    const stem = m?.stem(stemId);
    if (!m || !stem || this.spindle.capacity === 0) return false;
    if (stem.golden) {
      void this.say("bobbin", "loom.golden_copy");
      return false;
    }
    this.spindle.copyThread({ song: m.def.id, stem: stemId });
    this.setFlag(`spooled:${m.def.id}:${stemId}`);
    void this.say("bobbin", "loom.copied", { thread: t(stem.label), n: String(this.spindle.selected + 1) });
    this.persist(true);
    this.checkPuzzles();
    return true;
  }

  dropFromSpool(slot: number, stemId: string): boolean {
    const m = this.loom?.song.model;
    const stem = m?.stem(stemId);
    const s = this.spindle.spool(slot);
    if (!m || !stem || s?.kind !== "thread") return false;
    if (stem.sealed) {
      void this.say("bobbin", "loom.sealed");
      return false;
    }
    if (s.thread.song === m.def.id && s.thread.stem === stemId) return false;
    for (const [k, v] of Object.entries(m.mods.replaced)) if (v === slot) delete m.mods.replaced[k];
    m.mods.replaced[stemId] = slot;
    this.logic?.update?.();
    this.persist(true);
    this.checkPuzzles();
    return true;
  }

  removeDrop(stemId: string): void {
    const m = this.loom?.song.model;
    if (!m) return;
    delete m.mods.replaced[stemId];
    this.persist(true);
  }

  // ---- Skein's hints -------------------------------------------------------------------------

  async hint(): Promise<void> {
    if (this.busy || !this.flag("skein")) return;
    const p = this.puzzles.current(this.room.id);
    if (!p) {
      await this.say("bobbin", "hint.none");
      return;
    }
    const tier = this.save.hints[p.id] ?? 0;
    this.save.hints[p.id] = Math.min(2, tier + 1);
    if (tier === 0) {
      const focus = p.room === this.room.id ? p.focus : this.exitToward(p.room);
      const c = focus ? this.view?.hotspotCenter(focus) : null;
      this.view?.skeinLook(c ? c[0] : null);
      this.view?.glint(focus ?? null);
      await this.say("skein", p.hints[0]);
    } else await this.say("bobbin", p.hints[tier]);
    this.persist(true);
  }

  /** The exit in this room on the shortest open route toward `roomId`. */
  exitToward(roomId: string): string | undefined {
    const first = new Map<string, string>();
    const queue: string[] = [];
    for (const h of this.hotspots()) {
      if (h.exit && this.cond(h.exit.when) && !first.has(h.exit.to)) {
        first.set(h.exit.to, h.id);
        queue.push(h.exit.to);
      }
    }
    const seen = new Set([this.room.id, ...queue]);
    while (queue.length) {
      const r = queue.shift()!;
      if (r === roomId) return first.get(r);
      for (const h of rooms.get(r)?.hotspots ?? []) {
        if (!h.exit || seen.has(h.exit.to) || !this.cond(h.when) || !this.cond(h.exit.when)) continue;
        seen.add(h.exit.to);
        first.set(h.exit.to, first.get(r)!);
        queue.push(h.exit.to);
      }
    }
    return undefined;
  }

  /** In Practice the Book writes itself; in Standard and Expert the player's notes live here. */
  bookNotes(id: string): (number | null)[] {
    if (this.save.difficulty === "practice") return [...this.library.phraseOf(id)];
    return this.save.book[id] ?? [null, null, null, null];
  }

  frame(): void {
    this.song?.update();
    this.logic?.update?.();
  }
}
