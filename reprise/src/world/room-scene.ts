// src/world/room-scene.ts: one Phaser scene builds any room from its JSON (GDD 9.7).
import * as Phaser from "phaser";
import * as Tone from "tone";
import type { HotspotDef, RoomDef } from "../content/types";
import { artUrl, manifest } from "../content/load";
import type { Song } from "../audio/song";
import type { Game, View } from "./game";
import { clampInside, findPath, type Pt } from "./walker";

export const WORLD_W = 640;
export const WORLD_H = 360;
const WALK_SPEED = 72; // px per second
const DOUBLE_MS = 350;

interface Walk {
  path: Pt[];
  done: () => void;
}

export class RoomScene extends Phaser.Scene implements View {
  private g!: Game;
  private layers: Phaser.GameObjects.Image[] = [];
  private sprites = new Map<string, Phaser.GameObjects.Sprite>();
  private controlled = new Set<string>(); // sprites a script has posed; they don't idle-animate
  private spriteDefs = new Map<string, HotspotDef>();
  private bobbin!: Phaser.GameObjects.Sprite;
  private skein!: Phaser.GameObjects.Sprite;
  private walk: Walk | null = null;
  private lastClick = { t: 0, x: 0, y: 0 };
  private glintAt: Phaser.GameObjects.Graphics | null = null;
  private glintId: string | null = null;
  private colour: Phaser.Filters.ColorMatrix | null = null;
  private restored = 1;
  private flockWhite = 1;
  private swan = false;
  private skeinFacing: number | null = null;
  private lit = true;
  onHover: (label: string | null, sx: number, sy: number) => void = () => {};
  onReady: () => void = () => {};
  onSkein: () => void = () => {};
  onProgress: (p: number) => void = () => {};

  constructor() {
    super({ key: "room" });
  }

  init(data: { game: Game }): void {
    this.g = data.game;
  }

  preload(): void {
    this.load.on("progress", (p: number) => this.onProgress(p));
    for (const img of manifest.images) {
      const url = artUrl(img.path);
      const normal = img.normal ? artUrl(img.normal) : undefined;
      if (img.frames > 1) {
        this.load.spritesheet({ key: img.id, url, normalMap: normal, frameConfig: { frameWidth: img.frameW ?? img.w / img.frames, frameHeight: img.h } });
      } else {
        this.load.image({ key: img.id, url, normalMap: normal });
      }
    }
  }

  create(): void {
    for (const img of manifest.images) {
      if (img.frames <= 1) continue;
      this.anims.create({ key: img.id, frames: this.anims.generateFrameNumbers(img.id, {}), frameRate: 8, repeat: -1 });
    }
    this.anims.create({ key: "bobbin_walk", frames: this.anims.generateFrameNumbers("bobbin", { start: 1, end: 8 }), frameRate: 12, repeat: -1 });
    this.anims.create({ key: "conveyor_fast", frames: this.anims.generateFrameNumbers("conveyor", {}), frameRate: 18, repeat: -1 });
    this.anims.create({ key: "dancers_free", frames: this.anims.generateFrameNumbers("dancers", { frames: [0, 2, 1, 3, 2, 0, 3, 1] }), frameRate: 7, repeat: -1 });
    this.input.on("pointerdown", (p: Phaser.Input.Pointer) => this.click(p));
    this.input.on("pointermove", (p: Phaser.Input.Pointer) => this.hover(p));
    this.colour = this.cameras.main.filters.internal.addColorMatrix();
    this.g.view = this;
    this.onReady();
  }

  setLighting(on: boolean): void {
    this.lit = on;
  }

  buildRoom(room: RoomDef, entry: string): void {
    for (const l of this.layers) l.destroy();
    for (const s of this.sprites.values()) s.destroy();
    this.bobbin?.destroy();
    this.skein?.destroy();
    this.glintAt?.destroy();
    this.glintAt = null;
    this.glintId = null;
    this.layers = [];
    this.sprites.clear();
    this.controlled.clear();
    this.spriteDefs.clear();
    this.walk = null;
    this.skeinFacing = null;

    const lighting = this.lit && !this.g.settings.lowDetail;
    for (const l of [...this.lights.lights]) this.lights.removeLight(l);
    if (lighting) {
      this.lights.enable();
      this.lights.setAmbientColor(Phaser.Display.Color.HexStringToColor(room.ambient ?? "#b0b0b8").color);
      for (const l of room.lights ?? []) {
        this.lights.addLight(l.x, l.y, l.radius, Phaser.Display.Color.HexStringToColor(l.color).color, l.intensity, 120);
      }
    } else this.lights.disable();

    room.layers.forEach((l, i) => {
      const img = this.add.image(0, 0, l.image).setOrigin(0, 0).setScrollFactor(l.scroll).setDepth(-100 + i);
      if (l.lit && lighting) img.setLighting(true);
      this.layers.push(img);
    });

    for (const h of room.hotspots) {
      if (!h.sprite) continue;
      const s = this.add.sprite(h.sprite.x, h.sprite.y, h.sprite.image).setOrigin(0.5, 1);
      s.setDepth(h.sprite.depth ?? h.sprite.y);
      if (h.sprite.lit && lighting) s.setLighting(true);
      this.sprites.set(h.id, s);
      this.spriteDefs.set(h.id, h);
    }

    const start = room.entries[entry] ?? Object.values(room.entries)[0] ?? [320, 280];
    this.bobbin = this.add.sprite(start[0], start[1], "bobbin", 0).setOrigin(0.5, 1);
    if (lighting) this.bobbin.setLighting(true);
    this.skein = this.add.sprite(start[0] - 22, start[1], "skein", 0).setOrigin(0.5, 1);
    this.skein.play("skein");
    this.setSwan(this.swan);
    this.cameras.main.setBounds(0, 0, room.width, WORLD_H);
    this.cameras.main.centerOn(start[0], WORLD_H / 2);
    this.refreshHotspots();
    this.applyColour();
  }

  setSwan(swan: boolean): void {
    this.swan = swan;
    if (!this.bobbin) return;
    if (swan) {
      this.bobbin.setTexture("bobbin_swan");
      this.bobbin.play("bobbin_swan");
    } else {
      this.bobbin.anims.stop();
      this.bobbin.setTexture("bobbin", 0);
    }
    this.bobbin.setVisible(!(this.g.room?.id === "crossing" && !swan));
  }

  refreshHotspots(): void {
    for (const [id, s] of this.sprites) {
      const h = this.spriteDefs.get(id)!;
      s.setVisible(this.g.cond(h.when));
      const fw = h.sprite?.frameWhen?.find(([, c]) => this.g.cond(c));
      if (fw) this.setSprite(id, { frame: fw[0] });
    }
    this.skein?.setVisible(this.g.flag("skein") && !this.g.room.swan);
  }

  hotspotCenter(id: string): [number, number] | null {
    const h = this.g.room.hotspots.find((x) => x.id === id);
    if (!h) return null;
    return [h.rect[0] + h.rect[2] / 2, h.rect[1] + h.rect[3] / 2];
  }

  /** Screen-space rectangles of every live hotspot, for the hotspot-reveal key. */
  hotspotScreenRects(): { h: HotspotDef; x: number; y: number; w: number; hgt: number }[] {
    const cam = this.cameras.main;
    return this.g.hotspots().filter((h) => h.id !== "_self").map((h) => ({ h, x: h.rect[0] - cam.scrollX, y: h.rect[1] - cam.scrollY, w: h.rect[2], hgt: h.rect[3] }));
  }

  private hit(x: number, y: number): HotspotDef | null {
    const hs = this.g.hotspots();
    for (let i = hs.length - 1; i >= 0; i--) {
      const h = hs[i];
      if (h.id === "_self") continue;
      const [rx, ry, rw, rh] = h.rect;
      if (x >= rx && x < rx + rw && y >= ry && y < ry + rh) return h;
    }
    return null;
  }

  private click(p: Phaser.Input.Pointer): void {
    if (this.g.loom || this.g.busy) return;
    if (p.y >= 304) return; // the Distaff bar
    const now = performance.now();
    const double = now - this.lastClick.t < DOUBLE_MS && Math.hypot(p.x - this.lastClick.x, p.y - this.lastClick.y) < 12;
    this.lastClick = { t: double ? 0 : now, x: p.x, y: p.y };
    if (this.skein?.visible && this.skein.getBounds().contains(p.worldX, p.worldY)) {
      this.onSkein();
      return;
    }
    const h = this.hit(p.worldX, p.worldY);
    if (h) void this.g.clickHotspot(h.id, double);
    else this.g.clickFloor(p.worldX, p.worldY, double);
  }

  private hover(p: Phaser.Input.Pointer): void {
    if (this.g.loom) return this.onHover(null, 0, 0);
    const h = p.y < 304 ? this.hit(p.worldX, p.worldY) : null;
    this.onHover(h ? h.name : null, p.x, p.y);
  }

  bobbinPos(): [number, number] {
    return [this.bobbin.x, this.bobbin.y];
  }

  face(x: number): void {
    this.bobbin.setFlipX(x < this.bobbin.x);
  }

  walkTo(x: number, y: number, instant = false): Promise<void> {
    const poly = this.g.room.walk as Pt[];
    if (this.swan && this.g.room.id === "crossing") return Promise.resolve();
    this.walk?.done();
    if (instant || this.g.fast) {
      const [tx, ty] = clampInside(poly, [x, y]);
      this.bobbin.setPosition(tx, ty);
      this.walk = null;
      this.idle();
      return Promise.resolve();
    }
    const path = findPath(poly, [this.bobbin.x, this.bobbin.y], [x, y]);
    return new Promise((res) => {
      this.walk = { path, done: res };
      if (!this.swan) this.bobbin.play("bobbin_walk", true);
    });
  }

  private idle(): void {
    if (this.swan) return;
    this.bobbin.anims.stop();
    this.bobbin.setFrame(0);
  }

  setSprite(id: string, s: { anim?: string; frame?: number; visible?: boolean; flipX?: boolean; alpha?: number }): void {
    const sp = this.sprites.get(id);
    if (!sp) return;
    if (s.anim !== undefined || s.frame !== undefined) this.controlled.add(id);
    if (s.anim) sp.play(s.anim, true);
    if (s.frame !== undefined) {
      sp.anims.stop();
      sp.setFrame(s.frame);
    }
    if (s.visible !== undefined) sp.setVisible(s.visible);
    if (s.flipX !== undefined) sp.setFlipX(s.flipX);
    if (s.alpha !== undefined) sp.setAlpha(s.alpha);
  }

  moveSprite(id: string, x: number, y: number, seconds: number): Promise<void> {
    const sp = id === "bobbin" ? this.bobbin : this.sprites.get(id);
    if (!sp) return Promise.resolve();
    if (this.g.fast || seconds <= 0) {
      sp.setPosition(x, y);
      return Promise.resolve();
    }
    return new Promise((res) => this.tweens.add({ targets: sp, x, y, duration: seconds * 1000, onComplete: () => res() }));
  }

  glint(id: string | null): void {
    this.glintAt?.destroy();
    this.glintAt = null;
    this.glintId = id;
    if (!id) return;
    const c = this.hotspotCenter(id);
    if (!c) return;
    this.glintAt = this.add.graphics().setDepth(900);
    this.glintAt.setPosition(c[0], c[1]);
  }

  skeinLook(x: number | null): void {
    this.skeinFacing = x;
  }

  flash(color: number, ms: number): void {
    const [r, g, b] = [(color >> 16) & 255, (color >> 8) & 255, color & 255];
    this.cameras.main.flash(ms, r, g, b);
  }

  setRestored(level: number): void {
    this.restored = level;
    this.applyColour();
  }

  setFlockWhite(level: number): void {
    this.flockWhite = level;
  }

  private applyColour(): void {
    if (!this.colour) return;
    const cm = this.colour.colorMatrix;
    cm.reset();
    if (this.restored < 1) {
      cm.saturate(-0.55 * (1 - this.restored));
      cm.contrast(-0.08 * (1 - this.restored), true);
    }
  }

  openLoom(song: Song): void {
    this.scene.launch("loom", { game: this.g, song });
  }

  closeLoom(): void {
    this.scene.stop("loom");
  }

  override update(_time: number, delta: number): void {
    if (!this.g?.room || !this.bobbin) return;
    if (this.walk) {
      let step = (WALK_SPEED * delta) / 1000;
      while (step > 0 && this.walk.path.length) {
        const [tx, ty] = this.walk.path[0];
        const d = Math.hypot(tx - this.bobbin.x, ty - this.bobbin.y);
        if (d <= step) {
          this.bobbin.setPosition(tx, ty);
          this.walk.path.shift();
          step -= d;
        } else {
          this.bobbin.setFlipX(tx < this.bobbin.x);
          this.bobbin.x += ((tx - this.bobbin.x) / d) * step;
          this.bobbin.y += ((ty - this.bobbin.y) / d) * step;
          step = 0;
        }
      }
      if (!this.walk.path.length) {
        const w = this.walk;
        this.walk = null;
        this.idle();
        w.done();
      }
    }
    this.bobbin.setDepth(this.bobbin.y);
    const room = this.g.room;
    if (room.width > WORLD_W) this.cameras.main.centerOn(this.bobbin.x, WORLD_H / 2);

    if (this.skein.visible) {
      const tx = this.bobbin.x + (this.bobbin.flipX ? 24 : -24);
      this.skein.x += (tx - this.skein.x) * Math.min(1, delta / 260);
      this.skein.y += (this.bobbin.y - this.skein.y) * Math.min(1, delta / 260);
      this.skein.setDepth(this.skein.y - 1);
      this.skein.setFlipX(this.skeinFacing !== null ? this.skeinFacing < this.skein.x : this.bobbin.flipX);
    }

    // Drained places animate in rigid loops locked to the beat; restored ones drift (GDD 7.4, 7.5).
    const beat = this.g.mixer ? this.g.conductor.beatsAt(Tone.now()) : 0;
    for (const [id, s] of this.sprites) {
      const def = this.spriteDefs.get(id)!.sprite!;
      if (id.startsWith("flock")) s.setTint(Phaser.Display.Color.GetColor(...grey(this.flockWhite)));
      if (this.controlled.has(id) || !this.anims.exists(def.image)) continue;
      if (this.restored < 1) {
        if (s.anims.isPlaying) s.anims.stop();
        const frames = s.texture.frameTotal - 1;
        s.setFrame(Math.floor(beat * 2 + (def.x % 3)) % Math.max(1, frames));
      } else if (!s.anims.isPlaying) {
        s.play({ key: def.image, frameRate: (def.fps ?? 8) * (0.9 + ((def.x * 7) % 20) / 100), startFrame: def.x % 4 });
      }
    }

    if (this.glintAt && this.glintId) {
      const k = (Math.sin(performance.now() / 160) + 1) / 2;
      this.glintAt.clear();
      this.glintAt.fillStyle(0xffe9a0, 0.35 + 0.5 * k);
      this.glintAt.fillCircle(0, 0, 2 + 2 * k);
      this.glintAt.lineStyle(1, 0xfff6d0, 0.6 * k);
      this.glintAt.lineBetween(-6 - 3 * k, 0, 6 + 3 * k, 0);
      this.glintAt.lineBetween(0, -6 - 3 * k, 0, 6 + 3 * k);
    }
    this.g.frame();
  }
}

function grey(white: number): [number, number, number] {
  const v = Math.round(150 + 105 * white);
  return [v, v, Math.min(255, v + 4)];
}
