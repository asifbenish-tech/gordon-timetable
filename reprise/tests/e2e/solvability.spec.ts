// The solvability bot (GDD 9.8): from a fresh save, every puzzle's bot script for 50 seeds.
import { expect, test } from "@playwright/test";
import { RELEASE_1, boot, solve, state, watchErrors } from "./helpers";

const SEEDS = Number(process.env.BOT_SEEDS ?? 50);
const DIFFS = ["practice", "standard", "expert"];

for (let i = 0; i < SEEDS; i++) {
  const seed = (i + 1) * 7919;
  test(`Release 1 is solvable, seed ${seed}`, async ({ page }) => {
    const errors = watchErrors(page);
    await boot(page, seed, DIFFS[i % 3]);
    await solve(page, RELEASE_1, errors);
    const s = await state(page);
    expect(s.solved).toEqual(expect.arrayContaining(RELEASE_1));
    expect(s.notes).toBe(5); // c d e, then f and g returned
    expect(errors).toEqual([]);
  });
}
