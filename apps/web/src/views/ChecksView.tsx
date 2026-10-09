import evaluation from "../lib/checks-evaluation.json";
import { ArrowRight, FileCode2, LoaderCircle, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { api, bundleUrl, fileUrl } from "../api/client";
import type { CatalogModule, CheckRound, Run, Status } from "../api/types";
import { Callout, Disclosure, ErrorNotice, Loading, Section, TableScroll } from "../components/common";
import { isRecordedDemo, LOCAL_BUILD_URL } from "../components/DeploymentNotice";
import { Badge } from "../components/StatusBadge";
import { checkOutcome, gateStages, promotedRound } from "../lib/checks";
import { formatDateTime } from "../lib/format";
import { useAsync, useDocumentTitle, type AsyncState } from "../lib/hooks";
import { href, navigate } from "../lib/route";

function ModuleSpec({ module }: { module: CatalogModule }) {
  return <div className="checks-spec">
    <p className="eyebrow">What the model receives</p><h2>{module.title}</h2>
    <p className="checks-spec-text">{module.spec}</p>
    <dl className="checks-parameter-list"><div><dt>Clock / reset</dt><dd>{module.clock} / {module.reset}</dd></div><div><dt>Parameter settings</dt><dd>{module.params.map((p,i)=><span key={i}>{Object.entries(p).map(([k,v])=>`${k} = ${v}`).join(", ") || "Fixed configuration"}</span>)}</dd></div></dl>
    <Disclosure summary="Ports and widths"><TableScroll label="Module ports"><table><thead><tr><th>Port</th><th>Direction</th><th>Width</th></tr></thead><tbody><tr><td><code>{module.clock}</code></td><td>Clock input</td><td>1</td></tr>{([['Input',module.inputs],['Output',module.outputs]] as const).flatMap(([direction,ports])=>Object.entries(ports).map(([name,width])=><tr key={name}><td><code>{name}</code></td><td>{direction}</td><td>{width}</td></tr>))}</tbody></table></TableScroll></Disclosure>
    <p className="small muted">The hand-written golden implementation stays outside the model context. Only the specification, ports, settings, and bounded gate feedback are sent.</p>
  </div>;
}

export function ChecksStartAction({module,busy,ready,onStart,unavailable}:{module:CatalogModule;busy:boolean;ready:boolean;onStart:()=>void;unavailable:string|null}) {
  const reserved=module.split==='heldout';
  return <>{reserved&&<Callout kind="warn" title="Reserved for frozen evaluation"><p>This held-out module is not available for exploratory check writing. Choose a development module to keep the frozen evaluation separate.</p></Callout>}
    <button className="btn btn-primary" onClick={()=>{if(!reserved&&ready&&!busy)onStart();}} disabled={reserved||!ready||busy}>{busy?<LoaderCircle className="spin" size={16} aria-hidden="true"/>:<FileCode2 size={16} aria-hidden="true"/>}{reserved?'Reserved for frozen evaluation':busy?'Starting run…':'Ask Nemotron to write checks'}</button>
    {!reserved&&unavailable&&<p className="small muted">{unavailable}</p>}</>;
}

function ModuleCards({modules}:{modules:CatalogModule[]}) {
  return <div className="checks-catalog-grid">{modules.map((m,i)=><a href={href.checks(m.id)} className="checks-module-card" key={m.id}><span className="eyebrow">{String(i+1).padStart(2,'0')} / {m.split==='heldout'?'Reserved for frozen evaluation':'Development'}</span><h3>{m.title}</h3><p>{m.spec.split('\n')[0]}</p><span className="checks-module-meta">{Object.keys(m.inputs).length} inputs · {Object.keys(m.outputs).length} outputs · {m.params.length} settings</span><span className="checks-module-link">Read specification <ArrowRight size={16} aria-hidden="true"/></span></a>)}</div>;
}

export function FeaturedJourney({run}:{run:Run}) {
  const round=promotedRound(run.checks), demo=run.checks?.demonstration;
  if(run.state!=='complete'||run.module_id!=='sync_fifo'||!round||!demo?.hunt_run_id||!demo.repair_run_id)return null;
  return <Section title="Follow one check set all the way." eyebrow="Start here · the complete FIFO case">
    <p>Nemotron wrote the checks. They caught a real seeded defect. A repair then faced the same frozen checks. Open each step and inspect what actually ran.</p>
    <ol className="checks-journey">
      <li><a href={href.run(run.id)}><span className="eyebrow">01 / Write &amp; challenge</span><strong>{round.gate?.killed} / {round.gate?.nonequivalent} faulty variants caught</strong><span>Inspect generated checks <ArrowRight size={16} aria-hidden="true"/></span></a></li>
      <li><a href={href.run(demo.hunt_run_id)}><span className="eyebrow">02 / Find &amp; confirm</span><strong>Replay the overflowing queue</strong><span>Inspect the bug hunt <ArrowRight size={16} aria-hidden="true"/></span></a></li>
      <li><a href={href.run(demo.repair_run_id)}><span className="eyebrow">03 / Repair &amp; recheck</span><strong>A patch, unchanged checks</strong><span>Inspect the repair <ArrowRight size={16} aria-hidden="true"/></span></a></li>
    </ol><p className="small muted">One recorded development case, not a benchmark. Mutation counts apply to the recorded primary setting; golden proof covers both listed settings.</p>
  </Section>;
}

function EvaluationEvidence() {
  return <Section title="Beyond the showcase." eyebrow="Frozen evaluation · October 9">
    <p><strong>{evaluation.promoted} of {evaluation.attempts} attempts promoted</strong> across four held-out modules, three runs each. {evaluation.first_round} passed in their first gate round, including {evaluation.schema_retries} that needed a schema retry. {evaluation.first_response} succeeded from the first model response. The full results retain every attempted round.</p>
    <TableScroll label="Held-out check-generation results"><table><thead><tr><th>Module</th><th>Promoted</th><th>Rounds by run</th></tr></thead><tbody>{evaluation.modules.map(m=><tr key={m.module}><th scope="row">{m.title}</th><td>{m.promoted} / {m.attempts}</td><td>{m.rounds.join(' / ')}</td></tr>)}</tbody></table></TableScroll>
    <p>The first debouncer proposal failed on the golden reference. After the gate returned a counterexample, Nemotron corrected its shadow counter and passed in round two.</p>
    <div className="actions"><a className="btn btn-secondary" href={href.run(evaluation.feedback_recording)}>Inspect the rejected check and revision <ArrowRight size={16} aria-hidden="true"/></a><a href="https://github.com/Jeremiah-Sakuda/countertrace/blob/main/evaluation/results/checks-v1/REPORT.md">Read all twelve attempts</a></div>
    <p className="small muted">{evaluation.scope} The goldens were not independently reviewed. A passing mutation score is not a guarantee about arbitrary designs.</p>
  </Section>;
}

export function ChecksHome({moduleId,status}:{moduleId:string|null;status:AsyncState<Status>}) {
  useDocumentTitle(moduleId ? "Write checks" : "Who checks the checks?");
  const catalog=useAsync(()=>api.modules(),[]);
  const recordings=useAsync(async()=>{const list=await api.recorded();return Promise.all(list.filter(r=>r.kind==='checks').map(r=>api.run(r.id)));},[]);
  const [busy,setBusy]=useState(false),[error,setError]=useState<unknown>(null);
  const selected=catalog.status==='ok'&&moduleId?catalog.data.find(m=>m.id===moduleId):null;
  const recorded=isRecordedDemo(status);
  const ready=status.status==='ok'&&!recorded&&status.data.model.configured&&status.data.verifier.docker&&status.data.verifier.image_built;
  const unavailable=status.status!=='ok'?'Runtime status is unavailable.':recorded?'This edition replays recorded evidence. New model calls and verifier jobs run in the local test build.':!status.data.model.configured?'Configure Nebius model access on this server to write checks.':!status.data.verifier.docker||!status.data.verifier.image_built?'The isolated verifier must be ready before starting.':null;
  const start=async()=>{if(!selected||selected.split!=='development'||busy||!ready)return;setBusy(true);setError(null);try{const run=await api.createChecks(selected.id);navigate(href.run(run.id));}catch(e){setError(e);}finally{setBusy(false);}};
  const visibleRecordings=recordings.status==='ok'?recordings.data.filter(r=>!moduleId||r.module_id===moduleId).sort((a,b)=>b.created_at.localeCompare(a.created_at)):[];
  const featured=visibleRecordings.find(r=>r.module_id==='sync_fifo'&&r.state==='complete'&&promotedRound(r.checks)&&r.checks?.demonstration?.hunt_run_id&&r.checks?.demonstration?.repair_run_id);
  return <div className="checks-view stack-lg">
    {!moduleId ? <>
      <div className="studio-masthead"><span>COUNTERTRACE / MODEL-WRITTEN CHECKS</span><span>{recorded?'RECORDED EDITION':'CATALOG WORKBENCH'}</span></div>
      <section className="checks-hero" aria-labelledby="checks-title"><div><p className="eyebrow">NVIDIA Nemotron × Nebius</p><h1 id="checks-title">Who checks<br/><em>the checks?</em></h1><p className="checks-lede">An AI can write an assertion.<br/>Making it earn your trust is the interesting part.</p><p>Give Nemotron a hardware specification. Watch it write properties, face an independent golden-reference gate, and revise them when the evidence disagrees.</p><div className="actions">{featured&&<a className="btn btn-primary" href={href.run(featured.id)}>Follow the complete FIFO case <ArrowRight size={16} aria-hidden="true"/></a>}<button className="btn btn-ghost" onClick={()=>document.getElementById("catalog-title")?.focus()}>Explore specifications</button></div><p className="small muted">Bundled synchronous modules. No uploads. Every conclusion stays attached to its evidence.</p></div>
      <aside className="checks-exhibit" aria-label="How a check earns promotion"><span className="specimen-label">THE CHECKER IS UNDER TEST <ShieldCheck size={20} aria-hidden="true"/></span><ol><li><b>01</b><div><strong>Does it hold on the golden?</strong><p>Prove the properties at the listed parameter settings.</p></div></li><li><b>02</b><div><strong>Is its trigger witnessed?</strong><p>Each trigger must be reached within the configured horizon.</p></div></li><li><b>03</b><div><strong>Does it catch broken variants?</strong><p>Count kills, survivors, equivalents, invalids, and unresolved evidence.</p></div></li></ol><p className="checks-exhibit-foot">The model proposes. The verifier decides.</p></aside></section>
    </>:<p><a href={href.checks()}>← Module catalog</a></p>}
    {recorded&&<Callout title="Recorded evidence, not live inference"><p>Explore actual preserved calls and tool results below. To start a fresh run, use the <a href={LOCAL_BUILD_URL}>local test build</a> with configured Nebius access and Docker.</p></Callout>}
    {!moduleId&&featured&&<FeaturedJourney run={featured}/>}
    {catalog.status==='loading'?<Loading label="Loading module catalog"/>:catalog.status==='error'?<ErrorNotice error={catalog.error} title="Module catalog unavailable" onRetry={catalog.reload}/>:selected?<div className="checks-module-layout"><ModuleSpec module={selected}/><aside className="checks-start"><p className="eyebrow">A bounded agent loop</p><h2>Write. Challenge.<br/>Revise.</h2><p>Up to four rounds. Compiler errors, counterexamples, triggers not reached within the configured horizon, and surviving variants guide the next proposal.</p><p className="small">Requests send this public specification to Nebius. The isolated RTL verifier has no model credentials or network access.</p><ChecksStartAction module={selected} ready={ready} busy={busy} onStart={start} unavailable={unavailable}/>{error?<ErrorNotice error={error} title="Could not start check writing"/>:null}</aside></div>:moduleId?<Callout kind="warn" title="Module not found"><p>This module is not in the public catalog. <a href={href.checks()}>Choose an available module.</a></p></Callout>:<section id="checks-catalog" className="checks-catalog" aria-labelledby="catalog-title"><div className="checks-section-title"><div><p className="eyebrow">Start from a specification</p><h2 id="catalog-title" tabIndex={-1}>The module catalog</h2></div><p>Catalog coverage is not model success. Each run below reports its own result.</p></div><ModuleCards modules={catalog.data.filter(m=>m.split==='development').sort((a,b)=>Number(b.id==='sync_fifo')-Number(a.id==='sync_fifo'))}/><Disclosure summary="Four modules reserved for evaluation"><p className="small muted">These specifications are held separate from exploratory model development. They are gate-only; the complete bug-hunt and repair journey currently supports the FIFO.</p><ModuleCards modules={catalog.data.filter(m=>m.split==='heldout')}/></Disclosure></section>}
    {!moduleId&&<EvaluationEvidence/>}
    <section aria-labelledby="recorded-checks-title"><div className="checks-section-title"><div><p className="eyebrow">Inspect the agent's actual work</p><h2 id="recorded-checks-title">Recorded check-writing runs</h2></div><p>Preserved outcomes, including failed rounds. Playback does not make a new model call.</p></div>{recordings.status==='loading'?<Loading label="Loading recorded check runs"/>:recordings.status==='error'?<ErrorNotice error={recordings.error} title="Recorded runs unavailable" onRetry={recordings.reload}/>:visibleRecordings.length?<div className="checks-recordings">{visibleRecordings.map(r=><a className="checks-recording" href={href.run(r.id)} key={r.id}><span><strong>{r.module?.title??r.title}</strong><small>{r.checks?.rounds.length??0} rounds · {formatDateTime(r.created_at)}</small></span><span>{checkOutcome(r)} <ArrowRight size={16} aria-hidden="true"/></span></a>)}</div>:<p className="muted">No recorded check-writing run is published{selected?` for ${selected.title}`:''} in this edition. The <a href="#/repair">repair lab</a> contains separately recorded model repairs.</p>}</section>
    {!moduleId&&<div className="studio-directions"><a href="#/repair"><span className="eyebrow">Use it to learn</span><h2>Challenge a repair.</h2><p>Predict whether a real Nemotron patch will work, probe it, then inspect the independent result.</p><span>Open the repair lab <ArrowRight size={16} aria-hidden="true"/></span></a><a href={href.setup()}><span className="eyebrow">The FIFO workbench</span><h2>Follow a counterexample.</h2><p>Inspect reference checks, signal traces, explanations, and repairs under an unchanged contract.</p><span>Open the workbench <ArrowRight size={16} aria-hidden="true"/></span></a></div>}
  </div>;
}

function RoundEvidence({round}:{round:CheckRound}) {
  const g=round.gate;
  return <div className="checks-round-content"><ol className="checks-stage-list">{gateStages(g).map(s=><li key={s.label}><strong>{s.label}</strong><span>{s.result}</span></li>)}</ol>
    {g?.error&&<Callout kind="error" title="Gate feedback"><p>{g.error}</p></Callout>}{round.detail&&<p>{round.detail}</p>}
    {g?.config&&<p className="small">Reported configuration: {Object.entries(g.config.params).map(([k,v])=>`${k} = ${v}`).join(', ')}</p>}
    {g?.stage==='mutants'&&<><dl className="checks-counts">{[['Killed',g.killed],['Non-equivalent',g.nonequivalent],['Survived',g.survived?.length],['Equivalent',g.equivalent],['Invalid',g.invalid],['Unresolved',g.unresolved],['Total variants',g.total]].map(([label,value])=><div key={label}><dt>{label}</dt><dd>{value??'Not recorded'}</dd></div>)}</dl><p className="small muted">Promotion requires at least 90% of non-equivalent mutants killed. Equivalent mutants are excluded from the denominator. Any invalid or unresolved result blocks promotion. This is a finite mutation challenge, not a guarantee of completeness.</p></>}
    {g?.failed?.length?<p>Failing properties: <code>{g.failed.join(', ')}</code></p>:null}{g?.unreached?.length?<p>Triggers not reached within the configured horizon: <code>{g.unreached.join(', ')}</code></p>:null}
    {round.properties&&<Disclosure summary={`${round.properties.properties.length} model-written properties`}><div className="checks-properties">{round.properties.properties.map(p=><article key={p.id}><h3>{p.id}</h3><p>{p.why}</p><dl><div><dt>When</dt><dd><code>{p.when}</code></dd></div><div><dt>Must hold</dt><dd><code>{p.then}</code></dd></div></dl></article>)}</div><Disclosure summary="Full structured proposal, including shadow state"><pre className="checks-code">{JSON.stringify(round.properties,null,2)}</pre></Disclosure></Disclosure>}
    {round.feedback&&<p className="small">This round returned feedback to Nemotron. Open the exact message below to inspect the counterexample or diagnostic.</p>}{round.feedback&&<Disclosure summary="Exact feedback for the next round"><pre className="checks-code checks-feedback">{round.feedback}</pre></Disclosure>}
    <Disclosure summary="Model call provenance">{round.calls.length?<div className="checks-call-list">{round.calls.map((c,i)=><dl key={i}><div><dt>Model</dt><dd>{c.model_id??'Not recorded'}</dd></div><div><dt>Provider endpoint</dt><dd>{c.endpoint_host??'Not recorded'}</dd></div><div><dt>Call status</dt><dd>{c.status}</dd></div><div><dt>Duration / tokens</dt><dd>{c.latency_ms==null?'Unknown duration':`${(c.latency_ms/1000).toFixed(1)} s`} · {c.prompt_tokens??'?'} input / {c.completion_tokens??'?'} output</dd></div></dl>)}</div>:<p>No call metadata was preserved for this round.</p>}</Disclosure>
  </div>;
}

function HuntNext({run,status}:{run:Run;status:AsyncState<Status>}) {
  const [busy,setBusy]=useState(false),[error,setError]=useState<unknown>(null);
  const example="showcase-overwrite-when-full";
  const supported=run.module_id==='sync_fifo';
  const ready=status.status==='ok'&&!isRecordedDemo(status)&&status.data.verifier.docker&&status.data.verifier.image_built;
  const demonstration=run.checks?.demonstration;
  const hunt=async()=>{if(!ready||busy)return;setBusy(true);setError(null);try{const result=await api.hunt(run.id,example);navigate(href.run(result.id));}catch(e){setError(e);}finally{setBusy(false);}};
  return <Section title="Put the promoted checks to work" eyebrow="Next: a confirmed bug, then a repair"><p>The FIFO demonstration runs this exact check set on a bundled faulty design. A failing property counts as a defect only after the same inputs are replayed against the independent golden reference. The repair must face the same frozen checks.</p>
    {demonstration?.hunt_run_id&&<div className="actions"><a className="btn btn-primary" href={href.run(demonstration.hunt_run_id)}>Open recorded bug hunt <ArrowRight size={16} aria-hidden="true"/></a>{demonstration.repair_run_id&&<a className="btn btn-secondary" href={href.run(demonstration.repair_run_id)}>Inspect recorded repair</a>}</div>}
    {supported?<><button className="btn btn-secondary" disabled={!ready||busy} onClick={hunt}>{busy?<LoaderCircle className="spin" size={16} aria-hidden="true"/>:<ShieldCheck size={16} aria-hidden="true"/>}{busy?'Starting verification…':'Run checks on the bundled overflow bug'}</button>{!ready&&<p className="small muted">Starting a new hunt requires the local test build and its isolated verifier. Recorded evidence above can be opened without making a new call.</p>}</>:<p className="small muted">The downstream demonstration currently supports the FIFO. Other catalog modules stop at check-set promotion.</p>}
    {error?<ErrorNotice error={error} title="Could not start the bug hunt"/>:null}</Section>;
}

export function PromotedChecksPanel({run}:{run:Run}) {
  const check=run.promoted_checks;
  if(!check)return null;
  const confirmed=check.status==='counterexample'&&check.confirmation?.status==='confirmed';
  const headline=confirmed?'Defect confirmed by golden replay':check.status==='counterexample'?'Counterexample awaiting confirmation':check.status==='proved'?'Promoted properties proved on this design':'Promoted checks remain unresolved';
  return <Section title={headline} eyebrow="Model-written checks · independent result"><p>{check.detail}</p><p className="small">{confirmed?'The candidate and golden were given the same failing inputs; replay confirmed a design defect.':check.status==='proved'?'This result covers the frozen promoted property set and stated configuration. It does not establish arbitrary behavior or all-parameter correctness.':'A raw property failure alone is not counted as a confirmed design defect.'}</p>
    <p><a href={href.run(check.source_run)}>Inspect the check-writing run and promotion gate →</a></p>
    {!!check.failed?.length&&<p>Failing properties: <code>{check.failed.join(', ')}</code></p>}
    {check.confirmation&&<Callout kind={confirmed?'info':'warn'} title={`Golden replay: ${check.confirmation.status}`}><p>{check.confirmation.detail}</p></Callout>}
    {!!check.trace?.length&&<Disclosure summary="Counterexample values before each edge" defaultOpen><TableScroll label="Promoted property counterexample"><table><thead><tr><th>Step</th><th>Inputs</th><th>Candidate outputs</th></tr></thead><tbody>{check.trace.map((row,i)=><tr key={i}><td>{row.step??i}</td><td><code>{Object.entries(row.inputs??{}).map(([k,v])=>`${k}=${v??'unknown'}`).join(' · ')}</code></td><td><code>{Object.entries(row.outputs??{}).map(([k,v])=>`${k}=${v??'unknown'}`).join(' · ')}</code></td></tr>)}</tbody></table></TableScroll></Disclosure>}
    <Disclosure summary="Frozen comparison metadata"><pre className="checks-code">{JSON.stringify(check.frozen,null,2)}</pre><p className="small muted">Every repair candidate must rerun this same property set and configuration. A changed comparison cannot authorize an accepted repair.</p></Disclosure>
  </Section>;
}

export function ChecksRunBody({run,status}:{run:Run;status:AsyncState<Status>}) {
  const checks=run.checks, promoted=run.state==='complete'?promotedRound(checks):null;
  return <div className="stack-lg checks-view">{checks?.review_note&&<Callout kind="warn" title="Later transfer audit"><p>{checks.review_note}</p></Callout>}<Section title={checkOutcome(run)} eyebrow={run.recorded?'Recorded agent run':'Agent run'}><p>{promoted?`Round ${promoted.index+1} passed the independent gate for the recorded settings. These checks can now be used to look for defects; a failure still needs confirmation against the golden.`:'No promoted check set is established yet. Errors, cancellations, missing evidence, and unfinished checks remain visible.'}</p>{checks?.detail&&<p>{checks.detail}</p>}{checks?.status==='promoted'&&!promoted&&<Callout kind="warn" title="Cannot display promotion"><p>The result does not contain a complete, consistent promotion record. Inspect the raw evidence; no success is inferred.</p></Callout>}<p className="small muted">Golden proof applies to the listed settings. Triggers must be reached within the configured horizon; a missing witness does not establish impossibility. Mutants are tested at the primary setting. The model never decides these outcomes.</p></Section>
    {run.module&&<Disclosure summary={`Specification: ${run.module.title}`}><ModuleSpec module={run.module}/></Disclosure>}
    <section aria-labelledby="rounds-title"><div className="checks-section-title"><div><p className="eyebrow">The bounded feedback loop</p><h2 id="rounds-title">Every proposal. Every outcome.</h2></div><p>{checks?.rounds.length??0} recorded rounds{run.max_rounds?` / ${run.max_rounds} maximum`:''}</p></div>{checks?.rounds.length?checks.rounds.map(round=><article className="checks-round" key={round.index}><header><span className="checks-round-number">{String(round.index+1).padStart(2,'0')}</span><div><h3>Round {round.index+1}</h3><p>{round.gate?.passed?'Gate threshold met':round.gate?`Stopped at ${round.gate.stage}`:`Model status: ${round.model_status}`}</p></div>{round.index===promoted?.index&&<Badge tone="proved" icon={ShieldCheck}>Promoted set</Badge>}</header><RoundEvidence round={round}/></article>):(run.state==='running'||run.state==='queued'?<Loading label="Waiting for the first completed round"/>:<p className="muted">No completed rounds were recorded.</p>)}</section>
    {checks?.secondary_audit&&<Section title="A second depth, the same properties" eyebrow="Separate transfer audit"><p>The generated property set was also tested at {checks.secondary_audit.params.map(p=>Object.entries(p).map(([k,v])=>`${k} = ${v}`).join(', ')).join('; ')} without another model call. This follow-up is separate from the primary-setting promotion result above.</p><dl className="checks-counts">{[['Killed',checks.secondary_audit.gate.killed],['Non-equivalent',checks.secondary_audit.gate.nonequivalent],['Equivalent',checks.secondary_audit.gate.equivalent],['Invalid',checks.secondary_audit.gate.invalid],['Unresolved',checks.secondary_audit.gate.unresolved]].map(([label,value])=><div key={label}><dt>{label}</dt><dd>{value??'Not recorded'}</dd></div>)}</dl>{checks.secondary_audit.gate.error&&<p>{checks.secondary_audit.gate.error}</p>}<p className="small muted">These counts describe separate mutation sets at two specific depths. They do not establish all-parameter correctness. <a href="https://github.com/Jeremiah-Sakuda/countertrace/blob/main/evaluation/results/checks-transfer/REPORT.md">Read the original audit failure and correction.</a></p></Section>}
    {promoted&&<HuntNext run={run} status={status}/>}
    <Section title="Preserved evidence" eyebrow="Reproduce and inspect"><p>Read the complete run record and export the preserved tool artifacts. Model output and independent gate results are kept separately.</p><div className="actions"><a className="btn btn-secondary" href={fileUrl(run.id,'run.json')} target="_blank" rel="noreferrer">Run JSON</a><a className="btn btn-ghost" href={bundleUrl(run.id)}>Download evidence bundle</a><a className="btn btn-ghost" href={href.checks(run.module_id)}>Back to this specification</a></div></Section>
  </div>;
}
