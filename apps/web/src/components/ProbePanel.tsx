import { useEffect, useState } from 'react';
import { Delete, RotateCcw } from 'lucide-react';
import { actionNames, hex, type Action, type Library } from '../lib/learning';
import { parseProbes, probeRows, PROBE_STEPS } from '../lib/repairProbe';

let cached: Promise<Library> | null = null;
function loadProbes(): Promise<Library> {
  cached ??= fetch('/learning/repair-probes.json').then(async r => {
    if (!r.ok) throw new Error('The probe evidence could not be loaded.');
    return parseProbes(await r.text());
  }).catch(e => { cached = null; throw e; });
  return cached;
}
const flag = (v: number) => v ? '1' : '0';

/** Build an input sequence and replay what this candidate actually did on it. */
export function ProbePanel({runId}: {runId: string}) {
  const [open, setOpen] = useState(false);
  const [library, setLibrary] = useState<Library | null>(null);
  const [error, setError] = useState('');
  const [path, setPath] = useState('');
  useEffect(() => { setPath(''); }, [runId]);
  useEffect(() => { if (open && !library) loadProbes().then(setLibrary, e => setError(String(e.message ?? e))); }, [open, library]);
  let result: ReturnType<typeof probeRows> | null = null;
  let rowError = '';
  if (library) { try { result = probeRows(library, runId, path); } catch (e) { rowError = String((e as Error).message); } }
  const full = path.length >= PROBE_STEPS || result?.stoppedAt != null;
  return <details className="repair-probe" open={open} onToggle={e => setOpen((e.target as HTMLDetailsElement).open)}>
    <summary><b>Test it yourself first</b><span>Build an input sequence and see what this candidate actually did on it.</span></summary>
    {error && <p className="callout" role="alert">{error}</p>}
    {!library && !error && open && <p role="status" className="small muted">Loading the recorded simulations…</p>}
    {library && <>
      <p className="small muted">The queue starts empty after reset. Each action is one rising edge; writes store a byte that depends on the edge. Every sequence of up to {PROBE_STEPS} actions was run on this candidate in the isolated verifier; your browser replays that recording.</p>
      <div className="probe-actions" role="group" aria-label="Add an action">{(['w', 'r', 'b', 'x'] as Action[]).map(a => <button key={a} className="button" disabled={full} onClick={() => setPath(p => p + a)}>{actionNames[a]}</button>)}
        <button className="button" disabled={!path} onClick={() => setPath(p => p.slice(0, -1))} aria-label="Remove the last action"><Delete size={15}/> Undo</button>
        <button className="button" disabled={!path} onClick={() => setPath('')}><RotateCcw size={15}/> Clear</button></div>
      {rowError && <p className="callout" role="alert">{rowError}</p>}
      {result && result.rows.length > 0 && <div className="table-scroll"><table className="probe-table"><caption className="sr-only">Reference and candidate outputs for each edge</caption>
        <thead><tr><th scope="col">Edge</th><th scope="col">Action</th><th scope="col">Reference queue after</th><th scope="col">Expected empty / full / data</th><th scope="col">Candidate empty / full / data</th></tr></thead>
        <tbody>{result.rows.map(r => <tr key={r.cycle} className={r.mismatches.length ? 'probe-mismatch' : ''}>
          <td>{r.cycle}</td><td>{actionNames[r.action]}{r.action === 'w' || r.action === 'b' ? <small> {hex(r.data)}</small> : null}</td>
          <td><code>[{r.queue.map(v => hex(v)).join(', ')}]</code></td>
          <td><code>{flag(r.expected[1])} / {flag(r.expected[2])} / {r.expected[0] === null ? '–' : hex(r.expected[0])}</code></td>
          <td><code>{flag(r.observed[1])} / {flag(r.observed[2])} / {r.observed[0] === null ? '–' : hex(r.observed[0])}</code>{r.mismatches.length ? <strong> {r.mismatches.join(', ')} differ</strong> : null}</td></tr>)}</tbody></table></div>}
      <p className="probe-verdict" aria-live="polite">{!path ? 'Add actions to build a sequence.' : result?.stoppedAt != null
        ? `Counterexample found at edge ${result.stoppedAt}. The probe stops at the first disagreement; later edges would depend on what earlier sequences left in memory.`
        : `No disagreement in these ${path.length} ${path.length === 1 ? 'edge' : 'edges'}. That is evidence about this sequence only, not a proof.`}</p>
    </>}
  </details>;
}
