from __future__ import annotations

from invoice_benchmark.adapters.gdocai import GDocAIAdapter
from invoice_benchmark.adapters.nanonets import NanonetsAdapter
from invoice_benchmark.adapters.upstage import UpstageAdapter
from invoice_benchmark.adapters.veryfi import VeryfiAdapter

ADAPTERS = {
    "veryfi": VeryfiAdapter,
    "nanonets": NanonetsAdapter,
    "upstage": UpstageAdapter,
    "gdocai": GDocAIAdapter,
}
