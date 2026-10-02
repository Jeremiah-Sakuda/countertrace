# Independently authored FIFO: admission pending

The current count-based and wrap-bit FIFOs share an author. Different implementations or depths from that author do not meet the PRD's independently authored requirement.

An external candidate has been acquired into ignored `evaluation/holdout/billdmar-sync-fifo/`. Only repository metadata, README, license, and byte hashes were used for selection. Its RTL has not been read into development context or executed by Countertrace. Its status is **candidate only**, not a correct control or an admitted evaluation case.

| Provenance | Value |
| --- | --- |
| Repository | [billdmar/fifo-verification-suite](https://github.com/billdmar/fifo-verification-suite) |
| Author attribution | William Mar, from the MIT license |
| Pinned commit | `07da90c68d6d43c245d3ead9e5894d8398390f34` |
| Candidate | `rtl/sync_fifo.sv` |
| Source SHA-256 | `7f360f186f3194d6ba9ac9017e343124b8a41b547615257c0300d530adc6ca65` |
| License SHA-256 | `fbe71839f7e00220bbeaa84b8378255d71315e51cb4c3edb098c0ac45755b66b` |
| Local evidence | Original source, MIT license, and `provenance.json` in the ignored directory |

The README describes a parameterized registered-read FIFO; that does not establish compatibility with the entire Countertrace contract. The current admission layer is intentionally strict. Extra outputs, reset semantics, syntax, parameter names, and boundary behavior still need review.

## Reviewer handoff

Ask the technical reviewer to assess the unmodified source against `sync-fifo-v1`, particularly synchronous active-high reset, registered reads, ignored writes while full including simultaneous reads, ignored reads while empty, and 8-bit depth-4 behavior. Depth 2 is not assumed supported by this candidate. Record the author's provenance and any shared ancestry with development fixtures.

A validated port-name mapping is permitted by the PRD; arbitrary adapter logic or edits that turn an incompatible design into a compatible one are not a clean held-out control. If the source requires unsupported syntax or behavior, report it as unsupported and select another candidate or have an independent reviewer author one from the frozen public contract. Do not weaken admission, change the oracle, or tune prompts around this source to make it count.

Keep review notes, ground-truth labels, derived faults, and final regressions in ignored `holdout/`. The reviewer should document the source hash, accepted configuration/mapping, expected outcomes, defect classes, and evidence for labels. Commit the public protocol and frozen configuration hashes before running final evaluation; keep hidden labels out of model feedback. After evaluation, publish only authorized fixtures and outcomes with attribution and any contamination disclosed.

One accepted independent FIFO can satisfy the implementation-diversity requirement alongside the existing implementation, but the suite still needs eight faulty cases and four controls. Candidate acquisition does not establish that suite. Preserve unsupported cases in the acquisition record and replace them before the evaluation freeze.
