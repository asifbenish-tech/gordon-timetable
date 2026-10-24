// src/core/effects.ts: one-bar states (GDD 5: a state needs the Spindle to last; a change never does).

export class Effects {
  private until = new Map<string, number>();

  /** `draftKey` is "hushing" or "hushing_rev". */
  apply(target: string, draftKey: string, from: number, seconds: number): void {
    const k = `${target}|${draftKey}`;
    this.until.set(k, Math.max(this.until.get(k) ?? 0, from + seconds));
  }

  isActive(target: string, draftKey: string, at: number): boolean {
    return (this.until.get(`${target}|${draftKey}`) ?? -1) > at;
  }

  end(target: string, draftKey: string): void {
    this.until.delete(`${target}|${draftKey}`);
  }

  clearAll(): void {
    this.until.clear();
  }

  activeOn(target: string, at: number): string[] {
    const out: string[] = [];
    for (const [k, t] of this.until) {
      const [tg, d] = k.split("|");
      if (tg === target && t > at) out.push(d);
    }
    return out;
  }
}
