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

## Schema Strategy For Diverse Invoice Types
Question: if invoice layouts vary, should we create one schema per type, or force one engine/schema for all?

### Short answer
Use a **hybrid strategy**:
1. Keep one canonical output schema for evaluation (`normalized_invoice_v1`).
2. Group invoice types into 2-4 families and use one extraction schema/model per family.
3. Split into fully separate schemas only when line-item/table semantics are fundamentally different.

### Why this is better than extremes
- One schema per invoice template:
  - High precision early, but maintenance cost grows quickly as formats drift.
  - Community/open-source template projects (for example `invoice2data`) explicitly operate template-by-template, and users report ongoing debugging/maintenance pain in issue threads.
- One universal schema for everything:
  - Lower maintenance, but recall drops when table structures differ too much (different columns, units, discount/tax logic).
- Hybrid (recommended):
  - Preserves one benchmark target while allowing type-aware extraction where needed.
  - Fits your chosen stack: Document AI Custom Extractor + Nanonets Custom + Upstage Universal (schema-driven), with Veryfi as prebuilt baseline.

### Split vs Group decision rules
Create a separate type-family schema/model when at least one is true:
1. Line item column meaning differs (e.g., `qty x unit_price` vs weight/pack-size price logic).
2. Required fields differ by business logic (e.g., credit memo style vs standard invoice).
3. One family causes repeated extraction failure/noise in another family.

Keep grouped when:
1. Header fields are mostly shared (`invoice_number/date/due_date/subtotal/tax/total`).
2. Table differences can be normalized by adapter mapping without losing meaning.
3. Accuracy delta is small enough versus operational cost.

### Practical plan for this repo
1. Keep `normalized_invoice_v1` as the only scoring schema.
2. Start with 4 invoice types grouped into 2-4 families (initially same as current type folders).
3. Use one extractor config per family for:
   - Document AI Custom Extractor
   - Nanonets Custom Model
   - Upstage Universal `response_format` schema
4. Revisit grouping after first benchmark round (12-20 docs).

### Sources
- Veryfi docs (data extraction + model training updates): [docs.veryfi.com](https://docs.veryfi.com/) and [Model Training](https://docs.veryfi.com/api/getting-started/model-training/)
- Nanonets prebuilt invoice/custom model docs: [Invoices](https://docs.nanonets.com/docs/invoices), [Pre-Built Model](https://docs.nanonets.com/docs/setup-pre-built-model), [Custom Model](https://docs.nanonets.com/docs/setup-custom-model)
- Google Document AI docs: [Extraction overview](https://docs.cloud.google.com/document-ai/docs/extracting-overview), [Template-based extraction](https://docs.cloud.google.com/document-ai/docs/template-based-extraction), [Custom extractor with generative AI](https://docs.cloud.google.com/document-ai/docs/ce-with-genai), [Custom splitter](https://docs.cloud.google.com/document-ai/docs/custom-splitter)
- Upstage references: [Universal Extraction](https://console.upstage.ai/api/information-extraction/universal-extraction), [Schema Generation](https://console.upstage.ai/api/information-extraction/universal-extraction/schema-generation), [Async](https://console.upstage.ai/api/information-extraction/universal-extraction/async), [Prebuilt Extraction](https://console.upstage.ai/api/information-extraction/prebuilt-extraction), [Universal extraction blog](https://www.upstage.ai/blog/en/introducing-upstage-universal-information-extraction)
- Community references: [`invoice2data` project](https://github.com/invoice-x/invoice2data), [maintenance discussion example](https://github.com/invoice-x/invoice2data/issues/339)

Inference note: rows above reflect the currently selected operating mode for each vendor in this project, not all product modes each vendor offers.
