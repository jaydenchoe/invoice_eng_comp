from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class InvoiceDoc:
    invoice_type: str
    relative_path: str

    def absolute_path(self, input_root: Path) -> Path:
        return input_root / self.relative_path


@dataclass
class ParseResult:
    vendor: str
    invoice_type: str
    file_name: str
    raw_response: dict[str, Any]
    latency_ms: float
    cost_usd_estimated: float | None
    status: str
    error_message: str | None = None
