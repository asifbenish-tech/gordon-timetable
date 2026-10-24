// src/ui/settings.ts: latency calibration, text size, contrast, captions, volumes, difficulty,
// saves (export and import as a file, never sent anywhere) and, in development builds, the name set.
import * as Tone from "tone";
import { t, nameSet, setNameSet } from "../content/strings";
import { clearSave, isSave, writeSettings, type Difficulty } from "../core/save";
import type { Game } from "../world/game";
import { append, clear, h } from "./dom";

declare const __DEBUG__: boolean;

export class SettingsPanel {
  readonly el: HTMLElement;
  private body: HTMLElement;
  private status = h("p", { class: "fine", role: "status" });
  onQuit: () => void = () => {};
  onBook: () => void = () => {};
  onApply: () => void = () => {};

  constructor(private g: Game) {
    this.body = h("div", { class: "settings-body" });
    this.el = h(
      "div",
      { id: "settings", class: "modal hidden", role: "dialog", "aria-modal": "true", "aria-label": t("ui.menu") },
      h("div", { class: "modal-head" }, h("h2", {}, t("ui.menu")), h("button", { class: "icon-btn", "aria-label": t("ui.close"), onclick: () => this.close() }, "✕")),
      this.body,
    );
  }

  get isOpen(): boolean {
    return !this.el.classList.contains("hidden");
  }

  open(): void {
    this.render();
    this.el.classList.remove("hidden");
    (this.el.querySelector("button") as HTMLButtonElement | null)?.focus();
  }

  close(): void {
    this.el.classList.add("hidden");
  }

  private save(): void {
    writeSettings(this.g.settings);
    this.onApply();
  }

  private row(label: string, control: HTMLElement): HTMLElement {
    return h("label", { class: "set-row" }, h("span", {}, label), control);
  }

  private select<T extends string | number>(value: T, options: [T, string][], set: (v: T) => void): HTMLSelectElement {
    const s = h("select", { onchange: () => { set(options[s.selectedIndex][0]); this.save(); } });
    for (const [v, l] of options) s.append(h("option", { selected: v === value }, l));
    return s;
  }

  private check(value: boolean, set: (v: boolean) => void): HTMLInputElement {
    const c = h("input", { type: "checkbox", checked: value, onchange: () => { set(c.checked); this.save(); } });
    return c;
  }

  private slider(value: number, set: (v: number) => void): HTMLInputElement {
    const r = h("input", { type: "range", min: 0, max: 1, step: 0.05, value, oninput: () => { set(Number(r.value)); this.save(); } });
    return r;
  }

  render(): void {
    const s = this.g.settings;
    clear(this.body);
    const inGame = !!this.g.save;
    append(
      this.body,
      inGame ? h("div", { class: "set-actions" },
        h("button", { onclick: () => { this.close(); void this.g.hint(); } }, t("menu.hint")),
        h("button", { onclick: () => { this.close(); this.onBook(); } }, t("ui.book")),
      ) : null,
      h("h3", {}, t("menu.sound")),
      this.row(t("set.music"), this.slider(s.music, (v) => { s.music = v; this.g.mixer?.setVolumes(s.music, s.effects); })),
      this.row(t("set.effects"), this.slider(s.effects, (v) => { s.effects = v; this.g.mixer?.setVolumes(s.music, s.effects); })),
      this.row(t("set.captions"), this.check(s.captions, (v) => (s.captions = v))),
      h("div", { class: "set-row" }, h("span", {}, t("set.latency", { ms: Math.round(s.calibrationSec * 1000) })), h("button", { onclick: () => { this.close(); void runCalibration(this.g); } }, t("set.calibrate"))),
      h("h3", {}, t("menu.reading")),
      this.row(t("set.textsize"), this.select(s.textSize, [["s", t("set.small")], ["m", t("set.medium")], ["l", t("set.large")]], (v) => (s.textSize = v))),
      this.row(t("set.textspeed"), this.select(s.textSpeed, [["auto", t("set.auto")], ["click", t("set.click")]], (v) => (s.textSpeed = v))),
      this.row(t("set.contrast"), this.check(s.contrast, (v) => (s.contrast = v))),
      this.row(t("set.lowdetail"), this.check(s.lowDetail, (v) => (s.lowDetail = v))),
      this.row(t("set.reset"), this.select(s.resetBeats, [[2, t("set.reset.2")], [4, t("set.reset.4")], [999, t("set.reset.never")]], (v) => { s.resetBeats = v; if (this.g.distaff) this.g.distaff.resetBeats = v; })),
      inGame ? this.row(t("set.difficulty"), this.select(this.g.save.difficulty, [["practice", t("diff.practice")], ["standard", t("diff.standard")], ["expert", t("diff.expert")]], (v: Difficulty) => { this.g.save.difficulty = v; this.g.persist(true); this.g.hud?.refresh(); })) : null,
      typeof __DEBUG__ !== "undefined" && __DEBUG__ ? this.row(t("set.names"), this.select(nameSet(), [["loom", "loom"], ["original", "original"]], (v) => { setNameSet(v); s.names = v; })) : null,
      h("h3", {}, t("menu.saves")),
      h("div", { class: "set-actions" },
        inGame ? h("button", { onclick: () => this.exportSave() }, t("save.export")) : null,
        h("button", { onclick: () => this.importSave() }, t("save.import")),
        inGame ? h("button", { onclick: () => this.onQuit() }, t("save.title")) : null,
        h("button", {
          class: "danger",
          // two clicks instead of confirm(), which some hosts never show
          onclick: (e: Event) => {
            const b = e.currentTarget as HTMLButtonElement;
            if (b.dataset.armed) {
              clearSave();
              location.reload();
            } else {
              b.dataset.armed = "1";
              b.textContent = t("save.erase.confirm");
            }
          },
        }, t("save.erase")),
      ),
      this.status,
      h("p", { class: "fine" }, t("set.privacy")),
    );
  }

  /** A file where downloads work, and always the text itself to copy (some hosts block downloads). */
  private exportSave(): void {
    this.g.persist(true);
    const json = JSON.stringify(this.g.save);
    try {
      const blob = new Blob([json], { type: "application/json" });
      const a = h("a", { href: URL.createObjectURL(blob), download: "reprise-save.json" });
      document.body.append(a);
      a.click();
      a.remove();
    } catch {
      // the text below is enough
    }
    const area = h("textarea", { id: "save-text", class: "save-text", readonly: true, rows: 3, "aria-label": t("save.text") });
    area.value = json;
    const copy = h("button", {
      onclick: () => {
        navigator.clipboard?.writeText(json).then(
          () => (this.status.textContent = t("save.copied")),
          () => area.select(),
        );
      },
    }, t("save.copy"));
    this.status.replaceChildren(h("span", {}, t("save.export.help")), area, copy);
  }

  private importSave(): void {
    const load = (text: string) => {
      try {
        const data = JSON.parse(text) as unknown;
        if (!isSave(data)) throw new Error("not a save");
        this.close();
        this.g.load(data);
      } catch {
        this.status.textContent = t("save.import.bad");
      }
    };
    const input = h("input", { id: "save-file", type: "file", accept: "application/json,.json" });
    input.onchange = async () => {
      const f = input.files?.[0];
      if (f) load(await f.text());
    };
    const area = h("textarea", { id: "save-paste", class: "save-text", rows: 3, placeholder: t("save.paste"), "aria-label": t("save.paste") });
    this.status.replaceChildren(input, area, h("button", { onclick: () => load(area.value) }, t("save.load")));
  }
}

/** Tap along with eight clicks; the median offset becomes the input latency (GDD 4.7, M1). */
export function runCalibration(g: Game): Promise<void> {
  return new Promise((done) => {
    const taps: number[] = [];
    const clicks: number[] = [];
    const beat = 0.6;
    const flash = h("div", { class: "cal-flash" });
    const status = h("p", { class: "cal-status" }, t("cal.tap"));
    const finish = (apply: boolean) => {
      window.removeEventListener("keydown", key);
      if (apply && taps.length >= 4) {
        const offs = taps.map((tp) => {
          let best = Infinity;
          for (const c of clicks) if (Math.abs(tp - c) < Math.abs(best)) best = tp - c;
          return best;
        }).filter((o) => Math.abs(o) < 0.3).sort((a, b) => a - b);
        if (offs.length) g.settings.calibrationSec = Math.max(0, offs[Math.floor(offs.length / 2)]);
      }
      g.settings.calibrated = true;
      g.conductor.calibrationSec = g.settings.calibrationSec;
      writeSettings(g.settings);
      box.remove();
      done();
    };
    const tap = () => taps.push(Tone.immediate());
    const key = (e: KeyboardEvent) => {
      if (e.key === " " || e.key === "Enter") {
        e.preventDefault();
        tap();
      }
    };
    const box = h(
      "div",
      { id: "calibration", class: "modal", role: "dialog", "aria-modal": "true" },
      h("h2", {}, t("cal.title")),
      h("p", {}, t("cal.body")),
      h("p", { class: "warn" }, t("cal.bluetooth")),
      flash,
      h("button", { class: "big tap", onpointerdown: (e: Event) => { e.preventDefault(); tap(); } }, t("cal.tapbtn")),
      status,
      h("div", { class: "set-actions" }, h("button", { onclick: () => finish(false) }, t("cal.skip"))),
    );
    (document.getElementById("hud") ?? document.body).append(box);
    window.addEventListener("keydown", key);
    if (!g.mixer) return finish(false);
    const synth = new Tone.MembraneSynth({ envelope: { attack: 0.001, decay: 0.08, sustain: 0 } }).connect(g.mixer.sfx);
    const start = Tone.now() + 0.6;
    for (let i = 0; i < 10; i++) {
      const at = start + i * beat;
      clicks.push(at);
      synth.triggerAttackRelease(i % 4 === 0 ? "C5" : "G4", 0.05, at);
      Tone.getDraw().schedule(() => {
        flash.classList.remove("on");
        void flash.offsetWidth;
        flash.classList.add("on");
      }, at);
    }
    Tone.getContext().setTimeout(() => {
      synth.dispose();
      status.textContent = taps.length >= 4 ? t("cal.done", { ms: 0 }) : t("cal.few");
      if (box.isConnected) finish(true);
    }, 0.6 + 10 * beat + 0.5);
  });
}
