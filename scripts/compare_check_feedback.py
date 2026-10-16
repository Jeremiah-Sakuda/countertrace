#!/usr/bin/env python3
"""Paired recovery experiment on two already-public failed proposals (not holdouts).

Freeze before execution. Exactly one structured revision (at most two schema
attempts) per arm. The same original proposal, specification, model and verifier
are supplied to both arms; only the diagnostic text differs. No runtime changes.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
import time
from unittest.mock import patch

from countertrace import model, runner, runs
from countertrace.checks import agent, gate, modules
from countertrace.checks.compile import validate
from countertrace.checks.design import frozen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'evaluation/results/feedback-recovery-v1'
PROTOCOL = OUT / 'protocol.json'
RESULTS = OUT / 'results.json'
SEEDS = {'sync_fifo': 'rec-20261009-154341-che-06ba10', 'debouncer': 'rec-20261009-153159-che-312266'}
CONTROL = 'Your previous properties were rejected. Revise and resubmit the whole set.'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def seed_record(module_id):
    path = ROOT / 'recorded' / SEEDS[module_id] / 'round-0/round.json'
    return json.loads(path.read_text())


def prompt(module_id, arm):
    seed = seed_record(module_id)
    message = seed['feedback'] if arm == 'detailed' else CONTROL
    return f"{agent.describe(modules.load(module_id))}\n\nYour previous properties:\n{json.dumps(seed['properties'])}\n\n{message}"


def configuration():
    cfg = model.config()
    paths = [*ROOT.glob('src/countertrace/**/*.py'), *ROOT.glob('verifier/**/*'),
             *ROOT.glob('fixtures/modules/**/*'), Path(__file__)]
    paths += [modules.load(m).golden_path for m in SEEDS]
    paths += [ROOT / 'recorded' / r / 'round-0/round.json' for r in SEEDS.values()]
    return {'files': {str(p.relative_to(ROOT)): sha(p) for p in sorted(set(paths)) if p.is_file() and '__pycache__' not in p.parts},
            'model_id': cfg['model_id'], 'endpoint': cfg['base_url'], 'input_limit': cfg['input_limit'],
            'output_limit': agent.output_cap(), 'timeout': cfg['timeout'], 'system_prefix': cfg['system_prefix'],
            'thinking_off_tasks': os.environ.get('COUNTERTRACE_THINKING_OFF_TASKS', ''),
            'prices': model.price_for(cfg, cfg['model_id']), 'verifier_digest': runner.verifier_digest()}


def freeze():
    if PROTOCOL.exists():
        raise SystemExit('Protocol already exists; do not overwrite it.')
    cfg = model.config()
    start = model.spend_summary(cfg)['estimated_cost_usd']
    if start is None or model.unavailable_reason(cfg):
        raise SystemExit('Configured model access and estimated prices are required.')
    order = []
    for repeat in range(1, 4):
        for index, module_id in enumerate(SEEDS):
            arms = ['detailed', 'rejection_only'] if (repeat + index) % 2 else ['rejection_only', 'detailed']
            order += [{'module': module_id, 'repeat': repeat, 'arm': arm} for arm in arms]
    save(PROTOCOL, {'schema': 'countertrace-paired-recovery/1', 'frozen_at': runs.now(),
        'source_commit': subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'configuration': configuration(), 'seeds': SEEDS, 'order': order,
        'system': agent.SYSTEM, 'prompts': {m: {a: prompt(m,a) for a in ['detailed','rejection_only']} for m in SEEDS},
        'starting_ledger_usd': start, 'incremental_credit_allowance_usd': 1.5,
        'ledger_stop_usd': min(cfg['spend_limit'] if cfg['spend_limit'] is not None else start+1.5, start+1.5),
        'design': 'Six matched pairs: two known rejected proposals, three repeats. One revision per arm; at most two schema attempts using the shipped client. Alternating arm order. Both arms see the same previous properties. No implementation source is sent to the model.',
        'primary': 'Gate promotion after one revision; report all 6 outcomes per arm and pair discordance.',
        'secondary': 'Gate stage, mutation outcomes, raw model calls/tokens, estimated inference cost and total latency.',
        'limits': 'Selected historical failures, not fresh holdouts or independent fixtures. Only two modules. No model seed control. Conditional recovery pilot, not full-workflow or broad causal reliability evidence. Pricing is estimated; transport failures can have unknown usage.'})
    print(json.dumps({'protocol': str(PROTOCOL.relative_to(ROOT)), 'sha256': sha(PROTOCOL)}))


def execute():
    protocol = json.loads(PROTOCOL.read_text())
    # JSON normalizes tuple prices to a list.
    if json.loads(json.dumps(configuration())) != protocol['configuration']:
        raise SystemExit('Frozen configuration changed.')
    if subprocess.check_output(['git','status','--porcelain','--',str(PROTOCOL),__file__],text=True).strip():
        raise SystemExit('Commit runner and protocol before model calls.')
    os.environ['COUNTERTRACE_DEPLOYMENT_SPEND_LIMIT_USD'] = str(protocol['ledger_stop_usd'])
    image = runner.ensure_image(build=False)
    data = json.loads(RESULTS.read_text()) if RESULTS.exists() else {'protocol_sha256': sha(PROTOCOL), 'started_at': runs.now(), 'seed_replays': {}, 'attempts': []}
    if data['protocol_sha256'] != sha(PROTOCOL):
        raise SystemExit('Results belong to a different protocol.')
    store = runs.RunStore()
    for module_id in SEEDS:
        if module_id in data['seed_replays']:
            if not data['seed_replays'][module_id]['matches']:
                raise SystemExit('Original seed did not reproduce; no inference permitted.')
            continue
        seed = seed_record(module_id)
        actual = gate.run_gate(modules.load(module_id), seed['properties'], runs.data_dir() / 'evaluation/feedback-recovery-v1' / module_id, image, threading.Event())
        data['seed_replays'][module_id] = {'matches': agent.summary(actual) == seed['gate'], 'gate': agent.summary(actual)}
        save(RESULTS, data)
        if not data['seed_replays'][module_id]['matches'] or actual.get('passed'):
            raise SystemExit('Original rejection did not reproduce; no inference permitted.')
    original_chat = model.chat
    for index, item in enumerate(protocol['order']):
        if index < len(data['attempts']):
            if not data['attempts'][index].get('finished_at'):
                data['attempts'][index].update(outcome='interrupted', finished_at=runs.now())
                save(RESULTS,data)
            continue
        if json.loads(json.dumps(configuration())) != protocol['configuration']:
            raise SystemExit('Configuration changed during evaluation.')
        state = store.create_checks(item['module'], max_rounds=2)
        attempt = {**item, 'run_id': state['id'], 'started_at': runs.now(), 'raw_calls': []}
        data['attempts'].append(attempt)
        save(RESULTS,data)
        print(json.dumps({'starting': item, 'run_id': state['id']}),flush=True)
        started = time.monotonic()
        def capture(*args, **kwargs):
            raw = {'system': args[1], 'user': args[2]}
            attempt['raw_calls'].append(raw)
            save(RESULTS,data)
            try:
                content, meta = original_chat(*args, **kwargs)
                raw.update(content=content, meta=meta)
                return content, meta
            except model.ModelError as exc:
                raw.update(error=str(exc), meta=exc.meta)
                raise
            finally:
                save(RESULTS,data)
        module = modules.load(item['module'])
        with patch.object(model,'chat',capture):
            reply = model.guarded(model.structured)(agent.TASK, agent.SYSTEM, protocol['prompts'][item['module']][item['arm']],
                lambda value: validate(value,module), max_tokens=agent.output_cap(), model_id=protocol['configuration']['model_id'])
        record = {'index':1, 'calls':reply.get('calls',[]), 'model_status':reply['status'], 'feedback':None}
        attempt['model_status'] = reply['status']
        if reply['status'] == 'ok':
            props = reply['result']
            result = gate.run_gate(module,props,store.run_dir(state['id'])/'round-1',image,threading.Event())
            record.update(properties=props,gate=agent.summary(result),frozen=frozen(module,props))
            if not result.get('passed'):
                record['feedback'] = agent.feedback(result,module)
            save(store.run_dir(state['id'])/'round-1/round.json',{**record,'gate_full':result})
            attempt.update(gate=record['gate'], outcome='promoted' if result.get('passed') else 'not_promoted')
        else:
            record['detail'] = reply.get('detail')
            attempt.update(outcome=reply['status'], detail=reply.get('detail'))
        seed = seed_record(item['module'])
        shutil.copytree(ROOT/'recorded'/SEEDS[item['module']]/'round-0',store.run_dir(state['id'])/'round-0')
        initial = {k:v for k,v in seed.items() if k != 'gate_full'}
        # The historical call is context, not new experimental consumption.
        initial['calls'] = []
        initial['historical_source'] = SEEDS[item['module']]
        state.update(state='complete',finished_at=runs.now(),image=image,checks={
            'status':attempt['outcome'], 'rounds':[initial,record], 'promoted_round':1 if attempt['outcome']=='promoted' else None},
            evaluation={'protocol_sha256':sha(PROTOCOL), **item})
        store.save(state)
        attempt.update(finished_at=runs.now(),elapsed_s=round(time.monotonic()-started,3),properties=record.get('properties'))
        save(RESULTS,data)
        print(json.dumps({'finished':item,'outcome':attempt['outcome'],'stage':attempt.get('gate',{}).get('stage'),'calls':len(attempt['raw_calls'])}),flush=True)
        if reply['status'] not in ('ok','schema_error'):
            raise SystemExit('Stopped after model service/budget failure; no automatic experiment retry.')
    data['completed_at']=runs.now()
    save(RESULTS,data)


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['freeze','run'])
    args=parser.parse_args()
    freeze() if args.command=='freeze' else execute()
