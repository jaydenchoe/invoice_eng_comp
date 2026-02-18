from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from invoice_benchmark.adapters.registry import ADAPTERS
from invoice_benchmark.config import load_dotenv
from invoice_benchmark.models import InvoiceDoc
from invoice_benchmark.normalize import to_normalized


def scan_input(input_root: Path) -> dict[str, int]:
    result: dict[str, int] = {}
    for d in sorted(input_root.iterdir()):
        if not d.is_dir():
            continue
        count = 0
        for f in d.iterdir():
            if f.is_file() and f.suffix.lower() == ".pdf":
                count += 1
        result[d.name] = count
    return result


def build_manifest(input_root: Path, per_type: int, output_csv: Path) -> int:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with output_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["invoice_type", "relative_path"])
        writer.writeheader()

        for invoice_type in sorted([d.name for d in input_root.iterdir() if d.is_dir()]):
            files = sorted(
                [f for f in (input_root / invoice_type).iterdir() if f.is_file() and f.suffix.lower() == ".pdf"],
                key=lambda x: x.name,
            )
            for f in files[:per_type]:
                rel = str(Path(invoice_type) / f.name)
                writer.writerow({"invoice_type": invoice_type, "relative_path": rel})
                total += 1
    return total


def load_manifest(manifest_csv: Path) -> list[InvoiceDoc]:
    docs: list[InvoiceDoc] = []
    with manifest_csv.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            docs.append(InvoiceDoc(invoice_type=row["invoice_type"], relative_path=row["relative_path"]))
    return docs


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def run_benchmark(manifest: Path, input_root: Path, vendors: list[str], dry_run: bool) -> Path:
    docs = load_manifest(manifest)

    raw_root = Path("artifacts/raw")
    norm_root = Path("artifacts/normalized")
    metrics_root = Path("artifacts/metrics")
    ensure_dir(raw_root)
    ensure_dir(norm_root)
    ensure_dir(metrics_root)

    rows = []

    for vendor in vendors:
        adapter_cls = ADAPTERS[vendor]
        adapter = adapter_cls()
        for doc in docs:
            file_path = doc.absolute_path(input_root)
            result = adapter.parse(file_path=file_path, invoice_type=doc.invoice_type, dry_run=dry_run)
            normalized = to_normalized(result)

            safe_stem = file_path.stem.replace("/", "_")
            raw_path = raw_root / vendor / doc.invoice_type / f"{safe_stem}.json"
            norm_path = norm_root / vendor / doc.invoice_type / f"{safe_stem}.json"
            ensure_dir(raw_path.parent)
            ensure_dir(norm_path.parent)

            raw_path.write_text(json.dumps(result.raw_response, ensure_ascii=False, indent=2), encoding="utf-8")
            norm_path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")

            rows.append(
                {
                    "vendor": vendor,
                    "invoice_type": doc.invoice_type,
                    "file_name": file_path.name,
                    "status": result.status,
                    "latency_ms": round(result.latency_ms, 2),
                    "cost_usd_estimated": result.cost_usd_estimated,
                    "error_message": result.error_message,
                    "raw_path": str(raw_path),
                    "normalized_path": str(norm_path),
                }
            )

    metrics_csv = metrics_root / "run_metrics.csv"
    with metrics_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "vendor",
                "invoice_type",
                "file_name",
                "status",
                "latency_ms",
                "cost_usd_estimated",
                "error_message",
                "raw_path",
                "normalized_path",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    return metrics_csv


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Invoice benchmark CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    scan_p = sub.add_parser("scan")
    scan_p.add_argument("--input", required=True)

    manifest_p = sub.add_parser("manifest")
    manifest_p.add_argument("--input", required=True)
    manifest_p.add_argument("--per-type", type=int, default=3)
    manifest_p.add_argument("--output", required=True)

    run_p = sub.add_parser("run")
    run_p.add_argument("--manifest", required=True)
    run_p.add_argument("--input-root", required=True)
    run_p.add_argument("--vendors", default="veryfi,nanonets,upstage,gdocai")
    run_p.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    if args.cmd == "scan":
        counts = scan_input(Path(args.input))
        print(json.dumps(counts, ensure_ascii=False, indent=2))
        return

    if args.cmd == "manifest":
        total = build_manifest(Path(args.input), args.per_type, Path(args.output))
        print(f"manifest created: {args.output} (rows={total})")
        return

    if args.cmd == "run":
        vendors = [v.strip() for v in args.vendors.split(",") if v.strip()]
        invalid = [v for v in vendors if v not in ADAPTERS]
        if invalid:
            raise SystemExit(f"Unknown vendors: {', '.join(invalid)}")

        metrics_csv = run_benchmark(
            manifest=Path(args.manifest),
            input_root=Path(args.input_root),
            vendors=vendors,
            dry_run=args.dry_run,
        )
        print(f"run complete: {metrics_csv}")
        return


if __name__ == "__main__":
    main()
