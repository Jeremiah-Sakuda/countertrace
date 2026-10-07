import type { Run } from '../api/types';

/**
 * Curated investigations of real recorded Nemotron repairs. Every rejected
 * candidate must carry a counterexample and every accepted one must pass all
 * obligations under the parent's frozen check set; validateRepairCase fails
 * closed otherwise. Headings describe each patch before its result is shown.
 */
export interface RepairCase {
  id: string;
  number: string;
  title: string;
  design: string;
  parent: string;
  candidates: string[];
  headings: string[];
  prompts: string[];
  /** Shown after a rejected candidate's result; empty for accepted ones. */
  afterReveal: string[];
  explanation: string;
  discussion: string;
}

const FEEDBACK_PROMPT = 'The previous candidate’s counterexample was supplied to the next model call. This cumulative diff is relative to the original design.';

export const repairCases: RepairCase[] = [
  {
    id: 'two-bugs', number: '01', title: 'Two bugs, one bug report', design: 'Wrap-bit FIFO',
    parent: 'rec-20261004-010137-ver-dd43e0',
    candidates: ['rec-20261004-010200-ver-42e87f', 'rec-20261004-010214-ver-b5bcad'],
    headings: ['Guard the read.', 'Revisit the pointer comparison.'],
    prompts: ['Compare the proposed change with the contract. Could another boundary still fail?', FEEDBACK_PROMPT],
    afterReveal: ['A read guard does not address every possible failure. Inspect the fill sequence and pointer wrap in the evidence before proposing another change.', ''],
    explanation: 'The first change guarded reads but left a flag error when the pointer’s low bits wrapped. Comparing the full pointers and guarding reads passed the frozen depth-4 checks.',
    discussion: 'Which test would you preserve as a regression, and what would a passing simulation alone leave uncertain?',
  },
  {
    id: 'reset', number: '02', title: 'A fix that breaks working code', design: 'Registered-flags FIFO',
    parent: 'rec-20261004-005900-ver-08fd75',
    candidates: ['rec-20261004-005924-ver-ac5ac4', 'rec-20261004-005944-ver-099d40'],
    headings: ['Clear full on reset, and recompute the idle flags.', 'Clear full on reset, and hold the idle flags.'],
    prompts: ['The patch changes two things. Check each one against the contract, including cycles with no read and no write.', FEEDBACK_PROMPT],
    afterReveal: ['The reset fix was right, but the rewritten default branch recomputes both flags on idle cycles from the advanced pointers. Right after reset, an idle cycle clears empty while the queue is still empty.', ''],
    explanation: 'The original reset left the registered full flag untouched, so it could start high. Candidate 1 added the reset but also rewrote the idle branch, which had correctly held both flags, and that cleared empty on an idle cycle. Candidate 2 kept the reset fix and held both flags on idle cycles; it passed the frozen depth-4 checks. A patch can fix the reported bug and break code that was working, so check every changed line against the contract, not only the line the bug report points to.',
    discussion: 'Which test in your own suite would have caught candidate 1’s idle-cycle change, and why did the bug report not point there?',
  },
  {
    id: 'simultaneous', number: '03', title: 'Three rounds on one flag', design: 'Registered-flags FIFO',
    parent: 'rec-20261004-005755-ver-a8ded4',
    candidates: ['rec-20261004-005824-ver-b150cd', 'rec-20261004-005841-ver-739960', 'rec-20261004-005853-ver-c66323'],
    headings: ['Compute both flags from next-state logic.', 'Hold the flags when occupancy does not change.', 'Compare against the write pointer that will exist.'],
    prompts: ['The original design updates the flags in two separate if-statements. Does computing them once cover every combination of read and write?', FEEDBACK_PROMPT, FEEDBACK_PROMPT],
    afterReveal: [
      'The new logic sets both flags to 0 whenever the cycle is not write-only or read-only. On an idle cycle right after reset, empty drops to 0 while the queue is still empty.',
      'Idle cycles now hold the flags, but a read with no write compares the advanced read pointer with the advanced write pointer, although no write happened. After one write and one read, empty stays 0 on an empty queue.',
      '',
    ],
    explanation: 'The original design wrote the flags in two if-statements, so on a simultaneous read and write the second block won and set empty at occupancy 1. Candidate 1 moved to next-state logic but set both flags to 0 on idle and simultaneous cycles. Candidate 2 held the flags in those cases but compared against the advanced write pointer on a read-only cycle. Candidate 3 compared against the current write pointer and passed the frozen depth-4 checks. Each counterexample exposed a different combination of read and write.',
    discussion: 'List the four read and write combinations and the correct next value of each flag. Which combination did each candidate get wrong?',
  },
  {
    id: 'right-first-time', number: '04', title: 'When the model is right', design: 'Count-based FIFO',
    parent: 'rec-20261004-003607-ver-4cc749',
    candidates: ['rec-20261004-003622-ver-d88ef8'],
    headings: ['Ignore writes when full.'],
    prompts: ['One condition added. What evidence would convince you it is enough?'],
    afterReveal: [''],
    explanation: 'The original design accepted writes when full, so the write pointer overwrote the oldest word and a later read returned the wrong byte. Gating the write with !full matches the contract: a write is ignored when the queue is full, including when a read arrives in the same cycle. The candidate passed the frozen depth-4 checks on its first attempt. Accepting a fix needs evidence too: a passing directed test would not cover every simultaneous request at the full boundary, while the proofs under the recorded assumptions do.',
    discussion: 'If you were reviewing this one-line change in a pull request, which evidence would you ask for before approving it?',
  },
];

export const caseById = (id: string | null | undefined): RepairCase => repairCases.find(c => c.id === id) ?? repairCases[0]!;

export type Prediction = '' | 'pass' | 'fail' | 'unsure';
export interface RepairNotes {
  schema: 'countertrace-repair-practice-v2';
  caseId: string;
  predictions: Prediction[];
  revealed: boolean[];
  reasoning: string[];
  reflection: string;
  transfer: string;
  compared: boolean;
}
export const notesKey = (c: RepairCase) => `countertrace:repair-practice:${c.id}`;
/** Notes saved by the single-case lab before the casebook existed. */
export const LEGACY_NOTES_KEY = 'countertrace:repair-practice';

export const freshRepairNotes = (c: RepairCase): RepairNotes => {
  const n = c.candidates.length;
  return {schema: 'countertrace-repair-practice-v2', caseId: c.id, predictions: Array(n).fill(''), revealed: Array(n).fill(false),
    reasoning: Array(n).fill(''), reflection: '', transfer: '', compared: false};
};

const isText = (v: unknown) => typeof v === 'string' && v.length <= 2000;

export function readRepairNotes(raw: string | null, c: RepairCase): RepairNotes {
  const fresh = freshRepairNotes(c);
  const n = c.candidates.length;
  try {
    let v = JSON.parse(raw ?? 'null');
    if (v?.schema === 'countertrace-repair-practice-v1' && c.id === repairCases[0]!.id) v = {...v, schema: fresh.schema, caseId: c.id};
    if (v?.schema !== fresh.schema || v.caseId !== c.id) return fresh;
    const arrays = [v.predictions, v.revealed, v.reasoning];
    if (!arrays.every(a => Array.isArray(a) && a.length === n)) return fresh;
    if (!v.predictions.every((p: unknown) => ['', 'pass', 'fail', 'unsure'].includes(p as string)) || !v.revealed.every((r: unknown) => typeof r === 'boolean')
      || !v.reasoning.every(isText) || !isText(v.reflection) || !isText(v.transfer) || typeof v.compared !== 'boolean') return fresh;
    const revealed = v.revealed as boolean[];
    if (revealed.some((r, i) => r && (!v.predictions[i] || !v.reasoning[i].trim() || (i > 0 && !revealed[i - 1])))) return fresh;
    if (v.compared && (!revealed.every(Boolean) || !v.transfer.trim() || !v.reflection.trim())) return fresh;
    return v as RepairNotes;
  } catch { return fresh; }
}

const canonical = (v: unknown): string => {
  if (Array.isArray(v)) return `[${v.map(canonical).join(',')}]`;
  if (v && typeof v === 'object') return `{${Object.entries(v).sort(([a],[b])=>a.localeCompare(b)).map(([k,x])=>`${JSON.stringify(k)}:${canonical(x)}`).join(',')}}`;
  return JSON.stringify(v);
};
const EXPECTED = new Map([['simulation:empty_flag','simulation_passed'],['simulation:full_flag','simulation_passed'],['simulation:read_data','simulation_passed'],['bmc:empty_flag','bounded_pass'],['bmc:full_flag','bounded_pass'],['bmc:read_data','bounded_pass'],['prove:empty_flag','proved'],['prove:full_flag','proved'],['prove:read_data','proved'],['cover:reachability','bounded_pass']]);

/** Fail closed before presenting a curated case as a complete comparison. */
export function validateRepairCase(c: RepairCase, parent: Run, candidates: Run[]) {
  const n = c.candidates.length;
  if (parent.id !== c.parent || parent.state !== 'complete' || !parent.recorded || !parent.verification?.frozen || !parent.verification.findings.length
    || parent.repair?.attempts.length !== n || candidates.length !== n) throw new Error('The recorded repair case is incomplete.');
  candidates.forEach((run, i) => {
    const a = parent.repair!.attempts[i]!; const v = run.verification; const last = i === n - 1;
    if (run.id !== c.candidates[i] || run.parent_id !== parent.id || !run.recorded || run.state !== 'complete' || !v || !v.frozen || !Array.isArray(v.integrity) || v.integrity.length
      || !v.integrity_checked?.includes('sim') || !v.integrity_checked?.includes('formal') || a.candidate_run_id !== run.id || a.origin !== 'model' || !a.diff || !a.calls?.length
      || a.frozen_match !== true || canonical(v.frozen) !== canonical(parent.verification!.frozen) || canonical(parent.repair!.parent_frozen) !== canonical(v.frozen)
      || v.obligations.length !== EXPECTED.size || new Set(v.obligations.map(o => o.id)).size !== EXPECTED.size || v.obligations.some(o => !EXPECTED.has(o.id)))
      throw new Error('Candidate evidence or the unchanged comparison could not be confirmed.');
    if (!last && (a.status !== 'failed_checks' || !v.findings.length || !v.obligations.some(o => o.status === 'counterexample')))
      throw new Error('A rejected candidate has no confirming counterexample.');
    if (last && (!v.formal_covers || Object.keys(v.formal_covers).length !== 12 || Object.values(v.formal_covers).some(cv => cv.reached !== true)
      || a.status !== 'passed_unchanged_checks' || v.findings.length || v.obligations.some(o => o.status !== EXPECTED.get(o.id))))
      throw new Error('The final candidate does not have all expected check results.');
  });
  return {parent, candidates, attempts: parent.repair.attempts};
}

export function repairNotesReport(c: RepairCase, n: RepairNotes): string {
  return ['# Countertrace: challenge a Nemotron repair', 'Anonymous, self-reported practice. No measured learning gain.',
    `Case ${c.number}: ${c.title} (recorded case ${c.parent})`,
    ...n.predictions.map((p, i) => `## Candidate ${i + 1}\nPrediction: ${p || 'Unanswered'}\nReason: ${n.reasoning[i] || 'Unanswered'}\nRecorded result viewed: ${n.revealed[i] ? 'yes' : 'no'}\nEvidence: ${c.candidates[i]}`),
    '## What changed my decision\n' + (n.reflection || 'Unanswered'), '## Transfer: does depth 4 establish depth 8?\n' + (n.transfer || 'Unanswered'),
    'Reference explanation viewed: ' + (n.compared ? 'yes' : 'no')].join('\n\n');
}

/** Signal a finding's check reads, for the expected/observed witness. */
export function witnessSignal(check: string): 'empty' | 'full' | 'dout' {
  return check === 'full_flag' ? 'full' : check === 'read_data' ? 'dout' : 'empty';
}
