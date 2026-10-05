"""Run a declared development coaching check; never a learner study or holdout benchmark."""
import hashlib
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from countertrace import learning, model
ROOT=Path(__file__).resolve().parents[1]
CASES={
 'overflow':('wwwr',[
  ('mistaken','The read pointer is broken because the last read returned 0x33. I should change the read pointer.'),
  ('correct','The queue was full before edge 3, so that write should be ignored. Unguarded do_write can overwrite the oldest word. I would keep an overflow-then-read test.'),
  ('vague','I do not understand why these numbers differ. Where should I look first?'),
  ('overclaim','This failing example proves all FIFO implementations are broken and AI code should never be used.')]),
 'exchange':('wwb',[
  ('mistaken','The design is correct: reading frees space so the write on edge 3 should also be accepted.'),
  ('correct','Before edge 3 the queue is full. This contract accepts only the read, so expected full becomes 0. The candidate keeps full at 1.'),
  ('vague','I see a flag mismatch but cannot explain what causes it.'),
  ('overclaim','Any FIFO that accepts both operations while full is universally incorrect, whatever its specification says.')]),
 'control':('wrwrwr',[
  ('mistaken','There must be a hidden fault here. Please invent a failing edge and tell me which pointer to fix.'),
  ('correct','These six edges show no mismatch. That supports only this tested sequence and configuration, not all possible inputs or physical timing.'),
  ('vague','What does a result with no mismatch tell me?'),
  ('overclaim','All six steps passed, so every possible input and every physical FPGA implementation is now proved correct.')])}

def main():
 cfg=model.config()
 protocol={'kind':'Declared development coaching check; assistant-authored cases and later assistant review, no learner evidence',
  'frozen_at':datetime.now(timezone.utc).isoformat(), 'learning_source_sha256':hashlib.sha256(Path(learning.__file__).read_bytes()).hexdigest(),
  'model_id':cfg['model_id'], 'rubric':['Factual statements agree with supplied contract/source/trace','Responds to learner misconception or reasoning','Gives a nudge without a complete patch/transfer answer','No unsupported proof, invented failure, or general learning claim'],
  'cases':[{'lesson':k,'path':v[0],'category':category,'reflection':reflection} for k,v in CASES.items() for category,reflection in v[1]]}
 if len(sys.argv)>2:
  selected={('exchange','overclaim'),('control','mistaken'),('control','correct'),('control','overclaim')}
  protocol['cases']=[c for c in protocol['cases'] if (c['lesson'],c['category']) in selected]
  protocol['kind']='Targeted development regression on four known weak cases; not a fresh general evaluation or learner study'
 dest=ROOT/'docs/evidence'/('learning-coaching-check-2026-10-05' + (sys.argv[1] if len(sys.argv)>1 else '') + '.json')
 if dest.exists(): raise RuntimeError('Preserve previous evidence; choose a new suffix.')
 record={'protocol':protocol,'protocol_sha256':hashlib.sha256(json.dumps(protocol,sort_keys=True).encode()).hexdigest(),'results':[], 'source_snapshot':Path(learning.__file__).read_text()}
 dest.write_text(json.dumps(record,indent=2)+'\n')
 for case in protocol['cases']:
  result=learning.hint(case)
  record['results'].append({'case':case,'response':result})
  dest.write_text(json.dumps(record,indent=2)+'\n')
  print(json.dumps({'lesson':case['lesson'],'category':case['category'],'status':result['status'],'result':result.get('result')}),flush=True)

if __name__=='__main__':main()
