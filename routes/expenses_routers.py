import os
import hashlib
from datetime import date

from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy import func


from database.db import db
from models.expense import Expense
from utils.api_response import success_response, error_response


expenses_bp = Blueprint("expenses", __name__)


ALLOWED_RECEIPT_MIMES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
}

MAX_RECEIPT_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
MAX_DESCRIPTION_LENGTH = 1000
TITLE_MIN_LEN = 3

CATEGORY_AUTOSUGGESTION_RULES = [
    ("pizza", "Food"),
    ("burger", "Food"),
    ("restaurant", "Food"),
    ("uber", "Travel"),
    ("ola", "Travel"),
    ("bus", "Travel"),
]


def _user_id_from_claims():
    claims = get_jwt()
    user_id = claims.get("sub") or claims.get("user_id") or claims.get("identity")
    return user_id


def _normalize_title(title: str) -> str:
    return " ".join((title or "").strip().lower().split())


def _fingerprint_for_duplicate(title: str, amount, expense_date: str, merchant: str, currency: str):
    raw = "|".join([
        _normalize_title(title),
        str(amount or ""),
        str(expense_date or ""),
        (merchant or "").strip().lower(),
        (currency or "").strip().upper(),
    ])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _parse_date(value):
    # Expect YYYY-MM-DD from client
    if not value:
        return None
    try:
        parts = str(value).split("-")
        if len(parts) != 3:
            return None
        y, m, d = map(int, parts)
        return date(y, m, d)
    except Exception:
        return None


def _suggest_category(title: str, category: str | None):
    if category:
        return category
    t = (title or "").lower()
    for needle, suggested in CATEGORY_AUTOSUGGESTION_RULES:
        if needle in t:
            return suggested
    return None


@expenses_bp.route("/", methods=["POST"])
@jwt_required()
def create_expense():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    # Support multipart for receipt upload
    form = request.form or {}
    json_body = request.get_json(silent=True) or {}

    payload = {}
    payload.update(json_body)
    # overlay form fields
    for k in form.keys():
        payload[k] = form.get(k)

    title = (payload.get("title") or "").strip()
    category = (payload.get("category") or "").strip() or None

    amount_raw = payload.get("amount")
    expense_date_raw = payload.get("expense_date")

    payment_method = (payload.get("payment_method") or "").strip()
    account_id_raw = payload.get("account_id")
    merchant_name = (payload.get("merchant_name") or "").strip() or None
    location = (payload.get("location") or "").strip() or None
    description = (payload.get("description") or "").strip() or None

    tags = payload.get("tags")
    if isinstance(tags, str):
        # Expect JSON string from client; fallback to comma-separated
        try:
            import json

            tags = json.loads(tags)
        except Exception:
            tags = [x.strip() for x in tags.split(",") if x.strip()]

    recurring_raw = payload.get("recurring")
    currency = (payload.get("currency") or "").strip() or None
    priority_raw = payload.get("priority")
    mood = (payload.get("mood") or "").strip() or None

    # Optional receipt upload
    receipt_file = request.files.get("receipt") if hasattr(request, "files") else None

    # Validations
    errors = {}

    if not title or len(title) < TITLE_MIN_LEN:
        errors["title"] = f"Title must be at least {TITLE_MIN_LEN} characters."

    suggested_category = _suggest_category(title, category)
    if not suggested_category:
        errors["category"] = "Category is required."
    category_final = suggested_category

    try:
        amount = float(amount_raw)
    except Exception:
        errors["amount"] = "Amount must be a valid number."
        amount = None

    if amount is None or amount <= 0:
        errors["amount"] = "Amount must be greater than 0."

    expense_date = _parse_date(expense_date_raw)
    if not expense_date:
        errors["expense_date"] = "Expense date is invalid or missing."
    else:
        if expense_date > date.today():
            errors["expense_date"] = "Date cannot be in the future."

    if not payment_method:
        errors["payment_method"] = "Payment method is required."

    if description is not None:
        if len(description) > MAX_DESCRIPTION_LENGTH:
            errors["description"] = f"Description cannot exceed {MAX_DESCRIPTION_LENGTH} characters."

    # account_id optional for this milestone
    account_id = None
    if account_id_raw not in (None, "", "null"):
        try:
            account_id = int(account_id_raw)
        except Exception:
            errors["account_id"] = "Account used is invalid."

    recurring = False
    if recurring_raw in (True, "true", "1", 1, "yes"):
        recurring = True

    priority = None
    if priority_raw not in (None, "", "null"):
        try:
            priority = int(priority_raw)
            if priority < 1 or priority > 5:
                errors["priority"] = "Priority must be between 1 and 5."
        except Exception:
            errors["priority"] = "Priority must be an integer."

    # Receipt validation + structure
    receipt_filename = receipt_url = receipt_mime = None
    receipt_size = None
    ocr_ready = False
    receipt_ocr_text = None
    receipt_ocr_confidence = None

    if receipt_file and receipt_file.filename:
        receipt_mime = receipt_file.mimetype
        receipt_size = request.content_length

        if receipt_mime not in ALLOWED_RECEIPT_MIMES:
            errors["receipt"] = "Receipt must be an image (jpg/png/webp) or PDF."
        if receipt_size is not None and receipt_size > MAX_RECEIPT_SIZE_BYTES:
            errors["receipt"] = "Receipt file size exceeds limit (5MB)."

    if errors:
        return error_response("Validation failed", errors=errors), 400

    # Persist receipt to disk if present
    if receipt_file and receipt_file.filename:
        upload_dir = os.path.join(current_app.root_path, "uploads", "receipts", str(user_id))
        os.makedirs(upload_dir, exist_ok=True)

        ext = os.path.splitext(receipt_file.filename)[1].lower()
        safe_name = f"expense_{user_id}_{int(date.today().strftime('%s'))}_{hashlib.sha256(receipt_file.filename.encode('utf-8')).hexdigest()}{ext}"
        file_path = os.path.join(upload_dir, safe_name)
        receipt_file.save(file_path)

        receipt_filename = safe_name
        # Since static serving for uploads isn't implemented in this milestone,
        # keep a relative URL-like path for frontend preview and future endpoints.
        receipt_url = f"/uploads/receipts/{user_id}/{safe_name}"

    fingerprint = _fingerprint_for_duplicate(title, amount, expense_date_raw, merchant_name, currency)

    new_expense = Expense(
        user_id=user_id,
        title=title,
        category=category_final,
        amount=amount,
        expense_date=expense_date,
        payment_method=payment_method,
        account_id=account_id,
        merchant_name=merchant_name,
        location=location,
        description=description,
        tags_json=tags,
        recurring=recurring,
        currency=currency,
        priority=priority,
        mood=mood,
        receipt_filename=receipt_filename,
        receipt_url=receipt_url,
        receipt_mime=receipt_mime,
        receipt_size=receipt_size,
        ocr_ready=ocr_ready,
        receipt_ocr_text=receipt_ocr_text,
        receipt_ocr_confidence=receipt_ocr_confidence,
        normalized_title=_normalize_title(title),
        fingerprint=fingerprint,
        status="active",
        is_deleted=False,
        deleted_at=None,
    )

    try:
        db.session.add(new_expense)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return error_response("Expense creation failed", errors={"error": str(e)}), 500

    return success_response(
        message="Expense added successfully.",
        data={"expense_id": new_expense.id},
    ), 201


@expenses_bp.route("/<int:expense_id>", methods=["GET"])
@jwt_required()
def get_expense(expense_id: int):
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    exp = (
        Expense.query.filter_by(id=expense_id, user_id=user_id, is_deleted=False)
        .first()
    )
    if not exp:
        return error_response("Expense not found"), 404

    return success_response(
        message="Expense fetched successfully.",
        data={
            "id": exp.id,
            "title": exp.title,
            "category": exp.category,
            "amount": str(exp.amount),
            "expense_date": exp.expense_date.isoformat(),
            "payment_method": exp.payment_method,
            "account_id": exp.account_id,
            "merchant_name": exp.merchant_name,
            "location": exp.location,
            "description": exp.description,
            "tags": exp.tags_json,
            "recurring": exp.recurring,
            "currency": exp.currency,
            "priority": exp.priority,
            "mood": exp.mood,
            "receipt_url": exp.receipt_url,
            "receipt_filename": exp.receipt_filename,
        },
    ), 200


@expenses_bp.route("/<int:expense_id>", methods=["PUT"])
@jwt_required()
def update_expense(expense_id: int):
    # For milestone: implement validation & update without receipt changes first.
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    exp = Expense.query.filter_by(id=expense_id, user_id=user_id, is_deleted=False).first()
    if not exp:
        return error_response("Expense not found"), 404

    payload = request.get_json(silent=True) or {}

    title = payload.get("title", exp.title)
    category = payload.get("category", exp.category)
    amount = payload.get("amount", exp.amount)
    expense_date_raw = payload.get("expense_date", exp.expense_date.isoformat())
    payment_method = payload.get("payment_method", exp.payment_method)

    errors = {}

    if not title or len(title) < TITLE_MIN_LEN:
        errors["title"] = f"Title must be at least {TITLE_MIN_LEN} characters."

    expense_date = _parse_date(expense_date_raw)
    if not expense_date:
        errors["expense_date"] = "Expense date is invalid or missing."
    else:
        if expense_date > date.today():
            errors["expense_date"] = "Date cannot be in the future."

    try:
        amount_f = float(amount)
    except Exception:
        errors["amount"] = "Amount must be a valid number."
        amount_f = None

    if amount_f is None or amount_f <= 0:
        errors["amount"] = "Amount must be greater than 0."

    if not payment_method:
        errors["payment_method"] = "Payment method is required."

    description = payload.get("description", exp.description)
    if description is not None and len(description) > MAX_DESCRIPTION_LENGTH:
        errors["description"] = f"Description cannot exceed {MAX_DESCRIPTION_LENGTH} characters."

    if errors:
        return error_response("Validation failed", errors=errors), 400

    exp.title = title.strip()
    exp.category = category
    exp.amount = amount_f
    exp.expense_date = expense_date
    exp.payment_method = payment_method
    exp.description = description

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return error_response("Expense update failed", errors={"error": str(e)}), 500

    return success_response(message="Expense updated successfully.", data={"expense_id": exp.id}), 200


@expenses_bp.route("/<int:expense_id>", methods=["DELETE"])
@jwt_required()
def delete_expense(expense_id: int):
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    exp = Expense.query.filter_by(id=expense_id, user_id=user_id, is_deleted=False).first()
    if not exp:
        return error_response("Expense not found"), 404

    exp.is_deleted = True

    # Use DB default for deleted_at if not stored; set explicitly for consistency
    exp.deleted_at = func.now()

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return error_response("Expense delete failed", errors={"error": str(e)}), 500

    return success_response(message="Expense archived (soft-deleted).", data={"expense_id": exp.id}), 200


@expenses_bp.route("/duplicate-check", methods=["POST"])
@jwt_required()
def duplicate_check():
    """Lightweight heuristic check. Used by frontend to warn before save.

    Returns {possible_duplicate: bool, duplicates: [{id, title, amount, expense_date}]}.
    """
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    payload = request.get_json(silent=True) or {}

    title = (payload.get("title") or "").strip()
    amount = payload.get("amount")
    expense_date = payload.get("expense_date")
    merchant_name = (payload.get("merchant_name") or "").strip() or None
    currency = (payload.get("currency") or "").strip() or ""

    if not title or amount is None or not expense_date:
        return success_response(message="Duplicate check skipped (missing fields).", data={"possible_duplicate": False, "duplicates": []}), 200

    amount_f = None
    try:
        amount_f = float(amount)
    except Exception:
        amount_f = None

    if amount_f is None:
        return success_response(message="Duplicate check skipped (invalid amount).", data={"possible_duplicate": False, "duplicates": []}), 200

    normalized = _normalize_title(title)

    possible = (
        Expense.query.filter(
            Expense.user_id == user_id,
            Expense.is_deleted == False,
            Expense.normalized_title == normalized,
            Expense.amount == amount_f,
            Expense.expense_date == _parse_date(expense_date),
        )
        .order_by(Expense.created_at.desc())
        .limit(5)
        .all()
    )

    duplicates = [
        {
            "id": e.id,
            "title": e.title,
            "amount": str(e.amount),
            "expense_date": e.expense_date.isoformat(),
            "merchant_name": e.merchant_name,
        }
        for e in possible
    ]

    return success_response(
        message="Duplicate check completed.",
        data={
            "possible_duplicate": len(duplicates) > 0,
            "duplicates": duplicates,
        },
    ), 200

