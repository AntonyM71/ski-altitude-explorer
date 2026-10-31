// The network from a structure file, and quickest routes over it.

/**
 * @typedef {object} Link
 * @property {number} a  junction it leaves (index; junctions are numbered highest first)
 * @property {number} b  junction it reaches
 * @property {"run"|"lift"|"walk"|"download"} k
 * @property {number} len  metres
 * @property {number} rt  seconds, as it feels before ability
 * @property {number} [g]  runs: grade 0 green .. 3 black, 4 ungraded
 * @property {number} [grad]  runs: average gradient
 * @property {number} [cm]  blacks: committed length, metres
 * @property {string} [run]  runs: the run's id in the site's runs file
 * @property {number} [cap]  lifts and rides down: capacity per hour
 * @property {number} [lift]  lifts and rides down: the lift's key in structure.lifts
 * @property {1} [nur]  nursery lift or slope
 */

/**
 * The network, with adjacency lists and the lifts that carry skiing.
 * @param {object} structure  a structure file
 */
export function network(structure) {
  const N = structure.z.length;
  const L = structure.links;
  const outs = Array.from({ length: N }, () => []);
  const ins = Array.from({ length: N }, () => []);
  L.forEach((l, i) => {
    outs[l.a].push(i);
    ins[l.b].push(i);
  });
  const lifts = [];
  L.forEach((l, i) => {
    if (l.k === "lift" && !l.nur) lifts.push(i);
  });
  return { structure, N, L, z: structure.z, outs, ins, lifts, sectorOf: (lift) => structure.lifts[lift].sector };
}

/** A binary min-heap of (distance, node). */
export class Heap {
  constructor() {
    this.d = [];
    this.n = [];
    this.lastDist = 0;
  }
  get size() {
    return this.d.length;
  }
  push(dist, node) {
    const d = this.d;
    const n = this.n;
    let i = d.length;
    d.push(dist);
    n.push(node);
    while (i > 0) {
      const p = (i - 1) >> 1;
      if (d[p] <= dist) break;
      d[i] = d[p];
      n[i] = n[p];
      i = p;
    }
    d[i] = dist;
    n[i] = node;
  }
  /** Removes the nearest node; its distance is left in lastDist. */
  pop() {
    const d = this.d;
    const n = this.n;
    const topD = d[0];
    const topN = n[0];
    const lastD = d.pop();
    const lastN = n.pop();
    if (d.length) {
      let i = 0;
      const len = d.length;
      for (;;) {
        let c = 2 * i + 1;
        if (c >= len) break;
        if (c + 1 < len && d[c + 1] < d[c]) c++;
        if (d[c] >= lastD) break;
        d[i] = d[c];
        n[i] = n[c];
        i = c;
      }
      d[i] = lastD;
      n[i] = lastN;
    }
    this.lastDist = topD;
    return topN;
  }
}

/**
 * Quickest routes from any of the sources, or (reverse) to any of them.
 * @param {ReturnType<typeof network>} net
 * @param {number[]} sources
 * @param {Float64Array} times  per link
 * @param {boolean} [reverse]
 * @returns {{best: Float64Array, prev: Int32Array}}  time and the last link on the route, by junction
 */
export function routes(net, sources, times, reverse = false) {
  const { N, L } = net;
  const best = new Float64Array(N).fill(Infinity);
  const prev = new Int32Array(N).fill(-1);
  const h = new Heap();
  for (const s of sources) {
    best[s] = 0;
    h.push(0, s);
  }
  const adj = reverse ? net.ins : net.outs;
  while (h.size) {
    const n = h.pop();
    const d = h.lastDist;
    if (d > best[n]) continue;
    for (const i of adj[n]) {
      const m = reverse ? L[i].a : L[i].b;
      const nd = d + times[i];
      if (nd < best[m]) {
        best[m] = nd;
        prev[m] = i;
        h.push(nd, m);
      }
    }
  }
  return { best, prev };
}

/**
 * Add amount to every link on the route between home and n (from home, or reversed, to home).
 * @param {ReturnType<typeof network>} net
 * @param {{best: Float64Array, prev: Int32Array}} r
 * @param {number} n
 * @param {number} home
 * @param {boolean} reverse
 * @param {number} amount
 * @param {Float64Array} acc
 */
export function addPath(net, r, n, home, reverse, amount, acc) {
  let guard = 0;
  while (n !== home) {
    const i = r.prev[n];
    if (i < 0 || ++guard > net.N) return;
    acc[i] += amount;
    n = reverse ? net.L[i].b : net.L[i].a;
  }
}
