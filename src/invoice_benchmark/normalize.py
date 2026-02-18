from __future__ import annotations

from typing import Any

from invoice_benchmark.models import ParseResult


def _find_first(data: Any, candidate_keys: list[str]) -> Any:
    if isinstance(data, dict):
        lower_map = {k.lower(): k for k in data.keys()}
        for c in candidate_keys:
            if c.lower() in lower_map:
                return data[lower_map[c.lower()]]
        for value in data.values():
            found = _find_first(value, candidate_keys)
            if found is not None:
                return found
    elif isinstance(data, list):
        for item in data:
            found = _find_first(item, candidate_keys)
            if found is not None:
                return found
    return None


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.replace(",", "").replace("$", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def _as_name(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        name = value.get("name")
        if isinstance(name, str):
            return name
    return None


def to_normalized(result: ParseResult) -> dict[str, Any]:
    raw = result.raw_response
    invoice_number = _find_first(raw, ["invoice_number", "invoice_no", "invoice id", "invoice"])
    invoice_date = _find_first(raw, ["invoice_date", "date"])
    due_date = _find_first(raw, ["due_date", "payment_due_date", "due"])
    subtotal = _as_float(_find_first(raw, ["subtotal", "sub_total"]))
    tax = _as_float(_find_first(raw, ["tax", "tax_amount", "vat"]))
    total = _as_float(_find_first(raw, ["total", "amount_due", "grand_total"]))

    line_items = _find_first(raw, ["line_items", "items", "products"]) or []
    if not isinstance(line_items, list):
        line_items = []

    normalized_items = []
    for item in line_items:
        if not isinstance(item, dict):
            continue
        normalized_items.append(
            {
                "description": _find_first(item, ["description", "name", "item"]),
                "quantity": _as_float(_find_first(item, ["quantity", "qty"])),
                "unit_price": _as_float(_find_first(item, ["unit_price", "price", "rate"])),
                "amount": _as_float(_find_first(item, ["amount", "line_total", "total"]))
            }
        )

    return {
        "source": {
            "vendor": result.vendor,
            "invoice_type": result.invoice_type,
            "file_name": result.file_name,
        },
        "invoice": {
            "invoice_number": invoice_number,
            "invoice_date": invoice_date,
            "due_date": due_date,
            "currency": _find_first(raw, ["currency", "currency_code"]),
            "vendor_name": _as_name(_find_first(raw, ["vendor_name", "supplier", "seller", "vendor"])),
            "bill_to_name": _as_name(_find_first(raw, ["bill_to_name", "bill_to", "customer", "buyer"])),
        },
        "amounts": {
            "subtotal": subtotal,
            "tax": tax,
            "total": total,
        },
        "line_items": normalized_items,
        "meta": {
            "latency_ms": result.latency_ms,
            "cost_usd_estimated": result.cost_usd_estimated,
            "parse_status": result.status,
            "error_message": result.error_message,
        },
    }
