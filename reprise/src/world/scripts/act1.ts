// src/world/scripts/act1.ts: the Guild of Pop Stars, "Who is singing?" (A1-1 to A1-7).
import * as Tone from "tone";
import type { Game, LogicFactory, ScriptFn } from "../game";

/** Says a line once per save. */
function once(g: Game, flag: string, key: string, speaker = "bobbin"): void {
  if (g.flag(flag)) return;
  g.setFlag(flag);
  void g.say(speaker, key);
}

/** A1-3: isolating the coach's voice lifts her scale out of the piano. */
const fitting: LogicFactory = (g) => ({
  cast(e) {
    if (e.id !== "_isolate" || e.target?.kind !== "thread" || e.target.stem !== "voice") return false;
    if (!g.library.learned.has("tuning")) {
      void g.cutscene(async () => {
        await g.say("bobbin", "fitting.isolated");
        await g.teach("coach", "tuning");
        await g.say("coach", "fitting.coach_hears");
      });
    }
    return true;
  },
});

/** A1-4: the dancers hang on the click; pull it and they freeze, then drift off to find a beat. */
const corridor: LogicFactory = (g) => ({
  enter() {
    if (g.flag("dancers_frozen")) g.view?.setSprite("dancers", { frame: 0 });
  },
  update() {
    if (g.flag("dancers_frozen") || g.loom?.song.def.id !== "mirror") return;
    if (g.loom.song.model.tether("click", Tone.now()) === "slack") {
      g.setFlag("dancers_frozen");
      g.view?.setSprite("dancers", { frame: 0 });
      void g.say("bobbin", "corridor.frozen");
    }
  },
  loomClosed() {
    if (!g.flag("dancers_frozen") || g.flag("dancers_gone")) return;
    void g.cutscene(async () => {
      await g.say("bobbin", "corridor.waiting");
      await g.view?.moveSprite("dancers", 760, 268, 2.5);
      g.setFlag("dancers_gone");
      await g.say("bobbin", "corridor.drift");
    });
  },
});

/** A1-5, puzzle 1: "The Hit That Ate a Song". */
const hall: LogicFactory = (g) => {
  let dancersFrozen = false;
  return {
    loomOpened() {
      if (g.loom?.song.def.id === "again_again" && !g.flag("golden_revealed:again_again")) once(g, "said_glint", "hall.glint");
    },
    cast(e) {
      if (e.id === "_isolate" && e.target?.kind === "thread" && e.target.stem === "vocal") {
        if (g.loom?.song.model.isTied("vocal")) void g.say("bobbin", "hall.robotic");
        return true;
      }
      return false;
    },
    update() {
      const lv = g.loom;
      if (lv?.song.def.id !== "again_again") {
        if (dancersFrozen) {
          dancersFrozen = false;
          g.view?.setSprite("dancers", { anim: "dancers" });
        }
        return;
      }
      const m = lv.song.model;
      const now = Tone.now();
      const slack = m.tether("kick", now) !== "taut";
      if (slack !== dancersFrozen) {
        dancersFrozen = slack;
        g.view?.setSprite("dancers", slack ? { frame: 0 } : { anim: "dancers" });
        if (slack) once(g, "said_dancers_stop", "hall.dancers_stop");
      }
      if (g.flag("golden_revealed:again_again") || g.busy) return;
      const level = m.goldenLevel(now);
      const pulled = (id: string) => m.pulled.has(id);
      if (["kick", "bass", "supersaw", "vocal", "riser"].every(pulled)) once(g, "said_miming", "hall.miming");
      else if (pulled("supersaw") && m.isTied("vocal") && level > 0.5) once(g, "said_braided", "hall.braided");
      else if (level > 0.2 && level < 0.6) once(g, "said_closer", "hall.closer");
      if (level >= 0.99) {
        void g.cutscene(async () => {
          g.setFlag("golden_revealed:again_again");
          await g.say("bobbin", "hall.revealed1");
          await g.teach("hum", "unmasking");
          await g.say("bobbin", "hall.revealed2");
        });
      }
    },
  };
};

export const scripts: Record<string, ScriptFn> = {
  async watch_engineer(g) {
    if (g.flag("watched_engineer")) return void (await g.say("bobbin", "mixing.desk_again"));
    await g.cutscene(async () => {
      await g.say("engineer", "mixing.solo1");
      const m = g.model("again_again");
      for (const stem of ["kick", "bass", "supersaw", "vocal"]) {
        m.isolated = stem;
        await g.say("engineer", `mixing.solo_${stem}`);
        await g.waitSeconds(g.conductor.barSeconds() * 0.75);
      }
      m.isolated = null;
      await g.say("bobbin", "mixing.flax1");
      await g.say("bobbin", "mixing.flax2");
      g.giveTool("combing");
      g.setFlag("watched_engineer");
      await g.say("bobbin", "mixing.flax3");
    });
  },

  async detune_engine(g, _arg, quiet) {
    const m = g.model("again_again");
    const now = Tone.now();
    for (const s of m.stems()) g.effects.apply(m.key(s.id), "tuning_rev", now, g.conductor.barSeconds());
    if (quiet) return;
    await g.cutscene(async () => {
      await g.say("choreographer", "hall.detune_shriek");
      await g.say("bobbin", "hall.detune_phones");
    });
  },

  async unmask_lyrix(g) {
    await g.cutscene(async () => {
      g.view?.flash(0x66e0ff, 500);
      await g.say("bobbin", "hall.unmask1");
      g.setFlag("lyra_unmasked");
      g.view?.refreshHotspots();
      await g.dialogue("lyra_unmasked");
      g.playSong("lyra");
      g.caption("caption.lyra_hum");
      await g.waitBars(4);
      g.playSong("again_again");
      await g.dialogue("lyra_after");
    });
  },

  async mask_self(g) {
    if (g.flag("masked")) return void (await g.say("bobbin", "elevator.already_masked"));
    await g.cutscene(async () => {
      g.view?.flash(0x9a8cc8, 400);
      await g.say("bobbin", "elevator.masked1");
      g.view?.setSprite("scanner", { frame: 1 });
      g.setFlag("masked");
      await g.say("bobbin", "elevator.scanner_ok");
      await g.say("lyra", "elevator.lyra_bye");
    });
  },
};

export const logic: Record<string, LogicFactory> = { fitting, corridor, hall };
