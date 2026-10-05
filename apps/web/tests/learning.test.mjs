import assert from 'node:assert/strict';
import test from 'node:test';
import {readFile} from 'node:fs/promises';
import {createServer} from 'vite';
import {createElement} from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
test('all browser queue states agree with independent executed evidence; errors never pass', async()=>{
  const vite=await createServer({server:{middlewareMode:true,hmr:false,ws:false,watch:null}});
  try {
    const {evidenceRows,lessons,newSession,sessionReport,validateSession,parseLibrary}=await vite.ssrLoadModule('/src/lib/learning.ts');
    const raw=await readFile(new URL('../public/learning/library.json',import.meta.url),'utf8');
    const library=await parseLibrary(raw);
    const altered=JSON.parse(raw); altered.designs.overflow.nodes.wwwr[3]=17;
    await assert.rejects(()=>parseLibrary(JSON.stringify(altered)),/integrity/);
    assert.throws(()=>validateSession({...newSession('overflow'),transferAnswer:1,completed:new Date().toISOString()}),/progression/);
    assert.throws(()=>validateSession({...newSession('overflow'),recordedCoachingViewed:true}),/progression/);
    for(const id of Object.keys(library.designs)) for(const key of Object.keys(library.designs[id].nodes)) if(key) assert.equal(evidenceRows(library,id,key).length,key.length);
    assert.equal(evidenceRows(library,'overflow','wr').some(r=>r.mismatches.length),false);
    assert.equal(evidenceRows(library,'overflow','wwwr').find(r=>r.mismatches.length).cycle,4);
    assert.equal(evidenceRows(library,'exchange','wwb').find(r=>r.mismatches.length).cycle,3);
    assert.equal(evidenceRows(library,'control','wrwrwr').some(r=>r.mismatches.length),false);
    for(const path of ['', 'q', 'wwwwwww']) assert.throws(()=>evidenceRows(library,'control',path));
    const bad=structuredClone(library); delete bad.designs.control.nodes.w;
    assert.throws(()=>evidenceRows(bad,'control','w'));
    const wrong=structuredClone(library); wrong.designs.control.nodes.w[1]=1;
    assert.throws(()=>evidenceRows(wrong,'control','w'));
    assert.throws(()=>validateSession({...newSession('overflow'),attempts:[{path:42}]}));
    assert.throws(()=>validateSession({...newSession('overflow'),reflection:{}}));
    assert.equal(validateSession({...newSession('overflow'),initialAnswer:1,initialCorrect:true}).initialCorrect,false);
    for(const l of lessons) assert.match(sessionReport(newSession(l.id)),/not a certificate/);
    const {LearnHome,TeachView}=await vite.ssrLoadModule('/src/views/LearnView.tsx');
    assert.match(renderToStaticMarkup(createElement(LearnHome)),/does not execute RTL/);
    assert.match(renderToStaticMarkup(createElement(TeachView)),/not yet been piloted/);
    const {parseHash,href}=await vite.ssrLoadModule('/src/lib/route.ts');
    assert.deepEqual(parseHash('#/'),{name:'learn',id:null});
    assert.deepEqual(parseHash(href.setup()),{name:'setup',exampleId:null});
  } finally {await vite.close();}
});
