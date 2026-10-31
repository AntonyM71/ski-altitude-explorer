// Impossible results stop the engine: they mean a bug, not a busy run (busyness-validation).

export class EngineError extends Error {}

/** Throws if any commuting share is outside 0-100%. */
export function checkShares(structure) {
  for (const s of structure.sectors) {
    if (!(s.share >= 0 && s.share <= 1)) throw new EngineError(`commuting share ${s.share} outside 0-100%`);
  }
}

/**
 * Throws if any traffic is negative.
 * @param {Record<string, Float64Array>} arrays  per link
 */
export function checkTraffic(arrays, links) {
  for (const [key, arr] of Object.entries(arrays)) {
    for (let i = 0; i < arr.length; i++) {
      if (arr[i] < -1e-6) {
        throw new EngineError(`negative ${key} traffic (${arr[i].toFixed(1)}) on a ${links[i].k} link: a bug`);
      }
    }
  }
}
