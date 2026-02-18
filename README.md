# invoice_comparison

Local CLI benchmark harness for comparing invoice parsing across Veryfi, Nanonets, Upstage, and Google Document AI.

## What this does
- Reads invoices from `invoices/input/<invoice_type>/*`
- Calls each vendor adapter and stores vendor `raw JSON`
- Builds a vendor-agnostic `normalized JSON` (common schema)
- Produces run metrics and a benchmark markdown report template

## Project layout
- `invoices/input/`: source invoice files grouped by type (folder name = type)
- `invoices/manifests/`: selected invoice lists for runs
- `src/invoice_benchmark/`: CLI + adapters + normalization
- `schemas/normalized_invoice_v1.schema.json`: common schema
- `artifacts/raw/`: vendor raw responses
- `artifacts/normalized/`: normalized outputs
- `artifacts/metrics/`: run metrics/results
- `benchmarks/report_template.md`: benchmark report template

## Quick start
1. Create and activate a Python 3.10+ environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Scan dataset:
   ```bash
   python -m invoice_benchmark.cli scan --input invoices/input
   ```
4. Build manifest (example: 3 per type => 12 total for 4 types):
   ```bash
   python -m invoice_benchmark.cli manifest \
     --input invoices/input \
     --per-type 3 \
     --output invoices/manifests/manifest_4x3.csv
   ```
5. Run benchmark (dry run first):
   ```bash
   python -m invoice_benchmark.cli run \
     --manifest invoices/manifests/manifest_4x3.csv \
     --input-root invoices/input \
     --vendors veryfi,nanonets,upstage,gdocai \
     --dry-run
   ```

## Vendor integration notes
Adapters are scaffolded behind a single interface. Real API calls are implemented in adapter classes and controlled by env vars.
- `VERYFI_API_URL`, `VERYFI_CLIENT_ID`, `VERYFI_USERNAME`, `VERYFI_API_KEY`
- `NANONETS_BASE_URL`, `NANONETS_API_KEY`, `NANONETS_MODEL_ID` (or `NANONETS_MODEL_ENDPOINT`)
- `UPSTAGE_EXTRACT_ENDPOINT`, `UPSTAGE_API_KEY` (`UPSTAGE_MODEL`/`UPSTAGE_RESPONSE_SCHEMA_JSON` optional)
- `GDOCAI_PROCESSOR_ENDPOINT`, `GDOCAI_ACCESS_TOKEN`

Copy `.env.example` to `.env` and fill values before non-dry runs.
Google Document AI access tokens expire; refresh `GDOCAI_ACCESS_TOKEN` when needed.

Update adapter request/response mapping as needed for your API contracts.

## Active Type Comparison (checked 2026-02-18)
This project uses one active mode per vendor (not every possible mode).

| Service | Active type in this project | Schema definition required? | Labeled training data required up front? | Practical interpretation |
|---|---|---|---|---|
| Veryfi | Invoice OCR API (prebuilt) | No (vendor-defined output) | No | Prebuilt baseline. Fast onboarding, then map to normalized schema. |
| Nanonets | Custom Model | Yes (label set / field design) | Yes | Best when your invoice layout variation is large and you can maintain labels. |
| Google Document AI | Custom Extractor only | Yes | Depends on mode (schema-only zero-shot possible, few-shot/fine-tune uses labels) | Main custom baseline for your variable invoice structures. |
| Upstage | Universal Extraction | Yes (`response_format.json_schema`) | No (schema-driven extraction) | Schema-driven without classical training pipeline. |

### What this means for us
1. Keep one canonical benchmark target: `normalized_invoice_v1`.
2. Run a mixed benchmark by design:
   - Prebuilt baseline: Veryfi
   - Custom/schema-driven: Nanonets Custom, Document AI Custom Extractor, Upstage Universal
3. For fair comparison, evaluate only normalized outputs and the same required fields.
4. Project decision: Google Document AI stays **Custom Extractor only**.

### Sources
- Veryfi docs (data extraction + model training updates): [docs.veryfi.com](https://docs.veryfi.com/) and [Model Training](https://docs.veryfi.com/api/getting-started/model-training/)
- Nanonets prebuilt invoice/custom model docs: [Invoices](https://docs.nanonets.com/docs/invoices), [Pre-Built Model](https://docs.nanonets.com/docs/setup-pre-built-model), [Custom Model](https://docs.nanonets.com/docs/setup-custom-model)
- Google Document AI extraction docs: [Extraction overview](https://docs.cloud.google.com/document-ai/docs/extracting-overview), [Custom extractor with generative AI](https://docs.cloud.google.com/document-ai/docs/ce-with-genai)
- Upstage Information Extraction API console references: [Universal Extraction](https://console.upstage.ai/api/information-extraction/universal-extraction), [Schema Generation](https://console.upstage.ai/api/information-extraction/universal-extraction/schema-generation), [Async](https://console.upstage.ai/api/information-extraction/universal-extraction/async), [Prebuilt Extraction](https://console.upstage.ai/api/information-extraction/prebuilt-extraction)

Inference note: rows above reflect the currently selected operating mode for each vendor in this project, not all product modes each vendor offers.
