# FIFO specification alignment and second-depth audit

This is development work after the frozen checks-v1 evaluation, not additional held-out attempts. It tests the same model-written FIFO properties at both supported depths and preserves the initial audit failure.

## What the additional check found

The original recorded FIFO set (`rec-20261009-130847-che-c5ecc4`) passed its primary depth-four gate. A separate depth-two audit then stopped with an integrity error: mutant 1 was equivalent within the comparator's observation window but violated `dout_after_read`. The gate refused promotion rather than treating that contradiction as a kill. The [original audit result](fifo-depth2.json) is unchanged.

The catalog text promised that the last read value remains stable until the next accepted read, while the existing FIFO contract and equivalence miter constrain `dout` only after an accepted read. The specification was corrected to match that established contract. Neither the monitor nor the original outcome was changed. The original recording now carries a retrospective caveat.

## Fresh model generation and execution

Nemotron received the corrected specification without golden source. A new four-round run rejected three proposals on the golden before the fourth promoted. The first omitted reset from the acceptance guards. The second used a doubly delayed array index, and the third repeated it. The fourth used the previous selected memory value with the reset-qualified acceptance guard. All proposals, feedback, token-limit retries and timings remain in `rec-20261009-154341-che-06ba10`.

| Configuration | Killed / non-equivalent | Equivalent | Invalid | Unresolved | Result |
| --- | --- | --- | --- | --- | --- |
| Depth 4, width 8 | 39 / 39 | 1 | 0 | 0 | Primary promotion gate passed |
| Depth 2, width 8 | 37 / 37 | 3 | 0 | 0 | Separate transfer audit passed |

The property set was unchanged between these audits. These are two finite mutation sets, not an all-depth proof or 76 independent designs. The gate still uses the first setting automatically; the second-depth challenge here is an explicitly executed follow-up. Golden proofs and bounded trigger reachability passed for the corresponding settings.

The promoted set found the bundled overflow bug in `rec-20261009-154734-ver-dfae43`; the same inputs passed the golden and failed the candidate against the independent reference queue. One Nemotron patch then passed all 11 unchanged obligations in `rec-20261009-154833-ver-5bb770`. Generation took 213 seconds, the hunt 49 seconds, and candidate verification 31 seconds on local Docker while other checks ran. These are not hosted latency promises. See [machine-readable result](corrected-fifo.json).

## Replay and scope

The three recordings pin source revision `28ee40cbd5ca7892f90a00a7dab2ecbf12237e71`. Exported bundles replay the four primary gate rounds, the confirmed hunt and the accepted repair without inference. The extra depth-two audit is preserved separately under the check recording's `secondary-depth2/` directory and in the result above; it is not silently included in the standard primary-gate replay claim.

To rerun that separate audit from matching source, using the downloaded/checked-out recording and a built verifier image:

```python
from dataclasses import replace
import json
from pathlib import Path
from countertrace import runner
from countertrace.checks import gate, modules

record = json.loads(Path('recorded/rec-20261009-154341-che-06ba10/run.json').read_text())
props = record['checks']['rounds'][record['checks']['promoted_round']]['properties']
module = modules.load('sync_fifo')
secondary = replace(module, params=[module.params[1]])
result = gate.run_gate(secondary, props, Path('.countertrace/replay-depth2-audit'),
                       runner.ensure_image(build=False))
print(result)
```

Use a fresh output directory. This runs deterministic RTL verification only, with no model request. Historical primary-only claims retain their original scope; none of these results removes the dependency on a correct golden reference.
