# Hosted deployment (not yet performed)

Nothing in this document has been deployed or tested. It is the proposed route for a judge-accessible build and must be rehearsed before submission (see the [roadmap](ROADMAP.md)).

## Proposed shape

One Nebius Compute CPU VM (start with 4 vCPU and 16 GiB) runs Docker, the verifier image, and the control service behind Caddy for TLS. Runtime Nemotron calls go to Nebius Token Factory. Verification runs in local containers on that VM; Serverless Jobs remain a measured option, not a dependency (the PRD allows the alternative CPU runner, and the documented Jobs startup time and one-hour minimum timeout make per-run jobs a poor fit for the 120-second live-finding target).

## Steps

1. Create the VM (Ubuntu LTS), install Docker, Python 3.11+, Node 20+, Git, and Caddy. Create a `countertrace` user in the `docker` group.
2. Clone the repository to `/opt/countertrace` at the release tag. Run `make image` and `make web`.
3. Write `/etc/countertrace.env` (mode 0600): `NEBIUS_API_KEY`, `NEBIUS_BASE_URL`, `NEBIUS_MODEL_ID`, both token limits, the spend limit with per-token prices, `COUNTERTRACE_PUBLIC_UPLOADS_ENABLED=false`, and optionally `COUNTERTRACE_MODEL_CALLS_PER_VISITOR_HOUR`.
4. Install [deploy/countertrace.service](../deploy/countertrace.service) and [deploy/Caddyfile](../deploy/Caddyfile); enable both.
5. Record curated runs (`countertrace record`) on the VM or ship them from the repository so the first screen opens recorded evidence immediately.
6. From a logged-out browser on another network, complete the judge journey: open the recorded run, start a live run, request an explanation, export a bundle. Measure first-finding and total times cold and warm.

## Operating obligations through December 15, 2026

- Fund Token Factory usage and the VM; record credit expiry dates and the owner responsible.
- Keep the token limits and spend limit configured; watch `.countertrace/model_usage.jsonl`.
- Keep one tested release tag and its recorded runs; do not change the harness or stimulus on the judged deployment.
- Recovery: keep the VM image or a script that rebuilds it from the tag; the verifier image rebuild is checksum-pinned. If inference becomes unavailable, the recorded runs and deterministic checks still work and the interface states that the model is unavailable.
- Judges must not need to buy credits or supply a paid key.
