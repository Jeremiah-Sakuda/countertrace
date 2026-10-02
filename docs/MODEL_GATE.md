# Authenticated model gate

Status on October 1, 2026: **pending**. The owner is not signed into Nebius, and `NEBIUS_API_KEY` is absent. The check against local showcase run `20261001-193038-ver-de51cd` returned `unavailable` with zero API calls. No model explanation or repair has been evaluated.

## Account and configuration

Sign in to [Token Factory](https://tokenfactory.nebius.com/), confirm the account's NVIDIA model catalog, endpoint, quotas, and billing, then put the key directly in the ignored `.env`. Never paste the key into chat or commit it. Use mode 0600 for this file.

The local configuration has these provisional, nonsecret values:

```dotenv
NEBIUS_BASE_URL=https://api.tokenfactory.us-central1.nebius.com/v1
NEBIUS_MODEL_ID=nvidia/Nemotron-3-Ultra-550b-a55b
COUNTERTRACE_MODEL_INPUT_TOKEN_LIMIT=16384
COUNTERTRACE_MODEL_OUTPUT_TOKEN_LIMIT=4096
COUNTERTRACE_MODEL_SYSTEM_PREFIX=
```

The endpoint and model are listed in the [official Nebius cookbook](https://github.com/nebius/token-factory-cookbook/blob/main/models/nemotron/nemotron3-ultra-550b-a55b.md), which lists $1 input and $3 output per million tokens. These are public catalog values, **not confirmed account availability or billing**. Leave the repair model unset to use the same model. Confirm account prices before filling the price fields and an inference spending threshold. A 16,384-input/4,096-output request at those prices is about $0.029 at the caps; retries, interpretation, and repair add requests. This is an estimate, not observed usage.

Leave the system prefix blank until the selected endpoint's reasoning controls are verified. The Llama-Nemotron `detailed thinking off` prefix is no longer a universal default. Blank uses provider defaults; it does not promise reasoning is disabled. Check finish reason, schema acceptance, citations, latency, and actual usage before accepting these token limits. Do not tune against the held-out implementation.

## Check, review, and record

Activate `.venv` or use `.venv/bin/countertrace` for these commands:

```sh
countertrace verify --example showcase-overwrite-when-full
# Use the run ID printed by verify, or the existing completed local showcase.
countertrace model-check --run-id <local-run-id>
```

The result is attached to the run and also saved under `.countertrace/model_checks/`. A report with `status: ok` confirms accepted output, not usefulness. Review the actual explanation against the trace and source. Score each item 0 (incorrect), 1 (partial), or 2 (correct):

| Item | Evidence the reviewer should find |
| --- | --- |
| Requirement | Names the accepted contract's violated behavior without inventing intent. |
| Transaction | Locates the first failing check in the trace being explained; distinguishes the formal flag failure from the later visible data corruption. |
| Expected versus observed | Uses the actual byte values, accepted requests, and queue state. |
| Limits | Does not treat simulation or a bounded pass as complete correctness. |

For the showcase, confirm the explanation handles the offered write at full occupancy and the overwritten stored item. The formal flag failure is at cycle 5; the simulation data mismatch is at cycle 6. Citation validity alone cannot establish causal correctness. Record scores, reviewer, timestamp, report path, exact model ID, token usage, and latency in a local review note. Mark usefulness accepted only if all four items are correct and no unsupported causal claim remains; retain failed attempts. This is a development gate, not independent user evidence.

Only after that review:

```sh
countertrace record <local-run-id> --note "Showcase with reviewed Nemotron explanation; development fixture"
```

Inspect the recorded run in the UI and its exported bundle to confirm the explanation, citations, model ID, usage, and original timings survived. Do not replace the shipped recording with a missing-key result.

## First real repair

On the completed local showcase run, use the interface's repair action. Preserve every candidate, admission rejection, failure, timeout, and usage record. Success requires `passed_unchanged_checks`, matching frozen inputs, and resolved obligations, not an encouraging model response. Export the original run and any successful candidate; record the attempt count, time, cost availability, and checker outcomes in [STATUS.md](STATUS.md).

This first repair is development evidence only. It neither satisfies the eight-case repair target nor authorizes a primary release by itself. Use the [release decision](RELEASE_DECISION.md) and keep held-out regressions out of the feedback loop.
