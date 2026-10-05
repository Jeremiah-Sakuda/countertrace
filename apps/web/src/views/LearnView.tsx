import { useEffect, useRef, useState } from 'react';
import { ArrowRight, Download, FlaskConical, Lightbulb, RotateCcw } from 'lucide-react';
import { useDocumentTitle, type AsyncState } from '../lib/hooks';
import type { Status } from '../api/types';
import { href } from '../lib/route';
import { actionNames, evidenceRows, hex, lessons, newSession, sessionReport, validateSession, validateSessionEvidence, MAX_SESSION_BYTES, parseLibrary, type Action, type Library, type Session } from '../lib/learning';

function download(name: string, content: string, type = 'text/plain') {
  const url = URL.createObjectURL(new Blob([content], {type}));
  const a = document.createElement('a'); a.href = url; a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function readSaved(id: string): Session {
  try {
    const s = validateSession(JSON.parse(localStorage.getItem(`countertrace:lesson:${id}`) ?? 'null'));
    if (s.lesson === id) return s;
  } catch { /* Storage can be unavailable. The lesson still works in memory. */ }
  return newSession(id);
}

export function LearnHome() {
  useDocumentTitle('Hardware debugging lab');
  return <div className="learning-home stack-lg">
    <section className="learning-hero">
      <div><p className="eyebrow">THE COUNTERTRACE LEARNING LAB</p><h1>A convincing fix.<br/><em>A better question.</em></h1>
      <p className="learning-deck">Learn to find hardware bugs, challenge a fix, and explain what your evidence actually proves.</p>
      <div className="actions"><a className="button primary" href="#/learn/overflow">Start the first lab <ArrowRight size={17}/></a><a href="#/teach">Teaching a group?</a></div>
      <p className="muted small">For students who know clocks, reset, and basic Verilog. No account, installation, or API key needed for these labs.</p></div>
      <div className="learning-specimen" aria-label="Illustration of a full two-slot queue"><span className="eyebrow">A QUESTION TO START WITH</span><div className="specimen-queue"><span>0x11<small>oldest</small></span><span>0x22<small>newest</small></span><b>← 0x33?</b></div><h2>Two slots. Three writes.</h2><p>The queue is full. Another word arrives. What should the next read return?</p><span className="specimen-caption">Predict it. Test it. Defend your answer.</span></div>
    </section>
    <div className="learning-method"><span><b>01</b> Predict the behavior</span><span><b>02</b> Build a counterexample</span><span><b>03</b> Explain & transfer</span></div>
    <section aria-labelledby="lab-list"><div className="section-heading"><h2 id="lab-list">Three experiments in good judgment</h2><span className="muted">8-bit FIFO · two slots · one clock</span></div>
      <div className="lesson-grid">{lessons.map(l => <a className="lesson-card" href={`#/learn/${l.id}`} key={l.id}><span className="eyebrow">LAB {l.number} / {l.minutes}</span><h3>{l.title}</h3><p>{l.brief}</p><span className="lesson-concept">{l.concept}<ArrowRight size={18}/></span></a>)}</div>
    </section>
    <section className="learning-footnote"><FlaskConical aria-hidden="true"/><div><h3>Real RTL evidence. Room to experiment.</h3><p>Every available sequence was run in isolated Verilator simulation. Your browser replays the matching evidence; it does not execute RTL or call an AI model. Curated candidates are authored fixtures, not claimed AI outputs.</p><p>Explore <a href={href.runs()}>actual Nemotron repairs and verification runs</a>, or use the <a href="https://github.com/Jeremiah-Sakuda/countertrace#quick-start">local build</a> for live model coaching and verification.</p></div></section>
  </div>;
}

export function LearnView({id, status}: {id: string; status: AsyncState<Status>}) {
  const lesson = lessons.find(l => l.id === id);
  const [session, setSession] = useState(() => readSaved(id));
  const [saved, setSaved] = useState(true);
  const [library, setLibrary] = useState<Library | null>(null);
  const [error, setError] = useState('');
  const [choice, setChoice] = useState<number | null>(null);
  const [path, setPath] = useState(session.attempts.at(-1)?.path ?? '');
  const [prediction, setPrediction] = useState(session.attempts.at(-1)?.prediction ?? '');
  const [tested, setTested] = useState(session.attempts.at(-1)?.path ?? '');
  const [transfer, setTransfer] = useState<number | null>(null);
  const [tutor, setTutor] = useState<{text: string; model?: string; path:string; reflection:string} | null>(null);
  const [tutoring, setTutoring] = useState(false);
  const tutorEpoch = useRef(0);
  const benchHeading = useRef<HTMLHeadingElement>(null);
  const advanceToBench = useRef(false);
  useEffect(()=>{if(advanceToBench.current && session.initialAnswer!==null){benchHeading.current?.focus();advanceToBench.current=false;}},[session.initialAnswer]);
  function invalidateTutor() {tutorEpoch.current++;setTutor(null);setTutoring(false);}
  const [coachExample, setCoachExample] = useState<{request:{reflection:string};response:{result:{hint:string};calls:{model_id:string;latency_ms:number}[]}} | null>(null);
  useEffect(()=>{if(id==='overflow') void fetch('/learning/coach.json').then(r=>r.ok?r.json():null).then(d=>{if(d?.attempts?.length) setCoachExample(d.attempts[d.attempts.length-1]);}).catch(()=>{});},[id]);
  useDocumentTitle(lesson?.title ?? 'Lab not found');
  useEffect(() => { let active = true; fetch('/learning/library.json').then(async r => {if (!r.ok) throw new Error('Learning evidence could not be loaded.'); const d = await parseLibrary(await r.text()); if (active) setLibrary(d);}).catch(e => active && setError(String(e.message))); return () => {active = false;}; }, []);
  useEffect(() => {try { localStorage.setItem(`countertrace:lesson:${id}`, JSON.stringify(session)); setSaved(true); } catch {setSaved(false);}}, [id, session]);
  if (!lesson) return <section className="card"><h1>Lab not found</h1><a href="#/">Choose a lab</a></section>;
  const patch = (value: Partial<Session>) => setSession(s => ({...s, ...value}));
  let rows: ReturnType<typeof evidenceRows> = [];
  let evidenceError = '';
  if (tested && library) { try { rows = evidenceRows(library, id, tested); } catch(e) {evidenceError = String(e);} }
  const first = rows.find(r => r.mismatches.length);
  const investigated = session.attempts.length > 0;
  const live = status.status === 'ok' && status.data.deployment?.mode !== 'recorded' && status.data.model.configured;
  async function askTutor() {
    const ticket=++tutorEpoch.current;
    const context={path:tested,reflection:session.reflection,requested:new Date().toISOString()};
    setTutoring(true); setTutor(null);
    patch({hints:session.hints+1});
    try {
      const response = await fetch('/api/learn/hint', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({lesson:id, path:tested, reflection:session.reflection})});
      const result = await response.json();
      if (!response.ok || result.status !== 'ok') throw new Error(result.detail ?? result.error ?? 'Model coaching is unavailable.');
      if(ticket!==tutorEpoch.current) return;
      const model=result.calls?.[0]?.model_id ?? 'Unknown model';
      setTutor({text:result.result.hint,model,...context});
      setSession(s=>({...s,coaching:[...s.coaching.slice(-99),{...context,status:'ok',hint:result.result.hint,cycles:result.result.cycles,model,latency_ms:result.calls?.[0]?.latency_ms ?? null}]}));
    } catch(e) {if(ticket===tutorEpoch.current) {const detail=`Could not get a model hint: ${e instanceof Error ? e.message : String(e)}. The authored hints still work.`.slice(0,1600); setTutor({text:detail,...context}); setSession(s=>({...s,coaching:[...s.coaching.slice(-99),{...context,status:'error',hint:detail,cycles:[],model:'Unavailable',latency_ms:null}]}));}} finally {if(ticket===tutorEpoch.current)setTutoring(false);}
  }
  function testSequence() {
    if (!library || !path || !prediction) return;
    try { const result = evidenceRows(library, id, path); setTested(path); setError(''); invalidateTutor(); patch({attempts:[...session.attempts.slice(-199), {path, prediction, firstMismatch:result.find(r => r.mismatches.length)?.cycle ?? null}]}); }
    catch(e) {setError(String(e));}
  }
  return <div className="learning-lab stack-lg">
    <a href="#/">← All labs</a>
    <header className="lab-heading"><p className="eyebrow">LAB {lesson.number} / {lesson.concept}</p><h1>{lesson.title}</h1><p className="learning-deck">{lesson.brief}</p><p className="muted small">Practice is saved in this browser only. Download it to share with a mentor. {saved ? '' : 'Storage unavailable: download before leaving.'}</p></header>
    <div className="learning-contract"><strong>The contract on your bench</strong><p>Two slots, 8-bit words, rising-edge clock. Accept requests using occupancy <em>before</em> the edge. A full queue ignores writes, even alongside a read. An empty queue ignores reads, even alongside a write. Reset empties the queue. Read data is checked only on accepted reads.</p></div>
    <section className="learning-stage" aria-labelledby="predict-heading"><div className="stage-number">01</div><div><h2 id="predict-heading">Make a prediction</h2><p>{lesson.question}</p>
      {session.initialAnswer === null ? <><fieldset className="choice-list"><legend className="sr-only">Your initial prediction</legend>{lesson.choices.map((c,i)=><label key={c}><input type="radio" name="initial" checked={choice===i} onChange={()=>setChoice(i)}/>{c}</label>)}</fieldset><button className="button primary" disabled={choice===null} onClick={()=>{advanceToBench.current=true;patch({initialAnswer:choice, initialCorrect:choice===lesson.answer});}}>Commit prediction & open the bench</button></> : <p className="learning-feedback">Your prediction: <strong>{lesson.choices[session.initialAnswer]}</strong>. Keep it in mind as you investigate.</p>}
    </div></section>
    {session.initialAnswer !== null && <section className="learning-stage" aria-labelledby="investigate-heading"><div className="stage-number">02</div><div><h2 id="investigate-heading" ref={benchHeading} tabIndex={-1}>Build the experiment</h2><p>Start after reset. Add up to six clock edges. Each write offers the next numbered word: edge 1 offers 0x11, edge 2 offers 0x22, and so on.</p>
      <div className="lab-toolbar" aria-label="Add a clock edge">{(Object.keys(actionNames) as Action[]).map(a=><button className="button" key={a} disabled={path.length>=6} onClick={()=>{setPath(p=>p+a);setTested('');setPrediction('');invalidateTutor();}}>{actionNames[a]}</button>)}</div>
      <ol className="sequence-strip" aria-label="Your experiment">{[...path].map((a,i)=><li key={i}><small>EDGE {i+1}</small><strong>{actionNames[a as Action]}</strong>{(a==='w'||a==='b')&&<code>{hex(17*(i+1))}</code>}</li>)}{!path&&<li className="sequence-empty">Add your first action above.</li>}</ol>
      <div className="actions"><button className="button" disabled={!path} onClick={()=>{setPath(p=>p.slice(0,-1));setTested('');setPrediction('');invalidateTutor();}}>Undo edge</button><button className="button" disabled={!path} onClick={()=>{setPath('');setTested('');setPrediction('');invalidateTutor();}}>Clear sequence</button><span className="muted">{path.length}/6 edges</span></div>
      <label className="lab-select">Before running, what do you expect?<select value={prediction} onChange={e=>setPrediction(e.target.value)}><option value="">Choose an expectation</option><option value="mismatch">This sequence will expose a mismatch</option><option value="no-mismatch">No mismatch in this sequence</option><option value="unsure">I am unsure; I want to investigate</option></select></label>
      <button className="button primary" disabled={!library||!path||!prediction} onClick={testSequence}>{library ? 'Run my experiment' : 'Loading recorded evidence…'} <ArrowRight size={16}/></button>
      <p className="muted small">Replays an actually executed RTL sequence from the recorded library. No live RTL execution or model call.</p>
      {(error||evidenceError)&&<p role="alert" className="error-text">{error||evidenceError}</p>}
      {!!rows.length && <div className="experiment-result" aria-live="polite"><h3>{first ? `Mismatch witnessed at edge ${first.cycle}` : 'No mismatch in this sequence'}</h3><p>{first ? `The first differing check is ${first.mismatches.join(', ')}. Inspect earlier edges too: the damage may precede the symptom.` : 'These inputs matched the contract. This does not prove the design correct for other sequences.'}</p>
        <div className="table-wrap" role="region" aria-label="Experiment evidence" tabIndex={0}><table><thead><tr><th>Edge / request</th><th>Expected queue after edge</th><th>Read data expected / observed</th><th>Empty expected / observed</th><th>Full expected / observed</th></tr></thead><tbody>{rows.map(r=><tr key={r.cycle} className={r.mismatches.length?'lab-mismatch':''}><th>{r.cycle} · {actionNames[r.action]}{r.mismatches.length>0&&<small> Mismatch</small>}</th><td><code>[{r.queue.map(hex).join(', ')}]</code></td><td>{hex(r.sample[0])} / {hex(r.sample[3])}</td><td>{r.sample[1]} / {r.sample[4]}</td><td>{r.sample[2]} / {r.sample[5]}</td></tr>)}</tbody></table></div>
        <p className="small muted">Queue values come from the independent reference, not sampled DUT memory. “Not checked” means no read was accepted.</p>
      </div>}
      <details className="lab-source"><summary>Inspect candidate RTL & evidence provenance</summary><p>{library?.designs[id]?.origin} You may inspect source; this is an open practice lab.</p><pre><code>{library?.designs[id]?.source}</code></pre><p>Source SHA-256: <code>{library?.designs[id]?.source_sha256}</code></p><p>{library?.method} {library?.sequences_per_design.toLocaleString()} six-edge sequences per candidate, including all shorter prefixes. Recorded {library?.created_at.slice(0,10)}.</p><a href="/learning/evidence.zip" download>Download raw traces, RTL, stimulus & hash manifest</a></details>
      <div className="hint-panel"><h3><Lightbulb size={18} aria-hidden="true"/> Need a nudge?</h3><p className="small muted">Authored hints; opening a hint is recorded as assistance.</p>{lesson.hints.slice(0,session.authoredHints).map(h=><p key={h}>{h}</p>)}<button className="button" disabled={session.authoredHints>=3} onClick={()=>patch({hints:session.hints+1,authoredHints:session.authoredHints+1})}>Reveal next hint ({session.authoredHints}/3)</button></div>
    </div></section>}
    {investigated && <section className="learning-stage" aria-labelledby="explain-heading"><div className="stage-number">03</div><div><h2 id="explain-heading">Explain it. Then transfer it.</h2><label className="lab-select">What did your experiment establish? What test would you keep?<textarea rows={4} maxLength={2000} value={session.reflection} disabled={!!session.completed} onChange={e=>{patch({reflection:e.target.value});invalidateTutor();}} placeholder="Name the edge, the rule, and the evidence. A no-mismatch result also has limits."/></label><p className="small muted">Your explanation is for discussion with a mentor. It is not automatically graded.</p>
      {live ? <><button className="button" disabled={tutoring||!tested||!session.reflection.trim()} onClick={()=>void askTutor()}>{tutoring?'Getting a grounded hint…':'Ask Nemotron about my reasoning'}</button><p className="small muted">Sends this explanation and sequence to Nebius Token Factory. AI feedback is advisory and counts as assistance.</p></> : <p className="small muted">Live Nemotron coaching is available in the configured local build. These hosted labs use authored hints.</p>}
      {tutor&&<div className="learning-feedback"><strong>Model coaching · advisory {tutor.model??''}</strong><p className="small">For sequence {tutor.path.toUpperCase()} and the explanation: “{tutor.reflection}”</p><p>{tutor.text}</p><p className="small muted">Coaching checks references, not semantic accuracy. Development checks found some incorrect edge and scope wording; compare the evidence and discuss uncertain claims with a mentor.</p></div>}
      {coachExample && <details className="lab-source" onToggle={e=>{if(e.currentTarget.open&&!session.recordedCoachingViewed) setSession(s=>s.recordedCoachingViewed?s:{...s,recordedCoachingViewed:true,hints:s.hints+1});}}><summary>See an actual recorded Nemotron coaching example</summary><p><strong>Recorded development example · not a response to your text.</strong> The example used Write → Write → Write → Read on this candidate.</p><p>Example learner explanation: “{coachExample.request.reflection}”</p><blockquote>{coachExample.response.result.hint}</blockquote><p className="small muted">{coachExample.response.calls[0]?.model_id} via Nebius Token Factory · {coachExample.response.calls[0]?.latency_ms} ms. Two earlier Super responses followed the mistaken cause. The revised Ultra prompt includes source and an authored facilitator focus; this is one useful assistant-reviewed example, not an efficacy result.</p><a href="/learning/coach.json">Inspect all three development calls</a></details>}
      <h3 className="transfer-heading">A new situation</h3><p>{lesson.transfer}</p><fieldset className="choice-list" disabled={session.transferAnswer!==null}><legend className="sr-only">Transfer answer</legend>{lesson.transferChoices.map((c,i)=><label key={c}><input type="radio" name="transfer" checked={(session.transferAnswer??transfer)===i} onChange={()=>setTransfer(i)}/>{c}</label>)}</fieldset>
      {session.transferAnswer===null ? <button className="button primary" disabled={transfer===null||!session.reflection.trim()||!tested||!rows.length||tutoring} onClick={()=>{invalidateTutor();patch({transferAnswer:transfer,transferCorrect:transfer===lesson.transferAnswer,completed:new Date().toISOString(),completionEvidence:{path:tested,hints:session.hints,authoredHints:session.authoredHints,recordedCoachingViewed:session.recordedCoachingViewed,coachingCount:session.coaching.length,attemptCount:session.attempts.length}});}}>Check my reasoning</button> : <div className="learning-feedback" role="status"><h3>{session.transferCorrect?'Your transfer answer matches the contract.':'Revisit the boundary rule.'}</h3><p>{lesson.transferWhy}</p><p><strong>Initial prediction:</strong> {session.initialCorrect?'Matched the contract.':'Needed revision.'}</p><p>{lesson.takeaway}</p><p className="small muted">At submission: {session.completionEvidence ? `${session.completionEvidence.hints} assistance requests/views; evidence ${session.completionEvidence.path.toUpperCase()}. Later exploration does not change this snapshot.` : 'This older record has no assistance snapshot.'}</p><p>This is practice on a small set of cases, not a certification or evidence of learning gains.</p></div>}
    </div></section>}
    {session.attempts.length>0 && <details className="lab-source"><summary>Previous experiments ({session.attempts.length})</summary><ol>{session.attempts.map((a,i)=><li key={i}><span>{a.path.split('').map(x=>actionNames[x as Action]).join(' → ')} · {a.firstMismatch===null?'no mismatch':`mismatch at edge ${a.firstMismatch}`} </span><button className="button" onClick={()=>{setPath(a.path);setTested(a.path);setPrediction(a.prediction);invalidateTutor();}}>Replay experiment {i+1}</button></li>)}</ol><p className="small muted">Replay restores the evidence without adding an attempt.</p></details>}
    <section className="lab-session"><div><h3>Your lab notebook</h3><p>{session.attempts.length} experiment{session.attempts.length===1?'':'s'} · {session.hints} hint request{session.hints===1?'':'s'} · {session.completed?'Reflection completed':'In progress'}</p></div><div className="actions"><button className="button" onClick={()=>download(`countertrace-${id}.md`,sessionReport(session))}><Download size={16}/> Download notes</button><button className="button" onClick={()=>download(`countertrace-${id}.json`,JSON.stringify(session,null,2),'application/json')}>Export session JSON</button><button className="button" onClick={()=>{if(window.confirm('Clear this lab’s saved answers and attempts? Download them first if you want to keep them.')){setSession(newSession(id));setPath('');setTested('');setChoice(null);setTransfer(null);invalidateTutor();}}}><RotateCcw size={16}/> Start over</button></div></section>
    {session.completed&&<section className="learning-contract"><h3>Now challenge a real AI repair</h3><p>The lab candidates were authored exercises. In this separate recorded Nemotron run, an initial patch failed and the next candidate passed the unchanged checks. Inspect what evidence justified the decision.</p><a href="#/runs/rec-20261004-010137-ver-dd43e0">Inspect the rejected and accepted Nemotron repairs →</a></section>}
    {session.completed&&<a className="button primary" href={`#/learn/${lessons[(lessons.findIndex(l=>l.id===id)+1)%lessons.length]!.id}`}>Try another lab <ArrowRight size={16}/></a>}
  </div>;
}

export function TeachView() {
  useDocumentTitle('Facilitator desk');
  const [records, setRecords] = useState<Session[]>([]);
  const [error, setError] = useState('');
  return <div className="stack-lg learning-lab"><header><p className="eyebrow">FOR INSTRUCTORS & FPGA CLUB MENTORS</p><h1>Bring a better bug<br/>to your next session.</h1><p className="learning-deck">A ready-to-run lab on prediction, boundary conditions, and the limits of passing tests.</p></header>
    <section className="learning-contract"><h2>A 20-minute session</h2><ol><li><strong>3 minutes:</strong> introduce the two-slot contract and let learners commit a prediction.</li><li><strong>8 minutes:</strong> pair up and build experiments. Ask for an input sequence before revealing hints.</li><li><strong>5 minutes:</strong> explain the evidence and answer the transfer question independently.</li><li><strong>4 minutes:</strong> compare reasoning, collect optional anonymous records, and discuss what remains unchecked.</li></ol><p className="small muted">Suggested pacing, not a measured completion time. Requires basic clocks, reset, and RTL. No learner accounts.</p></section>
    <div className="lesson-grid">{lessons.map(l=><section className="lesson-card" key={l.id}><span className="eyebrow">LAB {l.number}</span><h2>{l.title}</h2><p>{l.concept}</p><a href={`#/learn/${l.id}`}>Open learner link</a><p className="small muted">Share the link from your address bar.</p><details><summary>Facilitator notes & answer key</summary><p>{l.takeaway}</p><p>Initial: {l.choices[l.answer]}</p><p>Transfer: {l.transferChoices[l.transferAnswer]}</p><p>{l.transferWhy}</p></details></section>)}</div>
    <section className="card stack"><h2>Review a group’s practice</h2><p>Ask learners to export their session JSON and share it through your usual channel. Import the files here to review answers and assistance. Files stay in this browser tab; nothing is uploaded. Recorded mismatch claims are checked against the library; activity and assistance remain self-reported, editable practice notes. Use anonymous records and obtain permission before collecting them.</p><label className="lab-select">Import session records (JSON, up to 30; 2 MB each)<input type="file" accept=".json,application/json" multiple onChange={async e=>{setError(''); try {const files=Array.from(e.target.files??[]);if(files.length>30) throw new Error('Import at most 30 files.'); const response=await fetch('/learning/library.json');if(!response.ok)throw new Error('Could not validate records: evidence unavailable.');const library=await parseLibrary(await response.text());const imported=[];for(const f of files){if(f.size>MAX_SESSION_BYTES)throw new Error('A file exceeds 2 MB.');imported.push(validateSessionEvidence(validateSession(JSON.parse(await f.text())),library));}setRecords(imported);}catch(err){setError(err instanceof Error?err.message:String(err));}}}/></label>{error&&<p role="alert" className="error-text">{error}</p>}
    {records.length>0&&<><p><strong>{records.length} records</strong> · {records.filter(r=>r.transferCorrect).length} matching transfer answers · {records.filter(r=>r.hints>0).length} used hints. Counts describe imported practice, not measured learning gains or unique participants.</p><div className="table-wrap"><table><thead><tr><th>Record</th><th>Lab</th><th>Initial prediction</th><th>Transfer</th><th>Assistance before transfer / total</th><th>Explanation (ungraded)</th></tr></thead><tbody>{records.map((s,i)=><tr key={i}><td>{i+1}</td><td>{s.lesson}</td><td>{s.initialCorrect===null?'Unanswered':`${s.initialCorrect?'Matched':'Revisit'}: ${lessons.find(l=>l.id===s.lesson)!.choices[s.initialAnswer!]}`}</td><td>{s.transferCorrect===null?'Unanswered':`${s.transferCorrect?'Matched':'Revisit'}: ${lessons.find(l=>l.id===s.lesson)!.transferChoices[s.transferAnswer!]}`}</td><td>{s.completionEvidence?.hints ?? 'Unknown'} / {s.hints}</td><td>{s.reflection}</td></tr>)}</tbody></table></div><button className="button" onClick={()=>download('countertrace-group-notes.md',records.map(sessionReport).join('\n\n---\n\n'))}>Download group notes</button><button className="button" onClick={()=>setRecords([])}>Clear imported records</button></>}
    </section><section className="learning-footnote"><div><h2>What this can establish</h2><p>Observe whether a learner can name a violated rule, build a useful sequence, and transfer the idea to a new boundary case. Hints and retries matter. This lab has not yet been piloted with learners; no classroom outcomes or preparation-time savings are claimed.</p><p><a href="https://github.com/Jeremiah-Sakuda/countertrace/blob/main/docs/TEACHING.md">Full facilitation guide</a> · <a href="/learning/evidence.zip">Simulation evidence bundle</a> · <a href={href.runs()}>Verification workbench</a></p></div></section>
  </div>;
}
