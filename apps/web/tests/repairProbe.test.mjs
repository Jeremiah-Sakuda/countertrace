import assert from 'node:assert/strict';
import test from 'node:test';
import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {createServer} from 'vite';
test('probe library covers every casebook candidate, is pinned, and matches the recorded verdicts',async()=>{
  const vite=await createServer({server:{middlewareMode:true,hmr:false,ws:false,watch:null}});
  try {
    const probe=await vite.ssrLoadModule('/src/lib/repairProbe.ts');
    const lab=await vite.ssrLoadModule('/src/lib/repairLab.ts');
    const text=await readFile(new URL('../public/learning/repair-probes.json',import.meta.url),'utf8');
    const lib=await probe.parseProbes(text);
    await assert.rejects(()=>probe.parseProbes(text.replace('"depth":4','"depth":5')));
    for (const c of lab.repairCases) {
      for (const [i,id] of c.candidates.entries()) {
        const design=lib.designs[id];
        assert.ok(design,`${id} missing from the probe library`);
        const source=await readFile(new URL(`../../../recorded/${id}/dut.v`,import.meta.url),'utf8');
        assert.equal(design.source_sha256,createHash('sha256').update(source).digest('hex'),`${id} source changed`);
        const accepted=i===c.candidates.length-1;
        const failing=Object.keys(design.nodes).filter(p=>{const v=design.nodes[p];return v[0]!==v[3]||v[1]!==v[4]||v[2]!==v[5];});
        assert.equal(failing.length===0,accepted,`${id}: probe disagreements must match the recorded verdict`);
        if (!accepted) {
          const shortest=failing.sort((a,b)=>a.length-b.length)[0];
          const {rows,stoppedAt}=probe.probeRows(lib,id,shortest);
          assert.equal(stoppedAt,shortest.length);assert.ok(rows.at(-1).mismatches.length);
          // Actions after the first disagreement are not replayed.
          assert.equal(probe.probeRows(lib,id,(shortest+'wwwwww').slice(0,6)).stoppedAt,shortest.length);
        } else {
          assert.equal(probe.probeRows(lib,id,'wwwwwb').stoppedAt,null);
        }
      }
    }
    assert.throws(()=>probe.probeRows(lib,'rec-unknown','w'));
    assert.throws(()=>probe.probeRows(lib,lab.repairCases[0].candidates[0],'wwwwwww'));
    const tampered=structuredClone(lib);const id=lab.repairCases[3].candidates[0];tampered.designs[id].nodes.w[1]=1;
    assert.throws(()=>probe.probeRows(tampered,id,'w'));
  } finally {await vite.close();}
});
