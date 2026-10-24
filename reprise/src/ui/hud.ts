// src/ui/hud.ts: the HTML layer over the canvas: speech, dialogue with portraits, captions,
// the Distaff, the Loom View's controls and the menus. Screen readers read it (GDD 4.7, 7.9).
import type * as Phaser from "phaser";
import type { Phrase, SpeakerDef, Target } from "../content/types";
import { manifest, artUrl, speakers } from "../content/load";
import { t, textDir } from "../content/strings";
import type { Game, Hud } from "../world/game";
import type { RoomScene } from "../world/room-scene";
import { threadRows } from "./loom-view";
import { DistaffBar } from "./distaff-bar";
import { BookOfPatterns } from "./book-of-patterns";
import { SettingsPanel } from "./settings";
import { NOTE_COLORS, NOTE_GLYPHS, clear, h } from "./dom";

export class HudImpl implements Hud {
  readonly root: HTMLElement;
  readonly distaff: DistaffBar;
  private speech: HTMLElement;
  private captionEl: HTMLElement;
  private toastEl: HTMLElement;
  private dialog: HTMLElement;
  private hoverEl: HTMLElement;
  private revealEl: HTMLElement;
  private loomPanel: HTMLElement;
  private loomLabels: HTMLElement;
  private loomActions: HTMLElement;
  private live: HTMLElement;
  private wheel: HTMLElement;
  private sayChain: Promise<void> = Promise.resolve();
  private skipSpeech: (() => void) | null = null;
  private loomThread: string | null = null;
  private loomSig = "";
  readonly book: BookOfPatterns;
  readonly settings: SettingsPanel;
  scene: RoomScene | null = null;
  phaser: Phaser.Game | null = null;

  constructor(private g: Game, parent: HTMLElement) {
    this.speech = h("div", { id: "speech", role: "status", onclick: () => this.skipSpeech?.() });
    this.captionEl = h("div", { id: "caption", "aria-hidden": "true" });
    this.toastEl = h("div", { id: "toast", "aria-hidden": "true" });
    this.dialog = h("div", { id: "dialog", class: "hidden" });
    this.hoverEl = h("div", { id: "hover", "aria-hidden": "true" });
    this.revealEl = h("div", { id: "reveal", "aria-hidden": "true" });
    this.loomLabels = h("div", { class: "loom-labels", role: "listbox", "aria-label": t("loom.threads") });
    this.loomActions = h("div", { class: "loom-actions" });
    this.loomPanel = h("div", { id: "loom-panel", class: "hidden" }, this.loomActions, this.loomLabels);
    this.live = h("div", { class: "sr-only", "aria-live": "polite" });
    this.wheel = h("div", { id: "wheel", class: "hidden", "aria-hidden": "true" });
    NOTE_GLYPHS.forEach((gl, i) => {
      const a = (i / 8) * Math.PI * 2 - Math.PI / 2;
      this.wheel.append(h("span", { class: "wheel-note", style: `--nc:${NOTE_COLORS[i]};left:${50 + Math.cos(a) * 38}%;top:${50 + Math.sin(a) * 38}%` }, gl));
    });
    this.distaff = new DistaffBar(g);
    this.book = new BookOfPatterns(g);
    this.settings = new SettingsPanel(g);
    this.distaff.onBook = () => this.book.open();
    this.distaff.onMenu = () => this.settings.open();
    this.settings.onBook = () => this.book.open();
    this.root = h("div", { id: "hud", dir: textDir() }, this.loomPanel, this.revealEl, this.hoverEl, this.speech, this.captionEl, this.toastEl, this.dialog, this.wheel, this.distaff.el, this.book.el, this.settings.el, this.live);
    parent.append(this.root);
    g.hudSelectThread = (id) => this.selectThread(id);
    g.bus.on("learned", () => this.book.render());
  }

  // ---- speech ----------------------------------------------------------------------------------

  say(speaker: string, text: string): Promise<void> {
    const run = async () => {
      const sp = speakers.get(speaker);
      clear(this.speech);
      this.speech.append(h("span", { class: "who", style: `color:${sp?.color ?? "#fff"}` }, sp ? t(sp.name) : speaker), h("span", { class: "line" }, text));
      this.speech.classList.add("show");
      this.announce(`${sp ? t(sp.name) : speaker}: ${text}`);
      await new Promise<void>((res) => {
        const ms = this.g.fast ? 0 : this.g.settings.textSpeed === "click" ? 1e9 : Math.max(1700, 900 + text.length * 55);
        const timer = window.setTimeout(done, ms);
        function done() {
          window.clearTimeout(timer);
          res();
        }
        this.skipSpeech = done;
      });
      this.skipSpeech = null;
      this.speech.classList.remove("show");
    };
    this.sayChain = this.sayChain.then(run, run);
    return this.sayChain;
  }

  skip(): boolean {
    if (this.skipSpeech) {
      this.skipSpeech();
      return true;
    }
    return false;
  }

  dialogue(sp: SpeakerDef, text: string, choices: string[] | null): Promise<number> {
    clear(this.dialog);
    const portrait = manifest.images.find((i) => i.id === sp.portrait);
    const img = portrait ? h("img", { class: "portrait", src: artUrl(portrait.path), alt: "" }) : h("div", { class: "portrait" });
    const body = h("div", { class: "dlg-body" }, h("div", { class: "who", style: `color:${sp.color}` }, t(sp.name)), h("p", { class: "dlg-text" }, text));
    this.dialog.append(img, body);
    this.dialog.classList.remove("hidden");
    this.announce(`${t(sp.name)}: ${text}`);
    return new Promise((res) => {
      const finish = (i: number) => {
        this.dialog.classList.add("hidden");
        this.advance = null;
        res(i);
      };
      if (choices && choices.length) {
        const list = h("div", { class: "choices", role: "menu" });
        choices.forEach((c, i) => list.append(h("button", { class: "choice", role: "menuitem", onclick: () => finish(i) }, c)));
        body.append(list);
        (list.firstChild as HTMLButtonElement | null)?.focus();
        this.advance = this.g.fast ? () => finish(0) : null;
        if (this.g.fast) finish(0);
      } else {
        const next = h("button", { class: "dlg-next", "aria-label": t("ui.continue"), onclick: () => finish(0) }, "▸");
        body.append(next);
        this.dialog.onclick = (e) => {
          if (e.target === this.dialog || (e.target as HTMLElement).classList.contains("dlg-text")) finish(0);
        };
        this.advance = () => finish(0);
        if (this.g.fast) finish(0);
        else next.focus({ preventScroll: true });
      }
    });
  }

  advance: (() => void) | null = null;

  caption(text: string): void {
    this.captionEl.textContent = `♪ ${text}`;
    this.captionEl.classList.remove("show");
    void this.captionEl.offsetWidth;
    this.captionEl.classList.add("show");
    this.announce(text);
  }

  toast(text: string): void {
    this.toastEl.textContent = text;
    this.toastEl.classList.remove("show");
    void this.toastEl.offsetWidth;
    this.toastEl.classList.add("show");
    this.announce(text);
  }

  announce(text: string): void {
    this.live.textContent = text;
  }

  selection(label: string | null, target: Target | null): void {
    let sprite: { url: string; w: number; h: number; frameW: number } | null = null;
    if (target?.kind === "hotspot") {
      const hs = this.g.hotspot(target.id);
      const img = hs?.sprite ? manifest.images.find((i) => i.id === hs.sprite!.image) : null;
      if (img) sprite = { url: artUrl(img.path), w: img.w, h: img.h, frameW: img.frameW ?? img.w / img.frames };
    }
    this.distaff.setCloseup(label, sprite);
    if (this.g.loom) this.renderLoom(true);
  }

  refresh(): void {
    this.distaff.refresh();
    if (this.g.loom) this.renderLoom(true);
  }

  teachNotes(phrase: Phrase, times: number[]): void {
    this.distaff.showPhrase(phrase, times);
  }

  busy(on: boolean): void {
    this.root.classList.toggle("busy", on);
  }

  hover(label: string | null, sx: number, sy: number): void {
    if (!label) {
      this.hoverEl.classList.remove("show");
      return;
    }
    this.hoverEl.textContent = t(label);
    this.hoverEl.style.left = `calc(var(--s) * ${sx}px)`;
    this.hoverEl.style.top = `calc(var(--s) * ${Math.max(6, sy - 18)}px)`;
    this.hoverEl.classList.add("show");
  }

  /** The hotspot-reveal key: every clickable thing names itself. */
  reveal(on: boolean): void {
    clear(this.revealEl);
    if (!on || !this.scene || this.g.loom) return;
    for (const r of this.scene.hotspotScreenRects()) {
      this.revealEl.append(h("div", { class: "reveal-tag", style: `left:calc(var(--s) * ${r.x + r.w / 2}px);top:calc(var(--s) * ${r.y + r.hgt / 2}px)` }, t(r.h.name)));
    }
  }

  wheelState(sector: number | null): void {
    this.wheel.classList.toggle("hidden", sector === null);
    [...this.wheel.children].forEach((c, i) => c.classList.toggle("on", i === sector));
  }

  // ---- the Loom View's controls -------------------------------------------------------------------

  loomOpened(): void {
    this.loomThread = null;
    this.loomPanel.classList.remove("hidden");
    this.root.classList.add("loom-open");
    this.renderLoom(true);
    this.distaff.refresh();
  }

  loomClosed(): void {
    this.loomPanel.classList.add("hidden");
    this.root.classList.remove("loom-open");
    this.loomThread = null;
    this.distaff.refresh();
  }

  selectThread(id: string | null): void {
    this.loomThread = id;
    const song = this.g.loom?.song;
    if (song && id && !id.startsWith("spool:")) this.g.select({ kind: "thread", song: song.def.id, stem: id });
    else this.g.select(null);
    const ls = this.phaser?.scene.isActive("loom") ? this.phaser.scene.getScene("loom") : null;
    if (ls) (ls as unknown as { selected: string | null }).selected = id;
    this.renderLoom(true);
  }

  tick(): void {
    this.distaff.tick();
    if (this.g.loom) this.renderLoom(false);
  }

  private renderLoom(force: boolean): void {
    const lv = this.g.loom;
    if (!lv) return;
    const rows = threadRows(this.g, lv.song);
    const m = lv.song.model;
    const now = this.g.conductor.now();
    const sig = rows.map((r) => `${r.id}:${Math.round(r.y)}:${m.pulled.has(r.id)}:${m.isTied(r.id)}:${m.replacedBy(r.id)}:${m.silenced(r.id, now)}`).join("|") + `|${this.loomThread}|${this.g.spindle.capacity}|${JSON.stringify(this.g.spindle.save().map((s) => s?.kind))}`;
    if (!force && sig === this.loomSig) return;
    this.loomSig = sig;
    clear(this.loomLabels);
    for (const r of rows) {
      const stem = r.stem;
      const tags: string[] = [];
      if (!r.id.startsWith("spool:") && stem) {
        if (stem.sealed) tags.push(t("loom.tag.sealed"));
        if (m.isTied(r.id)) tags.push(t("loom.tag.knot"));
        if (stem.tether) tags.push(t("loom.tag.tether"));
        if (m.pulled.has(r.id)) tags.push(t("loom.tag.pulled"));
        else if (m.silenced(r.id, now)) tags.push(t("loom.tag.silent"));
        if (m.replacedBy(r.id) !== null) tags.push(t("loom.tag.replaced", { n: m.replacedBy(r.id)! + 1 }));
      } else tags.push(t("loom.tag.carried"));
      const name = r.id.startsWith("spool:") ? t("loom.spool_thread", { n: Number(r.id.slice(6)) + 1, thread: stem ? t(stem.label) : "" }) : t(stem!.label);
      const b = h(
        "button",
        {
          class: `thread-label${this.loomThread === r.id ? " selected" : ""}`,
          role: "option",
          "aria-selected": String(this.loomThread === r.id),
          style: `top:calc(var(--s) * ${r.y - 7}px);--tc:${stem?.color ?? "#ccc"}`,
          onclick: () => this.selectThread(r.id),
        },
        h("span", { class: "swatch" }),
        name,
        tags.length ? h("small", {}, ` · ${tags.join(" · ")}`) : null,
      );
      this.loomLabels.append(b);
    }
    clear(this.loomActions);
    const id = this.loomThread;
    const isStem = !!id && !id.startsWith("spool:");
    const pulled = isStem && m.pulled.has(id!);
    const act = (label: string, fn: () => void, enabled: boolean, extra: Record<string, unknown> = {}) =>
      h("button", { class: "loom-btn", disabled: !enabled, onclick: () => { fn(); this.renderLoom(true); }, ...extra } as never, label);
    this.loomActions.append(
      act(pulled ? t("loom.put_back") : t("loom.pull"), () => this.g.pull(id!), isStem),
      h("button", {
        class: "loom-btn",
        disabled: !id,
        onpointerdown: () => id && this.g.isolate(id),
        onpointerup: () => this.g.isolate(null),
        onpointerleave: () => this.g.isolate(null),
        onpointercancel: () => this.g.isolate(null),
        onkeydown: (e: Event) => {
          const k = (e as KeyboardEvent).key;
          if ((k === "Enter" || k === " ") && id) this.g.isolate(id);
        },
        onkeyup: () => this.g.isolate(null),
      }, t("loom.isolate")),
      act(t("loom.copy", { n: this.g.spindle.selected + 1 }), () => this.g.copyToSpool(id!), isStem && this.g.spindle.capacity > 0),
    );
    for (const { slot } of this.g.spindle.threadSlots()) {
      this.loomActions.append(act(t("loom.drop", { n: slot + 1 }), () => this.g.dropFromSpool(slot, id!), isStem && m.replacedBy(id!) !== slot));
    }
    if (isStem && m.replacedBy(id!) !== null) this.loomActions.append(act(t("loom.undrop"), () => this.g.removeDrop(id!), true));
    this.loomActions.append(act(t("loom.close"), () => this.g.closeLoom(), true, { class: "loom-btn close" }));
  }

  // ---- the end of Episode 1 ------------------------------------------------------------------------

  episodeEnd(): Promise<void> {
    return new Promise((res) => {
      const card = h(
        "div",
        { id: "episode-end", role: "dialog", "aria-modal": "true" },
        h("h2", {}, t("end.title")),
        h("p", {}, t("end.body")),
        h("p", { class: "credits" }, t("end.credits")),
        h("button", { class: "big", onclick: () => { card.remove(); res(); } }, t("end.continue")),
      );
      this.root.append(card);
      (card.querySelector("button") as HTMLButtonElement).focus();
      if (this.g.fast) {
        card.remove();
        res();
      }
    });
  }
}
