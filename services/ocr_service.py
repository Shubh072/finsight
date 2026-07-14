"""Receipt OCR and heuristic extraction (Python-only, no external API required)."""

from __future__ import annotations

import io
import re
from datetime import date, datetime
from typing import Any

CATEGORY_MERCHANT_RULES = [
    (r"uber|ola|lyft|rapido", "Travel"),
    (r"swiggy|zomato|pizza\s*hut|domino|mcdonald|kfc|restaurant|food", "Food"),
    (r"amazon|flipkart|myntra|shopping", "Shopping"),
    (r"netflix|spotify|prime\s*video|hotstar|subscription", "Subscription"),
    (r"apollo|pharmacy|medplus|healthcare|hospital", "Healthcare"),
    (r"electricity|bescom|bill\s*payment|bills", "Bills"),
    (r"petrol|diesel|fuel|hp\s*clinic|indian\s*oil|bharat\s*petroleum", "Fuel"),
    (r"emi|loan", "EMI"),
    (r"rent", "Rent"),
    (r"insurance", "Insurance"),
    (r"education|udemy|coursera", "Education"),
]

PAYMENT_HINTS = [
    (r"\bupi\b|gpay|phonepe|paytm", "UPI"),
    (r"credit\s*card|visa|mastercard|amex", "Credit Card"),
    (r"debit\s*card", "Debit Card"),
    (r"net\s*banking|neft|imps|rtgs", "Net Banking"),
    (r"\bcash\b", "Cash"),
    (r"wallet", "Wallet"),
    (r"cheque|check", "Cheque"),
]

AMOUNT_PATTERNS = [
    re.compile(r"(?:total|grand\s*total|amount\s*due|payable|balance)\s*[:\-]?\s*(?:₹|rs\.?|inr)?\s*([\d,]+\.?\d*)", re.I),
    re.compile(r"(?:₹|rs\.?|inr)\s*([\d,]+\.?\d*)", re.I),
    re.compile(r"\b([\d,]+\.\d{2})\b"),
]

DATE_PATTERNS = [
    re.compile(r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b"),
    re.compile(r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})\b"),
    re.compile(r"\b(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{2,4})\b", re.I),
]

GST_PATTERN = re.compile(r"(?:gstin|gst\s*no\.?|gst)\s*[:\-]?\s*([0-9A-Z]{15})", re.I)
INVOICE_PATTERN = re.compile(r"(?:invoice\s*(?:no|#|number)?|inv\s*#?)\s*[:\-]?\s*([A-Z0-9\-/]+)", re.I)
RECEIPT_NUM_PATTERN = re.compile(r"(?:receipt\s*(?:no|#|number)?)\s*[:\-]?\s*([A-Z0-9\-/]+)", re.I)
TAX_PATTERN = re.compile(r"(?:tax|cgst|sgst|igst|gst\s*amount)\s*[:\-]?\s*(?:₹|rs\.?)?\s*([\d,]+\.?\d*)", re.I)


def _extract_text_from_image(file_bytes: bytes) -> str:
    try:
        from PIL import Image
        import pytesseract

        img = Image.open(io.BytesIO(file_bytes))
        return pytesseract.image_to_string(img) or ""
    except Exception:
        return ""


def _extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(stream=file_bytes, filetype="pdf")
        parts = []
        for page in doc:
            parts.append(page.get_text())
        return "\n".join(parts)
    except Exception:
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(file_bytes))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            return ""


def extract_text_from_receipt(file_bytes: bytes, mimetype: str) -> str:
    if mimetype == "application/pdf":
        return _extract_text_from_pdf(file_bytes)
    if mimetype and mimetype.startswith("image/"):
        return _extract_text_from_image(file_bytes)
    return ""


def _parse_amount(text: str) -> float | None:
    candidates: list[float] = []
    for pat in AMOUNT_PATTERNS:
        for match in pat.finditer(text):
            raw = match.group(1).replace(",", "")
            try:
                val = float(raw)
                if 0 < val < 10_000_000:
                    candidates.append(val)
            except ValueError:
                continue
    return max(candidates) if candidates else None


def _parse_date(text: str) -> str | None:
    month_map = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    }
    for pat in DATE_PATTERNS:
        for match in pat.finditer(text):
            groups = match.groups()
            try:
                if len(groups) == 3 and groups[1].isalpha():
                    d, mon, y = groups
                    y = int(y)
                    if y < 100:
                        y += 2000
                    parsed = date(y, month_map[mon[:3].lower()], int(d))
                elif len(groups[0]) == 4:
                    y, m, d = map(int, groups)
                    parsed = date(y, m, d)
                else:
                    d, m, y = map(int, groups)
                    if y < 100:
                        y += 2000
                    parsed = date(y, m, d)
                if parsed <= date.today():
                    return parsed.isoformat()
            except (ValueError, KeyError):
                continue
    return None


def _suggest_category(text: str, merchant: str | None = None) -> tuple[str | None, float]:
    combined = f"{merchant or ''} {text}".lower()
    for pattern, category in CATEGORY_MERCHANT_RULES:
        if re.search(pattern, combined, re.I):
            return category, 0.85
    return None, 0.0


def _guess_merchant(text: str) -> str | None:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for line in lines[:8]:
        if len(line) < 3 or re.match(r"^\d", line):
            continue
        if re.search(r"invoice|receipt|tax|gst|total|date", line, re.I):
            continue
        if len(line) <= 80:
            return line.title()
    return None


def _guess_payment_method(text: str) -> str | None:
    for pattern, method in PAYMENT_HINTS:
        if re.search(pattern, text, re.I):
            return method
    return None


def _extract_items(text: str) -> list[dict[str, Any]]:
    items = []
    line_pat = re.compile(r"^(.{2,40}?)\s+(?:₹|rs\.?)?\s*([\d,]+\.\d{2})\s*$", re.I | re.M)
    for match in line_pat.finditer(text):
        name = match.group(1).strip()
        if re.search(r"total|subtotal|tax|gst|change", name, re.I):
            continue
        try:
            price = float(match.group(2).replace(",", ""))
            items.append({"name": name, "qty": 1, "price": price})
        except ValueError:
            continue
        if len(items) >= 20:
            break
    return items


def _confidence_score(text: str, fields: dict[str, Any]) -> float:
    score = 0.0
    if text and len(text) > 30:
        score += 25
    if fields.get("merchant"):
        score += 15
    if fields.get("amount"):
        score += 25
    if fields.get("expense_date"):
        score += 15
    if fields.get("category"):
        score += 10
    if fields.get("items"):
        score += 5
    if fields.get("tax"):
        score += 5
    return min(round(score, 1), 99.0)


def scan_receipt(file_bytes: bytes, mimetype: str, filename: str = "") -> dict[str, Any]:
    text = extract_text_from_receipt(file_bytes, mimetype)

    if not text.strip():
        # Fallback: infer from filename
        text = filename.replace("_", " ").replace("-", " ")

    merchant = _guess_merchant(text)
    amount = _parse_amount(text)
    expense_date = _parse_date(text) or date.today().isoformat()
    category, cat_conf = _suggest_category(text, merchant)
    payment_method = _guess_payment_method(text)
    items = _extract_items(text)

    tax_match = TAX_PATTERN.search(text)
    tax = float(tax_match.group(1).replace(",", "")) if tax_match else None

    gst_match = GST_PATTERN.search(text)
    gst = gst_match.group(1) if gst_match else None

    inv_match = INVOICE_PATTERN.search(text)
    invoice_number = inv_match.group(1) if inv_match else None

    rcpt_match = RECEIPT_NUM_PATTERN.search(text)
    receipt_number = rcpt_match.group(1) if rcpt_match else None

    currency = "INR" if re.search(r"₹|rs\.?|inr|india", text, re.I) else "USD"

    address_lines = []
    for line in text.splitlines()[:15]:
        if re.search(r"\d{6}|street|road|city|pin", line, re.I):
            address_lines.append(line.strip())
    address = ", ".join(address_lines[:3]) if address_lines else None

    result = {
        "merchant": merchant,
        "amount": amount,
        "expense_date": expense_date,
        "category": category,
        "category_confidence": cat_conf,
        "tax": tax,
        "items": items,
        "payment_method": payment_method,
        "currency": currency,
        "invoice_number": invoice_number,
        "gst": gst,
        "receipt_number": receipt_number,
        "address": address,
        "raw_text_preview": (text[:500] + "...") if len(text) > 500 else text,
    }
    result["confidence"] = _confidence_score(text, result)
    return result
