#!/usr/bin/env python3
"""Freeze and run the held-out check-generation protocol without prompt tuning.

Run --freeze first, commit the freeze and this runner, then --run. Model/RTL
artifacts stay in the private RunStore; the public result preserves every attempt.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from countertrace import model, runner, runs
from countertrace.checks import agent, gate, modules

ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / '.countertrace/evaluation/checks-v1-freeze.json'
COMMITMENT = ROOT / 'evaluation/checks-v1-commitment.json'
RESULTS = ROOT / 'evaluation/results/checks-v1/results.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def configuration():
    cfg = model.config()
    paths = [*ROOT.glob('src/countertrace/**/*.py'), *ROOT.glob('verifier/**/*'),
             *ROOT.glob('fixtures/modules/**/*'), ROOT / 'scripts/evaluate_checks.py']
    files = {str(p.relative_to(ROOT)): digest(p) for p in sorted(paths)
             if p.is_file() and '__pycache__' not in p.parts}
    # Include fixture dependencies outside modules/ without showing golden code.
    for m in modules.catalog():
        files[str(m.golden_path.relative_to(ROOT))] = digest(m.golden_path)
    return {'files': files, 'model_id': cfg['model_id'], 'endpoint': cfg['base_url'],
            'input_limit': cfg['input_limit'], 'checks_output_limit': agent.output_cap(),
            'model_timeout_s': cfg['timeout'], 'system_prefix': cfg['system_prefix'],
            'thinking_off_tasks': os.environ.get('COUNTERTRACE_THINKING_OFF_TASKS', ''),
            'mutants': gate.MUTANTS, 'limits': gate.LIMITS, 'max_rounds': agent.MAX_ROUNDS,
            'threshold': gate.PROMOTION_KILL_RATE, 'verifier_digest': runner.verifier_digest()}


def freeze():
    if FREEZE.exists():
        raise SystemExit('Freeze exists; never overwrite a running or completed evaluation.')
    suite = [m.id for m in modules.catalog() if m.split == 'heldout']
    assert len(suite) == 4
    data = {'schema': 'countertrace-checks-evaluation/1', 'frozen_at': runs.now(),
            'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
            'configuration': configuration(), 'modules': suite, 'repeats': 3,
            'order': [{'module': m, 'repeat': r} for r in range(1, 4) for m in suite],
            'scoring': {'primary': 'Promoted within four rounds; show all 12 attempts.',
                        'target': 'At least three of four modules promote; separately show modules promoting in all three repeats.',
                        'mutation_scope': 'Primary parameter setting only; golden proof and trigger reachability use both settings.',
                        'feedback': 'Normal shipped feedback only; no prompt or fixture edits between attempts.',
                        'limits': 'No causal feedback-benefit claim without a matched control. No general accuracy claim.',
                        'provenance': 'Assistant-authored catalog goldens/specifications; held out of model/prompt development, not independently authored or externally reviewed.'}}
    FREEZE.parent.mkdir(parents=True, exist_ok=True)
    FREEZE.write_text(json.dumps(data, indent=2) + '\n')
    COMMITMENT.write_text(json.dumps({'schema': data['schema'], 'frozen_at': data['frozen_at'],
        'protocol_sha256': digest(FREEZE), 'module_count': 4, 'repeats': 3, 'max_rounds': 4,
        'note': 'Complete protocol and held-out identities retained privately until evaluation ends.'}, indent=2) + '\n')
    print(FREEZE)


def execute():
    frozen = json.loads(FREEZE.read_text())
    if json.loads(COMMITMENT.read_text())['protocol_sha256'] != digest(FREEZE):
        raise SystemExit('Private protocol differs from the public commitment.')
    if configuration() != frozen['configuration']:
        raise SystemExit('Frozen configuration changed; do not continue this evaluation.')
    if subprocess.check_output(['git', 'status', '--porcelain', '--', str(COMMITMENT), __file__], text=True).strip():
        raise SystemExit('Commit the protocol and runner before execution.')
    cfg = model.config()
    if model.unavailable_reason(cfg):
        raise SystemExit(model.unavailable_reason(cfg))
    runner.ensure_image(build=False)
    data = json.loads(RESULTS.read_text()) if RESULTS.exists() else {
        'freeze_sha256': digest(FREEZE), 'execution_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        'started_at': runs.now(), 'attempts': []}
    if data['freeze_sha256'] != digest(FREEZE):
        raise SystemExit('Results belong to a different protocol.')
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    def save():
        temporary = RESULTS.with_suffix('.tmp')
        temporary.write_text(json.dumps(data, indent=2) + '\n')
        temporary.replace(RESULTS)
    store = runs.RunStore()
    for index, item in enumerate(frozen['order']):
        if configuration() != frozen['configuration']:
            raise SystemExit('Frozen configuration changed during evaluation.')
        if index < len(data['attempts']):
            attempt = data['attempts'][index]
            if attempt.get('finished_at'):
                continue
            # Never silently repeat an interrupted inference attempt.
            state = store.load(attempt['run_id'])
            if state['state'] != 'complete':
                attempt.update(finished_at=runs.now(), outcome='interrupted', detail='Original attempt retained; not rerun.')
                save()
                continue
        else:
            state = store.create_checks(item['module'], max_rounds=frozen['configuration']['max_rounds'])
            attempt = {**item, 'run_id': state['id'], 'started_at': runs.now()}
            data['attempts'].append(attempt)
            save()
            print(json.dumps({'starting': item, 'run_id': state['id']}), flush=True)
            store.execute(state['id'])
            state = store.load(state['id'])
        attempt.update(finished_at=runs.now(), outcome=state.get('checks', {}).get('status', state['state']),
                       state=state['state'], error=state.get('error'), checks=state.get('checks', {}))
        save()
        print(json.dumps({'finished': item, 'outcome': attempt['outcome'],
                          'rounds': len(attempt['checks'].get('rounds', []))}), flush=True)
    data['completed_at'] = runs.now()
    save()


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    choice = p.add_mutually_exclusive_group(required=True)
    choice.add_argument('--freeze', action='store_true')
    choice.add_argument('--run', action='store_true')
    args = p.parse_args()
    freeze() if args.freeze else execute()
