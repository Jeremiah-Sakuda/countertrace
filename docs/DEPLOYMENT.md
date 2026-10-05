# Deployment

## Public recorded demo on Vercel

**Available:** https://countertrace.vercel.app. The primary route is an interactive learning lab with three lessons, learner-composed experiments, authored hints, transfer questions, local practice exports, and a facilitator desk. Its finite library contains actually executed RTL observations, pinned to the release by SHA-256. Live coaching is available only in the configured local build. The verification workbench retains the published recorded journey: seven recordings, ten bundled examples, two preserved model interpretations, traces, repair histories, the audit exercise, and six downloadable verification bundles. It does not run RTL or make model calls. The UI labels this mode and disables live actions. The full local Docker build remains available separately.

Vercel container functions are stateless; the current control service uses persistent local run files, in-memory ownership/quotas, background threads, and a Docker daemon. Deploying its HTTP process unchanged would not preserve those guarantees. This static deployment keeps the current isolated verifier intact. A future live deployment needs a separately provisioned compatible worker service or an explicitly tested backend adaptation; a container-image upload alone does not supply that. [Vercel container deployment model](https://vercel.com/kb/guide/docker-on-vercel-vs-render), [function limits](https://vercel.com/docs/functions/limitations).

### Reproduce this deployment

```sh
make check
npm --prefix apps/web test
make static-demo
vercel link --project countertrace --scope jeremiah-sakudas-projects
vercel pull --yes --environment=production --scope jeremiah-sakudas-projects
vercel deploy --prebuilt --prod --yes --scope jeremiah-sakudas-projects
.venv/bin/python scripts/check_static_demo.py https://countertrace.vercel.app
```

Build from a clean committed checkout so downloaded bundle manifests identify a replayable commit. `make static-demo` exports the frontend plus API-shaped static data using Vercel's Build Output API. Only Git-tracked curated recordings and verifier files are copied into the export, including the inputs used to assemble bundles. The exporter never loads `.env`, the local run store, or the model usage ledger. Tracked symlinks are refused. No secrets or paid runtime environment variables are required on Vercel.

The Vercel project uses the **Other** framework preset. Its automatic Git deployment was disconnected after linking auto-detected the Python package; publish the explicit prebuilt output above instead of deploying the repository as a Python function. GitHub CI still runs normally. `.vercel/`, CLI environment files, and generated outputs are ignored.

### Public access check, October 4

Unauthenticated HTTP requests (no cookies, CLI bypass token, or owner login) loaded all ten example endpoints and all seven recorded runs. All six verification ZIPs downloaded with matching manifest hashes; mutation requests returned 405 with the recorded-mode explanation. `.env`, `.env.local`, the private model ledger, and an unknown run returned 404. These checks validate the recorded route, not a hosted verifier or a future availability guarantee.

### Remaining live judge access

Judges can inspect and download the recorded evidence free of charge. The local test build runs deterministic verification without an API key, but live Nemotron calls currently need model access. Before submission, provide a project-funded live route or an owner-funded testing arrangement that does not require judges to purchase credits. Preserve the recorded deployment and local release through December 15. Account credit expiry and live-service operating ownership still need verification.

## Optional live CPU service (not deployed)

No VM has been created or funded. The Caddyfile passed local configuration validation with Caddy 2.11.4 on October 1; this does not test DNS, certificates, systemd, public connectivity, or the live judge journey. The following is a retained alternative deployment plan, not work performed by the Vercel release.

## Proposed shape

One Nebius Compute CPU VM (start with 4 vCPU, 16 GiB, and 50 GiB SSD) runs Docker, the verifier image, and the control service behind Caddy for TLS. Runtime Nemotron calls go to Nebius Token Factory. Use local Docker on the VM for the MVP; defer Serverless Jobs unless a measured batch workload justifies it. The PRD permits this CPU runner. Jobs startup can take minutes and its minimum configurable timeout is one hour; that is not a minimum billing duration. [Jobs documentation](https://docs.nebius.com/serverless/jobs/manage)

## Proposed budget, not spending authorization

Use **$300 before tax** as a planning envelope through December 15, 2026, with no GPU VM. A conservative 76 full days starting October 1 is 1,824 hours:

| Item | Calculation | Estimated USD |
| --- | --- | ---: |
| AMD Genoa CPU and RAM | `(4 × 0.015 + 16 × 0.0045) × 1,824` | 240.77 |
| 50 GiB network SSD | `50 × 0.071 × 1,824 / 730` | 8.87 |
| Inference allowance | Proposed starting allocation; not measured usage | 20.00 |
| Reserve | Approximately 10% of the above | 26.96 |
| Total planning estimate | Round up for planning | 296.60 |

Infrastructure rates are the published rates effective October 1, 2026, before tax. Account credits, expiry dates, selected region/preset availability, actual start date, and pricing must be checked before provisioning. Domain registration and additional backups are not included. [Official Compute pricing](https://docs.nebius.com/compute/resources/pricing)

Use the hackathon credits first; do not treat a cash top-up as a prerequisite. The [hackathon resources](https://nebiusglobalaihackathon.devpost.com/resources) offer a $25 Token Factory promo and a further $25 through the Builders Program. The owner reports claiming credits, but balance, application, and expiry remain unverified. The October 3 model experiments used about $0.082 at public rates; this is not confirmed invoiced spend. No top-up or hosting purchase has been made. Confirm whether Token Factory and Cloud have separate balances and where hackathon credits apply. Delaying VM creation reduces compute cost; storage is still charged while a VM is stopped. The owner has asked for a recommendation and has not yet authorized a dollar limit.

The current `COUNTERTRACE_DEPLOYMENT_SPEND_LIMIT_USD` is an inference-ledger threshold, not a hard total deployment cap. Each in-flight call reserves estimated input cost plus its full output allowance; tokenization, missing usage after transport failures, and actual prices can differ, so this does not guarantee a maximum bill. It excludes compute and storage. Configure account billing alerts and record an operating owner before public access. Verify spending and credit validity cover the entire judging window.

## Steps

1. Create the VM (Ubuntu LTS), install Docker, Python 3.11+, Node 20+, Git, and Caddy. Create a `countertrace` user in the `docker` group.
2. Clone the repository to `/opt/countertrace` at the release tag. Run `make image` and `make web`.
3. Write `/etc/countertrace.env` (mode 0600): `NEBIUS_API_KEY`, `NEBIUS_BASE_URL`, `NEBIUS_MODEL_ID`, both token limits, the spend limit with per-token prices, `COUNTERTRACE_PUBLIC_UPLOADS_ENABLED=false`, and optionally `COUNTERTRACE_MODEL_CALLS_PER_VISITOR_HOUR`.
4. Replace the example domain in [deploy/Caddyfile](../deploy/Caddyfile), point DNS to the VM, and install it and [deploy/countertrace.service](../deploy/countertrace.service). Validate the service with `systemd-analyze verify`, run Caddy validation, then enable both. Allow public HTTP/HTTPS; keep the control port bound to loopback.
5. Record curated runs (`countertrace record`) on the VM or ship them from the repository so the first screen opens recorded evidence immediately.
6. From a logged-out browser on another network, complete the judge journey: open the recorded run, start a live run, request an explanation, export a bundle. Measure first-finding and total times cold and warm.

For each deployment check, record the public URL, release commit/image, date, browser/session state, result, timings, and bundle hash. Also test restarting the service and VM, persistence of recordings, missing-model recovery, and disabled public uploads. Do not mark access passed from an owner-authenticated browser or merely from a successful HTTP response.

## Local validation performed

`caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile` returned `Valid configuration` inside a network-disabled, read-only container with writable temporary `/config`, `/data`, and `/tmp`. Image: `caddy:2`, resolved digest `sha256:0c994536bddb66445885237f1a5dcc1916bccea922661c76b4e9fc24061f9b52`; binary version 2.11.4. No ports were exposed. The placeholder domain was not changed, and no certificate was issued. The systemd unit remains untested on Linux.

## Operating obligations through December 15, 2026

- Fund Token Factory usage and the VM; record credit expiry dates and the owner responsible.
- Keep the token limits and spend limit configured; watch `.countertrace/model_usage.jsonl`.
- Keep one tested release tag and its recorded runs; do not change the harness or stimulus on the judged deployment.
- Recovery: keep the VM image or a script that rebuilds it from the tag; the verifier image rebuild is checksum-pinned. If inference becomes unavailable, the recorded runs and deterministic checks still work and the interface states that the model is unavailable.
- Judges must not need to buy credits or supply a paid key.
