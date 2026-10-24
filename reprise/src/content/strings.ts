// src/content/strings.ts: every player-facing string comes from content/strings/en.json,
// every franchise name from content/names.json (GDD 0, 1).
import en from "../../content/strings/en.json";
import names from "../../content/names.json";

type NameSet = Record<string, string>;
const SETS = names.sets as Record<string, NameSet>;

declare const __NAMES__: string;
let current: string = typeof __NAMES__ !== "undefined" && __NAMES__ in SETS ? __NAMES__ : names.default;
let table: Record<string, string> = en as Record<string, string>;

export function nameSet(): string {
  return current;
}

/** Development builds only (Settings): switch the franchise names live. */
export function setNameSet(id: string): void {
  if (id in SETS) current = id;
}

export function setStrings(t: Record<string, string>): void {
  table = t;
}

export function has(key: string): boolean {
  return key in table;
}

/** `{bobbin}` and friends come from the name set; other `{x}` from vars. */
export function fill(text: string, vars: Record<string, string | number> = {}): string {
  return text.replace(/\{(\w+)\}/g, (m, k: string) => {
    if (k in vars) return String(vars[k]);
    const n = SETS[current][k];
    return n ?? m;
  });
}

export function t(key: string, vars: Record<string, string | number> = {}): string {
  const raw = table[key];
  if (raw === undefined) {
    if (import.meta.env?.DEV) console.warn(`missing string ${key}`);
    return key;
  }
  return fill(raw, vars);
}

export function textDir(): "ltr" | "rtl" {
  return table["meta.dir"] === "rtl" ? "rtl" : "ltr";
}
