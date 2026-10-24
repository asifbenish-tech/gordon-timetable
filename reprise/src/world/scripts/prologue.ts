// src/world/scripts/prologue.ts: the Crossing, the landing, and the park (P1-P6).
import type { Game, LogicFactory, ScriptFn } from "../game";

async function callDraft(g: Game, draft: "opening" | "healing"): Promise<void> {
  g.view?.setSprite("lead_swan", { anim: "lead_swan" });
  await g.say("lead_swan", draft === "opening" ? "crossing.call_landing" : "crossing.call_resting");
  await g.teach("swan", draft);
}

async function crossingIntro(g: Game): Promise<void> {
  await g.cutscene(async () => {
    g.caption("caption.crossing");
    await g.say("bobbin", "crossing.intro1");
    await g.say("bobbin", "crossing.intro2");
    await callDraft(g, "opening");
    g.setFlag("await_opening");
    await g.say("bobbin", "crossing.echo_prompt");
  });
}

async function echoed(g: Game, draft: "opening" | "healing"): Promise<void> {
  await g.cutscene(async () => {
    if (draft === "opening") {
      g.setFlag("await_opening", false);
      g.view?.flash(0x8f7cff, 300);
      g.view?.setSprite("flock", { anim: "flock_flight" });
      await g.say("bobbin", "crossing.formation");
      await callDraft(g, "healing");
      g.setFlag("await_healing");
      await g.say("bobbin", "crossing.echo_rest");
    } else {
      g.setFlag("await_healing", false);
      g.view?.flash(0xffffff, 500);
      await g.say("bobbin", "crossing.landing");
      g.setFlag("p1_echoed");
      await g.waitSeconds(0.6);
      g.enterRoom("pond", "start");
    }
  });
}

const crossing: LogicFactory = (g) => {
  let off: (() => void) | null = null;
  let recalling = false;
  return {
    enter() {
      off = g.bus.on("phraseFailed", () => {
        if (recalling || g.busy) return;
        const which = g.flag("await_opening") ? "opening" : g.flag("await_healing") ? "healing" : null;
        if (!which) return;
        recalling = true;
        void g.cutscene(async () => {
          await g.say("bobbin", "crossing.wrong");
          await callDraft(g, which);
        }).finally(() => (recalling = false));
      });
      if (!g.flag("p1_echoed") && !g.flag("await_opening") && !g.flag("await_healing")) void crossingIntro(g);
      else if (g.flag("p1_echoed")) g.enterRoom("pond", "start");
    },
    leave() {
      off?.();
    },
    cast(e, key) {
      if (e.fromLoop) return false;
      if (g.flag("await_opening") && key === "opening") {
        void echoed(g, "opening");
        return true;
      }
      if (g.flag("await_healing") && key === "healing") {
        void echoed(g, "healing");
        return true;
      }
      if (g.flag("await_opening") || g.flag("await_healing")) {
        void g.say("bobbin", "crossing.not_that");
        return true;
      }
      return false;
    },
  };
};

const parkGate: LogicFactory = (g) => ({
  enter() {
    g.view?.setSprite("gate", { frame: g.flag("gate_open") ? 1 : 0 });
  },
});

export const scripts: Record<string, ScriptFn> = {
  async flock_call(g) {
    if (g.busy) return;
    if (g.flag("await_opening")) await g.cutscene(() => callDraft(g, "opening"));
    else if (g.flag("await_healing")) await g.cutscene(() => callDraft(g, "healing"));
    else await g.say("bobbin", "look.crossing.lead_swan");
  },

  async pond_enter(g) {
    if (g.flag("landed")) return;
    await g.cutscene(async () => {
      g.setFlag("landed");
      g.caption("caption.park");
      await g.say("bobbin", "pond.land1");
      await g.say("bobbin", "pond.land2");
      g.setFlag("jogger_here");
      g.playSong("again_again");
      g.caption("caption.again_again_phone");
      const move = g.view?.moveSprite("jogger", 700, 280, 7) ?? Promise.resolve();
      await g.say("jogger", "pond.jogger");
      await g.say("bobbin", "pond.jogger2");
      g.setFlag("flock_grey");
      g.refreshLook();
      g.view?.flash(0x606070, 400);
      await g.say("bobbin", "pond.grey");
      await move;
      g.setFlag("jogger_here", false);
      g.playSong("park");
      await g.say("bobbin", "pond.skein_fading");
      await g.say("bobbin", "pond.skein_prompt");
    });
  },

  async heal_skein(g) {
    await g.cutscene(async () => {
      g.view?.flash(0xc8bbff, 400);
      await g.say("bobbin", "pond.skein_up");
      await g.say("skein", "pond.skein_honk");
      await g.say("bobbin", "pond.skein_follow");
      g.setFlag("skein");
      g.setFlag("skein_healed");
      await g.say("bobbin", "pond.weave1");
      await g.say("bobbin", "pond.weave2");
      g.view?.flash(0xffffff, 900);
      g.setFlag("human");
      g.view?.setSwan(false);
      g.view?.refreshHotspots();
      await g.waitSeconds(0.5);
      g.crackDistaff();
      g.caption("caption.crack");
      await g.say("bobbin", "pond.crack1");
      await g.say("bobbin", "pond.crack2");
      await g.say("skein", "pond.skein_hint_intro");
    });
  },

  async open_gate(g) {
    if (g.flag("gate_open")) return void (await g.say("bobbin", "gate.already"));
    await g.cutscene(async () => {
      g.view?.setSprite("gate", { frame: 1 });
      g.setFlag("gate_open");
      await g.say("bobbin", "gate.opened");
      await g.say("bobbin", "gate.opened2");
    });
  },

  async listen_marcus(g) {
    if (g.library.learned.has("waking")) return void (await g.dialogue("marcus"));
    await g.cutscene(async () => {
      await g.say("bobbin", "street.marcus1");
      await g.say("marcus", "street.marcus_roll");
      await g.teach("bucket", "waking");
      g.caption("caption.flock_brightens");
      await g.say("bobbin", "street.marcus2");
      await g.say("bobbin", "street.marcus3");
    });
  },

  async wake_commuter(g) {
    await g.cutscene(async () => {
      g.view?.setSprite("commuter", { frame: 1 });
      await g.dialogue("commuter");
      g.setFlag("commuter_woken");
      g.view?.refreshHotspots();
      await g.say("bobbin", "street.goal1");
      await g.say("bobbin", "street.goal2");
    });
  },
};

export const logic: Record<string, LogicFactory> = { crossing, park_gate: parkGate };
