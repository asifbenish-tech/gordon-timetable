import type { Page } from "@playwright/test";

export const RELEASE_1 = ["P1", "P2", "P3", "P4", "P5", "P6", "A1-1", "A1-2", "A1-3", "A1-4", "A1-5", "A1-6", "A1-7",
  "A2-1", "A2-2", "A2-3", "A2-4", "A2-5", "A2-6", "A2-7", "A2-8", "A2-9", "A2-10"];

/** Console errors and uncaught exceptions: the definition of done allows none. */
export function watchErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(`pageerror: ${e.message}\n${e.stack ?? ""}`));
  let loads = 0;
  page.on("framenavigated", (f) => {
    if (f === page.mainFrame() && loads++ > 0) errors.push(`navigated again: ${f.url()}`);
  });
  page.on("crash", () => errors.push("crash"));
  page.on("console", (m) => {
    if (m.type() === "error") errors.push(`console: ${m.text()}`);
  });
  return errors;
}

export async function boot(page: Page, seed: number, difficulty = "standard", tempo = 4): Promise<void> {
  await page.goto("/");
  await page.waitForFunction(() => (window as unknown as { __reprise?: unknown }).__reprise, null, { timeout: 20_000 });
  await page.evaluate(([s, d, t]) => (window as any).__reprise.start(s, d, { fast: true, tempo: t }), [seed, difficulty, tempo] as const);
}

export async function solve(page: Page, ids: string[], errors?: string[]): Promise<void> {
  for (const id of ids) {
    try {
      await page.evaluate((p) => (window as any).__reprise.runPuzzle(p), id);
    } catch (e) {
      throw new Error(`${id}: ${(e as Error).message}\n${(errors ?? []).join("\n")}`);
    }
  }
}

export const step = (page: Page, s: string) => page.evaluate((x) => (window as any).__reprise.step(x), s);
export const state = (page: Page) => page.evaluate(() => (window as any).__reprise.state());
