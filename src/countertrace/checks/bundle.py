"""Portable deterministic replay of check-writing rounds; never regenerates model text."""
import json
from pathlib import Path
import tempfile
import threading
import zipfile

from countertrace import runner
from countertrace.checks import agent, gate, modules
from countertrace.checks.design import frozen

SCHEMA = 'countertrace-checks-evidence/1'


def export(store, run_id, output_dir=None):
    from countertrace.bundle import sha256, git_commit, BUNDLE_LIMIT
    from countertrace.runs import data_dir
    state = store.load(run_id)
    if state.get('kind') != 'checks' or state.get('state') != 'complete':
        raise ValueError('Only completed check-writing runs can be exported.')
    payload = {'module_id': state['module_id'], 'checks': state['checks']}
    files = {'checks.json': json.dumps(payload, indent=2).encode(),
             'REPLAY.md': b'# Replay check-writing evidence\n\nRun `countertrace replay <bundle.zip>` from the matching checkout with Docker. No model key or inference is needed. Every round containing properties is gated again. Format/model errors are preserved, not regenerated. Recorded mutation checks are bounded and use the first parameter setting.\n'}
    omitted, budget = [], BUNDLE_LIMIT
    for path in sorted(store.run_dir(run_id).glob('round-*/**/*')):
        if not path.is_file():
            continue
        name = f'artifacts/{path.relative_to(store.run_dir(run_id))}'
        data = path.read_bytes()
        if len(data) > budget:
            omitted.append(name)
            continue
        files[name] = data
        budget -= len(data)
    manifest = {'schema': SCHEMA, 'run_id': run_id, 'git_commit': git_commit(), 'omitted': omitted,
                'files': {name: sha256(data) for name, data in files.items()}}
    files['manifest.json'] = json.dumps(manifest, indent=2).encode()
    out = (output_dir or data_dir() / 'bundles') / f'countertrace-{run_id}.zip'
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    return out


def replay(zf):
    from countertrace.bundle import sha256
    manifest = json.loads(zf.read('manifest.json'))
    if manifest.get('schema') != SCHEMA:
        return {'matches': False, 'error': 'Unknown checks bundle schema.'}
    for name, digest in manifest['files'].items():
        if sha256(zf.read(name)) != digest:
            return {'matches': False, 'error': f'{name} has changed.'}
    payload = json.loads(zf.read('checks.json'))
    module = modules.load(payload['module_id'])
    rounds = payload['checks']['rounds']
    if not rounds:
        return {'matches': False, 'error': 'No check-writing rounds.'}
    for r in rounds:
        if 'properties' in r and r.get('frozen') != frozen(module, r['properties']):
            return {'matches': False, 'error': 'Check compiler, gate, golden, properties or configuration differs; use the matching checkout.'}
    image = runner.ensure_image(build=True)
    comparisons = []
    with tempfile.TemporaryDirectory(dir=Path.home()) as tmp:
        for r in rounds:
            if 'properties' not in r:
                comparisons.append({'round': r['index'], 'skipped': 'Model/format failure retained; no deterministic properties to replay.'})
                continue
            result = gate.run_gate(module, r['properties'], Path(tmp) / f"round-{r['index']}", image, threading.Event())
            current = agent.summary(result)
            comparisons.append({'round': r['index'], 'matches': current == r['gate'], 'recorded': r['gate'], 'replayed': current})
    checked = [r for r in comparisons if 'matches' in r]
    return {'matches': bool(checked) and all(r['matches'] for r in checked), 'rounds': comparisons, 'image': image,
            'note': 'Replayed deterministic gates only, not inference, latency or model text.'}
