from __future__ import annotations

import abc
from pathlib import Path

from invoice_benchmark.models import ParseResult


class VendorAdapter(abc.ABC):
    name: str

    @abc.abstractmethod
    def parse(self, file_path: Path, invoice_type: str, dry_run: bool = False) -> ParseResult:
        raise NotImplementedError
