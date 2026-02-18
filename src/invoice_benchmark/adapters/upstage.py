from __future__ import annotations

import base64
import json
import os
import time
from pathlib import Path

from invoice_benchmark.adapters.base import VendorAdapter
from invoice_benchmark.models import ParseResult


class UpstageAdapter(VendorAdapter):
    name = "upstage"

    @staticmethod
    def _resolve_endpoint() -> str:
        return os.getenv(
            "UPSTAGE_EXTRACT_ENDPOINT",
            "https://api.upstage.ai/v1/information-extraction/chat/completions",
        )

    @staticmethod
    def _mime_type(file_path: Path) -> str:
        ext = file_path.suffix.lower()
        if ext == ".pdf":
            return "application/pdf"
        if ext in (".jpg", ".jpeg"):
            return "image/jpeg"
        if ext == ".png":
            return "image/png"
        if ext in (".tif", ".tiff"):
            return "image/tiff"
        return "application/octet-stream"

    @staticmethod
    def _invoice_schema() -> dict:
        default_schema = {
            "type": "object",
            "properties": {
                "invoice_number": {"type": "string"},
                "invoice_date": {"type": "string"},
                "due_date": {"type": "string"},
                "vendor_name": {"type": "string"},
                "bill_to_name": {"type": "string"},
                "subtotal": {"type": "number"},
                "tax": {"type": "number"},
                "total": {"type": "number"},
                "line_items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string"},
                            "quantity": {"type": "number"},
                            "unit_price": {"type": "number"},
                            "amount": {"type": "number"},
                        },
                    },
                },
            },
        }

        raw = os.getenv("UPSTAGE_RESPONSE_SCHEMA_JSON", "").strip()
        if not raw:
            return default_schema
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
        return default_schema

    @staticmethod
    def _extract_json_from_response(data: dict) -> dict | None:
        try:
            choices = data.get("choices") or []
            if not choices:
                return None
            content = (choices[0].get("message") or {}).get("content")
            if isinstance(content, str):
                parsed = json.loads(content)
                if isinstance(parsed, dict):
                    return parsed
            if isinstance(content, list):
                # Handle multimodal content blocks if returned as list.
                for block in content:
                    text = block.get("text") if isinstance(block, dict) else None
                    if isinstance(text, str):
                        parsed = json.loads(text)
                        if isinstance(parsed, dict):
                            return parsed
        except Exception:
            return None
        return None

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
        api_key = os.getenv("UPSTAGE_API_KEY")

        if not api_key:
            return ParseResult(
                vendor=self.name,
                invoice_type=invoice_type,
                file_name=file_path.name,
                raw_response={},
                latency_ms=0.0,
                cost_usd_estimated=None,
                status="error",
                error_message="Missing env var: UPSTAGE_API_KEY",
            )

        base64_data = base64.b64encode(file_path.read_bytes()).decode("utf-8")
        mime_type = self._mime_type(file_path)
        payload = {
            "model": os.getenv("UPSTAGE_MODEL", "information-extract"),
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{base64_data}"},
                        }
                    ],
                }
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "invoice_schema", "schema": self._invoice_schema()},
            },
        }

        start = time.perf_counter()
        try:
            import requests

            response = requests.post(
                endpoint,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=120,
            )
            latency_ms = (time.perf_counter() - start) * 1000.0
            response.raise_for_status()
            data = response.json()
            extracted = self._extract_json_from_response(data)
            raw_payload = {
                "upstage_response": data,
                "extracted": extracted if extracted is not None else {},
            }
            return ParseResult(
                vendor=self.name,
                invoice_type=invoice_type,
                file_name=file_path.name,
                raw_response=raw_payload,
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
