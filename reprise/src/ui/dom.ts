// src/ui/dom.ts: a tiny element builder. Text is never pixel art (GDD 7.9).
type Attrs = Record<string, string | number | boolean | ((e: Event) => void) | undefined>;
type Child = Node | string | null | undefined | false;

export function h<K extends keyof HTMLElementTagNameMap>(tag: K, attrs: Attrs = {}, ...children: Child[]): HTMLElementTagNameMap[K] {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === undefined || v === false) continue;
    if (k.startsWith("on") && typeof v === "function") el.addEventListener(k.slice(2), v as EventListener);
    else if (k === "class") el.className = String(v);
    else if (v === true) el.setAttribute(k, "");
    else el.setAttribute(k, String(v));
  }
  for (const c of children) if (c !== null && c !== undefined && c !== false) el.append(c);
  return el;
}

/** append() that skips null, false and undefined, like h() does. */
export function append(el: Element, ...children: Child[]): void {
  for (const c of children) if (c !== null && c !== undefined && c !== false) el.append(c);
}

export function clear(el: Element): void {
  while (el.firstChild) el.firstChild.remove();
}

export const NOTE_COLORS = ["#e05a4f", "#f08c3a", "#efc94c", "#6cc070", "#4fb3c8", "#5b7be0", "#9a6ad6", "#ece8f6"];
export const NOTE_GLYPHS = ["●", "▲", "■", "◆", "★", "▼", "✚", "◎"];
export const NOTE_LETTERS = ["c", "d", "e", "f", "g", "a", "b", "C′"];
