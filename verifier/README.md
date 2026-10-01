# Trusted verifier

The pinned worker image and trusted harness. Build with `countertrace build-image` (or `make image`).

- `Dockerfile` pins the Debian base by digest and the OSS CAD Suite `2026-09-30` tarball by SHA-256 (arm64 and x64). The image tag is a content digest of this directory.
- `worker.py` runs inside the container. It validates `/job/job.json` strictly (ids, parameters, limits, test names, formal tasks), runs Yosys to export the elaborated ports and property netlist, compiles and runs the simulation driver with Verilator, and runs SBY tasks. Command lines are fixed in the worker; the job cannot supply commands, flags, or harness files. It writes raw artifacts and a step log to `/out` and makes no pass/fail decision.
- `harness/ct_sim_top.sv` drives one stimulus file per test following the PRD sampling convention and records post-edge outputs with an `END` marker.
- `harness/ct_formal_top.sv` is the independent formal monitor: a reference queue with three assertions (empty flag, full flag, read data after an accepted read), one input assumption (reset at the first edge), and twelve reachability covers. The step-to-cycle offset is documented in the file and in [ARCHITECTURE.md](../docs/ARCHITECTURE.md).
- `harness/ct.sby.in` defines `bmc` (`abc bmc3`), `prove` (`abc pdr`), and `cover` (`smtbmc yices`).

The control service runs the container with no network, a read-only root, a tmpfs `/tmp`, all capabilities dropped, no-new-privileges, CPU, memory, and process limits, and no host environment. It compares the worker's harness hashes with the checkout on every batch and counts the elaborated properties itself.

Generated checks are supplemental and never replace this core. Do not edit the harness during a repair comparison: any change alters the frozen check set and starts a new baseline.
