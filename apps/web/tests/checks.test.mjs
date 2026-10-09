import assert from 'node:assert/strict';
import test from 'node:test';
import {createServer} from 'vite';

test('check promotion presentation rejects absent, inconsistent, cancelled and unresolved evidence',async()=>{
  const vite=await createServer({server:{middlewareMode:true,hmr:false,ws:false,watch:null}});
  try {
    const {promotedRound,checkOutcome,gateStages}=await vite.ssrLoadModule('/src/lib/checks.ts');
    const good={status:'promoted',promoted_round:1,rounds:[{index:1,properties:{properties:[{id:'reset'}]},gate:{stage:'mutants',passed:true,total:40,killed:18,nonequivalent:20,equivalent:20,invalid:0,unresolved:0,survived:[2,4]}}]};
    assert.equal(promotedRound(good).index,1);
    assert.equal(checkOutcome({state:'complete',checks:good}),'Checks promoted');
    for (const change of [x=>delete x.rounds[0].gate.total,x=>x.rounds[0].gate.unresolved=1,x=>{x.rounds[0].gate.invalid=1;x.rounds[0].gate.equivalent=19;},x=>x.rounds[0].gate.killed=17,x=>x.rounds[0].gate.nonequivalent=0,x=>x.rounds[0].gate.survived=[],x=>x.promoted_round=0,x=>x.rounds[0].properties.properties=[],x=>x.rounds[0].gate.passed=false]) {
      const bad=structuredClone(good);change(bad);assert.equal(promotedRound(bad),null);assert.equal(checkOutcome({state:'complete',checks:bad}),'Promotion evidence incomplete');
    }
    assert.equal(checkOutcome({state:'cancelled',checks:good}),'Cancelled — no promotion');
    assert.equal(checkOutcome({state:'failed',checks:good}),'Run failed — no promotion');
    assert.equal(checkOutcome({state:'running',checks:good}),'Writing and checking');
    assert.ok(gateStages(undefined).every(s=>s.result==='Not established'||s.result==='Not reached'));
    assert.equal(gateStages({stage:'golden',status:'FAIL',passed:false})[1].result,'Counterexample');
    assert.equal(gateStages({stage:'golden',status:'FAIL',passed:false})[2].result,'Not established');
    assert.equal(gateStages({stage:'mutants',passed:true})[2].result,'Reached within the configured horizon');
    assert.equal(gateStages({stage:'vacuity',passed:false})[2].result,'Not reached within the configured horizon');
    const {parseHash,href}=await vite.ssrLoadModule('/src/lib/route.ts');
    assert.deepEqual(parseHash(href.checks('sync_fifo')),{name:'checks',moduleId:'sync_fifo'});
    assert.deepEqual(parseHash('#/checks'),{name:'checks',moduleId:null});
    assert.deepEqual(parseHash('#/repair'),{name:'repair',caseId:null});
  } finally {await vite.close();}
});

test('recorded checks link the real downstream run, disable new execution, and never call unconfirmed evidence a defect',async()=>{
  const vite=await createServer({server:{middlewareMode:true,hmr:false,ws:false,watch:null}});
  try {
    const {createElement}=await import('react');
    const {renderToStaticMarkup}=await import('react-dom/server');
    const {ChecksRunBody,PromotedChecksPanel}=await vite.ssrLoadModule('/src/views/ChecksView.tsx');
    const gate={stage:'mutants',passed:true,total:3,killed:2,nonequivalent:2,equivalent:1,invalid:0,unresolved:0,survived:[]};
    const run={id:'recorded-checks',kind:'checks',module_id:'sync_fifo',state:'complete',recorded:true,checks:{status:'promoted',promoted_round:0,rounds:[{index:0,calls:[],model_status:'ok',properties:{properties:[{id:'reset',when:'$past(rst)',then:'empty',why:'Reset empties the queue.'}]},gate}],demonstration:{hunt_run_id:'recorded-hunt',repair_run_id:'recorded-repair'}}};
    const status={status:'ok',data:{deployment:{mode:'recorded'},verifier:{docker:true,image_built:true},model:{configured:true}}};
    const html=renderToStaticMarkup(createElement(ChecksRunBody,{run,status}));
    assert.match(html,/href="#\/runs\/recorded-hunt"/);assert.match(html,/href="#\/runs\/recorded-repair"/);
    assert.match(html,/<button[^>]*disabled=""[^>]*>[\s\S]*?Run checks on the bundled overflow bug/);
    assert.match(html,/Any invalid or unresolved result blocks promotion/);
    const {Header}=await vite.ssrLoadModule('/src/components/Header.tsx');
    const header=renderToStaticMarkup(createElement(Header,{status,route:{name:'run',id:run.id},run:{kind:'checks'}}));
    assert.match(header,/<a href="#\/" aria-current="page">Write checks<\/a>/);
    assert.doesNotMatch(header,/aria-label="Workbench"/);
    assert.match(html,/Golden proof/);assert.match(html,/Trigger reachability/);assert.match(html,/Mutation challenge/);
    const check={status:'counterexample',source_run:'source',module_id:'sync_fifo',frozen:{},properties:{properties:[]},promotion:gate,confirmation:{status:'unconfirmed',detail:'Replay missing'}};
    const raw=renderToStaticMarkup(createElement(PromotedChecksPanel,{run:{promoted_checks:check}}));
    assert.match(raw,/Counterexample awaiting confirmation/);assert.doesNotMatch(raw,/Defect confirmed by golden replay/);
    check.confirmation.status='confirmed';
    assert.match(renderToStaticMarkup(createElement(PromotedChecksPanel,{run:{promoted_checks:check}})),/Defect confirmed by golden replay/);
  } finally {await vite.close();}
});


test('held-out modules remain reserved with the exploratory start disabled even when the live runtime is ready',async()=>{
  const vite=await createServer({server:{middlewareMode:true,hmr:false,ws:false,watch:null}});
  try {
    const {createElement}=await import('react');
    const {renderToStaticMarkup}=await import('react-dom/server');
    const {ChecksStartAction}=await vite.ssrLoadModule('/src/views/ChecksView.tsx');
    let calls=0;
    const props={module:{split:'heldout'},busy:false,ready:true,onStart:()=>calls++,unavailable:null};
    const html=renderToStaticMarkup(createElement(ChecksStartAction,props));
    assert.match(html,/Reserved for frozen evaluation/);
    assert.match(html,/<button[^>]*disabled=""/);
    assert.doesNotMatch(html,/Ask Nemotron to write checks/);
    // The handler also refuses a programmatic click on the reserved control.
    const tree=ChecksStartAction(props);
    tree.props.children[1].props.onClick();
    assert.equal(calls,0);
    const development={...props,module:{split:'development'}};
    const enabled=renderToStaticMarkup(createElement(ChecksStartAction,development));
    assert.doesNotMatch(enabled,/disabled=""/);
    ChecksStartAction(development).props.children[1].props.onClick();
    assert.equal(calls,1);
  } finally {await vite.close();}
});

test('featured journey requires a complete promoted FIFO with both recorded downstream links',async()=>{
  const vite=await createServer({server:{middlewareMode:true,hmr:false,ws:false,watch:null}});
  try {
    const {createElement}=await import('react');
    const {renderToStaticMarkup}=await import('react-dom/server');
    const {FeaturedJourney}=await vite.ssrLoadModule('/src/views/ChecksView.tsx');
    const run={id:'checks',state:'complete',module_id:'sync_fifo',checks:{status:'promoted',promoted_round:0,rounds:[{index:0,properties:{properties:[{id:'flags'}]},gate:{stage:'mutants',passed:true,total:40,killed:39,nonequivalent:39,equivalent:1,invalid:0,unresolved:0,survived:[]}}],demonstration:{hunt_run_id:'hunt',repair_run_id:'repair'}}};
    const render=x=>renderToStaticMarkup(createElement(FeaturedJourney,{run:x}));
    const html=render(run);
    assert.match(html,/39 \/ 39 faulty variants caught/);
    for(const id of ['checks','hunt','repair'])assert.match(html,new RegExp(`href="#/runs/${id}"`));
    for(const alter of [r=>r.state='failed',r=>r.module_id='debouncer',r=>delete r.checks.demonstration.repair_run_id,r=>r.checks.rounds[0].gate.unresolved=1]) {
      const invalid=structuredClone(run);alter(invalid);assert.equal(render(invalid),'');
    }
  } finally {await vite.close();}
});
