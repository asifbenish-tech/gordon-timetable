// src/ui/distaff-bar.ts: carved wood along the bottom, eight note positions as small spools
// that glow in the note's colour and show its glyph (GDD 4.1, 7.6). The Spindle rings its head.
import * as Tone from "tone";
import type { NoteIndex, Phrase } from "../content/types";
import { t } from "../content/strings";
import type { Game } from "../world/game";
import { NOTE_COLORS, NOTE_GLYPHS, NOTE_LETTERS, clear, h } from "./dom";

export class DistaffBar {
  readonly el: HTMLElement;
  private notes: HTMLButtonElement[] = [];
  private spools: HTMLButtonElement[] = [];
  private head: HTMLButtonElement;
  private combBtn: HTMLButtonElement;
  private closeup: HTMLElement;
  private contour: SVGSVGElement;
  private played: NoteIndex[] = [];
  private ring: HTMLElement;
  onBook: () => void = () => {};
  onMenu: () => void = () => {};
  onHint: () => void = () => {};

  constructor(private g: Game) {
    this.head = h("button", { class: "spindle-head", "aria-label": t("ui.spindle.arm"), onclick: () => this.toggleArm() }, "●");
    this.ring = h("div", { class: "spindle", role: "group", "aria-label": t("ui.spindle") }, this.head);
    for (let i = 0; i < 4; i++) {
      const b = h("button", {
        class: `spool spool-${i}`,
        onclick: () => this.g.spindle.select(i),
        oncontextmenu: (e: Event) => {
          e.preventDefault();
          this.g.spindle.clear(i);
        },
      });
      this.spools.push(b);
      this.ring.append(b);
    }
    this.combBtn = h("button", { class: "comb", "aria-label": t("ui.comb"), title: t("ui.comb"), onclick: () => this.comb() }, h("span", { class: "comb-teeth" }));
    const noteRow = h("div", { class: "notes", role: "group", "aria-label": t("ui.distaff") });
    for (let i = 0; i < 8; i++) {
      const b = h("button", {
        class: "note",
        style: `--nc:${NOTE_COLORS[i]}`,
        onpointerdown: (e: Event) => {
          e.preventDefault();
          this.g.playNote(i as NoteIndex);
        },
        onkeydown: (e: Event) => {
          const k = (e as KeyboardEvent).key;
          if (k === "Enter" || k === " ") {
            e.preventDefault();
            this.g.playNote(i as NoteIndex);
          }
        },
      });
      this.notes.push(b);
      noteRow.append(b);
    }
    this.contour = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    this.contour.setAttribute("class", "contour");
    this.contour.setAttribute("viewBox", "0 0 320 40");
    this.contour.setAttribute("aria-hidden", "true");
    noteRow.append(this.contour);
    this.closeup = h("div", { class: "closeup", "aria-live": "polite" });
    const book = h("button", { class: "icon-btn book-btn", "aria-label": t("ui.book"), title: t("ui.book"), onclick: () => this.onBook() }, "❦");
    const menu = h("button", { class: "icon-btn menu-btn", "aria-label": t("ui.menu"), title: t("ui.menu"), onclick: () => this.onMenu() }, "≡");
    this.el = h("div", { id: "distaff" }, this.ring, this.combBtn, noteRow, this.closeup, book, menu);

    g.bus.on("note", ({ n, cracked, index }) => {
      this.pulse(n, cracked);
      if (!cracked) {
        if (index === 0) this.played = [];
        this.played.push(n);
        this.drawContour(this.played, false);
      }
    });
    g.bus.on("noteCleared", () => this.fadeContour());
    g.bus.on("cast", (e) => {
      if (!e.fromLoop) this.fadeContour(true);
    });
    g.bus.on("phraseFailed", () => this.fadeContour(false));
  }

  private toggleArm(): void {
    const s = this.g.spindle;
    if (!s || s.capacity === 0) return;
    s.setArmed(!s.armed);
  }

  private comb(): void {
    if (this.g.loom) this.g.closeLoom();
    else this.g.comb();
  }

  pulse(n: NoteIndex, cracked: boolean): void {
    const b = this.notes[n];
    b.classList.remove("lit", "dead");
    void b.offsetWidth;
    b.classList.add(cracked ? "dead" : "lit");
  }

  /** A heard draft: notes glow as they sound, with or without labels by difficulty (GDD 4.1). */
  showPhrase(phrase: Phrase, times: number[]): void {
    const expert = this.g.save.difficulty === "expert";
    const shown: NoteIndex[] = [];
    phrase.forEach((n, i) => {
      Tone.getDraw().schedule(() => {
        shown.push(n);
        if (!expert) this.pulse(n, false);
        this.drawContour(shown, expert);
        if (i === 3) this.fadeContour(true);
      }, times[i]);
    });
  }

  private drawContour(ns: NoteIndex[], contourOnly: boolean): void {
    const svg = this.contour;
    while (svg.firstChild) svg.firstChild.remove();
    const xs = ns.map((n, i) => (contourOnly ? 40 + i * 80 : 20 + n * 40));
    const ys = ns.map((n) => 34 - n * 4);
    if (ns.length > 1) {
      const pl = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
      pl.setAttribute("points", xs.map((x, i) => `${x},${ys[i]}`).join(" "));
      pl.setAttribute("class", "contour-line");
      svg.append(pl);
    }
    ns.forEach((n, i) => {
      const c = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      c.setAttribute("cx", String(xs[i]));
      c.setAttribute("cy", String(ys[i]));
      c.setAttribute("r", "3");
      c.setAttribute("fill", contourOnly ? "#d8cff0" : NOTE_COLORS[n]);
      svg.append(c);
    });
    svg.classList.remove("fade", "ok", "bad");
  }

  private fadeContour(ok?: boolean): void {
    this.contour.classList.remove("ok", "bad");
    if (ok !== undefined) this.contour.classList.add(ok ? "ok" : "bad");
    this.contour.classList.add("fade");
  }

  setCloseup(label: string | null, sprite: { url: string; w: number; h: number; frameW: number } | null): void {
    clear(this.closeup);
    if (!label) return;
    const icon = h("div", { class: "closeup-icon" });
    if (sprite) {
      icon.style.backgroundImage = `url(${sprite.url})`;
      const scale = Math.min(1, 40 / Math.max(sprite.frameW, sprite.h));
      icon.style.backgroundSize = `${sprite.w * scale}px ${sprite.h * scale}px`;
      icon.style.width = `${sprite.frameW * scale}px`;
      icon.style.height = `${sprite.h * scale}px`;
    } else icon.textContent = label.slice(0, 1).toUpperCase();
    this.closeup.append(icon, h("span", { class: "closeup-label" }, label));
  }

  refresh(): void {
    const g = this.g;
    if (!g.save) return;
    const owned = g.library.ownedNotes;
    const diff = g.save.difficulty;
    this.notes.forEach((b, i) => {
      const cracked = i >= owned;
      b.classList.toggle("cracked", cracked);
      b.setAttribute("aria-label", cracked ? t("ui.note.cracked", { note: NOTE_LETTERS[i] }) : t("ui.note", { note: NOTE_LETTERS[i], n: i + 1 }));
      clear(b);
      b.append(h("span", { class: "spoolshape" }));
      if (diff !== "expert") b.append(h("span", { class: "glyph" }, NOTE_GLYPHS[i]));
      if (diff !== "expert") b.append(h("span", { class: "letter" }, NOTE_LETTERS[i]));
    });
    const s = g.spindle;
    const hasSpindle = s.capacity > 0;
    this.ring.classList.toggle("hidden", !hasSpindle);
    this.head.classList.toggle("armed", s.armed);
    this.head.setAttribute("aria-pressed", String(s.armed));
    this.spools.forEach((b, i) => {
      const sp = s.spool(i);
      b.disabled = i >= s.capacity;
      b.classList.toggle("selected", i === s.selected);
      b.classList.toggle("locked", i >= s.capacity);
      clear(b);
      let label = t("ui.spool.empty", { n: i + 1 });
      if (sp?.kind === "draft") {
        const name = t(`draft.${sp.reversed ? `${sp.id}_rev` : sp.id}`);
        b.append(h("span", { class: "spool-draft" }, name.slice(0, 1)));
        label = t("ui.spool.draft", { n: i + 1, draft: name });
      } else if (sp?.kind === "thread") {
        const stem = g.model(sp.thread.song).def.stems.find((x) => x.id === sp.thread.stem);
        b.append(h("span", { class: "spool-thread", style: `background:${stem?.color ?? "#ccc"}` }));
        label = t("ui.spool.thread", { n: i + 1, thread: stem ? t(stem.label) : "?" });
      }
      b.setAttribute("aria-label", label);
      b.title = label;
    });
    const canComb = g.save.tools.includes("combing");
    this.combBtn.classList.toggle("hidden", !canComb);
    this.combBtn.classList.toggle("open", !!g.loom);
  }

  /** The ring sweeps once per bar. */
  tick(): void {
    if (!this.g.mixer || this.ring.classList.contains("hidden")) return;
    const b = this.g.conductor.beatsAt(Tone.now());
    this.ring.style.setProperty("--sweep", `${((b % 4) / 4) * 360}deg`);
  }
}
