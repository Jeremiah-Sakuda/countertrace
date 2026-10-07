"""Build the repair lab's probe library by running every candidate in the isolated verifier.

For each Nemotron candidate in the repair casebook, every six-action sequence of
write, read, read+write, and reset (4,096 paths after a reset edge) runs in the
pinned Verilator image at depth 4. The browser replays the recorded outcome of
whatever sequence a learner builds; it never emulates the DUT. Each path is
recorded through its first disagreement only. Fails closed unless every rejected
candidate shows a mismatch within the horizon and every accepted candidate shows
none. Finite simulation, never a proof.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import tempfile
import zipfile

from countertrace import admission, runner
from countertrace.contract import Contract, Edge
from countertrace.formal import EXPECTED_PROPERTIES, property_inventory
from countertrace.scoreboard import normalize, parse_sim_trace

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'apps/web/public/learning'
DEPTH = 4
MAX_STEPS = 6
_spec = importlib.util.spec_from_file_location('learning_evidence', ROOT / 'scripts/build_learning_evidence.py')
_learning = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_learning)
edge = _learning.edge  # same action alphabet and data pattern as the practice bench


def casebook() -> list[tuple[str, bool]]:
    """(candidate run id, accepted) for every candidate in the published repair cases."""
    text = (ROOT / 'apps/web/src/lib/repairLab.ts').read_text()
    pairs = []
    for block in text.split("parent: '")[1:]:
        parent = block.split("'", 1)[0]
        state = json.loads((ROOT / 'recorded' / parent / 'run.json').read_text())
        for attempt in state['repair']['attempts']:
            pairs.append((attempt['candidate_run_id'], attempt['status'] == 'passed_unchanged_checks'))
    return pairs


def build():
    candidates = casebook()
    paths = [''.join(p) for p in itertools.product('wrbx', repeat=MAX_STEPS)]
    stimulus = []
    for path in paths:
        stimulus += [Edge(1, 0, 0, 0)] + [edge(a, i + 1) for i, a in enumerate(path)]
    text = ''.join(f'{e.rst} {e.wr_en} {e.rd_en} {e.din:02x}\n' for e in stimulus)
    designs, sources = [], {}
    for index, (run_id, _) in enumerate(candidates):
        source = (ROOT / 'recorded' / run_id / 'dut.v').read_text()
        admitted = admission.admit(source)
        if not admitted.accepted:
            raise RuntimeError(f'{run_id}: {admitted.as_dict()}')
        key = f'c{index}'
        sources[key] = (run_id, source)
        designs.append((dict(id=key, top=admitted.module, depth=DEPTH, width=8, sim_tests=['probe'], formal=[], seed=1), source))
    root = Path(tempfile.mkdtemp(prefix='repair-probes-', dir=ROOT / 'artifacts'))
    batch = runner.prepare_batch(root, designs, {'probe': text})
    result = runner.run_batch(batch, runner.ensure_image(build=False))
    worker = result.get('worker', {})
    if result['container_returncode'] != 0 or result['timed_out'] or worker.get('deadline_reached'):
        raise RuntimeError('Incomplete worker execution')
    if worker.get('harness_hashes') != runner.harness_hashes():
        raise RuntimeError('Stale or altered verifier image')
    if {s['id'] for s in worker.get('steps', [])} != {f'{k}:{s}' for k in sources for s in ('ports', 'properties', 'compile', 'sim:probe')}:
        raise RuntimeError('Missing or unexpected worker steps')
    if any(s.get('returncode') != 0 or s.get('timed_out') for s in worker['steps']):
        raise RuntimeError('A worker step failed')
    data = dict(schema='countertrace-learning/1', profile='sync-fifo-v1', depth=DEPTH, width=8,
                max_steps=MAX_STEPS, actions=list('wrbx'), sequences_per_design=len(paths),
                created_at=datetime.now(timezone.utc).isoformat(),
                method='Recorded Verilator simulation of each repair candidate; finite action alphabet and six-edge horizon; each path recorded through its first disagreement. Not a proof.',
                provenance=dict(image=result['image'], tools=worker['tool_versions'],
                                harness_hashes=worker['harness_hashes'], wall_s=result['wall_s']),
                designs={})
    files = {'stimulus.txt': text.encode(), 'worker_result.json': json.dumps(worker, indent=2).encode()}
    accepted = dict(candidates)
    for key, (run_id, source) in sources.items():
        out = batch.out_dir / key
        if admission.check_ports_json(json.loads((out / 'ports.json').read_text()), 'fifo', 8):
            raise RuntimeError(f'{run_id}: interface mismatch')
        inv = property_inventory(json.loads((out / 'properties.json').read_text()))
        if inv['counts'] != EXPECTED_PROPERTIES or inv['problems']:
            raise RuntimeError(f'{run_id}: property inventory mismatch')
        trace = (out / 'sim/probe.trace').read_text()
        rows = normalize(Contract(depth=DEPTH), parse_sim_trace(trace, DEPTH, 8, stimulus))
        nodes = {}
        for i, path in enumerate(paths):
            for j in range(MAX_STEPS + 1):
                r = rows[i * (MAX_STEPS + 1) + j]
                value = [r['expected']['dout'], int(r['expected']['empty']), int(r['expected']['full']),
                         r['observed']['dout'] if r['dout_checked'] else None,
                         int(r['observed']['empty']), int(r['observed']['full'])]
                prefix = path[:j]
                if prefix in nodes and nodes[prefix] != value:
                    raise RuntimeError(f'Non-repeatable prefix {run_id}/{prefix}')
                nodes[prefix] = value
                # After the first disagreement a faulty candidate can read memory a
                # previous sequence wrote, so later edges are not a function of this
                # path alone. Record each path only through its first counterexample.
                if value[:3] != value[3:]:
                    break
        failures = sum(v[:3] != v[3:] for v in nodes.values())
        if accepted[run_id] and failures:
            raise RuntimeError(f'{run_id}: an accepted candidate disagrees with the reference in simulation')
        if not accepted[run_id] and not failures:
            raise RuntimeError(f'{run_id}: a rejected candidate shows no mismatch within {MAX_STEPS} edges')
        data['designs'][run_id] = dict(source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                                       origin='Recorded NVIDIA Nemotron 3 Ultra repair candidate.', nodes=nodes)
        files[f'{run_id}/dut.v'] = source.encode()
        files[f'{run_id}/probe.trace'] = trace.encode()
        files[f'{run_id}/ports.json'] = (out / 'ports.json').read_bytes()
        files[f'{run_id}/properties.json'] = (out / 'properties.json').read_bytes()
    payload = (json.dumps(data, separators=(',', ':')) + '\n').encode()
    files['repair-probes.json'] = payload
    manifest = {name: hashlib.sha256(body).hexdigest() for name, body in files.items()}
    with zipfile.ZipFile(DEST / 'repair-probes-evidence.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, body in files.items():
            archive.writestr(name, body)
        archive.writestr('manifest.json', json.dumps(manifest, indent=2))
    (DEST / 'repair-probes.json').write_bytes(payload)
    (ROOT / 'apps/web/src/lib/repair-probes-manifest.json').write_text(
        json.dumps({'schema': 'countertrace-learning-integrity/1', 'sha256': hashlib.sha256(payload).hexdigest()}, indent=2) + '\n')
    print(json.dumps({'designs': len(sources), 'sequences_per_design': len(paths), 'wall_s': result['wall_s'],
                      'library_bytes': len(payload), 'artifact': str(root)}))


if __name__ == '__main__':
    build()
