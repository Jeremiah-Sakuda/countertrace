# Third party notices

Countertrace source, fixtures, harness, and fault library are new work for this project under the [MIT license](LICENSE). No AKILI code, tutorial defects, or model weights are included. One third-party RTL file is included for evaluation (below). The PRD and documentation cite research and tool documentation as references; citation is not incorporation.

## Third-party RTL

| File | Source | License | Modifications |
| --- | --- | --- | --- |
| `fixtures/independent/billdmar/sync_fifo.sv` | [billdmar/fifo-verification-suite](https://github.com/billdmar/fifo-verification-suite) `rtl/sync_fifo.sv` at commit `07da90c68d6d43c245d3ead9e5894d8398390f34`, by William Mar | MIT (copy in `fixtures/independent/billdmar/LICENSE`) | None. Evaluation faults are applied as separate edits at run time; a validated interface mapping is stored beside it. |

## Verification toolchain (not redistributed)

The verifier image is built locally by `countertrace build-image` from [verifier/Dockerfile](verifier/Dockerfile). This repository does not distribute the image or tool binaries. Anyone who publishes the image must include the notices of its components.

| Component | Pin | License | Source |
| --- | --- | --- | --- |
| Debian bookworm-slim base | `sha256:3783cc01769c7b2b1b83a5c5ad96c815348e28ed7da68e2e3687004faa906251` (multi-arch index) | Debian packages under their own licenses | https://hub.docker.com/_/debian |
| OSS CAD Suite release `2026-09-30` | tarball SHA-256 `128ea0dd…d257` (arm64), `9e50078d…95fc1` (x64) | Bundle of tools under their own licenses; see `/opt/oss-cad-suite/license/` in the image | https://github.com/YosysHQ/oss-cad-suite-build |
| Verilator 5.053 (from OSS CAD Suite) | as above | LGPL-3.0 (upstream also offers Artistic-2.0) | https://verilator.org |
| Yosys 0.69+158, SymbiYosys, yosys-abc, Yices 2 (from OSS CAD Suite) | as above | ISC (Yosys, SBY), UC Berkeley permissive license (ABC), GPL-3.0 (Yices 2) | https://github.com/YosysHQ |
| Debian packages: g++, make, python3, perl, curl, ca-certificates | Debian bookworm at build time | GPL / Artistic / other Debian licenses | https://www.debian.org |

The pinned tool versions observed in each run are recorded in its evidence manifest.

## Web interface dependencies

The web interface in `apps/web` depends on npm packages (React, Vite, TypeScript, lucide-react, and their transitive dependencies) under their own licenses, listed in `apps/web/package-lock.json`. The production build bundles React and lucide-react (MIT and ISC). Fonts Newsreader, DM Sans, and JetBrains Mono are loaded from Google Fonts under the SIL Open Font License 1.1.

## Design guidance

The interface's design system was generated with [UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) (commit `09170ee`, MIT License, Copyright (c) 2024 Next Level Builder). Its generated recommendations are persisted under `apps/web/design-system/`. No code from that project is included in the application.

## Services

NVIDIA Nemotron models are accessed at runtime through Nebius Token Factory under the account holder's terms. No model weights are distributed. GitHub Actions and Python build tooling are used under their own licenses and are not relicensed by this repository.

Before adding a dependency or fixture, record its source URL, pinned version or commit, license, modifications, and redistribution requirements here or in an adjacent provenance file.
