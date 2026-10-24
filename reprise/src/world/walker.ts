// src/world/walker.ts: a walkable polygon with simple pathfinding (visibility graph + A*).
export type Pt = [number, number];

export function inside(poly: Pt[], [x, y]: Pt): boolean {
  let c = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i];
    const [xj, yj] = poly[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) c = !c;
  }
  return c;
}

function closestOnSegment(p: Pt, a: Pt, b: Pt): Pt {
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  const l2 = dx * dx + dy * dy || 1;
  const t = Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2));
  return [a[0] + t * dx, a[1] + t * dy];
}

const dist = (a: Pt, b: Pt) => Math.hypot(a[0] - b[0], a[1] - b[1]);

/** The nearest walkable point, nudged inside so it is never on the edge. */
export function clampInside(poly: Pt[], p: Pt): Pt {
  if (inside(poly, p)) return p;
  let best: Pt = poly[0];
  let bd = Infinity;
  for (let i = 0; i < poly.length; i++) {
    const q = closestOnSegment(p, poly[i], poly[(i + 1) % poly.length]);
    const d = dist(p, q);
    if (d < bd) {
      bd = d;
      best = q;
    }
  }
  const cx = poly.reduce((s, v) => s + v[0], 0) / poly.length;
  const cy = poly.reduce((s, v) => s + v[1], 0) / poly.length;
  for (let k = 1; k <= 20; k++) {
    const q: Pt = [best[0] + ((cx - best[0]) * k) / 100, best[1] + ((cy - best[1]) * k) / 100];
    if (inside(poly, q)) return q;
  }
  return [cx, cy];
}

function segmentsCross(a: Pt, b: Pt, c: Pt, d: Pt): boolean {
  const o = (p: Pt, q: Pt, r: Pt) => Math.sign((q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0]));
  const o1 = o(a, b, c);
  const o2 = o(a, b, d);
  const o3 = o(c, d, a);
  const o4 = o(c, d, b);
  return o1 !== o2 && o3 !== o4 && o1 !== 0 && o2 !== 0 && o3 !== 0 && o4 !== 0;
}

export function visible(poly: Pt[], a: Pt, b: Pt): boolean {
  for (let i = 0; i < poly.length; i++) {
    if (segmentsCross(a, b, poly[i], poly[(i + 1) % poly.length])) return false;
  }
  for (let k = 1; k < 8; k++) {
    const m: Pt = [a[0] + ((b[0] - a[0]) * k) / 8, a[1] + ((b[1] - a[1]) * k) / 8];
    if (!inside(poly, m)) return false;
  }
  return true;
}

/** Concave corners, pulled one step inside: the only places a path needs to bend. */
function waypoints(poly: Pt[]): Pt[] {
  const out: Pt[] = [];
  for (let i = 0; i < poly.length; i++) {
    const p = poly[(i + poly.length - 1) % poly.length];
    const c = poly[i];
    const n = poly[(i + 1) % poly.length];
    const ax = (c[0] - p[0]) / (dist(c, p) || 1) - (n[0] - c[0]) / (dist(n, c) || 1);
    const ay = (c[1] - p[1]) / (dist(c, p) || 1) - (n[1] - c[1]) / (dist(n, c) || 1);
    for (const s of [3, -3]) {
      const q: Pt = [c[0] - ax * s, c[1] - ay * s];
      if (inside(poly, q)) {
        out.push(q);
        break;
      }
    }
  }
  return out;
}

export function findPath(poly: Pt[], from: Pt, to: Pt): Pt[] {
  const a = clampInside(poly, from);
  const b = clampInside(poly, to);
  if (visible(poly, a, b)) return [b];
  const nodes: Pt[] = [a, b, ...waypoints(poly)];
  const n = nodes.length;
  const g = new Array<number>(n).fill(Infinity);
  const prev = new Array<number>(n).fill(-1);
  const open = new Set<number>([0]);
  g[0] = 0;
  while (open.size) {
    let cur = -1;
    let best = Infinity;
    for (const i of open) {
      const f = g[i] + dist(nodes[i], b);
      if (f < best) {
        best = f;
        cur = i;
      }
    }
    open.delete(cur);
    if (cur === 1) break;
    for (let j = 0; j < n; j++) {
      if (j === cur || !visible(poly, nodes[cur], nodes[j])) continue;
      const ng = g[cur] + dist(nodes[cur], nodes[j]);
      if (ng < g[j]) {
        g[j] = ng;
        prev[j] = cur;
        open.add(j);
      }
    }
  }
  if (prev[1] < 0) return [b];
  const path: Pt[] = [];
  for (let i = 1; i !== 0; i = prev[i]) path.unshift(nodes[i]);
  return path;
}
