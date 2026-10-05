"""Build bounded, recorded learning branches using the isolated RTL verifier.

No browser-side DUT emulation: every offered sequence has actually run. This
is a finite simulation library, never a formal proof or unseen live execution.
"""
from __future__ import annotations
import hashlib
import itertools
import json
from pathlib import Path
import sys
import tempfile
import zipfile
from datetime import datetime, timezone

from countertrace import admission, catalog, runner
from countertrace.contract import Contract, Edge
from countertrace.formal import EXPECTED_PROPERTIES, property_inventory
from countertrace.scoreboard import normalize, parse_sim_trace

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'apps/web/public/learning'
MAX_STEPS = 6
# w = write, r = read, b = both, x = reset. Data depends on edge position.
def edge(action, index):
    return Edge(int(action == 'x'), int(action in 'wb'), int(action in 'rb'), 17 * index)


def build():
    paths = [''.join(p) for p in itertools.product('wrbx', repeat=MAX_STEPS)]
    stimulus = []
    for path in paths:
        stimulus += [Edge(1, 0, 0, 0)] + [edge(a, i + 1) for i, a in enumerate(path)]
    text = ''.join(f'{e.rst} {e.wr_en} {e.rd_en} {e.din:02x}\n' for e in stimulus)
    sources = {'overflow': catalog.fault_source('count-overwrite-when-full'),
               'exchange': catalog.fault_source('count-full-exchange'),
               'control': catalog.base_source('fifo_count.v')}
    designs = []
    for key, source in sources.items():
        admitted = admission.admit(source)
        if not admitted.accepted:
            raise RuntimeError(admitted.as_dict())
        designs.append((dict(id=key, top=admitted.module, depth=2, width=8,
                             sim_tests=['learning'], formal=[], seed=1), source))
    # Keep reproducibility inputs in the workspace; never publish the whole private run tree.
    root = Path(tempfile.mkdtemp(prefix='learning-', dir=ROOT / 'artifacts'))
    batch = runner.prepare_batch(root, designs, {'learning': text})
    result = runner.run_batch(batch, runner.ensure_image(build=False))
    worker = result.get('worker', {})
    if result['container_returncode'] != 0 or result['timed_out'] or worker.get('deadline_reached'):
        raise RuntimeError('Incomplete worker execution')
    if worker.get('harness_hashes') != runner.harness_hashes():
        raise RuntimeError('Stale or altered verifier image')
    expected_steps = {f'{k}:{s}' for k in sources for s in ('ports', 'properties', 'compile', 'sim:learning')}
    if {s['id'] for s in worker.get('steps', [])} != expected_steps:
        raise RuntimeError('Missing or unexpected worker steps')
    if any(s.get('returncode') != 0 or s.get('timed_out') for s in worker['steps']):
        raise RuntimeError('A worker step failed')
    data = dict(schema='countertrace-learning/1', profile='sync-fifo-v1', depth=2, width=8,
                max_steps=MAX_STEPS, actions=list('wrbx'), sequences_per_design=len(paths),
                created_at=datetime.now(timezone.utc).isoformat(),
                method='Recorded Verilator simulation; finite action alphabet and six-edge horizon. Not a proof.',
                provenance=dict(image=result['image'], tools=worker['tool_versions'],
                                harness_hashes=worker['harness_hashes'], wall_s=result['wall_s']),
                designs={})
    files = {'stimulus.txt': text.encode(), 'worker_result.json': json.dumps(worker, indent=2).encode()}
    for key, source in sources.items():
        out = batch.out_dir / key
        ports = json.loads((out / 'ports.json').read_text())
        if admission.check_ports_json(ports, 'fifo', 8):
            raise RuntimeError('Interface mismatch')
        inv = property_inventory(json.loads((out / 'properties.json').read_text()))
        if inv['counts'] != EXPECTED_PROPERTIES or inv['problems']:
            raise RuntimeError('Property inventory mismatch')
        trace = (out / 'sim/learning.trace').read_text()
        rows = normalize(Contract(depth=2), parse_sim_trace(trace, 2, 8, stimulus))
        nodes = {}
        for i, path in enumerate(paths):
            for j in range(MAX_STEPS + 1):
                r = rows[i * (MAX_STEPS + 1) + j]
                # Ignore undefined dout when no read was accepted, exactly as the core does.
                value = [r['expected']['dout'], int(r['expected']['empty']), int(r['expected']['full']),
                         r['observed']['dout'] if r['dout_checked'] else None,
                         int(r['observed']['empty']), int(r['observed']['full'])]
                prefix = path[:j]
                if prefix in nodes and nodes[prefix] != value:
                    raise RuntimeError(f'Non-repeatable prefix {key}/{prefix}')
                nodes[prefix] = value
        failures = sum(v[:3] != v[3:] for v in nodes.values())
        if (key == 'control' and failures) or (key != 'control' and not failures):
            raise RuntimeError('Control/fault expectation not supported by execution')
        data['designs'][key] = dict(source=source, source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                                   origin='Countertrace authored fixture; not an AI-generated patch.', nodes=nodes)
        files[f'{key}/dut.v'] = source.encode()
        files[f'{key}/learning.trace'] = trace.encode()
        files[f'{key}/ports.json'] = (out / 'ports.json').read_bytes()
        files[f'{key}/properties.json'] = (out / 'properties.json').read_bytes()
    DEST.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(data, separators=(',', ':')) + '\n').encode()
    files['library.json'] = payload
    manifest = {name: hashlib.sha256(body).hexdigest() for name, body in files.items()}
    with zipfile.ZipFile(DEST / 'evidence.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, body in files.items():
            archive.writestr(name, body)
        archive.writestr('manifest.json', json.dumps(manifest, indent=2))
    (DEST / 'library.json').write_bytes(payload)
    print(json.dumps({'designs':len(sources), 'sequences_per_design':len(paths),
                      'cycles_per_design':len(stimulus), 'wall_s':result['wall_s'],
                      'library_bytes':len(payload), 'artifact':str(root)}))

if __name__ == '__main__':
    build()
