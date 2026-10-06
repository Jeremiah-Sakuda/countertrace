import assert from 'node:assert/strict';
import test from 'node:test';
import {readFile} from 'node:fs/promises';
import {createServer} from 'vite';
test('repair lesson requires real linked, unchanged, complete evidence; saved notes fail closed',async()=>{
  const vite=await createServer({server:{middlewareMode:true,hmr:false,ws:false,watch:null}});
  try {
    const m=await vite.ssrLoadModule('/src/lib/repairLab.ts');
    const read=async id=>JSON.parse(await readFile(new URL(`../../../recorded/${id}/run.json`,import.meta.url),'utf8'));
    const parent=await read(m.repairCase.parent); const candidates=await Promise.all(m.repairCase.candidates.map(read));
    assert.equal(m.validateRepairCase(parent,candidates).attempts.length,2);
    for(const mutate of [c=>c[1].verification.obligations.pop(),c=>delete c[1].verification.integrity,c=>delete c[1].verification.formal_covers.cov_full,c=>c[1].verification.obligations[0].status='unresolved',c=>c[1].verification.frozen.limits.bmc_depth=999,c=>c[1].verification.integrity.push('missing artifact'),c=>c[0].verification.findings=[],c=>c[1].parent_id='another-run',c=>c[1].state='cancelled']) {
      const copy=structuredClone(candidates);mutate(copy);assert.throws(()=>m.validateRepairCase(parent,copy));
    }
    const fresh=m.freshRepairNotes();assert.deepEqual(m.readRepairNotes('broken'),fresh);
    assert.deepEqual(m.readRepairNotes(JSON.stringify({...fresh,revealed:[false,true]})),fresh);
    const notes={...fresh,predictions:['fail','pass'],reasoning:['Fill the queue and inspect empty.','Rerun the frozen comparison.'],revealed:[true,true],reflection:'A read guard left the flag bug.',transfer:'Reverify depth 8.',compared:true};
    assert.deepEqual(m.readRepairNotes(JSON.stringify(notes)),notes);
    assert.match(m.repairNotesReport(notes),/No measured learning gain/);
    assert.match(m.repairNotesReport(notes),/Reverify depth 8/);
    const {parseHash}=await vite.ssrLoadModule('/src/lib/route.ts');
    assert.deepEqual(parseHash('#/'),{name:'home'});assert.deepEqual(parseHash('#/repair'),{name:'repair'});assert.deepEqual(parseHash('#/learn'),{name:'learn',id:null});
  } finally {await vite.close();}
});
