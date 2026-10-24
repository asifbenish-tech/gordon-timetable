import { describe, expect, it } from "vitest";
import data from "../../content/drafts.json";
import type { DraftDef, Phrase } from "../../src/content/types";
import { DraftLibrary, distance, fits, generateDrafts, reversed, singable } from "../../src/core/drafts";

const defs = data.drafts as DraftDef[];
const pool = data.fallbackPool as Phrase[];

describe("draft generation (GDD 5, 9.6)", () => {
  it("is a pure function of the seed", () => {
    for (const seed of [0, 1, 42, 0xdeadbeef]) expect([...generateDrafts(defs, seed, pool)]).toEqual([...generateDrafts(defs, seed, pool)]);
  });

  it("keeps every rule for 100,000 seeds", () => {
    for (let seed = 0; seed < 100_000; seed++) {
      const m = generateDrafts(defs, seed * 2654435761, pool);
      const playable: Phrase[] = [];
      for (const d of defs) {
        const p = m.get(d.id)!;
        if (!p.every((n) => n <= d.highestNote)) throw new Error(`seed ${seed}: ${d.id} uses a note Bobbin doesn't own yet`);
        if (!singable(p, !!d.sung)) throw new Error(`seed ${seed}: ${d.id} breaks the melodic rules`);
        if (d.reverseId && distance(p, reversed(p)) < 2) throw new Error(`seed ${seed}: ${d.id} is a palindrome`);
        playable.push(p);
        if (d.reverseId) playable.push(reversed(p));
      }
      for (let i = 0; i < playable.length; i++)
        for (let j = i + 1; j < playable.length; j++)
          if (distance(playable[i], playable[j]) < 2) throw new Error(`seed ${seed}: two drafts one note apart`);
    }
  });

  it("only lets every fallback phrase in when it is singable", () => {
    for (const p of pool) expect(singable(p, false)).toBe(true);
  });

  it("rejects a player's motif that collides with a draft (the finale reuses fits())", () => {
    const lib = new DraftLibrary(defs, 99, pool);
    const taken = lib.allTaken();
    expect(fits(taken[0], false, taken)).toBe(false);
  });
});

describe("the melodic rules", () => {
  it("forbids tritones, leaps over a major sixth and fewer than three notes", () => {
    expect(singable([3, 6, 0, 1], false)).toBe(false); // f to b
    expect(singable([0, 7, 0, 1], false)).toBe(false); // an octave
    expect(singable([0, 0, 1, 1], false)).toBe(false);
    expect(singable([0, 1, 2, 0], false)).toBe(true);
  });
  it("sung drafts end on c, e, g or C' with at most one leap over a major third", () => {
    expect(singable([1, 2, 0, 1], true)).toBe(false);
    expect(singable([0, 4, 0, 2], true)).toBe(false);
    expect(singable([1, 2, 1, 0], true)).toBe(true);
  });
});

describe("the library", () => {
  it("matches learned drafts only, forwards and backwards", () => {
    const lib = new DraftLibrary(defs, 5, pool);
    const p = lib.phraseOf("opening");
    expect(lib.match(p)).toBeNull();
    lib.learned.add("opening");
    expect(lib.match(p)).toEqual({ id: "opening", reversed: false });
    expect(lib.match(reversed(p))).toEqual({ id: "opening", reversed: true });
  });
  it("never casts a different draft from one wrong note", () => {
    const lib = new DraftLibrary(defs, 77, pool);
    for (const d of defs) lib.learned.add(d.id);
    for (const d of defs) {
      const p = lib.phraseOf(d.id);
      for (let i = 0; i < 4; i++)
        for (let n = 0; n < 8; n++) {
          if (n === p[i]) continue;
          const q = [...p] as Phrase;
          q[i] = n as Phrase[number];
          const m = lib.match(q);
          expect(m === null || (m.id === d.id && m.reversed)).toBe(true);
        }
    }
  });
});
