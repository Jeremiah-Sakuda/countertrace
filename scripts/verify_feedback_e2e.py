#!/usr/bin/env python3
"""One synthetic FIFO journey after the paired recovery experiment; real inference/RTL.

Use the first detailed-feedback FIFO promotion, otherwise the first control
promotion, otherwise the existing recorded FIFO promotion (explicitly reported).
The comparison is finished before selection. No tuning or selection by repair result.
"""
import json
import os
from pathlib import Path
import subprocess
import time
from unittest.mock import patch

from countertrace import bundle, model, repair, runs
from countertrace.checks import design
from countertrace.contract import Contract
from countertrace.server import RecordedStore

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'evaluation/results/feedback-recovery-v1'
REPORT = OUT / 'end-to-end.json'
BRIEF = ('An 8-bit synchronous FIFO of depth 4, with active-high synchronous reset. '
         'Reset clears occupancy. Ignore writes when full, even with a simultaneous read; '
         'ignore reads when empty, even with a simultaneous write. In the interior accept '
         'both operations. Return the oldest accepted word after an accepted read. '
         'full and empty exactly reflect occupancy; preserve order across wraparound.')


def save(data):
    tmp=REPORT.with_suffix('.tmp')
    tmp.write_text(json.dumps(data,indent=2)+'\n')
    tmp.replace(REPORT)


def execute():
    if REPORT.exists():
        raise SystemExit('E2E report already exists; preserve it rather than silently rerun.')
    comparison=json.loads((OUT/'results.json').read_text())
    if not comparison.get('completed_at'):
        raise SystemExit('Complete the comparison before selecting the E2E property set.')
    store=runs.RunStore()
    selected=next((a for arm in ['detailed','rejection_only'] for a in comparison['attempts']
                   if a['module']=='sync_fifo' and a['arm']==arm and a['outcome']=='promoted'),None)
    checks=store.load(selected['run_id']) if selected else RecordedStore().load('rec-20261009-154341-che-06ba10')
    cfg=model.config()
    start=model.spend_summary(cfg)['estimated_cost_usd']
    if start is None:
        raise SystemExit('Estimated inference pricing required.')
    os.environ['COUNTERTRACE_DEPLOYMENT_SPEND_LIMIT_USD']=str(min(cfg['spend_limit'] or start+.25,start+.25))
    report={'started_at':runs.now(),'execution_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            'source_checks':checks['id'],'selection':'first promoted FIFO detailed, then control, then historical fallback',
            'historical_fallback':selected is None,'incremental_estimated_allowance_usd':.25,'raw_calls':[],
            'scope':'Synthetic FIFO, WIDTH=8 DEPTH=4. Local isolated Docker. Model proposals never approve a verdict. No public deployment or learner result.'}
    save(report)
    original=model.chat
    def capture(*args,**kwargs):
        raw={'task':args[0],'system':args[1],'user':args[2]}
        report['raw_calls'].append(raw); save(report)
        try:
            content,meta=original(*args,**kwargs)
            raw.update(content=content,meta=meta)
            return content,meta
        except model.ModelError as exc:
            raw.update(error=str(exc),meta=exc.meta)
            raise
        finally: save(report)
    with patch.object(model,'chat',capture):
        report['interpretation']=model.interpret(BRIEF,Contract(depth=4)); save(report)
        print(json.dumps({'interpretation':report['interpretation']['status']}),flush=True)
        # The owner-authorized fixed contract remains authoritative regardless of model advice.
        state=store.create_verification(example_id='showcase-overwrite-when-full',extra={'promoted_checks':design.selected(checks)})
        report['hunt_run_id']=state['id']; save(report)
        store.execute(state['id']); state=store.load(state['id'])
        report['hunt']={'state':state['state'],'verdict':state.get('verdict'),'promoted_checks_status':(state.get('promoted_checks') or {}).get('status'),
                        'golden_replay':(state.get('promoted_checks') or {}).get('replay')}
        save(report); print(json.dumps({'hunt':report['hunt']}),flush=True)
        if state['state']!='complete' or not model.primary_finding(state):
            raise SystemExit('No completed witnessed defect; repair not attempted.')
        explanation=model.explain_run(state,(store.run_dir(state['id'])/'dut.v').read_text())
        state['explanation']=explanation; store.save(state)
        report['explanation']=explanation; save(report)
        state['repair']={'status':'running','attempts':[],'max_attempts':repair.MAX_ATTEMPTS,
                         'started_at':runs.now(),'parent_frozen':state['verification']['frozen']}
        store.save(state)
        repair.run_loop(store,state['id'])
        state=store.load(state['id']); report['repair']=state['repair']; save(report)
        print(json.dumps({'repair':state['repair']['status']}),flush=True)
    bundle_states=[('checks',checks,store if selected else RecordedStore()),('hunt',state,store)]
    for attempt in state['repair']['attempts']:
        if attempt.get('candidate_run_id'):
            bundle_states.append(('candidate',store.load(attempt['candidate_run_id']),store))
    report['bundles']=[]
    for label,entry,source_store in bundle_states:
        archive=bundle.export(source_store,entry['id'])
        item={'kind':label,'run_id':entry['id'],'path':str(archive.relative_to(ROOT)),
              'sha256':bundle.sha256(archive.read_bytes())}
        report['bundles'].append(item); save(report)
        replay=bundle.replay(archive)
        item['replay']=replay; save(report)
        print(json.dumps({'replay':label,'matches':replay.get('matches')}),flush=True)
    report['completed_at']=runs.now(); save(report)


if __name__=='__main__':
    execute()
