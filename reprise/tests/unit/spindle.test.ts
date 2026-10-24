import { describe, expect, it } from "vitest";
import { GameBus, type CastEvent } from "../../src/core/bus";
import { Spindle, quantizeToBar } from "../../src/core/spindle";
import type { Conductor } from "../../src/audio/conductor";
import type { NoteVoice } from "../../src/audio/note-voice";

function rig() {
  let bar: ((b: number, t: number) => void) | null = null;
  const conductor = { onBar: (fn: (b: number, t: number) => void) => ((bar = fn), () => {}) } as unknown as Conductor;
  const bus = new GameBus();
  const casts: CastEvent[] = [];
  bus.on("cast", (e) => casts.push(e));
  const sp = new Spindle(conductor, {} as NoteVoice, bus, false);
  return { sp, casts, tick: (b: number) => bar?.(b, b * 2) };
}

describe("Spindle quantization (GDD 9.6)", () => {
  it("snaps to eighth notes and folds into one bar", () => {
    expect(quantizeToBar([4.02, 5.1, 5.96, 7.05])).toEqual([0, 1, 2, 3]);
    expect(quantizeToBar([8.49, 9.52, 10.24, 11.76])).toEqual([0.5, 1.5, 2, 0]);
    expect(quantizeToBar([2.9, 3.4, 4.1, 4.6])).toEqual([3, 3.5, 0, 0.5]);
  });
  it("never grades rhythm: any timing gives a valid one-bar loop", () => {
    for (let i = 0; i < 1000; i++) {
      const start = Math.random() * 100;
      const beats = [start, start + Math.random() * 2, start + 2 + Math.random() * 2, start + 4 + Math.random() * 3];
      for (const b of quantizeToBar(beats)) {
        expect(b).toBeGreaterThanOrEqual(0);
        expect(b).toBeLessThan(4);
        expect((b * 2) % 1).toBe(0);
      }
    }
  });
});

describe("Spindle loops", () => {
  it("re-casts a recorded draft every bar, so a one-bar state holds", () => {
    const { sp, casts, tick } = rig();
    sp.setCapacity(2);
    sp.recordDraft("hushing", false, { kind: "hotspot", id: "gate" }, [0, 1, 2, 3], [0, 1, 2, 3]);
    tick(1);
    tick(2);
    expect(casts).toHaveLength(2);
    expect(casts.every((c) => c.fromLoop && c.id === "hushing")).toBe(true);
    sp.clear(0);
    tick(3);
    expect(casts).toHaveLength(2);
  });
  it("keeps the selection below capacity and travels with copied threads", () => {
    const { sp } = rig();
    sp.setCapacity(2);
    sp.select(3);
    expect(sp.selected).toBe(0);
    sp.select(1);
    sp.copyThread({ song: "factory", stem: "kick" });
    expect(sp.threadSlots()).toEqual([{ slot: 1, thread: { song: "factory", stem: "kick" } }]);
    const saved = sp.save();
    const { sp: sp2 } = rig();
    sp2.load(saved, 2);
    expect(sp2.threadSlots()).toEqual(sp.threadSlots());
  });
  it("grows from two spools to four, never shrinks", () => {
    const { sp } = rig();
    sp.setCapacity(2);
    sp.setCapacity(4);
    sp.setCapacity(2);
    expect(sp.capacity).toBe(4);
  });
});
