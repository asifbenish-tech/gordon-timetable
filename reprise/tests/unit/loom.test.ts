import { describe, expect, it } from "vitest";
import song from "../../content/songs/again_again.json";
import juno from "../../content/songs/juno.json";
import type { SongDef } from "../../src/content/types";
import { Effects } from "../../src/core/effects";
import { LoomModel, checkWeave, goldenLevel } from "../../src/core/loom";

const model = (def: SongDef) => new LoomModel(def, new Effects(), { untied: [], replaced: {} }, () => true);

describe("the golden thread (GDD 6, puzzle 1)", () => {
  it("starts buried and rises as masking threads are pulled or untied", () => {
    const m = model(song as SongDef);
    expect(m.goldenLevel(0)).toBeCloseTo(0);
    m.pulled.add("kick");
    m.pulled.add("bass");
    expect(m.goldenLevel(0)).toBeCloseTo(0.75 - 0.5); // supersaw and vocal still mask it
    m.pulled.add("supersaw");
    expect(m.goldenLevel(0)).toBeCloseTo(0.65);
    m.untie("vocal");
    expect(m.goldenLevel(0)).toBeCloseTo(1);
  });
  it("is braided into the knotted vocal: pulling the vocal pulls it too, until Tuning splits them", () => {
    const m = model(song as SongDef);
    for (const id of ["kick", "bass", "supersaw", "vocal", "riser"]) m.pulled.add(id);
    expect(m.goldenLevel(0)).toBe(0);
    m.untie("vocal");
    expect(m.goldenLevel(0)).toBeCloseTo(1);
  });
  it("pulls only last while the Loom View is open; knots stay untied", () => {
    const m = model(song as SongDef);
    m.pulled.add("supersaw");
    m.untie("vocal");
    m.closeView();
    expect(m.pulled.size).toBe(0);
    expect(m.isTied("vocal")).toBe(false);
  });
  it("Juno's riff is fully revealed by pulling the hook and the bass", () => {
    const m = model(juno as SongDef);
    m.pulled.add("hook");
    m.pulled.add("bass");
    expect(m.goldenLevel(0)).toBeCloseTo(1);
  });
  it("matches GDD 9.6's formula", () => {
    const def = song as SongDef;
    expect(goldenLevel(def, () => true, () => false)).toBeCloseTo(0);
    expect(goldenLevel(def, (id) => id === "riser", () => false)).toBeCloseTo(1);
  });
});

describe("states and tethers", () => {
  it("a one-bar Hushing slackens a tether, then lets go", () => {
    const fx = new Effects();
    const m = new LoomModel(song as SongDef, fx, { untied: [], replaced: {} }, () => true);
    fx.apply(m.key("kick"), "hushing", 10, 2);
    expect(m.tether("kick", 11)).toBe("slack");
    expect(m.audible("kick", 11)).toBe(false);
    expect(m.tether("kick", 12.5)).toBe("taut");
  });
  it("a dropped spool replaces a thread and takes its tether", () => {
    const m = new LoomModel(song as SongDef, new Effects(), { untied: [], replaced: { kick: 1 } }, () => true);
    expect(m.tether("kick", 0)).toBe("replaced");
    expect(m.silenced("kick", 0)).toBe(true);
  });
});

describe("weave recipes (GDD 4.5)", () => {
  it("checks roles, never timing", () => {
    expect(checkWeave(["melody", "melody"], [{ role: "melody" }, { role: "melody" }]).ok).toBe(true);
    expect(checkWeave(["melody", "rhythm"], [{ role: "melody" }, { role: "harmony" }])).toMatchObject({ ok: false, missing: ["rhythm"] });
    expect(checkWeave(["melody"], [{ role: "melody" }, { role: "rhythm" }, { role: "harmony" }, { role: "melody" }]).ok).toBe(false);
  });
});
