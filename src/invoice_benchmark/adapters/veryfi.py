from __future__ import annotations

import os
import time
from pathlib import Path
from urllib.parse import urlparse

from invoice_benchmark.adapters.base import VendorAdapter
from invoice_benchmark.models import ParseResult


class VeryfiAdapter(VendorAdapter):
    name = "veryfi"

    @staticmethod
    def _resolve_endpoint(base_or_endpoint: str) -> str:
        parsed = urlparse(base_or_endpoint)
        path = parsed.path or ""
        # If user provided only API base URL, use the default invoice parse endpoint.
        if path in ("", "/"):
            return base_or_endpoint.rstrip("/") + "/api/v8/partner/documents/"
        return base_or_endpoint

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

        api_url = os.getenv("VERYFI_API_URL")
        client_id = os.getenv("VERYFI_CLIENT_ID")
        username = os.getenv("VERYFI_USERNAME")
        api_key = os.getenv("VERYFI_API_KEY")

        if not api_url:
            return ParseResult(
                vendor=self.name,
                invoice_type=invoice_type,
                file_name=file_path.name,
                raw_response={},
                latency_ms=0.0,
                cost_usd_estimated=None,
                status="error",
                error_message="Missing env var: VERYFI_API_URL",
            )

        if not client_id or not username or not api_key:
            return ParseResult(
                vendor=self.name,
                invoice_type=invoice_type,
                file_name=file_path.name,
                raw_response={},
                latency_ms=0.0,
                cost_usd_estimated=None,
                status="error",
                error_message="Missing env vars: VERYFI_CLIENT_ID, VERYFI_USERNAME, and/or VERYFI_API_KEY",
            )

        endpoint = self._resolve_endpoint(api_url)
        start = time.perf_counter()
        try:
            import requests

            with file_path.open("rb") as fh:
                response = requests.post(
                    endpoint,
                    headers={
                        "Client-Id": client_id,
                        "Authorization": f"apikey {username}:{api_key}",
                    },
                    files={"file": (file_path.name, fh, "application/pdf")},
                    timeout=60,
                )
            latency_ms = (time.perf_counter() - start) * 1000.0
            response.raise_for_status()
            payload = response.json()
            return ParseResult(
                vendor=self.name,
                invoice_type=invoice_type,
                file_name=file_path.name,
                raw_response=payload,
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
