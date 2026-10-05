# Facilitate the Countertrace learning lab

The primary audience is instructors and FPGA club mentors teaching learners who know clocks, reset, and basic RTL. Open the [facilitator desk](https://countertrace.vercel.app/#/teach) for shareable learner links and answer keys. The three interactive labs replace the worksheet as the primary journey. The worksheet below remains an optional workbench activity.

## Suggested 20 minute session

1. Introduce the fixed FIFO contract and ask each learner to commit a prediction (3 minutes).
2. In pairs, build input sequences and compare expected versus observed outputs (8 minutes).
3. Each learner writes an explanation and answers a new transfer question independently (5 minutes).
4. Discuss scope, hints used, and what remains unchecked (4 minutes).

This timing is a suggested plan, not measured. Lab 1 explores overflow, lab 2 simultaneous operations, and lab 3 a correct candidate and evidence limits. Start with one lab per session; the other lessons are extensions. Authored hints are available in the browser. The configured local build also offers live Nemotron coaching, which is advisory and counts as assistance.

Practice records contain initial answers, experiment predictions and action sequences, first mismatches, hints opened, ungraded reflection, and the first submitted transfer answer. Learners can download Markdown notes or JSON. With their permission, collect anonymous JSON records through your existing channel and import them at the facilitator desk. Imports remain in that browser tab. Counts describe self-reported records, not unique students, grades, or measured gains. Ask learners to download before resetting. No outreach or recruitment has occurred.

## Evidence and limits

All available browser sequences actually ran in the isolated Verilator worker: three authored candidates, 4,096 paths each, six edges after reset, four allowed actions, depth 2, width 8. Shorter prefixes share checked recorded observations. Write data is fixed by edge position. The library contains no novel-input live execution, no AI-generated candidate claim, and no formal proof. Download the source, raw traces, stimulus, and hash manifest from the bench. The existing workbench contains genuine Nemotron repair records under separate exact configurations.

Proposed observation: can a learner construct a useful boundary test, explain the governing rule, and answer a related transfer case? Record assistance, failed attempts, and exact answers. At least two of three unassisted transfer successes is a proposed pilot target, not an observed outcome. No learning efficacy, adoption, or preparation-time saving has been measured.

---

## Optional 15 minute workbench worksheet

Use Countertrace to teach the difference between the cycle where a bug becomes visible and the operation that caused it. This guide is for digital-design instructors and FPGA club mentors working with learners who understand clocks, reset, and basic RTL. It includes a guided example, a short worksheet, and an answer key.

Open the [public demo](https://countertrace.vercel.app). The lesson uses recorded tool and model results, so participants need only a browser; no account, installation, or paid API key is required. Live execution is a separate [local activity](submission/TESTING.md#local-working-test-build). The 15-minute duration is a planned lesson length, not a measured completion time. The lesson has not yet been tried with learners.

## Prepare the session

Open the [overwrite showcase](https://countertrace.vercel.app/#/runs/rec-20261004-003607-ver-4cc749), the [check-quality audit](https://countertrace.vercel.app/#/runs/rec-20261001-193049-aud-7cf847), and the [accepted repair](https://countertrace.vercel.app/#/runs/rec-20261004-003622-ver-d88ef8). Copy the worksheet questions below into your course notes, leaving the answer key for the facilitator. Pairs can share one browser.

State the supported contract before starting: a synchronous FIFO with 8-bit words and depth 2 or 4. At each edge, acceptance depends on occupancy **before** the edge. A write while full is ignored even if a simultaneous read frees space. When empty, a simultaneous read and write accepts only the write. Read data is checked only when a read is accepted. These are this profile's rules; other FIFO policies exist.

## Facilitate the lesson

| Minutes | Activity | What the learner produces |
| --- | --- | --- |
| 0 to 2 | Read the contract, then answer worksheet question 1 before opening the explanation. | A prediction about a boundary operation. |
| 2 to 6 | Open the showcase. Inspect cycles 1, 5, and 6 and the queue before/after the edge. Read the explanation, then the repair diff. | A causal account using the stored byte and the overwrite, plus the purpose of the write guard. |
| 6 to 10 | Open the recorded audit. Select the missing requirements before revealing its answer. Discuss one surviving fault and the test that would expose it. | A concrete missing test condition. |
| 10 to 13 | Answer worksheet question 3 individually before discussion. This is a new paper scenario, not a second executed hardware result. | A prediction for the empty boundary and the following read. |
| 13 to 15 | Inspect the accepted repair's method-specific results and answer question 4. | A scoped conclusion about what passed and what remains unclaimed. |

The original showcase explanation is preserved with a notice about corrected simulation summaries. Use the current check-results table for property outcomes. This is also a useful example of why a model's narrative is separate from the evidence that decides a result.

## Learner worksheet

1. A depth-2 FIFO is full: oldest first, `[0x11, 0x22]`. At the next edge, both read and write are requested, with `din=0x33`. What operations are accepted, what is `dout`, and what is the queue after the edge? Explain using the contract.
2. In the showcase, which cycle first displays the wrong read value, and which earlier operation caused it? Explain what happened to `0x21`. Why does adding `&& !full` address this particular defect? Propose a short test that would expose the original error.
3. A depth-2 FIFO is empty after reset. At edge A, both read and write are requested with `din=0xC3`. At edge B, only a read is requested. For each edge, write the accepted operations, queue afterward, `empty`, `full`, and whether `dout` must equal a particular value. Do this before looking at the key.
4. A repair passes the named simulation tests, bounded checks, and three unbounded property proofs. What can you conclude about this configuration? Name one thing those results do not establish.

## Facilitator answer key

1. Only the read is accepted. `dout=0x11`; the queue becomes `[0x22]`, `empty=0`, `full=0`. The write is ignored because the queue was full before the edge. Accepting `0x33` would implement a different contract policy.
2. The first observed mismatch is at cycle 6; the damaging write occurs at cycle 5. The first word `0x21`, accepted at cycle 1, is overwritten by `0x65` while full. The guard prevents that write. A useful test fills the queue, attempts one extra write, then drains it and compares every accepted word in order. These are distinct causal and observation points.
3. At A, only the write is accepted; queue `[0xC3]`, `empty=0`, `full=0`. No read was accepted, so this contract imposes no `dout` value at A. At B, the read is accepted and returns `0xC3`; queue `[]`, `empty=1`, `full=0`. The expectations follow the contract; this worksheet is not a measured verifier run.
4. The listed properties hold under their recorded assumptions, methods, parameter values, and tool semantics. Tests cover their named executions; the bounded check covers its stated horizon; each unbounded proof covers its particular property. None establishes every FIFO policy, every depth, electrical behavior, timing closure, or correctness of all hardware.

For the audit, the deliberately weak set misses writes while full, simultaneous operations while full, and simultaneous operations while empty. Its score describes this named set on its frozen stimulus, not an imported learner testbench or general design confidence.

## Record observations for a small pilot

For each consenting participant, use an anonymous identifier and record prior RTL experience, task time, exact answers, hints, and anything that confused them. Keep responses private unless the participant agrees to publication. The application does not collect these answers or generate study results.

Score four items from 0 to 2: cause versus symptom in question 2; repair rationale and missing test in question 2; empty-boundary transfer in question 3; and result scope in question 4. Use 0 for incorrect/absent, 1 for partial, and 2 for correct with a reason. Record assistance separately, even for a correct answer. Also record the audit selection before revealing its answer.

Start with one instructor or mentor and three learners. A useful pilot target is at least two learners correctly handling the transfer and scope questions without a hint, and an instructor willing to reuse the lab. Report the actual denominator, failures, assistance, and preparation time. If the target is missed, revise the confusing step before adding more module types. The questions differ in difficulty and are not a controlled before/after experiment; do not turn this pilot into a learning-gain or time-saving claim.

The next product decision is whether an instructor can reuse this lesson with little preparation. A public working runtime would reduce live-lab setup; more module families can wait for evidence that this lesson is useful. External technical review can strengthen the material but is not a prerequisite for trying the lesson.
