import manifest from './repair-probes-manifest.json';
import { reference, type Action, type Library } from './learning';

/**
 * Probe library for the repair lab: every six-action sequence was run on each
 * recorded Nemotron candidate in the isolated verifier (scripts/build_repair_probes.py).
 * Each path is recorded through its first disagreement only. Nothing runs here.
 */
export const PROBE_DEPTH = 4;
export const PROBE_STEPS = 6;

export async function parseProbes(text: string): Promise<Library> {
  const digest = [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text)))].map(x => x.toString(16).padStart(2, '0')).join('');
  if (digest !== manifest.sha256) throw new Error('Probe evidence integrity check failed. Reload the current release; no result is available.');
  const d = JSON.parse(text);
  if (d.schema !== 'countertrace-learning/1' || d.profile !== 'sync-fifo-v1' || d.depth !== PROBE_DEPTH || d.width !== 8 || d.max_steps !== PROBE_STEPS || JSON.stringify(d.actions) !== '["w","r","b","x"]')
    throw new Error('Unsupported probe evidence metadata.');
  return d;
}

export interface ProbeRow {
  cycle: number; action: Action; data: number; queue: number[];
  expected: [number | null, number, number]; observed: [number | null, number, number]; mismatches: string[];
}

/** Recorded rows for a learner's sequence, stopping at the first disagreement. Fails closed. */
export function probeRows(library: Library, runId: string, path: string): {rows: ProbeRow[]; stoppedAt: number | null} {
  const design = library.designs[runId];
  if (!design || !/^[wrbx]{0,6}$/.test(path)) throw new Error('Choose up to six supported actions.');
  const rows: ProbeRow[] = [];
  for (const ref of reference(path, PROBE_DEPTH)) {
    const sample = design.nodes[path.slice(0, ref.cycle)];
    if (!sample || sample.length !== 6 || [1, 2, 4, 5].some(j => sample[j] !== 0 && sample[j] !== 1)
      || (ref.read ? !Number.isInteger(sample[3]) || sample[3]! < 0 || sample[3]! > 255 : sample[3] !== null)
      || ref.expected.some((v, j) => v !== sample[j])) throw new Error('Recorded evidence does not match the reference. No result can be shown.');
    const mismatches = ['read data', 'empty flag', 'full flag'].filter((_, j) => sample[j] !== sample[j + 3]);
    rows.push({cycle: ref.cycle, action: ref.action, data: ref.data, queue: ref.queue,
      expected: [sample[0], sample[1], sample[2]], observed: [sample[3], sample[4], sample[5]], mismatches});
    if (mismatches.length) return {rows, stoppedAt: ref.cycle};
  }
  return {rows, stoppedAt: null};
}
