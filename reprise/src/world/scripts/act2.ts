// src/world/scripts/act2.ts: the Guild of Producers, "How is it made?" (A2-1 to A2-10).
import * as Tone from "tone";
import { targetKey } from "../../content/types";
import type { Game, LogicFactory, ScriptFn } from "../game";

function once(g: Game, flag: string, key: string, speaker = "bobbin"): void {
  if (g.flag(flag)) return;
  g.setFlag(flag);
  void g.say(speaker, key);
}

/** Is a draft looping on this target from any spool? */
function looped(g: Game, key: string, draft: string, reversed = false): boolean {
  return g.spindle.loopsOn(targetKey, key, draft, reversed).length > 0;
}

function carrying(g: Game, song: string, stem: string): boolean {
  return g.spindle.threadSlots().some(({ thread }) => thread.song === song && thread.stem === stem);
}

/** A2-1: under the factory-issue hook, Juno's own riff. */
const juno: LogicFactory = (g) => ({
  loomOpened() {
    if (g.loom?.song.def.id === "juno" && !g.flag("juno_ally")) once(g, "said_juno_glint", "juno.glint");
  },
  update() {
    const lv = g.loom;
    if (lv?.song.def.id !== "juno" || g.flag("juno_ally") || g.busy) return;
    if (lv.song.model.goldenLevel(Tone.now()) >= 0.99) {
      void g.cutscene(async () => {
        g.setFlag("juno_riff_found");
        await g.say("bobbin", "juno.riff_found");
        g.closeLoom();
        await g.dialogue("juno_riff");
        g.setFlag("juno_ally");
      });
    }
  },
});

/** A2-3: the Topline Conveyor carries Bobbin only while Quickening holds, bar after bar. */
const press: LogicFactory = (g) => ({
  update() {
    const quick = g.effects.isActive("hotspot:conveyor", "quickening", Tone.now());
    g.view?.setSprite("conveyor", quick ? { anim: "conveyor_fast" } : { anim: "conveyor" });
  },
  async exit(id) {
    if (id !== "conveyor_up") return true;
    if (g.flag("rode_conveyor")) return true;
    const quick = g.effects.isActive("hotspot:conveyor", "quickening", Tone.now());
    if (quick && looped(g, "hotspot:conveyor", "quickening")) {
      await g.cutscene(async () => {
        await g.say("bobbin", "press.ride");
        g.setFlag("rode_conveyor");
      });
      return true;
    }
    await g.say("bobbin", quick ? "press.ride_fail" : "press.too_slow");
    return false;
  },
});

/** A2-5: three listeners, one layer each; all three dials green at once. */
const panel: LogicFactory = (g) => {
  let greenBars = 0;
  const dials = () => {
    const m = g.model("panel");
    const now = Tone.now();
    return {
      rhythm: m.state("drums", "quickening", now),
      melody: !m.isTied("topline"),
      harmony: m.state("jingle", "hushing", now),
    };
  };
  return {
    enter() {
      greenBars = 0;
    },
    update() {
      const d = dials();
      g.view?.setSprite("dial_rhythm", { frame: d.rhythm ? 1 : 0 });
      g.view?.setSprite("dial_melody", { frame: d.melody ? 1 : 0 });
      g.view?.setSprite("dial_harmony", { frame: d.harmony ? 1 : 0 });
      const m = g.model("panel");
      if (m.state("drums", "hushing", Tone.now())) once(g, "said_panel_asleep", "panel.asleep");
    },
    bar() {
      if (g.flag("preset_pass") || g.busy) return;
      const d = dials();
      const n = Number(d.rhythm) + Number(d.melody) + Number(d.harmony);
      greenBars = n === 3 ? greenBars + 1 : 0;
      if (n === 2) once(g, "said_panel_two", "panel.two_green");
      if (greenBars >= 1) {
        void g.cutscene(async () => {
          g.caption("caption.panel_green");
          g.closeLoom();
          await g.dialogue("host_pass");
          g.setFlag("preset_pass");
        });
      }
    },
  };
};

/** A2-6, puzzle 2: "The Sidechain Gate". The gate is a state machine on the kick's hit events. */
const gate: LogicFactory = (g) => {
  let lastKick = 0;
  let deadBars = 0;
  let silentSince: number | null = null;
  let alarming = false;
  const kickSilent = () => g.model("factory").silenced("kick", Tone.now());
  const alarm = async (fromLoop: boolean) => {
    alarming = true;
    await g.cutscene(async () => {
      g.caption("caption.dead_air");
      g.view?.flash(0xff2020, 600);
      await g.say("klaxon", "gate3.klaxon");
      g.setFlag("foreman_here");
      await g.say("bobbin", "gate3.duck");
      await g.view?.walkTo(450, 284, true);
      await g.view?.moveSprite("foreman", 470, 280, 1.2);
      await g.say("foreman", "gate3.foreman_who");
      if (fromLoop) {
        for (let i = 0; i < 4; i++) {
          const s = g.spindle.spool(i);
          if (s?.kind === "draft" && targetKey(s.target) === "thread:factory:kick") g.spindle.clear(i);
        }
        await g.say("foreman", "gate3.foreman_clears");
        await g.say("juno", "gate3.cover_first");
      } else {
        await g.say("foreman", "gate3.foreman_reset");
      }
      await g.view?.moveSprite("foreman", 720, 280, 1.2);
      g.setFlag("foreman_here", false);
      g.effects.end("thread:factory:kick", "hushing");
      deadBars = 0;
      silentSince = null;
    });
    alarming = false;
  };
  return {
    hit(stem, time) {
      if (stem !== "kick") return;
      lastKick = time;
      if (g.flag("gate_passed")) return;
      g.view?.setSprite("gate", { frame: 0 });
      if (carrying(g, "factory", "kick")) once(g, "said_two_kicks", "gate3.two_kicks");
    },
    update() {
      if (g.flag("gate_passed")) return g.view?.setSprite("gate", { frame: 1 });
      const now = Tone.now();
      if (now - lastKick > 0.12) g.view?.setSprite("gate", { frame: 1 });
      // A single Hushing: the gate stays open for exactly that bar, then the floor notices the silence.
      const dead = kickSilent() && !carrying(g, "factory", "kick");
      if (!dead) silentSince = null;
      else if (silentSince === null) silentSince = now;
      else if (!alarming && !looped(g, "thread:factory:kick", "hushing") && now - silentSince > g.conductor.barSeconds() * 0.95) void alarm(false);
    },
    bar() {
      if (g.flag("gate_passed") || alarming) return;
      // Looped, the silence lasts: the alarm comes after two bars and the foreman clears the spool.
      if (kickSilent() && !carrying(g, "factory", "kick") && looped(g, "thread:factory:kick", "hushing")) {
        if (++deadBars >= 2) void alarm(true);
      } else deadBars = 0;
    },
    async exit(id) {
      if (id !== "gate" || g.flag("gate_passed")) return true;
      const open = Tone.now() - lastKick > g.conductor.barSeconds() * 0.9 && kickSilent();
      if (open && carrying(g, "factory", "kick") && looped(g, "thread:factory:kick", "hushing")) {
        await g.cutscene(async () => {
          await g.say("bobbin", "gate3.through");
          g.setFlag("gate_passed");
          await g.say("juno", "gate3.wedge");
        });
        return true;
      }
      const copy = carrying(g, "factory", "kick");
      await g.say("bobbin", !open ? "gate3.bounced" : copy ? "gate3.not_long" : "gate3.open_but_alarm");
      return false;
    },
  };
};

/** A2-10, puzzle 3: "The Unplugged Encore". */
const show: LogicFactory = (g) => {
  let micBars = 0;
  const m = () => g.model("arena");
  const slotThread = (stem: string) => {
    const slot = m().replacedBy(stem);
    const s = slot === null ? null : g.spindle.spool(slot);
    return s?.kind === "thread" ? s.thread : null;
  };
  return {
    enter() {
      if (!g.flag("show_started")) {
        g.setFlag("show_started");
        const mods = m().mods;
        if (!mods.untied.includes("live")) mods.untied.push("live");
        void g.cutscene(async () => {
          g.caption("caption.vamp");
          await g.say("bobbin", "show.intro1");
          await g.say("bobbin", "show.intro2");
          if (g.spindle.capacity && !carrying(g, "piano_room", "piano") && !carrying(g, "marcus", "groove")) await g.say("skein", "show.need_room");
        });
      }
      g.view?.setSprite("mic", { frame: g.flag("mic_open") ? 1 : 0 });
      if (g.flag("dancers_free")) g.view?.setSprite("dancers", { anim: "dancers_free" });
    },
    cast(e, key) {
      const t = e.target;
      if (t?.kind === "hotspot" && t.id === "mic" && key === "hushing_rev") {
        if (!e.fromLoop) void g.say("bobbin", "show.rouse_bar");
        else once(g, "said_two_lyras", "show.two_lyras");
        return true;
      }
      return false;
    },
    update() {
      if (g.flag("encore")) return;
      const now = Tone.now();
      const click = slotThread("click");
      if (click && !g.flag("dancers_free")) {
        if (click.song === "marcus" && click.stem === "groove") {
          g.setFlag("dancers_free");
          g.view?.setSprite("dancers", { anim: "dancers_free" });
          void g.say("bobbin", "show.dancers_free");
        } else once(g, "said_dancers_confused", "show.dancers_confused");
      }
      const saw = slotThread("supersaw");
      if (saw && !g.flag("lyra_turns")) {
        if (saw.song === "piano_room" && saw.stem === "piano") {
          g.setFlag("lyra_turns");
          void g.say("bobbin", "show.lyra_turns");
        } else if (saw.song === "piano_room") once(g, "said_piano_wrong", "show.piano_wrong");
        else once(g, "said_saw_wrong", "show.saw_wrong");
      }
      const muteSlack = m().tether("prerecorded", now) === "slack";
      g.view?.setSprite("mic", { frame: muteSlack || g.flag("mic_open") ? 1 : 0 });
      if (g.flag("dominic_knot") && !m().isTied("live") && !g.busy) void resolve(g);
    },
    bar() {
      if (g.flag("encore") || g.busy) return;
      const now = Tone.now() + 0.02;
      if (g.flag("dancers_free") && g.flag("lyra_turns") && !g.flag("chant_added")) {
        void g.cutscene(async () => {
          g.setFlag("chant_added");
          await g.say("dominic", "show.chant_added");
          await g.say("bobbin", "show.chant_added2");
        });
        return;
      }
      if (g.flag("chant_added") && !g.flag("chant_covered") && m().state("chant", "hushing", now) && looped(g, "thread:arena:chant", "hushing")) {
        g.setFlag("chant_covered");
        void g.say("bobbin", "show.chant_covered");
      }
      const preSilent = m().state("prerecorded", "hushing", now);
      if (preSilent && looped(g, "thread:arena:prerecorded", "hushing")) micBars++;
      else {
        if (preSilent) once(g, "said_mic_bar", "show.mic_bar");
        micBars = 0;
      }
      if (micBars >= 1 && !g.flag("mic_open")) {
        g.setFlag("mic_open");
        void g.say("bobbin", "show.mic_open");
      }
      if (g.flag("mic_open") && g.flag("chant_covered") && !g.flag("dominic_knot")) {
        void g.cutscene(async () => {
          await g.say("dominic", "show.knot1");
          const mods = m().mods;
          mods.untied = mods.untied.filter((s) => s !== "live");
          g.setFlag("dominic_knot");
          await g.say("bobbin", "show.knot2");
        });
      }
    },
  };
};

async function resolve(g: Game): Promise<void> {
  if (g.flag("encore")) return;
  await g.cutscene(async () => {
    g.setFlag("encore_start");
    g.caption("caption.encore");
    await g.say("bobbin", "show.res1");
    await g.say("bobbin", "show.res2");
    await g.waitBars(2);
    await g.say("bobbin", "show.res3");
    g.setFlag("encore");
    await g.dialogue("dominic_end");
    await g.say("bobbin", "show.res4");
    await g.hud?.episodeEnd();
  });
}

export const scripts: Record<string, ScriptFn> = {
  async mute_pedal(g) {
    if (!g.flag("juno_ally")) return void (await g.say("bobbin", "factory.mute_before"));
    if (g.library.learned.has("hushing")) return void (await g.say("bobbin", "look.factory_night.mute_pedal"));
    await g.cutscene(async () => {
      await g.say("juno", "factory.mute1");
      await g.teach("pedal", "hushing");
      await g.say("juno", "factory.mute2");
    });
  },

  async beat_press(g) {
    if (g.library.learned.has("quickening")) return void (await g.say("bobbin", "look.press_floor.beat_press"));
    await g.cutscene(async () => {
      await g.say("bobbin", "press.listen1");
      await g.teach("press", "quickening");
      await g.say("bobbin", "press.listen2");
    });
  },

  async conveyor_quick(g, _arg, quiet) {
    if (quiet || g.flag("rode_conveyor")) return;
    const isLooping = looped(g, "hotspot:conveyor", "quickening");
    await g.say("bobbin", isLooping ? "press.conveyor_looping" : "press.conveyor_lurch");
  },

  async tune_piano(g) {
    await g.cutscene(async () => {
      g.setFlag("piano_tuned");
      g.view?.refreshHotspots();
      g.caption("caption.piano_tuned");
      await g.say("bobbin", "basement.tuned1");
      await g.say("bobbin", "basement.tuned2");
    });
  },
};

export const logic: Record<string, LogicFactory> = { juno, press, panel, gate, show };
