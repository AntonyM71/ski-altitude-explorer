// Seeded random numbers, so the same structure and parameters always give the same result (busyness-commuting).

/**
 * Normally distributed numbers (mean 0, sd 1) from a seeded mulberry32 generator, by the Box-Muller method.
 * @param {number} seed
 * @returns {() => number}
 */
export function gaussian(seed) {
  let s = seed >>> 0;
  let spare = null;
  const uniform = () => {
    s = (s + 0x6d2b79f5) >>> 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  return () => {
    if (spare !== null) {
      const v = spare;
      spare = null;
      return v;
    }
    let u = 0;
    while (u === 0) u = uniform();
    const r = Math.sqrt(-2 * Math.log(u));
    const th = 2 * Math.PI * uniform();
    spare = r * Math.sin(th);
    return r * Math.cos(th);
  };
}
