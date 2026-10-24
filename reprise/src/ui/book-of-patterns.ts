// src/ui/book-of-patterns.ts: every heard draft, replayable (hold to repeat). Practice writes the notes;
// Standard and Expert leave four blanks the player fills in by ear (GDD 4.1, 4.7).
import * as Tone from "tone";
import type { NoteIndex, Phrase } from "../content/types";
import { drafts } from "../content/load";
import { t } from "../content/strings";
import type { Game } from "../world/game";
import { NOTE_COLORS, NOTE_GLYPHS, NOTE_LETTERS, clear, h } from "./dom";

export class BookOfPatterns {
  readonly el: HTMLElement;
  private list: HTMLElement;
  private repeating = false;

  constructor(private g: Game) {
    this.list = h("div", { class: "book-list" });
    this.el = h(
      "div",
      { id: "book", class: "modal hidden", role: "dialog", "aria-modal": "true", "aria-label": t("ui.book") },
      h("div", { class: "modal-head" }, h("h2", {}, t("ui.book")), h("button", { class: "icon-btn", "aria-label": t("ui.close"), onclick: () => this.close() }, "✕")),
      h("p", { class: "book-help" }),
      this.list,
    );
  }

  open(): void {
    this.render();
    this.el.classList.remove("hidden");
    (this.el.querySelector("button") as HTMLButtonElement | null)?.focus();
  }

  close(): void {
    this.el.classList.add("hidden");
    this.repeating = false;
  }

  get isOpen(): boolean {
    return !this.el.classList.contains("hidden");
  }

  render(): void {
    if (!this.g.save) return;
    const diff = this.g.save.difficulty;
    (this.el.querySelector(".book-help") as HTMLElement).textContent = t(`book.help.${diff}`);
    clear(this.list);
    const learned = drafts.drafts.filter((d) => this.g.library.learned.has(d.id));
    if (!learned.length) this.list.append(h("p", { class: "empty" }, t("book.empty")));
    for (const d of learned) {
      const notes = this.g.bookNotes(d.id);
      const slots = h("div", { class: "book-notes" });
      notes.forEach((n, i) => {
        const filled = n !== null && n !== undefined;
        const b = h(
          "button",
          {
            class: `book-slot${filled ? " filled" : ""}`,
            style: filled ? `--nc:${NOTE_COLORS[n]}` : "",
            disabled: diff === "practice",
            "aria-label": filled ? t("book.slot", { i: i + 1, note: NOTE_LETTERS[n] }) : t("book.slot.empty", { i: i + 1 }),
            onclick: () => this.cycle(d.id, i),
          },
          filled ? (diff === "expert" ? NOTE_LETTERS[n] : `${NOTE_GLYPHS[n]} ${NOTE_LETTERS[n]}`) : "·",
        );
        slots.append(b);
      });
      const hear = h("button", {
        class: "hear",
        onpointerdown: () => this.hear(d.id, true),
        onpointerup: () => (this.repeating = false),
        onpointerleave: () => (this.repeating = false),
        onkeydown: (e: Event) => {
          const k = (e as KeyboardEvent).key;
          if (k === "Enter" || k === " ") this.hear(d.id, false);
        },
      }, t("book.hear"));
      const rev = d.reverseId ? h("span", { class: "rev" }, t("book.reversed", { draft: t(`draft.${d.id}_rev`) })) : null;
      this.list.append(h("div", { class: "book-entry" }, h("div", { class: "book-name" }, h("strong", {}, t(`draft.${d.id}`)), rev, h("small", {}, t(`draft.${d.id}.effect`))), slots, hear));
    }
  }

  /** Standard and Expert: the player writes the notes, cycling through the notes the Distaff owns. */
  private cycle(id: string, i: number): void {
    const book = (this.g.save.book[id] ??= [null, null, null, null]);
    const cur = book[i];
    const owned = this.g.library.ownedNotes;
    book[i] = cur === null || cur === undefined ? 0 : cur + 1 >= owned ? null : cur + 1;
    this.g.persist(true);
    this.render();
  }

  /** Hold to repeat: the draft plays again and again while held. */
  private hear(id: string, hold: boolean): void {
    if (!this.g.mixer) return;
    this.repeating = hold;
    const play = () => {
      const phrase: Phrase = this.g.library.phraseOf(id);
      const beat = Math.max(0.3, this.g.conductor.beatSeconds());
      const start = Tone.now() + 0.05;
      const times = phrase.map((n: NoteIndex, k) => {
        const at = start + k * beat;
        this.g.voice.playAt(n, at, 0.8);
        return at;
      });
      this.g.hud?.teachNotes(phrase, times, id);
      Tone.getContext().setTimeout(() => {
        if (this.repeating) play();
      }, beat * 5);
    };
    play();
  }
}
