import type { Run } from '../api/types';

export const repairCase = {
  parent: 'rec-20261004-010137-ver-dd43e0',
  candidates: ['rec-20261004-010200-ver-42e87f', 'rec-20261004-010214-ver-b5bcad'],
};
export type Prediction = '' | 'pass' | 'fail' | 'unsure';
export interface RepairNotes {
  schema: 'countertrace-repair-practice-v1';
  predictions: [Prediction, Prediction];
  revealed: [boolean, boolean];
  reasoning: [string, string];
  reflection: string;
  transfer: string;
  compared: boolean;
}
export const freshRepairNotes = (): RepairNotes => ({schema:'countertrace-repair-practice-v1', predictions:['',''], revealed:[false,false], reasoning:['',''], reflection:'', transfer:'', compared:false});
export function readRepairNotes(raw: string | null): RepairNotes {
  try {
    const n = JSON.parse(raw ?? 'null');
    if (n?.schema !== 'countertrace-repair-practice-v1' || !Array.isArray(n.predictions) || n.predictions.length !== 2 || !n.predictions.every((p:unknown)=>['','pass','fail','unsure'].includes(p as string)) || !Array.isArray(n.revealed) || n.revealed.length !== 2 || !n.revealed.every((p:unknown)=>typeof p === 'boolean') || !Array.isArray(n.reasoning) || n.reasoning.length !== 2 || !n.reasoning.every((p:unknown)=>typeof p === 'string' && p.length <= 2000) || typeof n.reflection !== 'string' || n.reflection.length > 2000 || typeof n.transfer !== 'string' || n.transfer.length > 2000 || typeof n.compared !== 'boolean') return freshRepairNotes();
    if (n.revealed.some((r:boolean,i:number)=>r && (!n.predictions[i] || !n.reasoning[i].trim())) || (n.revealed[1] && !n.revealed[0]) || (n.compared && (!n.revealed[1] || !n.transfer.trim() || !n.reflection.trim()))) return freshRepairNotes();
    return n;
  } catch { return freshRepairNotes(); }
}
const canonical = (v: unknown): string => {
  if (Array.isArray(v)) return `[${v.map(canonical).join(',')}]`;
  if (v && typeof v === 'object') return `{${Object.entries(v).sort(([a],[b])=>a.localeCompare(b)).map(([k,x])=>`${JSON.stringify(k)}:${canonical(x)}`).join(',')}}`;
  return JSON.stringify(v);
};
/** Fail closed before presenting the curated case as a complete comparison. */
export function validateRepairCase(parent: Run, candidates: Run[]) {
  if (parent.id !== repairCase.parent || parent.state !== 'complete' || !parent.recorded || !parent.verification?.frozen || parent.repair?.attempts.length !== 2 || candidates.length !== 2) throw new Error('The recorded repair case is incomplete.');
  const expected = new Map([['simulation:empty_flag','simulation_passed'],['simulation:full_flag','simulation_passed'],['simulation:read_data','simulation_passed'],['bmc:empty_flag','bounded_pass'],['bmc:full_flag','bounded_pass'],['bmc:read_data','bounded_pass'],['prove:empty_flag','proved'],['prove:full_flag','proved'],['prove:read_data','proved'],['cover:reachability','bounded_pass']]);
  candidates.forEach((run,i)=>{
    const a=parent.repair!.attempts[i]!; const v=run.verification;
    if (run.id !== repairCase.candidates[i] || run.parent_id !== parent.id || !run.recorded || run.state !== 'complete' || !v || !v.frozen || !Array.isArray(v.integrity) || v.integrity.length || !v.integrity_checked?.includes('sim') || !v.integrity_checked?.includes('formal') || a.candidate_run_id !== run.id || a.origin !== 'model' || !a.diff || !a.calls?.length || a.frozen_match !== true || canonical(v.frozen)!==canonical(parent.verification!.frozen) || canonical(parent.repair!.parent_frozen)!==canonical(v.frozen) || v.obligations.length !== expected.size || new Set(v.obligations.map(o=>o.id)).size !== expected.size || v.obligations.some(o=>!expected.has(o.id))) throw new Error('Candidate evidence or the unchanged comparison could not be confirmed.');
    if (i===0 && (a.status!=='failed_checks' || !v.findings.length || !v.obligations.some(o=>o.status==='counterexample'))) throw new Error('The rejected candidate has no confirming counterexample.');
    if (i===1 && (!v.formal_covers || Object.keys(v.formal_covers).length !== 12 || Object.values(v.formal_covers).some(c=>c.reached !== true) || a.status!=='passed_unchanged_checks' || v.findings.length || v.obligations.some(o=>o.status!==expected.get(o.id)))) throw new Error('The final candidate does not have all expected check results.');
  });
  return {parent,candidates,attempts:parent.repair.attempts};
}
export function repairNotesReport(n: RepairNotes): string {
  return ['# Countertrace: challenge a Nemotron repair','Anonymous, self-reported practice. No measured learning gain.','Recorded case: '+repairCase.parent,...n.predictions.map((p,i)=>`## Candidate ${i+1}\nPrediction: ${p || 'Unanswered'}\nReason: ${n.reasoning[i] || 'Unanswered'}\nRecorded result viewed: ${n.revealed[i] ? 'yes' : 'no'}\nEvidence: ${repairCase.candidates[i]}`),'## What changed my decision\n'+(n.reflection || 'Unanswered'),'## Transfer: does depth 4 establish depth 8?\n'+(n.transfer || 'Unanswered'),'Reference explanation viewed: '+(n.compared?'yes':'no')].join('\n\n');
}
