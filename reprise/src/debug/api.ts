// src/debug/api.ts: window.__reprise, development and bot builds only (GDD 9.8). The verbs are the
// puzzle `bot` steps; each one goes through the same code paths as a player's clicks and notes.
import * as Tone from "tone";
import type { NoteIndex, Target } from "../content/types";
import { puzzles, rooms } from "../content/load";
import { Spindle } from "../core/spindle";
import { GameBus } from "../core/bus";
import type { Conductor } from "../audio/conductor";
import type { NoteVoice } from "../audio/note-voice";
import { readSave, type Difficulty } from "../core/save";
import type { Game } from "../world/game";
import type { HudImpl } from "../ui/hud";

interface Deps {
  begin: () => Promise<void>;
  start: (fn: () => void) => void;
  showMenu: () => void;
}

export function install(g: Game, hud: HudImpl, _deps: Deps): void {
  const sleep = (ms: number) => new Promise((r) => window.setTimeout(r, ms));
  const log: string[] = [];

  async function idle(timeoutMs = 60000): Promise<void> {
    const t0 = performance.now();
    while (g.busy || hud.advance) {
      hud.advance?.();
      hud.skip();
      if (performance.now() - t0 > timeoutMs) throw new Error(`still busy after ${timeoutMs} ms in ${g.room?.id}`);
      await sleep(20);
    }
  }

  async function until(what: string, ok: () => boolean, bars = 6): Promise<void> {
    const deadline = performance.now() + Math.max(2000, g.conductor.barSeconds() * bars * 1000);
    while (!ok()) {
      if (performance.now() > deadline) throw new Error(`${what} never became true (room ${g.room.id})`);
      await idle();
      await sleep(30);
    }
  }

  function target(spec: string): Target | null {
    if (spec === "self" || spec === "none") return null;
    const [kind, id] = spec.split(":");
    if (kind === "hotspot") return { kind: "hotspot", id };
    if (kind === "thread") {
      const song = g.loom?.song.def.id ?? g.song?.def.id;
      if (!song) throw new Error("no song for a thread target");
      return { kind: "thread", song, stem: id };
    }
    throw new Error(`bad target ${spec}`);
  }

  /** Plays a learned draft note by note through the Distaff, like the player. */
  async function cast(draftKey: string, tgt: string): Promise<void> {
    const rev = draftKey.endsWith("_rev");
    const id = rev ? draftKey.slice(0, -4) : draftKey;
    if (!g.library.learned.has(id)) throw new Error(`cast ${draftKey}: not learned`);
    const t = target(tgt);
    if (t?.kind === "hotspot" && !g.hotspot(t.id)) throw new Error(`cast: no hotspot ${t.id} in ${g.room.id}`);
    g.select(t);
    g.distaff.clear();
    for (const n of g.library.phraseOf(id, rev)) {
      g.playNote(n as NoteIndex);
      await sleep(40);
    }
  }

  /** Walks room to room through exits whose conditions hold, using each exit like the player does. */
  async function walk(to: string): Promise<void> {
    for (let hops = 0; g.room.id !== to; hops++) {
      if (hops > 20) throw new Error(`walk ${to}: too far`);
      const exitId = g.exitToward(to);
      if (!exitId) throw new Error(`walk ${to}: no open route from ${g.room.id}`);
      const from = g.room.id;
      await g.clickHotspot(exitId, true);
      await idle();
      if (g.room.id === from) throw new Error(`walk ${to}: exit ${exitId} in ${from} did not let us through`);
    }
  }

  async function step(s: string): Promise<void> {
    log.push(s);
    await idle();
    const [verb, ...rest] = s.split(":");
    const arg = rest.join(":");
    switch (verb) {
      case "walk": return walk(arg);
      case "comb": {
        if (g.loom) g.closeLoom();
        g.select({ kind: "hotspot", id: arg });
        if (!g.comb()) throw new Error(`comb ${arg}: nothing to comb`);
        return;
      }
      case "pull": if (!g.pull(arg)) throw new Error(`pull ${arg} failed`); return;
      case "isolate":
        g.isolate(arg);
        await sleep(250);
        await idle();
        g.isolate(null);
        return;
      case "cast": {
        const [d, t] = arg.split(">");
        return cast(d, t ?? "self");
      }
      case "spool": g.spindle.select(Number(arg) - 1); if (g.spindle.selected !== Number(arg) - 1) throw new Error(`spool ${arg}: locked`); return;
      case "arm": g.spindle.setArmed(true); return;
      case "copy": if (!g.copyToSpool(arg)) throw new Error(`copy ${arg} failed`); return;
      case "drop": {
        const [n, t] = arg.split(">");
        const stem = t.replace(/^thread:/, "");
        if (!g.dropFromSpool(Number(n) - 1, stem)) throw new Error(`drop ${arg} failed`);
        return;
      }
      case "clear": g.spindle.clear(Number(arg) - 1); return;
      case "close": g.closeLoom(); return;
      case "look": case "talk": case "listen": case "exit": case "use":
        if (!g.hotspot(arg)) throw new Error(`${verb}: no hotspot ${arg} in ${g.room.id}`);
        await g.clickHotspot(arg, verb !== "use");
        return;
      case "wait": return g.waitBars(Number(arg) || 1);
      case "learn": return until(`learned ${arg}`, () => g.library.learned.has(arg));
      case "flag": return until(`flag ${arg}`, () => g.flag(arg));
      default: throw new Error(`unknown bot step ${s}`);
    }
  }

  async function runPuzzle(id: string): Promise<void> {
    const p = puzzles.find((x) => x.id === id);
    if (!p) throw new Error(`no puzzle ${id}`);
    if (!g.puzzles.needsMet(p)) throw new Error(`${id}: needs not met (${p.needs.join(", ")})`);
    for (const s of p.bot) {
      try {
        await step(s);
      } catch (e) {
        throw new Error(`${id} step "${s}": ${(e as Error).message}`);
      }
    }
    await idle();
    await until(`${id} solved`, () => g.puzzles.isSolved(id));
  }

  async function start(seed: number, difficulty: Difficulty = "standard", opts: { fast?: boolean; tempo?: number } = {}): Promise<void> {
    g.settings.calibrated = true;
    g.fast = opts.fast ?? true;
    g.conductor.tempoScale = opts.tempo ?? 1;
    await g.conductor.start(96);
    g.audioReady();
    document.getElementById("title")?.classList.add("hidden");
    g.newGame(seed, difficulty);
    await idle();
  }

  async function resume(opts: { fast?: boolean; tempo?: number } = {}): Promise<void> {
    const save = readSave();
    if (!save) throw new Error("no save to resume");
    g.settings.calibrated = true;
    g.fast = opts.fast ?? true;
    g.conductor.tempoScale = opts.tempo ?? 1;
    await g.conductor.start(96);
    g.audioReady();
    document.getElementById("title")?.classList.add("hidden");
    g.load(save);
    await idle();
  }

  /** Offline render of one bar with two spools: every note on its grid position within 1 ms (GDD 9.8). */
  async function timingTest(): Promise<{ maxErrorMs: number; notes: number; detail: number[][] }> {
    const bpm = 120;
    const beat = 60 / bpm;
    const heard: number[] = [];
    const buffer = await Tone.Offline(async ({ transport }) => {
      transport.bpm.value = bpm;
      // a one-sample impulse per note, on a raw buffer source: its first non-zero sample is where the note landed
      const raw = Tone.getContext().rawContext as BaseAudioContext;
      const imp = raw.createBuffer(1, 64, raw.sampleRate);
      imp.getChannelData(0)[0] = 1;
      const fakeConductor = { onBar: () => () => {} } as unknown as Conductor;
      const voice = {
        playAt: (_n: NoteIndex, time: number) => {
          heard.push(time);
          const src = raw.createBufferSource();
          src.buffer = imp;
          src.connect(raw.destination);
          src.start(time);
        },
      } as unknown as NoteVoice;
      const sp = new Spindle(fakeConductor, voice, new GameBus(), true);
      sp.capacity = 2;
      sp.select(0);
      sp.recordDraft("opening", false, { kind: "self" }, [0, 1, 2, 0], [0.02, 1.1, 1.96, 3.05]);
      sp.select(1);
      sp.recordDraft("healing", false, { kind: "self" }, [2, 1, 0, 2], [0.49, 1.52, 2.48, 3.51]);
      transport.start(0);
    }, beat * 4 - 0.01);
    // grid: the recorded beats, quantized to eighths, in the first bar
    const grid = [0, 1, 2, 3, 0.5, 1.5, 2.5, 3.5].map((b) => b * beat).sort((a, b) => a - b);
    const data = buffer.getChannelData(0);
    const sr = buffer.sampleRate;
    const detail: number[][] = [];
    let maxErr = 0;
    for (const g of grid) {
      const scheduled = heard.reduce((best, t) => (Math.abs(t - g) < Math.abs(best - g) ? t : best), Infinity);
      let onset = Infinity;
      for (let i = Math.max(0, Math.floor((g - 0.002) * sr)); i < Math.min(data.length, (g + 0.01) * sr); i++) {
        if (Math.abs(data[i]) > 0.001) {
          onset = i / sr;
          break;
        }
      }
      const err = Math.max(Math.abs(scheduled - g), Math.abs(onset - g));
      detail.push([g, scheduled, onset]);
      maxErr = Math.max(maxErr, err);
    }
    return { maxErrorMs: maxErr * 1000, notes: heard.length, detail };
  }

  (window as unknown as { __reprise: unknown }).__reprise = {
    g,
    hud,
    rooms,
    puzzles,
    log,
    start,
    resume,
    step,
    runPuzzle,
    idle,
    timingTest,
    state: () => ({ room: g.room?.id, flags: { ...g.save.flags }, learned: [...g.library.learned], solved: [...g.save.solved], notes: g.library.ownedNotes, spools: g.spindle.save(), busy: g.busy }),
    phrase: (id: string) => g.library.phraseOf(id),
  };
}
