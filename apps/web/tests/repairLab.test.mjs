import assert from 'node:assert/strict';
import test from 'node:test';
import {readFile} from 'node:fs/promises';
import {createServer} from 'vite';
test('every repair case requires real linked, unchanged, complete evidence; saved notes fail closed',async()=>{
  const vite=await createServer({server:{middlewareMode:true,hmr:false,ws:false,watch:null}});
  try {
    const m=await vite.ssrLoadModule('/src/lib/repairLab.ts');
    const read=async id=>JSON.parse(await readFile(new URL(`../../../recorded/${id}/run.json`,import.meta.url),'utf8'));
    assert.ok(m.repairCases.length>=4);
    assert.equal(new Set(m.repairCases.map(c=>c.id)).size,m.repairCases.length);
    for (const c of m.repairCases) {
      const n=c.candidates.length;
      for (const field of ['headings','prompts','afterReveal']) assert.equal(c[field].length,n,`${c.id} ${field}`);
      const parent=await read(c.parent); const candidates=await Promise.all(c.candidates.map(read));
      assert.equal(m.validateRepairCase(c,parent,candidates).attempts.length,n,c.id);
      const last=n-1;
      const mutations=[x=>x[last].verification.obligations.pop(),x=>delete x[last].verification.integrity,x=>delete x[last].verification.formal_covers.cov_full,
        x=>x[last].verification.obligations[0].status='unresolved',x=>x[last].verification.frozen.limits.bmc_depth=999,x=>x[last].verification.integrity.push('missing artifact'),
        x=>x[last].parent_id='another-run',x=>x[last].state='cancelled'];
      if (n>1) mutations.push(x=>x[0].verification.findings=[],x=>x[0].verification.frozen.stimulus_version='other');
      for (const mutate of mutations) {const copy=structuredClone(candidates);mutate(copy);assert.throws(()=>m.validateRepairCase(c,parent,copy),undefined,c.id);}
      assert.throws(()=>m.validateRepairCase(c,parent,candidates.slice(0,last)));
      assert.throws(()=>m.validateRepairCase(m.repairCases.find(o=>o.id!==c.id),parent,candidates));
      // Rejected candidates must state what the counterexample shows; the accepted one must not.
      c.afterReveal.forEach((t,i)=>assert.equal(Boolean(t.trim()),i<last,`${c.id} afterReveal ${i}`));
      const fresh=m.freshRepairNotes(c);assert.deepEqual(m.readRepairNotes('broken',c),fresh);
      const skipped={...fresh,revealed:fresh.revealed.map((_,i)=>i===last)};
      if (n>1) assert.deepEqual(m.readRepairNotes(JSON.stringify(skipped),c),fresh);
      const done={...fresh,predictions:fresh.predictions.map((_,i)=>i<last?'fail':'pass'),reasoning:fresh.reasoning.map(()=>'Fill the queue and inspect empty.'),
        revealed:fresh.revealed.map(()=>true),reflection:'The counterexample moved.',transfer:'Reverify depth 8.',compared:true};
      assert.deepEqual(m.readRepairNotes(JSON.stringify(done),c),done);
      assert.deepEqual(m.readRepairNotes(JSON.stringify({...done,caseId:'other'}),c),fresh);
      const report=m.repairNotesReport(c,done);
      assert.match(report,/No measured learning gain/);assert.match(report,/Reverify depth 8/);assert.match(report,new RegExp(c.parent));
    }
    // Notes saved by the earlier single-case lab still load for the first case only.
    const first=m.repairCases[0];
    const legacy={schema:'countertrace-repair-practice-v1',predictions:['fail','pass'],reasoning:['a','b'],revealed:[true,true],reflection:'r',transfer:'t',compared:true};
    assert.deepEqual(m.readRepairNotes(JSON.stringify(legacy),first).predictions,['fail','pass']);
    assert.deepEqual(m.readRepairNotes(JSON.stringify(legacy),m.repairCases[1]),m.freshRepairNotes(m.repairCases[1]));
    assert.equal(m.caseById('missing').id,first.id);
    const {parseHash,href}=await vite.ssrLoadModule('/src/lib/route.ts');
    assert.deepEqual(parseHash('#/'),{name:'home'});assert.deepEqual(parseHash('#/repair'),{name:'repair',caseId:null});
    assert.deepEqual(parseHash(href.repair('reset')),{name:'repair',caseId:'reset'});assert.deepEqual(parseHash('#/learn'),{name:'learn',id:null});
  } finally {await vite.close();}
});
