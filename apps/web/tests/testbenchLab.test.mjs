import assert from 'node:assert/strict';
import test from 'node:test';
import {readFile} from 'node:fs/promises';
import {createServer} from 'vite';
test('testbench lab scores selections from the published audit matrix and fails closed',async()=>{
  const vite=await createServer({server:{middlewareMode:true,hmr:false,ws:false,watch:null}});
  try {
    const m=await vite.ssrLoadModule('/src/lib/testbenchLab.ts');
    const text=await readFile(new URL('../public/learning/audit.json',import.meta.url),'utf8');
    const d=m.parseTestbench(text);
    const all=['empty_flag','full_flag','read_data'];
    // The typical first testbench reproduces the recorded weak-set score.
    const typical=m.score(d,m.typicalFirstTestbench(d));
    assert.equal(typical.caught,3);
    assert.ok(typical.results.filter(r=>!r.caught).every(r=>r.miss.kind==='never_driven'));
    // One directed test catches all six; seeded random traffic does too, with many more edges.
    const one=m.score(d,{options:['simultaneous'],checks:all});
    const random=m.score(d,{options:[m.RANDOM_GROUP],checks:all});
    assert.equal(one.caught,6);assert.equal(random.caught,6);assert.ok(one.edges<random.edges);
    // Checking only the flags misses data-corruption bugs; checking only data misses a lost count. Both say why.
    const flagsOnly=m.score(d,{options:['simultaneous'],checks:['full_flag']});
    assert.equal(flagsOnly.caught,4);
    assert.deepEqual(flagsOnly.results.filter(r=>!r.caught).map(r=>r.miss),[{kind:'not_checked',checks:['read_data']},{kind:'not_checked',checks:['read_data']}]);
    const dataOnly=m.score(d,{options:['write_when_full'],checks:['read_data']});
    assert.ok(dataOnly.results.some(r=>r.bug.id==='count-lost-occupancy'&&r.miss?.kind==='not_checked'&&!r.miss.checks.includes('read_data')));
    // Caught entries name a selected test and check at a real edge.
    for (const r of one.results) {assert.equal(r.caught.test,'simultaneous');assert.ok(all.includes(r.caught.check));assert.ok(Number.isInteger(r.caught.cycle));}
    assert.equal(m.score(d,{options:[],checks:all}).caught,0);
    // Malformed evidence is rejected rather than scored.
    const bad=JSON.parse(text);
    for (const mutate of [x=>x.schema='other',x=>x.faults.pop(),x=>x.faults[0].matrix={nope:{empty_flag:{reset:1}}},x=>x.faults[0].matrix.simultaneous={bogus:{reset:1}},x=>x.tests[0].rows.push('unknown_row'),x=>x.checks=['empty_flag']]) {
      const copy=structuredClone(bad);mutate(copy);assert.throws(()=>m.parseTestbench(JSON.stringify(copy)));
    }
    // Saved notes fail closed.
    const fresh=m.freshTestbenchNotes();
    assert.deepEqual(m.readTestbenchNotes('broken'),fresh);
    assert.deepEqual(m.readTestbenchNotes(JSON.stringify({...fresh,attempts:[{options:['x'],checks:['bogus'],prediction:1,caught:1,edges:2}]})),fresh);
    const notes={...fresh,attempts:[{options:['simultaneous'],checks:all,prediction:4,caught:6,edges:one.edges}],revealed:[],reflection:'Drive both at the boundaries.'};
    assert.deepEqual(m.readTestbenchNotes(JSON.stringify(notes)),notes);
    assert.match(m.testbenchReport(notes),/No measured learning gain/);assert.match(m.testbenchReport(notes),/caught 6 of 6/);
    const {parseHash}=await vite.ssrLoadModule('/src/lib/route.ts');
    assert.deepEqual(parseHash('#/testbench'),{name:'testbench'});
  } finally {await vite.close();}
});
