from __future__ import annotations

import base64
import os
import time
from pathlib import Path

from invoice_benchmark.adapters.base import VendorAdapter
from invoice_benchmark.models import ParseResult


class GDocAIAdapter(VendorAdapter):
    name = "gdocai"

    @staticmethod
    def _mime_type(file_path: Path) -> str:
        ext = file_path.suffix.lower()
        if ext == ".pdf":
            return "application/pdf"
        if ext in (".jpg", ".jpeg"):
            return "image/jpeg"
        if ext == ".png":
            return "image/png"
        if ext == ".tif" or ext == ".tiff":
            return "image/tiff"
        return "application/octet-stream"

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

        endpoint = os.getenv("GDOCAI_PROCESSOR_ENDPOINT") or os.getenv("GDOCAI_API_URL")
        access_token = os.getenv("GDOCAI_ACCESS_TOKEN")

        if not endpoint:
            return ParseResult(
                vendor=self.name,
                invoice_type=invoice_type,
                file_name=file_path.name,
                raw_response={},
                latency_ms=0.0,
                cost_usd_estimated=None,
                status="error",
                error_message="Missing env var: GDOCAI_PROCESSOR_ENDPOINT",
            )

        if not access_token:
            return ParseResult(
                vendor=self.name,
                invoice_type=invoice_type,
                file_name=file_path.name,
                raw_response={},
                latency_ms=0.0,
                cost_usd_estimated=None,
                status="error",
                error_message="Missing env var: GDOCAI_ACCESS_TOKEN",
            )

        payload = {
            "skipHumanReview": True,
            "rawDocument": {
                "mimeType": self._mime_type(file_path),
                "content": base64.b64encode(file_path.read_bytes()).decode("utf-8"),
            },
        }

        start = time.perf_counter()
        try:
            import requests

            response = requests.post(
                endpoint,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
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
