"""Use promoted properties on bundled FIFO designs, with independent golden replay.

The existing hand-written monitor is retained. Model checks add obligations;
no core obligation is replaced. Other catalog modules remain gate-only.
"""
from dataclasses import replace
import json
from pathlib import Path

from countertrace import runner
from countertrace.admission import admit
from countertrace.contract import Contract, Edge, sha256_json
from countertrace.checks import gate, modules
from countertrace.checks.compile import compile_checker, validate
from countertrace.verify import Verification


def selected(state: dict) -> dict:
    checks = state.get('checks') or {}
    if state.get('kind') != 'checks' or state.get('state') != 'complete' or checks.get('status') != 'promoted':
        raise ValueError('Choose a completed promoted check-writing run.')
    if state.get('module_id') != 'sync_fifo':
        raise ValueError('Downstream design checking currently supports the synchronous FIFO only.')
    rounds = checks.get('rounds', [])
    chosen = next((r for r in rounds if r.get('index') == checks.get('promoted_round')), None)
    if not chosen or not (chosen.get('gate') or {}).get('passed'):
        raise ValueError('The promoted round is missing its gate evidence.')
    props = validate(chosen['properties'], modules.load('sync_fifo'))
    return {'source_run': state['id'], 'module_id': 'sync_fifo', 'properties': props}


def frozen(module, props):
    checker = compile_checker(props, module)
    return {'schema': 'countertrace-promoted-checks-v1', 'module': module.public(),
            'properties_hash': sha256_json(props), 'checker_hash': sha256_json(checker),
            'golden_hash': sha256_json(module.golden), 'harness': runner.harness_hashes(),
            'verifier_digest': runner.verifier_digest(),
            'trusted_code': {p.name: sha256_json(p.read_text()) for p in Path(__file__).parent.glob('*.py')},
            'limits': {**gate.LIMITS, **dict(module.limits)}, 'mutants': gate.MUTANTS,
            'promotion_threshold': gate.PROMOTION_KILL_RATE}


def replay(module, source, depth, rows, root, image, cancel):
    # Formal samples are pre-edge. The last sample observes the preceding edge.
    if len(rows) < 2 or rows[0]['inputs'].get('rst') != 1:
        return {'status': 'unconfirmed', 'detail': 'Counterexample lacks a complete initial reset.'}
    edges = []
    for row in rows[:-1]:
        vals = row['inputs']
        if any(type(vals.get(k)) is not int for k in ('rst', 'wr_en', 'rd_en', 'din')):
            return {'status': 'unconfirmed', 'detail': 'Counterexample has unknown input values.'}
        if any(vals[k] not in (0, 1) for k in ('rst', 'wr_en', 'rd_en')) or not 0 <= vals['din'] < 256:
            return {'status': 'unconfirmed', 'detail': 'Counterexample inputs are outside the FIFO profile.'}
        edges.append(Edge(**{k: vals[k] for k in ('rst', 'wr_en', 'rd_en', 'din')}))
    results = {}
    for name, rtl in (('golden', module.golden), ('candidate', source)):
        admission = admit(rtl)
        if not admission.accepted:
            return {'status': 'unconfirmed', 'detail': f'{name} failed admission.'}
        v = Verification(root / name, name, rtl, Contract(depth=depth), lambda: None, cancel, image, formal_tasks=())
        v.state['admission'] = admission.as_dict()
        v.sim_batch(admission.module, {'property_witness': edges})
        results[name] = v.state
        if v.state['integrity'] or any(o['status'] not in ('simulation_passed', 'counterexample') for o in v.state['obligations']) or not v.state['obligations']:
            return {'status': 'unconfirmed', 'detail': f'{name} replay did not complete.', 'runs': results}
    confirmed = not results['golden']['findings'] and bool(results['candidate']['findings'])
    return {'status': 'confirmed' if confirmed else 'unconfirmed',
            'detail': 'The same input sequence passes on the golden and violates the independent reference on the candidate.' if confirmed else 'No independently confirmed design mismatch on this input sequence.',
            'inputs': [e.__dict__ for e in edges], 'runs': results}


def check(source, depth, selection, root: Path, image, cancel):
    module = modules.load('sync_fifo')
    props = validate(selection['properties'], module)
    identity = frozen(module, props)
    result = {**selection, 'frozen': identity, 'status': 'unresolved'}
    admission = admit(source)
    if not admission.accepted or depth not in (2, 4):
        return {**result, 'detail': 'Unsupported FIFO source or parameters.'}
    promotion = gate.run_gate(module, props, root / 'promotion', image, cancel)
    result['promotion'] = promotion
    if not promotion.get('passed'):
        return {**result, 'detail': 'The selected properties did not pass the current golden gate.'}
    dut_module = replace(module, top=admission.module)
    checker = compile_checker(props, dut_module)
    limits = identity['limits']
    batch = gate._prepare(root / 'design', {'golden.v': source, 'props.sv': checker},
                          {'stage': 'design', 'top': admission.module, 'clock': module.clock,
                           'configs': [{'id': 'p0', 'params': {'DEPTH': depth, 'WIDTH': 8}}], 'limits': limits})
    try:
        gate._run(batch, image, cancel)
        inv = batch.out_dir / 'inventory/p0.json'
        if not inv.is_file() or gate.inventory(json.loads(inv.read_text()), props):
            return {**result, 'detail': 'Design property inventory is incomplete or altered.'}
        status = gate._status(batch.out_dir, 'golden_prove_p0')
        result['tool_status'] = status
        if status == 'PASS':
            return {**result, 'status': 'proved', 'detail': f'Promoted properties proved on this FIFO at depth {depth}; independent core checks remain required.'}
        if status == 'FAIL':
            text = gate._first_vcd(batch.out_dir, 'golden_prove_p0')
            if not text:
                return {**result, 'detail': 'Property failure has no trace; no design defect claimed.'}
            rows = gate.trace_rows(text, 'ct_props_top', module)
            result['failed'] = gate.failed_properties(gate._log(batch.out_dir, 'golden_prove_p0'))
            result['trace'] = rows
            confirmation = replay(module, source, depth, rows, root / 'replay', image, cancel)
            return {**result, 'confirmation': confirmation,
                    'status': 'counterexample' if confirmation['status'] == 'confirmed' else 'unresolved',
                    'detail': confirmation['detail']}
        return {**result, 'detail': f'Property checking returned {status}; no pass or confirmed defect.'}
    except (gate.GateToolError, ValueError, OSError) as exc:
        return {**result, 'detail': f'Property checking could not complete: {exc}'}
