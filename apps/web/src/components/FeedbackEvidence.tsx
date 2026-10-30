import summary from "../../../../evaluation/results/feedback-recovery-v1/summary.json";
import { Section, TableScroll } from "./common";

const evidence = "https://github.com/Jeremiah-Sakuda/countertrace/blob/6a17c53/evaluation/results/feedback-recovery-v1";

export function FeedbackEvidence() {
  return <Section title="Does feedback help?" eyebrow="Paired recovery pilot · October 16">
    <p><strong>This pilot did not demonstrate an advantage for detailed feedback.</strong> Nemotron revised the same rejected FIFO and debouncer properties with either gate diagnostics or a rejection notice alone. Three repeats per module, one revision per attempt; the independent gate judged both groups.</p>
    <TableScroll label="October 16 feedback comparison">
      <table>
        <thead><tr><th scope="col">Feedback supplied</th><th scope="col">Revisions promoted</th><th scope="col">Model calls</th></tr></thead>
        <tbody>{([
          ["Detailed gate diagnostics", summary.arms.detailed],
          ["Rejection notice only", summary.arms.rejection_only],
        ] as const).map(([label, arm]) => <tr key={label}><th scope="row">{label}</th><td>{arm.promoted} / {arm.attempts}</td><td>{arm.calls}</td></tr>)}</tbody>
      </table>
    </TableScroll>
    <p className="small muted">Two previously exposed fixtures, not a fresh held-out benchmark. Repeats are not independent designs. All failures and retries are retained; these results do not establish general reliability or learning benefits.</p>
    <h3>A new FIFO repair, checked end to end.</h3>
    <p>A newly promoted check set found the seeded overflow defect, confirmed by golden replay. One repair passed all 11 unchanged obligations, including four proved obligations. The checks, failing design and repaired design bundles all replayed successfully. This was a local run at WIDTH=8, DEPTH=4.</p>
    <p><strong>Advisory errors remain visible:</strong> interpretation falsely flagged a compatible full-write rule as conflicting, and the explanation included two unsupported <code>mem[0]</code> citations. Neither output authorized a verification result.</p>
    <p className="small muted">Comparison plus end-to-end run: {summary.total.calls + summary.end_to_end_usage.calls} model calls, approximately ${summary.combined_estimated_cost_usd.toFixed(2)} estimated inference cost. Token usage is provider-reported; cost is calculated, not an invoice. These are preserved October 16 results; opening this page makes no model call.</p>
    <div className="actions">
      <a className="btn btn-secondary" href={`${evidence}/REPORT.md`}>Read the October 16 report</a>
      <a href={`${evidence}/results.json`}>Inspect all comparison responses</a>
      <a href={`${evidence}/end-to-end.json`}>Inspect the repair and replay evidence</a>
    </div>
  </Section>;
}
