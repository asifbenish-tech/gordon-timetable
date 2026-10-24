import { execFileSync } from "node:child_process";
import { readdirSync, readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import type { RoomDef } from "../../src/content/types";
import { check, validCondition } from "../../src/world/flags";
import { clampInside, findPath, inside, type Pt } from "../../src/world/walker";

describe("conditions", () => {
  const s = { flags: { a: true }, learned: ["tuning"], solved: ["P1"], ownedNotes: 4, tools: ["combing"], capacity: 2 };
  it("joins terms with & and negates with !", () => {
    expect(check(s, "flag:a&draft:tuning&puzzle:P1&note:f&tool:combing&spools:2")).toBe(true);
    expect(check(s, "!flag:a")).toBe(false);
    expect(check(s, "note:g")).toBe(false);
    expect(check(s, undefined)).toBe(true);
  });
  it("rejects unknown terms", () => {
    expect(validCondition("flag:x&weird:y")).toBe(false);
  });
});

describe("walking (GDD 9.7)", () => {
  const rooms = readdirSync(new URL("../../content/rooms/", import.meta.url)).map(
    (f) => JSON.parse(readFileSync(new URL(`../../content/rooms/${f}`, import.meta.url), "utf8")) as RoomDef,
  );
  it("every entry and hotspot stand point can be reached inside the walkable polygon", () => {
    for (const r of rooms) {
      if (r.swan && r.id === "crossing") continue;
      const poly = r.walk as Pt[];
      for (const [name, p] of Object.entries(r.entries)) {
        const start = clampInside(poly, p as Pt);
        for (const h of r.hotspots) {
          const goal: Pt = h.stand ?? [h.rect[0] + h.rect[2] / 2, h.rect[1] + h.rect[3] + 6];
          const path = findPath(poly, start, goal);
          const end = path[path.length - 1];
          expect(inside(poly, end), `${r.id}: ${name} -> ${h.id}`).toBe(true);
        }
      }
    }
  });
});

describe("content", () => {
  it("passes schema and reference validation (tools/validate-content.ts)", () => {
    const out = execFileSync("npx", ["tsx", "tools/validate-content.ts"], { cwd: new URL("../../", import.meta.url), encoding: "utf8" });
    expect(out).toMatch(/content ok/);
  });
});
