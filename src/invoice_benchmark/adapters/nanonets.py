from __future__ import annotations

import os
import time
from pathlib import Path

from invoice_benchmark.adapters.base import VendorAdapter
from invoice_benchmark.models import ParseResult


class NanonetsAdapter(VendorAdapter):
    name = "nanonets"

    @staticmethod
    def _resolve_endpoint() -> str | None:
        model_endpoint = os.getenv("NANONETS_MODEL_ENDPOINT")
        if model_endpoint:
            return model_endpoint

        model_id = os.getenv("NANONETS_MODEL_ID")
        if not model_id:
            return None

        base_url = os.getenv("NANONETS_BASE_URL", "https://app.nanonets.com")
        return f"{base_url.rstrip('/')}/api/v2/OCR/Model/{model_id}/LabelFile/"

    def parse(self, file_path: Path, invoice_type: str, dry_run: bool = False) -> ParseResult:
        if dry_run:
            return ParseResult(
                vendor=self.name,
                invoice_type=invoice_type,
                file_name=file_path.name,
                raw_response={
                    "invoice_number": file_path.stem,
                    "invoice_date": None,
                    "due_date": None,
                    "subtotal": None,
                    "tax": None,
                    "total": None,
                    "line_items": [],
                },
                latency_ms=0.0,
                cost_usd_estimated=None,
                status="dry_run",
            )

        endpoint = self._resolve_endpoint()
        api_key = os.getenv("NANONETS_API_KEY")
        if not endpoint:
            return ParseResult(
                vendor=self.name,
                invoice_type=invoice_type,
                file_name=file_path.name,
                raw_response={},
                latency_ms=0.0,
                cost_usd_estimated=None,
                status="error",
                error_message="Missing env var: NANONETS_MODEL_ENDPOINT or NANONETS_MODEL_ID",
            )

        if not api_key:
            return ParseResult(
                vendor=self.name,
                invoice_type=invoice_type,
                file_name=file_path.name,
                raw_response={},
                latency_ms=0.0,
                cost_usd_estimated=None,
                status="error",
                error_message="Missing env var: NANONETS_API_KEY",
            )

        start = time.perf_counter()
        try:
            import requests
            from requests.auth import HTTPBasicAuth

            with file_path.open("rb") as fh:
                response = requests.post(
                    endpoint,
                    auth=HTTPBasicAuth(api_key, ""),
                    files={"file": (file_path.name, fh, "application/pdf")},
                    timeout=120,
                )
            latency_ms = (time.perf_counter() - start) * 1000.0
            response.raise_for_status()
            data = response.json()
            return ParseResult(
                vendor=self.name,
                invoice_type=invoice_type,
                file_name=file_path.name,
                raw_response=data,
                latency_ms=latency_ms,
                cost_usd_estimated=None,
                status="ok",
            )
        except Exception as exc:
            latency_ms = (time.perf_counter() - start) * 1000.0
            return ParseResult(
                vendor=self.name,
                invoice_type=invoice_type,
                file_name=file_path.name,
                raw_response={},
                latency_ms=latency_ms,
                cost_usd_estimated=None,
                status="error",
                error_message=str(exc),
            )
