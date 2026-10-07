import { useEffect, useMemo, useState } from 'react';
import { ArrowRight, Download, RotateCcw } from 'lucide-react';
import { useAsync, useDocumentTitle } from '../lib/hooks';
import { href } from '../lib/route';
import {
  CHECK_LABELS, freshTestbenchNotes, options, parseTestbench, readTestbenchNotes, score, testbenchReport, typicalFirstTestbench,
  type Check, type Selection, type TestbenchNotes,
} from '../lib/testbenchLab';

const KEY = 'countertrace:testbench-practice';

export function TestbenchLabView() {
  useDocumentTitle('Will your testbench catch it?');
  const data = useAsync(async () => {
    const r = await fetch('/learning/audit.json');
    if (!r.ok) throw new Error('The recorded audit evidence could not be loaded.');
    return parseTestbench(await r.text());
  }, []);
  const [notes, setNotes] = useState<TestbenchNotes>(() => { try { return readTestbenchNotes(localStorage.getItem(KEY)); } catch { return freshTestbenchNotes(); } });
  const [saved, setSaved] = useState(true);
  const [sel, setSel] = useState<Selection>({options: [], checks: []});
  const [prediction, setPrediction] = useState<number | null>(null);
  const [ran, setRan] = useState<Selection | null>(null);
  useEffect(() => { try { localStorage.setItem(KEY, JSON.stringify(notes)); setSaved(true); } catch { setSaved(false); } }, [notes]);

  const d = data.status === 'ok' ? data.data : null;
  const opts = useMemo(() => d ? options(d) : [], [d]);
  const result = d && ran ? score(d, ran) : null;
  const best = notes.attempts.filter(a => a.caught === 6).reduce<number | null>((m, a) => m === null || a.edges < m ? a.edges : m, null);
  const toggle = <T,>(list: T[], v: T) => list.includes(v) ? list.filter(x => x !== v) : [...list, v];
  const changed = !ran || ran.options.join() !== sel.options.join() || ran.checks.join() !== sel.checks.join();

  function run() {
    if (!d || prediction === null) return;
    const s = score(d, sel);
    setRan({options: [...sel.options].sort(), checks: [...sel.checks].sort()});
    setNotes(n => ({...n, attempts: [...n.attempts, {options: [...sel.options].sort(), checks: [...sel.checks].sort(), prediction, caught: s.caught, edges: s.edges}].slice(-200)}));
    setPrediction(null);
  }
  function download() {
    const url = URL.createObjectURL(new Blob([testbenchReport(notes)], {type: 'text/markdown'}));
    const a = document.createElement('a'); a.href = url; a.download = 'countertrace-testbench-notes.md'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  return <div className="stack-lg learning-lab testbench-lab">
    <header className="practice-heading"><p className="eyebrow">THE PRACTICE BENCH / TESTBENCH LAB</p><h1>Will your testbench<br/><em>catch it?</em></h1>
      <p className="learning-deck">Six bugs were seeded into copies of a correct four-slot FIFO. Choose the tests your testbench runs and the signals it checks, predict how many bugs it catches, then run it against the recorded results.</p></header>
    {data.status === 'loading' && <p role="status">Loading the recorded audit evidence…</p>}
    {data.status === 'error' && <div className="callout" role="alert"><h2>Evidence unavailable</h2><p>{String(data.error)}</p><button className="button" onClick={() => data.reload()}>Retry</button></div>}
    {d && <>
      <section className="testbench-builder" aria-labelledby="tb-tests">
        <div className="section-heading"><h2 id="tb-tests">1. Which tests does your testbench run?</h2><button className="button" onClick={() => { setSel(typicalFirstTestbench(d)); }}>Load a typical first testbench</button></div>
        <div className="testbench-options">{opts.map(o => <label key={o.id} className={sel.options.includes(o.id) ? 'selected' : ''}>
          <input type="checkbox" checked={sel.options.includes(o.id)} onChange={() => setSel(s => ({...s, options: toggle(s.options, o.id)}))}/>
          <span><b>{o.label}</b><small>{o.edges} edges</small></span><span className="small muted">{o.description}</span></label>)}</div>
        <h2>2. Which signals does it check against the expected behavior?</h2>
        <div className="testbench-checks">{d.checks.map((c: Check) => <label key={c}><input type="checkbox" checked={sel.checks.includes(c)} onChange={() => setSel(s => ({...s, checks: toggle(s.checks, c)}))}/>{CHECK_LABELS[c]}</label>)}</div>
        <fieldset className="testbench-predict"><legend><h2>3. How many of the six bugs will it catch?</h2></legend>
          <div className="choice-row">{[0, 1, 2, 3, 4, 5, 6].map(n => <label key={n}><input type="radio" name="tb-prediction" checked={prediction === n} onChange={() => setPrediction(n)}/>{n}</label>)}</div></fieldset>
        <div className="actions"><button className="button primary" disabled={!sel.options.length || !sel.checks.length || prediction === null || !changed} onClick={run}>Run my testbench <ArrowRight size={17}/></button>
          <span className="small muted">{!sel.options.length || !sel.checks.length ? 'Pick at least one test and one signal.' : !changed ? 'Change the tests or signals to run again.' : prediction === null ? 'Commit a prediction first.' : 'Replays recorded simulation traces. No RTL runs in your browser.'}</span></div>
      </section>
      {result && ran && <section className="testbench-result" aria-live="polite">
        <p className="eyebrow">YOUR TESTBENCH / RECORDED RESULTS</p>
        <h2><b>{result.caught}</b> of 6 bugs caught <span className="muted">· {result.edges} edges simulated</span></h2>
        <p className="prediction-comparison">You predicted {notes.attempts[notes.attempts.length - 1]?.prediction}. {result.caught === 6 ? (best !== null && best < result.edges ? `Every bug caught. Your best complete testbench so far used ${best} edges; can you do it with fewer?` : 'Every bug caught. Can you catch all six with fewer edges?') : 'Read each miss below before changing your testbench.'}</p>
        <ol className="testbench-bugs">{result.results.map(r => {
          const shown = r.caught || notes.revealed.includes(r.bug.id);
          return <li key={r.bug.id} className={r.caught ? 'caught' : 'missed'}>
            <div><b>{r.label}</b><span>{r.caught ? 'Caught' : 'Slipped through'}</span></div>
            {r.caught ? <p>Your <code>{r.caught.test}</code> test sees the <strong>{CHECK_LABELS[r.caught.check]}</strong> disagree with the reference at edge {r.caught.cycle} ({d.rows[r.caught.row]?.toLowerCase()}).</p>
              : r.miss?.kind === 'never_driven' ? <p>None of your tests ever produce this situation: <strong>{d.rows[r.miss.row]?.toLowerCase()}</strong>.</p>
              : r.miss?.kind === 'not_checked' ? <p>Your tests do expose it, but only on the <strong>{r.miss.checks.map(c => CHECK_LABELS[c]).join(' or ')}</strong>, which your testbench does not check.</p>
              : <p>Your tests drive the situation this bug targets, but never in a way that exposes it on the signals you check.</p>}
            {shown ? <p className="small muted">{r.bug.summary}</p> : <button className="link-button" onClick={() => setNotes(n => ({...n, revealed: [...n.revealed, r.bug.id]}))}>Show the bug</button>}
          </li>;
        })}</ol>
        <p className="small muted">{d.equivalent.length ? `A seventh change in the same set was proved behaviorally equivalent, so no test can catch it; it is not counted. ` : ''}Results come from the recorded check-quality audit (<a href={href.run(d.source_run)}>open the run</a>), reparsed from its raw simulation traces.</p>
      </section>}
      {best !== null && <section className="repair-reflection"><div><p className="eyebrow">MAKE THE REASONING YOURS</p><h2>Fewer edges,<br/>same bugs.</h2></div><div className="stack">
        <p>You caught all six. One well-placed directed test can do it in fewer than twenty edges, and the seeded random runs catch them too, with far more edges. Random traffic finds bugs but leaves you to work out which rule broke; a directed test names the rule. Neither proves the design correct: the workbench’s formal proofs cover cases a finite set of tests cannot.</p>
        <label className="lab-select">What would you add to your own FIFO testbench after this?<textarea maxLength={2000} rows={3} value={notes.reflection} onChange={e => setNotes(n => ({...n, reflection: e.target.value}))}/></label></div></section>}
      <section className="repair-notebook"><div><h3>Your field notes</h3><p className="small muted">{notes.attempts.length} {notes.attempts.length === 1 ? 'run' : 'runs'}{best !== null ? `, best complete testbench ${best} edges` : ''}. {saved ? 'Saved in this browser.' : 'Browser storage unavailable; download before leaving.'}</p></div>
        <div className="actions"><button className="button" onClick={download}><Download size={16}/> Download notes</button><button className="button" onClick={() => { if (window.confirm('Clear your saved testbench runs and notes?')) { setNotes(freshTestbenchNotes()); setRan(null); } }}><RotateCcw size={16}/> Start over</button></div></section>
      <div className="studio-next"><a href={href.repair()}>Challenge a real Nemotron repair <ArrowRight size={16}/></a><a href="#/learn">Back to the practice bench</a></div>
    </>}
  </div>;
}
