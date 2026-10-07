# Countertrace repair-lab demo script

Target length: 2:45. This is a script, not recorded or published footage. The owner records and publishes separately. Reviewers may assess the proposed story from this script; actual video quality remains unknown.

| Time | Screen and action | Spoken point |
| --- | --- | --- |
| 0:00–0:20 | New home; the casebook of four cases; enter case 01 | “A patch is a hypothesis. Countertrace helps digital-design students challenge actual Nemotron repairs using hardware evidence.” Name instructors and FPGA mentors as facilitators. |
| 0:20–0:55 | Case 01: read the contract and first patch, choose a prediction, open **Test it yourself first**, add Write four times, then reveal checks. | “Nemotron guarded the read. Before the reveal, I test it myself: four writes fill the queue, and at edge four this candidate also reports empty. The recorded checks find the same kind of counterexample.” Keep recorded labels visible. |
| 0:55–1:20 | Revised proposal; commit a prediction; reveal the frozen results. | “The counterexample went back to Nemotron, and the next patch compares the whole pointer. Same contract, harness, stimuli and configuration: three simulation passes, three bounded passes, three proofs, and the cover group.” Show the depth-4 scope. |
| 1:20–1:35 | Casebook row: open case 02, show its bug report and the rejected first patch | “Three more cases: a fix that breaks code that was working, three rounds on one flag, and a one-line fix that was right the first time.” |
| 1:35–2:05 | Testbench lab: load a typical first testbench, predict, run; then select only simultaneous and run again | “Now the learner’s own testbench. The typical first one catches three of six seeded bugs, and each miss names what it never tried, like writing while full. One well-chosen test catches all six in fifteen edges.” |
| 2:05–2:25 | Teaching desk and discussion plan; downloaded notes | “An instructor shares any case and reviews voluntarily shared notes. These are demonstration answers.” |
| 2:25–2:45 | Home and closing | “Real Nemotron proposals through Nebius Token Factory, independent RTL checks, and debugging exercises built from recorded evidence. Live verification and model calls run in the configured local build.” |

## Recording readiness

Case 01 uses three actual linked records: parent `rec-20261004-010137-ver-dd43e0`, rejected candidate `rec-20261004-010200-ver-42e87f`, and accepted candidate `rec-20261004-010214-ver-b5bcad`. The probe and testbench lab replay recorded verifier runs. Do not suggest the browser executes RTL or requests a new repair. Downloaded demo notes are created during rehearsal and explicitly labeled; no invented group import or testimonial is needed.

Derived finding metadata was corrected after trace review. When showing the detailed workbench, preserve its correction warning and original model text. Reference validation does not certify semantic accuracy. Do not cut errors into a successful result or imply the depth-4 proof covers all hardware.
