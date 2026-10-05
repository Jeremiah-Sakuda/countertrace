export type Action = 'w' | 'r' | 'b' | 'x';
export type Sample = [number | null, number, number, number | null, number, number];
export type Library = { schema: string; depth: number; width: number; max_steps: number; created_at: string; method: string; sequences_per_design: number; provenance: { tools: Record<string, string>; wall_s: number }; designs: Record<string, { source: string; source_sha256: string; origin: string; nodes: Record<string, Sample> }> };
export const actionNames: Record<Action, string> = {w: 'Write', r: 'Read', b: 'Read + write', x: 'Reset'};
export const hex = (n: number | null) => n === null ? 'Not checked' : `0x${n.toString(16).padStart(2, '0').toUpperCase()}`;
export function reference(path: string) {
  let queue: number[] = [];
  return [...path].map((a, i) => {
    const before = [...queue], data = 17 * (i + 1);
    const read = (a === 'r' || a === 'b') && before.length > 0;
    const write = (a === 'w' || a === 'b') && before.length < 2;
    if (a === 'x') queue = [];
    else { if (read) queue.shift(); if (write) queue.push(data); }
    return { cycle: i + 1, action: a as Action, data, before, queue: [...queue], read, write,
      expected: [read ? before[0]! : null, Number(queue.length === 0), Number(queue.length === 2)] };
  });
}
export function evidenceRows(library: Library, id: string, path: string) {
  if (!library.designs[id] || !/^[wrbx]{1,6}$/.test(path)) throw new Error('Choose one to six supported actions.');
  return reference(path).map((row, i) => {
    const sample = library.designs[id]!.nodes[path.slice(0, i + 1)];
    if (!sample || sample.length !== 6 || [1,2,4,5].some(j => sample[j] !== 0 && sample[j] !== 1) || (row.read ? !Number.isInteger(sample[3]) || sample[3]! < 0 || sample[3]! > 255 : sample[3] !== null) || row.expected.some((v, j) => v !== sample[j])) throw new Error('Recorded evidence does not match the reference. No result can be shown.');
    const mismatches = ['read_data', 'empty_flag', 'full_flag'].filter((_, j) => sample[j] !== sample[j + 3]);
    return {...row, sample, mismatches};
  });
}
export const lessons = [
  { id: 'overflow', number: '01', title: 'The disappearing word', concept: 'Capacity & data order', minutes: '5–8 min',
    question: 'When a full queue receives another write, what should happen to the oldest word?',
    choices: ['It stays until an accepted read', 'It is replaced by the new word', 'The queue becomes empty'], answer: 0,
    brief: 'A two-slot queue seems fine when you write and then read. Can a boundary case make it lose a word?',
    hints: ['Try the simplest write/read pair first. What condition does that leave untested?', 'Fill both slots, then request another write before reading.', 'Try Write → Write → Write → Read. Compare the oldest accepted word with dout.'],
    transfer: 'A full depth-4 queue holds [0x11, 0x22, 0x33, 0x44]. Read and write 0x55 are requested together. What remains after the edge?',
    transferChoices: ['[0x22, 0x33, 0x44, 0x55]', '[0x22, 0x33, 0x44]', '[0x11, 0x22, 0x33, 0x44]'], transferAnswer: 1,
    transferWhy: 'Acceptance uses occupancy before the edge: the full queue accepts the read and ignores the write. The slot freed by that read does not change the decision.',
    takeaway: 'A passing fill/drain test can miss a write while full. Preserve the oldest accepted word and test the ignored request explicitly.' },
  { id: 'exchange', number: '02', title: 'Two requests, one decision', concept: 'Simultaneous operations', minutes: '5–8 min',
    question: 'If read and write arrive together while the queue is full, which requests does this contract accept?',
    choices: ['Both, because reading frees space', 'Only the write', 'Only the read'], answer: 2,
    brief: 'This candidate accepts ordinary reads and writes. Investigate whether a simultaneous request changes the story.',
    hints: ['Test both requests with an empty queue, then with one item. Is full different?', 'Acceptance is decided from the queue before the clock edge.', 'Try Write → Write → Read + write. Compare the expected and observed full flag.'],
    transfer: 'The queue is empty. Read and write 0xA5 arrive together. On the following edge, a read arrives alone. Which outcome follows this contract?',
    transferChoices: ['0xA5 is consumed immediately; the next read is ignored', 'The first edge queues 0xA5; the next read returns it', 'Both requests are ignored'], transferAnswer: 1,
    transferWhy: 'When empty, only the write is accepted. There is no bypass read. The next read removes the queued word.',
    takeaway: 'A full-capacity exchange can be a valid policy elsewhere, but it violates this chosen contract. Check intent before calling behavior a bug.' },
  { id: 'control', number: '03', title: 'Know when to stop claiming', concept: 'Evidence & its limits', minutes: '5–8 min',
    question: 'Your sequence produces no mismatch. What can you conclude?',
    choices: ['The hardware is correct for every input', 'This sequence did not expose a mismatch', 'Any remaining bug must be in the checker'], answer: 1,
    brief: 'Candidates are not always faulty. Explore reset, simultaneous requests, and pointer wraparound, then state exactly what your tests establish.',
    hints: ['Try Write → Read → Write → Read → Write → Read to cross a pointer wrap.', 'Test Read + write when empty and when full. Also try a reset after writing.', 'No mismatch is a scoped observation. You do not have to invent a failure to finish this lab.'],
    transfer: 'A bounded checker finds no counterexample through 24 cycles. Which statement is justified?',
    transferChoices: ['No counterexample was found within 24 cycles under the stated assumptions', 'All future behavior is proved correct', 'Every physical FPGA implementation is safe'], transferAnswer: 0,
    transferWhy: 'A bounded result covers its stated horizon and assumptions. It is not an unbounded proof or evidence about physical timing.',
    takeaway: 'A useful engineer can distinguish a witnessed defect, a passing simulation, a bounded result, and a property proof.' },
] as const;
export type Attempt = {path: string; prediction: string; firstMismatch: number | null};
export type Session = {version: 1; lesson: string; started: string; initialAnswer: number | null; initialCorrect: boolean | null; attempts: Attempt[]; hints: number; authoredHints: number; reflection: string; transferAnswer: number | null; transferCorrect: boolean | null; completed: string | null};
export function newSession(lesson: string): Session { return {version:1, lesson, started:new Date().toISOString(), initialAnswer:null, initialCorrect:null, attempts:[], hints:0, authoredHints:0, reflection:'', transferAnswer:null, transferCorrect:null, completed:null}; }
export function sessionReport(s: Session) {
  return `# Countertrace learning record\n\nLesson: ${s.lesson}\nStarted: ${s.started}\nCompleted: ${s.completed ?? 'In progress'}\n\nInitial answer: ${s.initialAnswer === null ? 'Unanswered' : s.initialAnswer + 1} (${s.initialCorrect === null ? 'unscored' : s.initialCorrect ? 'matched contract' : 'revisit'})\nHints opened: ${s.hints}\n\n## Experiments\n${s.attempts.map((a,i)=>`${i+1}. ${a.path.split('').map(x=>actionNames[x as Action]).join(' → ')}; prediction: ${a.prediction}; ${a.firstMismatch === null ? 'no mismatch in this sequence' : `first mismatch at edge ${a.firstMismatch}`}`).join('\n')}\n\n## Learner explanation (ungraded)\n${s.reflection || 'Not supplied'}\n\nTransfer answer: ${s.transferAnswer === null ? 'Unanswered' : s.transferAnswer+1}; ${s.transferCorrect === null ? 'unscored' : s.transferCorrect ? 'matched contract' : 'revisit'}\n\nThis is a self-reported practice record, not a certificate or measured learning gain. Browser results replay a finite library of RTL simulations. No live model call or RTL execution occurs on Vercel.\n`;
}

export function validateSession(value: unknown): Session {
  if (!value || typeof value !== 'object') throw new Error('Invalid Countertrace session.');
  const s = value as Session;
  const l = lessons.find(l => l.id === s.lesson);
  if (s.version !== 1 || !l || typeof s.started !== 'string' || !Number.isFinite(Date.parse(s.started)) ||
      !(s.completed === null || typeof s.completed === 'string' && Number.isFinite(Date.parse(s.completed))) ||
      !Array.isArray(s.attempts) || s.attempts.length > 200 ||
      !Number.isInteger(s.hints) || s.hints < 0 || s.hints > 1000 ||
      !Number.isInteger(s.authoredHints) || s.authoredHints < 0 || s.authoredHints > 3 || s.hints < s.authoredHints ||
      typeof s.reflection !== 'string' || s.reflection.length > 2000 ||
      ![null,0,1,2].includes(s.initialAnswer) || ![null,0,1,2].includes(s.transferAnswer) ||
      s.attempts.some(a => !a || typeof a.path !== 'string' || !/^[wrbx]{1,6}$/.test(a.path) ||
        !['mismatch','no-mismatch','unsure'].includes(a.prediction) ||
        !(a.firstMismatch === null || Number.isInteger(a.firstMismatch) && a.firstMismatch >= 1 && a.firstMismatch <= a.path.length))) {
    throw new Error('Invalid Countertrace session.');
  }
  return {...s, initialCorrect:s.initialAnswer === null ? null : s.initialAnswer === l.answer,
    transferCorrect:s.transferAnswer === null ? null : s.transferAnswer === l.transferAnswer};
}
