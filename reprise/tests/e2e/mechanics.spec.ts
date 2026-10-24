// Wrong moves teach and never dead-end; saves restore; the Spindle keeps time (GDD 6, 9.8).
import { expect, test } from "@playwright/test";
import { RELEASE_1, boot, solve, state, step, watchErrors } from "./helpers";

const upTo = (id: string) => RELEASE_1.slice(0, RELEASE_1.indexOf(id));

test("an offline bar with two spools lands every note within 1 ms", async ({ page }) => {
  await page.goto("/");
  await page.waitForFunction(() => (window as any).__reprise);
  const r = await page.evaluate(() => (window as any).__reprise.timingTest());
  expect(r.notes).toBe(8);
  expect(r.detail.every((d: number[]) => Number.isFinite(d[2]))).toBe(true);
  expect(r.maxErrorMs).toBeLessThan(1);
});

test("a save restores the room, drafts and notes after a reload", async ({ page }) => {
  await boot(page, 4242);
  await solve(page, upTo("A1-1"));
  const before = await state(page);
  await page.evaluate(() => (window as any).__reprise.g.persist(true));
  await page.reload();
  await page.waitForFunction(() => (window as any).__reprise);
  await page.evaluate(() => (window as any).__reprise.resume({ fast: true, tempo: 4 }));
  const after = await state(page);
  expect(after.room).toBe(before.room);
  expect(after.learned.sort()).toEqual(before.learned.sort());
  expect(after.notes).toBe(3);
  await solve(page, ["A1-1"]);
});

test("puzzle 1: pulling everything is a joke, and an unknown draft does nothing", async ({ page }) => {
  const errors = watchErrors(page);
  await boot(page, 99);
  await solve(page, upTo("A1-5"));
  await step(page, "walk:rehearsal_hall");
  // Unmasking isn't learned yet: the phrase fails, nothing is cast
  const ph = await page.evaluate(() => (window as any).__reprise.phrase("unmasking"));
  await page.evaluate((p: number[]) => { const g = (window as any).__reprise.g; g.select({ kind: "hotspot", id: "lyrix" }); for (const n of p) g.playNote(n); }, ph);
  expect((await state(page)).flags.lyra_unmasked).toBeFalsy();
  for (const s of ["comb:hook_engine", "pull:kick", "pull:bass", "pull:supersaw", "pull:vocal", "pull:riser"]) await step(page, s);
  await step(page, "flag:said_miming");
  await step(page, "close");
  await solve(page, ["A1-5"]);
  expect(errors).toEqual([]);
});

test("the conveyor needs a loop, and the Sidechain Gate punishes the wrong order without a dead end", async ({ page }) => {
  await boot(page, 2024);
  await solve(page, upTo("A2-3"));
  // one Quickening: the conveyor slows halfway
  await step(page, "walk:press_floor");
  await step(page, "cast:quickening>hotspot:conveyor");
  await step(page, "exit:conveyor_up");
  expect((await state(page)).room).toBe("press_floor");
  await solve(page, ["A2-3", "A2-4", "A2-5"]);
  // Hushing looped on the kick before covering it: the alarm sounds and the foreman clears the spool
  for (const s of ["walk:floor3", "clear:1", "clear:2", "comb:speakers", "spool:2", "arm", "cast:hushing>thread:kick", "close"]) await step(page, s);
  await step(page, "flag:said_two_kicks").catch(() => {});
  await page.waitForFunction(() => (window as any).__reprise.g.spindle.spool(1) === null, null, { timeout: 60_000 });
  expect((await state(page)).flags.gate_passed).toBeFalsy();
  // the right order still works afterwards
  await solve(page, ["A2-6"]);
  expect((await state(page)).room).toBe("dominic_studio");
});
