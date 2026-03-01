# TODO - Next Work Session

Last updated: 2026-03-01 (Asia/Seoul)

## Progress Log
- 2026-03-01: Veryfi credentials switched to new account (`camille.choe`) and retested on `Outre/SINV1647411.pdf`.
  - Veryfi: `HTTP 201` (resolved from previous 403), `invoice_number=SINV1647411`, `total=800.0`, `line_items=6`
  - Saved files updated:
    - `artifacts/raw/smoke_single_20260301/veryfi_response.json`
    - `artifacts/raw/smoke_single_20260301/veryfi_http.txt`
- 2026-03-01: Veryfi account state confirmed as trial ended.
  - Message: `Your trial has ended. Please contact support@veryfi.com to upgrade your account.`
  - Impact: Veryfi API calls are blocked until billing/support action is completed.
  - Temporary plan: continue smoke/benchmark with `nanonets,upstage,gdocai`; mark Veryfi as blocked in comparison notes.
- 2026-03-01: All current local changes committed and pushed to GitHub (`main`, commit `2c51359`).
  - Includes: `README.md`, `SYSTEM_SUMMARY.md`, `TODO.md`, `reports/*`, `docs/*`
  - GitHub Pages content prepared under `docs/`
  - Target URL: `https://jaydenchoe.github.io/invoice_eng_comp/`
  - Current check: `404` (repository Pages setting still needs to be enabled)
- 2026-03-01: Single-file smoke run completed on `Outre/SINV1647411.pdf` with 3 engines (`veryfi,nanonets,upstage`).
  - Veryfi: `HTTP 403` (auth/plan/quota recheck needed), response saved at `artifacts/raw/smoke_single_20260301/veryfi_response.json`
  - Nanonets: `HTTP 200`, key fields detected (`invoice_number=SINV1647411`, `invoice_amount=800.00`)
  - Upstage: `HTTP 200`, structured extraction succeeded (`invoice_number=SINV1647411`, `total=800.0`, `line_items=3`)
  - HTTP logs:
    - `artifacts/raw/smoke_single_20260301/veryfi_http.txt`
    - `artifacts/raw/smoke_single_20260301/nanonets_http.txt`
    - `artifacts/raw/smoke_single_20260301/upstage_http.txt`
  - Next action: fix Veryfi 403, then rerun same single-file smoke set.
- 2026-03-01: Google Document AI added on the same sample (`Outre/SINV1647411.pdf`) for 4-service comparability.
  - Google Document AI: `HTTP 200`, `invoice_number=SINV1647411`, `invoice_date=03/03/23`, `entities_count=10`, `pages_count=1`
  - Saved files:
    - `artifacts/raw/smoke_single_20260301/gdocai_response.json`
    - `artifacts/raw/smoke_single_20260301/gdocai_http.txt`
    - `artifacts/raw/smoke_single_20260301/gdocai_summary.json`
- 2026-03-01: Web-view report generated for easy result review.
  - Report HTML: `reports/smoke_single_20260301.html`
  - Shortcut index: `reports/index.html`

## Current Direction (Confirmed)
- Invoice recognition services in scope: 4
  - Veryfi
  - Nanonets
  - Google Document AI
  - Upstage
- For the **next implementation step**, proceed **without Google Document AI**.
  - Reason: first stabilize common schema/adapter flow using other engines.
- Common schema work is still required and will be resumed later.

## Fixed Test Sample Index
- File: `/Users/jaehunchoe/projects/invoice_comparison/invoices/manifests/sample_index_4x1.csv`
- 4 files selected (1 per invoice type):
  - BEE SALES: `BEE SALES/05-20-2024 36949.pdf`
  - EBD: `EBD/06-29-2023 57156.pdf`
  - Outre: `Outre/SINV1647411.pdf`
  - SNG: `SNG/3000275215-IVC(06062024).PDF`

## Pending Tasks
- [x] Run smoke test on 3 engines only: `veryfi,nanonets,upstage`
- [ ] Store raw outputs and verify normalization mapping gaps
- [ ] Draft/adjust common schema based on real outputs (`normalized_invoice_v1` -> next revision if needed)
- [ ] Define table-handling policy for varying sub-table structures
- [ ] Re-enable Google Document AI in flow after schema refinement

## Resume Commands
```bash
cd /Users/jaehunchoe/projects/invoice_comparison
PYTHONPATH=src python3 -m invoice_benchmark.cli run \
  --manifest invoices/manifests/sample_index_4x1.csv \
  --input-root invoices/input \
  --vendors veryfi,nanonets,upstage
```

## Notes
- Keep secrets in `.env` only.
- Keep comparing on normalized outputs.
