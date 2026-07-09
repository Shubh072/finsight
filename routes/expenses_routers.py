import os
import json
import hashlib
from datetime import date, datetime, timedelta
from decimal import Decimal

from flask import Blueprint, request, current_app, jsonify, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy import func, or_
from database.db import db
from models.expense import (
    Expense, ExpenseCategory, Account, Budget,
    ExpenseSplit, ExpenseTemplate, FavoriteMerchant, ExpenseDraft
)
from utils.api_response import success_response, error_response
from utils import supabase_client as sb


expenses_bp = Blueprint("expenses", __name__)


ALLOWED_RECEIPT_MIMES = {
    "image/jpeg", "image/png", "image/webp", "application/pdf",
}

MAX_RECEIPT_SIZE_BYTES = 5 * 1024 * 1024
MAX_DESCRIPTION_LENGTH = 1000
TITLE_MIN_LEN = 3

CATEGORY_METADATA = {
    "Food": {"icon": "restaurant", "color": "#F59E0B", "keywords": ["pizza", "burger", "restaurant", "cafe", "coffee", "food", "swiggy", "zomato", "dominos", "mcdonald"]},
    "Travel": {"icon": "flight", "color": "#3B82F6", "keywords": ["uber", "ola", "taxi", "bus", "flight", "hotel", "travel", "irctc", "makemytrip", "airbnb"]},
    "Shopping": {"icon": "shopping_bag", "color": "#EC4899", "keywords": ["amazon", "flipkart", "myntra", "shopping", "mall", "store", "ebay"]},
    "Entertainment": {"icon": "theaters", "color": "#8B5CF6", "keywords": ["netflix", "spotify", "movie", "game", "entertainment", "prime", "hotstar", "disney"]},
    "Healthcare": {"icon": "local_hospital", "color": "#EF4444", "keywords": ["gym", "medical", "hospital", "doctor", "pharmacy", "apollo", "health", "clinic", "medicine"]},
    "Bills": {"icon": "receipt_long", "color": "#F97316", "keywords": ["electricity", "water", "internet", "phone", "bill", "gas", "broadband", "airtel", "jio"]},
    "Fuel": {"icon": "local_gas_station", "color": "#14B8A6", "keywords": ["fuel", "petrol", "diesel", "gas", "shell", "hp", "bharat petroleum", "indian oil"]},
    "Education": {"icon": "school", "color": "#6366F1", "keywords": ["school", "college", "course", "book", "tuition", "udemy", "coursera", "education"]},
    "Investment": {"icon": "trending_up", "color": "#10B981", "keywords": ["stock", "mutual fund", "sip", "investment", "zerodha", "groww", "invest"]},
    "Salary": {"icon": "payments", "color": "#22C55E", "keywords": ["salary", "wage", "paycheck", "income"]},
    "Gift": {"icon": "card_giftcard", "color": "#F472B6", "keywords": ["gift", "present", "birthday"]},
    "Insurance": {"icon": "shield", "color": "#0EA5E9", "keywords": ["insurance", "premium", "policy", "lic", "coverage"]},
    "EMI": {"icon": "credit_card", "color": "#DC2626", "keywords": ["emi", "installment", "loan", "mortgage"]},
    "Rent": {"icon": "home", "color": "#7C3AED", "keywords": ["rent", "lease", "landlord"]},
    "Utilities": {"icon": "bolt", "color": "#FBBF24", "keywords": ["utility", "electric", "power", "sewage", "trash"]},
    "Subscription": {"icon": "subscriptions", "color": "#A855F7", "keywords": ["subscription", "subscribe", "monthly", "annual", "recurring"]},
    "Others": {"icon": "category", "color": "#64748B", "keywords": []},
}

PAYMENT_METHODS = ["Cash", "UPI", "Debit Card", "Credit Card", "Wallet", "Bank Transfer", "Net Banking", "Cheque", "Crypto"]
ACCOUNT_TYPES = ["Cash Wallet", "Savings", "Current", "Credit Card", "Business Account", "Custom Account"]
QUICK_ADD_AMOUNTS = [100, 200, 500, 1000]
MOOD_OPTIONS = ["Happy", "Neutral", "Stressed", "Excited", "Guilty", "Necessary", "Impulse"]


def _user_id_from_claims():
    claims = get_jwt()
    user_id = claims.get("sub") or claims.get("user_id") or claims.get("identity")
    return user_id


def _normalize_title(title: str) -> str:
    return " ".join((title or "").strip().lower().split())


def _fingerprint_for_duplicate(title, amount, expense_date, merchant, currency):
    raw = "|".join([
        _normalize_title(title), str(amount or ""), str(expense_date or ""),
        (merchant or "").strip().lower(), (currency or "").strip().upper(),
    ])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _parse_date(value):
    if not value:
        return None
    try:
        if isinstance(value, date):
            return value
        parts = str(value).split("-")
        if len(parts) != 3:
            return None
        y, m, d = map(int, parts)
        return date(y, m, d)
    except Exception:
        return None


def _suggest_category(title, merchant, category=None):
    if category:
        return category
    text = f"{title or ''} {merchant or ''}".lower()
    for cat_name, meta in CATEGORY_METADATA.items():
        for needle in meta.get("keywords", []):
            if needle in text:
                return cat_name
    return "Others"


@expenses_bp.route("/", methods=["POST"])
@jwt_required()
def create_expense():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    form = request.form or {}
    json_body = request.get_json(silent=True) or {}

    payload = {}
    payload.update(json_body)
    for k in form.keys():
        payload[k] = form.get(k)

    title = (payload.get("title") or "").strip()
    category = (payload.get("category") or "").strip() or None
    sub_category = (payload.get("sub_category") or "").strip() or None
    amount_raw = payload.get("amount")
    expense_date_raw = payload.get("expense_date")
    payment_method = (payload.get("payment_method") or "").strip()
    account_id_raw = payload.get("account_id")
    merchant_name = (payload.get("merchant_name") or "").strip() or None
    location = (payload.get("location") or "").strip() or None
    description = (payload.get("description") or "").strip() or None

    tags = payload.get("tags")
    if isinstance(tags, str):
        try:
            tags = json.loads(tags)
        except Exception:
            tags = [x.strip() for x in tags.split(",") if x.strip()]

    recurring_raw = payload.get("recurring")
    recurring_frequency = (payload.get("recurring_frequency") or "").strip() or None
    currency = (payload.get("currency") or "USD").strip() or "USD"
    priority_raw = payload.get("priority")
    mood = (payload.get("mood") or "").strip() or None

    tax_included_raw = payload.get("tax_included")
    invoice_number = (payload.get("invoice_number") or "").strip() or None
    receipt_number = (payload.get("receipt_number") or "").strip() or None
    gst = (payload.get("gst") or "").strip() or None
    budget_id_raw = payload.get("budget_id")
    notes = (payload.get("notes") or "").strip() or None
    splits_raw = payload.get("splits")

    receipt_file = request.files.get("receipt") if hasattr(request, "files") else None

    errors = {}

    if not title or len(title) < TITLE_MIN_LEN:
        errors["title"] = f"Title must be at least {TITLE_MIN_LEN} characters."

    suggested_category = _suggest_category(title, merchant_name, category)
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

    if description is not None and len(description) > MAX_DESCRIPTION_LENGTH:
        errors["description"] = f"Description cannot exceed {MAX_DESCRIPTION_LENGTH} characters."

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

    tax_included = None
    if tax_included_raw not in (None, "", "null"):
        try:
            tax_included = float(tax_included_raw)
        except Exception:
            errors["tax_included"] = "Tax included must be a valid number."

    budget_id = None
    if budget_id_raw not in (None, "", "null"):
        try:
            budget_id = int(budget_id_raw)
        except Exception:
            errors["budget_id"] = "Budget ID is invalid."

    splits = None
    if splits_raw:
        if isinstance(splits_raw, str):
            try:
                splits = json.loads(splits_raw)
            except Exception:
                errors["splits"] = "Invalid splits format."
        else:
            splits = splits_raw

    receipt_filename = receipt_url = receipt_mime = None
    receipt_size = None

    if receipt_file and receipt_file.filename:
        receipt_mime = receipt_file.mimetype
        receipt_size = request.content_length
        if receipt_mime not in ALLOWED_RECEIPT_MIMES:
            errors["receipt"] = "Receipt must be an image (jpg/png/webp) or PDF."
        if receipt_size is not None and receipt_size > MAX_RECEIPT_SIZE_BYTES:
            errors["receipt"] = "Receipt file size exceeds limit (5MB)."

    if errors:
        return error_response("Validation failed", errors=errors), 400

    if receipt_file and receipt_file.filename:
        upload_dir = os.path.join(current_app.root_path, "uploads", "receipts", str(user_id))
        os.makedirs(upload_dir, exist_ok=True)
        ext = os.path.splitext(receipt_file.filename)[1].lower()
        safe_name = f"expense_{user_id}_{int(datetime.now().timestamp())}_{hashlib.sha256(receipt_file.filename.encode('utf-8')).hexdigest()[:16]}{ext}"
        file_path = os.path.join(upload_dir, safe_name)
        receipt_file.save(file_path)
        receipt_filename = safe_name
        receipt_url = f"/uploads/receipts/{user_id}/{safe_name}"

    fingerprint = _fingerprint_for_duplicate(title, amount, str(expense_date), merchant_name, currency)

    expense_data = {
        "user_id": user_id,
        "title": title,
        "category": category_final,
        "sub_category": sub_category,
        "amount": amount,
        "expense_date": str(expense_date),
        "payment_method": payment_method,
        "account_id": account_id,
        "merchant_name": merchant_name,
        "location": location,
        "description": description,
        "tags_json": json.dumps(tags) if tags else None,
        "recurring": recurring,
        "recurring_frequency": recurring_frequency,
        "currency": currency,
        "priority": priority,
        "mood": mood,
        "receipt_filename": receipt_filename,
        "receipt_url": receipt_url,
        "receipt_mime": receipt_mime,
        "receipt_size": receipt_size,
        "ocr_ready": False,
        "tax_included": tax_included,
        "invoice_number": invoice_number,
        "receipt_number": receipt_number,
        "gst": gst,
        "budget_id": budget_id,
        "notes": notes,
        "normalized_title": _normalize_title(title),
        "fingerprint": fingerprint,
        "status": "active",
        "is_deleted": False,
    }

    try:
        result = sb.insert("expenses", expense_data)
        expense_id = result.get("id") if result else None

        # Save splits
        if splits and isinstance(splits, list) and expense_id:
            for split in splits:
                split_data = {
                    "expense_id": expense_id,
                    "user_id": user_id,
                    "split_with_name": split.get("split_with_name", ""),
                    "split_type": split.get("split_type", "custom"),
                    "split_method": split.get("split_method", "equal"),
                    "amount": split.get("amount", 0),
                    "percentage": split.get("percentage"),
                }
                sb.insert("expense_splits", split_data)

        # Update favorite merchant
        if merchant_name:
            existing_fav = sb.select("favorite_merchants", filters={
                "user_id": user_id, "merchant_name": merchant_name
            }, limit=1)
            if existing_fav and len(existing_fav) > 0:
                sb.update("favorite_merchants", {
                    "user_id": user_id, "merchant_name": merchant_name
                }, {"usage_count": (existing_fav[0].get("usage_count", 0) or 0) + 1})
            else:
                sb.insert("favorite_merchants", {
                    "user_id": user_id,
                    "merchant_name": merchant_name,
                    "category": category_final,
                    "default_payment_method": payment_method,
                    "default_account_id": account_id,
                    "usage_count": 1,
                })

    except Exception as e:
        return error_response("Expense creation failed", errors={"error": str(e)}), 500

    return success_response(
        message="Expense added successfully.",
        data={"expense_id": expense_id},
    ), 201


@expenses_bp.route("/", methods=["GET"])
@jwt_required()
def get_expenses():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    # Build query params for Supabase
    filters = {"user_id": user_id, "is_deleted": "false"}
    
    search_term = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    payment_method = request.args.get("payment_method", "").strip()
    status = request.args.get("status", "").strip()
    
    if category:
        filters["category"] = category
    if payment_method:
        filters["payment_method"] = payment_method
    if status:
        filters["status"] = status

    sort_by = request.args.get("sort", "created_at").strip()
    order = request.args.get("order", "desc").strip().lower()
    order_param = f"{sort_by}.{order}"

    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = max(1, min(100, int(request.args.get("per_page", 20))))
    except Exception:
        page = 1
        per_page = 20

    # Get total count first
    all_expenses = sb.select("expenses", columns="id", filters=filters)
    total = len(all_expenses) if all_expenses else 0

    # Get paginated results
    offset = (page - 1) * per_page
    expenses = sb.select("expenses", columns="*", filters=filters, order=order_param, limit=per_page)

    # Manual pagination since Supabase REST doesn't support offset easily
    if expenses and len(expenses) > offset:
        expenses = expenses[offset:offset + per_page]
    else:
        expenses = []

    # Filter by search term if provided
    if search_term and expenses:
        search_lower = search_term.lower()
        expenses = [
            e for e in expenses
            if search_lower in (e.get("title", "")).lower()
            or search_lower in (e.get("merchant_name", "") or "").lower()
            or search_lower in (e.get("description", "") or "").lower()
        ]

    expenses_data = [
        {
            "id": exp.get("id"),
            "title": exp.get("title"),
            "category": exp.get("category"),
            "sub_category": exp.get("sub_category"),
            "amount": str(exp.get("amount", 0)),
            "expense_date": exp.get("expense_date"),
            "payment_method": exp.get("payment_method"),
            "merchant_name": exp.get("merchant_name"),
            "status": exp.get("status"),
            "receipt_url": exp.get("receipt_url"),
            "created_at": exp.get("created_at"),
        }
        for exp in expenses
    ]

    return success_response(
        message="Expenses fetched successfully.",
        data={
            "expenses": expenses_data,
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page if per_page > 0 else 0,
            },
        },
    ), 200


@expenses_bp.route("/<int:expense_id>", methods=["GET"])
@jwt_required()
def get_expense(expense_id: int):
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    try:
        exp = sb.select("expenses", filters={
            "id": expense_id, "user_id": user_id, "is_deleted": "false"
        }, single=True)
    except Exception:
        exp = None

    if not exp:
        return error_response("Expense not found"), 404

    return success_response(message="Expense fetched successfully.", data=exp), 200


@expenses_bp.route("/<int:expense_id>", methods=["PUT"])
@jwt_required()
def update_expense(expense_id: int):
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    try:
        exp = sb.select("expenses", filters={
            "id": expense_id, "user_id": user_id, "is_deleted": "false"
        }, single=True)
    except Exception:
        exp = None

    if not exp:
        return error_response("Expense not found"), 404

    payload = request.get_json(silent=True) or {}

    update_data = {}
    for field in ["title", "category", "sub_category", "amount", "expense_date",
                  "payment_method", "merchant_name", "location", "description",
                  "currency", "priority", "mood", "status", "notes"]:
        if field in payload:
            update_data[field] = payload[field]

    if "amount" in update_data:
        try:
            update_data["amount"] = float(update_data["amount"])
        except Exception:
            pass

    try:
        sb.update("expenses", {"id": expense_id, "user_id": user_id}, update_data)
    except Exception as e:
        return error_response("Expense update failed", errors={"error": str(e)}), 500

    return success_response(message="Expense updated successfully.", data={"expense_id": expense_id}), 200


@expenses_bp.route("/<int:expense_id>", methods=["DELETE"])
@jwt_required()
def delete_expense(expense_id: int):
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    try:
        sb.update("expenses", {"id": expense_id, "user_id": user_id}, {
            "is_deleted": True, "deleted_at": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return error_response("Expense delete failed", errors={"error": str(e)}), 500

    return success_response(message="Expense deleted successfully.", data={"expense_id": expense_id}), 200


@expenses_bp.route("/<int:expense_id>/duplicate", methods=["POST"])
@jwt_required()
def duplicate_expense(expense_id: int):
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    try:
        exp = sb.select("expenses", filters={
            "id": expense_id, "user_id": user_id, "is_deleted": "false"
        }, single=True)
    except Exception:
        exp = None

    if not exp:
        return error_response("Expense not found"), 404

    payload = request.get_json(silent=True) or {}

    new_data = {k: v for k, v in exp.items() if k not in ("id", "created_at", "updated_at", "deleted_at")}
    new_data.update({
        "title": payload.get("title", exp.get("title")),
        "amount": payload.get("amount", exp.get("amount")),
        "status": "active",
        "is_deleted": False,
    })

    try:
        result = sb.insert("expenses", new_data)
    except Exception as e:
        return error_response("Expense duplication failed", errors={"error": str(e)}), 500

    return success_response(
        message="Expense duplicated successfully.",
        data={"expense_id": result.get("id") if result else None},
    ), 201


@expenses_bp.route("/statistics", methods=["GET"])
@jwt_required()
def get_statistics():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    date_from_str = request.args.get("date_from", "").strip()
    date_to_str = request.args.get("date_to", "").strip()

    today = date.today()
    date_from = _parse_date(date_from_str) or today - timedelta(days=30)
    date_to = _parse_date(date_to_str) or today

    try:
        all_expenses = sb.select("expenses", columns="amount,category,payment_method,merchant_name,expense_date",
                                 filters={"user_id": user_id, "is_deleted": "false"})
    except Exception:
        all_expenses = []

    # Filter by date range
    filtered = [
        e for e in (all_expenses or [])
        if date_from.isoformat() <= (e.get("expense_date") or "") <= date_to.isoformat()
    ]

    total_expenses = len(filtered)
    total_amount = sum(float(e.get("amount", 0)) for e in filtered)
    avg_amount = total_amount / total_expenses if total_expenses > 0 else 0

    # Category stats
    cat_totals = {}
    for e in filtered:
        cat = e.get("category", "Others")
        cat_totals[cat] = cat_totals.get(cat, 0) + float(e.get("amount", 0))

    highest_category = max(cat_totals, key=cat_totals.get) if cat_totals else "N/A"
    highest_category_amount = cat_totals.get(highest_category, 0)

    # Payment method stats
    pm_counts = {}
    for e in filtered:
        pm = e.get("payment_method", "Unknown")
        pm_counts[pm] = pm_counts.get(pm, 0) + 1

    most_used_payment = max(pm_counts, key=pm_counts.get) if pm_counts else "N/A"

    # Top merchant
    merchant_totals = {}
    for e in filtered:
        m = e.get("merchant_name")
        if m:
            merchant_totals[m] = merchant_totals.get(m, 0) + float(e.get("amount", 0))

    top_merchant = max(merchant_totals, key=merchant_totals.get) if merchant_totals else "N/A"

    return success_response(
        message="Statistics fetched successfully.",
        data={
            "total_expenses": total_expenses,
            "total_amount": str(round(total_amount, 2)),
            "average_amount": str(round(avg_amount, 2)),
            "highest_spending_category": highest_category,
            "highest_category_amount": str(round(highest_category_amount, 2)),
            "most_used_payment_method": most_used_payment,
            "top_merchant": top_merchant,
            "date_range": {"from": date_from.isoformat(), "to": date_to.isoformat()},
        },
    ), 200


@expenses_bp.route("/chart-data", methods=["GET"])
@jwt_required()
def get_chart_data():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    date_from_str = request.args.get("date_from", "").strip()
    date_to_str = request.args.get("date_to", "").strip()

    today = date.today()
    date_from = _parse_date(date_from_str) or today - timedelta(days=30)
    date_to = _parse_date(date_to_str) or today

    try:
        all_expenses = sb.select("expenses", columns="amount,category,payment_method,expense_date",
                                 filters={"user_id": user_id, "is_deleted": "false"})
    except Exception:
        all_expenses = []

    filtered = [
        e for e in (all_expenses or [])
        if date_from.isoformat() <= (e.get("expense_date") or "") <= date_to.isoformat()
    ]

    # Category chart
    cat_data = {}
    for e in filtered:
        cat = e.get("category", "Others")
        if cat not in cat_data:
            cat_data[cat] = {"value": 0, "count": 0}
        cat_data[cat]["value"] += float(e.get("amount", 0))
        cat_data[cat]["count"] += 1

    category_chart = [{"name": k, "value": v["value"], "count": v["count"]} for k, v in cat_data.items()]

    # Monthly chart
    month_data = {}
    for e in filtered:
        d = e.get("expense_date", "")
        if d:
            month = d[:7]  # YYYY-MM
            month_data[month] = month_data.get(month, 0) + float(e.get("amount", 0))

    monthly_chart = [{"month": k, "total": v} for k, v in sorted(month_data.items())]

    # Payment chart
    pm_data = {}
    for e in filtered:
        pm = e.get("payment_method", "Unknown")
        if pm not in pm_data:
            pm_data[pm] = {"value": 0, "count": 0}
        pm_data[pm]["value"] += float(e.get("amount", 0))
        pm_data[pm]["count"] += 1

    payment_chart = [{"name": k, "value": v["value"], "count": v["count"]} for k, v in pm_data.items()]

    # Daily chart
    day_data = {}
    for e in filtered:
        d = e.get("expense_date", "")
        if d:
            day_data[d] = {"total": day_data.get(d, {}).get("total", 0) + float(e.get("amount", 0)),
                           "count": day_data.get(d, {}).get("count", 0) + 1}

    daily_chart = [{"date": k, "total": v["total"], "count": v["count"]} for k, v in sorted(day_data.items())]

    return success_response(
        message="Chart data fetched successfully.",
        data={
            "category_chart": category_chart,
            "monthly_chart": monthly_chart,
            "payment_chart": payment_chart,
            "daily_chart": daily_chart,
        },
    ), 200


@expenses_bp.route("/dashboard-stats", methods=["GET"])
@jwt_required()
def get_dashboard_stats():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    today = date.today()
    month_start = today.replace(day=1)
    week_start = today - timedelta(days=today.weekday())

    try:
        all_expenses = sb.select("expenses", columns="amount,expense_date",
                                 filters={"user_id": user_id, "is_deleted": "false"})
    except Exception:
        all_expenses = []

    total_expenses = len(all_expenses) if all_expenses else 0
    total_amount = sum(float(e.get("amount", 0)) for e in (all_expenses or []))

    today_expenses = [e for e in (all_expenses or []) if e.get("expense_date") == today.isoformat()]
    today_amount = sum(float(e.get("amount", 0)) for e in today_expenses)

    month_expenses = [e for e in (all_expenses or []) if e.get("expense_date", "") >= month_start.isoformat()]
    month_amount = sum(float(e.get("amount", 0)) for e in month_expenses)

    week_expenses = [e for e in (all_expenses or []) if e.get("expense_date", "") >= week_start.isoformat()]
    week_amount = sum(float(e.get("amount", 0)) for e in week_expenses)

    avg_amount = total_amount / total_expenses if total_expenses > 0 else 0
    largest_amount = max((float(e.get("amount", 0)) for e in (all_expenses or [])), default=0)

    return success_response(
        message="Dashboard stats fetched successfully.",
        data={
            "total_expenses": total_expenses,
            "total_amount": str(round(total_amount, 2)),
            "today_expenses": len(today_expenses),
            "today_amount": str(round(today_amount, 2)),
            "month_expenses": len(month_expenses),
            "month_amount": str(round(month_amount, 2)),
            "week_expenses": len(week_expenses),
            "week_amount": str(round(week_amount, 2)),
            "average_amount": str(round(avg_amount, 2)),
            "largest_amount": str(round(largest_amount, 2)),
        },
    ), 200


@expenses_bp.route("/duplicate-check", methods=["POST"])
@jwt_required()
def duplicate_check():
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
        return success_response(
            message="Duplicate check skipped (missing fields).",
            data={"possible_duplicate": False, "duplicates": []},
        ), 200

    try:
        amount_f = float(amount)
    except Exception:
        return success_response(
            message="Duplicate check skipped (invalid amount).",
            data={"possible_duplicate": False, "duplicates": []},
        ), 200

    normalized = _normalize_title(title)

    try:
        possible = sb.select("expenses", columns="id,title,amount,expense_date,merchant_name",
                             filters={
                                 "user_id": user_id, "is_deleted": "false",
                                 "normalized_title": normalized,
                             }, limit=5)
    except Exception:
        possible = []

    # Filter by amount and date
    duplicates = [
        {
            "id": e.get("id"),
            "title": e.get("title"),
            "amount": str(e.get("amount")),
            "expense_date": e.get("expense_date"),
            "merchant_name": e.get("merchant_name"),
        }
        for e in (possible or [])
        if float(e.get("amount", 0)) == amount_f and e.get("expense_date") == expense_date
    ]

    return success_response(
        message="Duplicate check completed.",
        data={"possible_duplicate": len(duplicates) > 0, "duplicates": duplicates},
    ), 200


@expenses_bp.route("/categories", methods=["GET"])
@jwt_required()
def get_categories():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    categories = [
        {"name": name, "icon": meta["icon"], "color": meta["color"]}
        for name, meta in CATEGORY_METADATA.items()
    ]

    return success_response(
        message="Categories fetched successfully.",
        data={"categories": categories},
    ), 200


@expenses_bp.route("/payment-methods", methods=["GET"])
@jwt_required()
def get_payment_methods():
    return success_response(
        message="Payment methods fetched successfully.",
        data={"payment_methods": PAYMENT_METHODS},
    ), 200


@expenses_bp.route("/accounts", methods=["GET"])
@jwt_required()
def get_accounts():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    try:
        accounts = sb.select("accounts", filters={"user_id": user_id, "is_deleted": "false"})
    except Exception:
        accounts = []

    accounts_data = [
        {"id": acc.get("id"), "name": acc.get("name"), "account_type": acc.get("account_type")}
        for acc in (accounts or [])
    ]

    return success_response(
        message="Accounts fetched successfully.",
        data={"accounts": accounts_data, "account_types": ACCOUNT_TYPES},
    ), 200


@expenses_bp.route("/accounts", methods=["POST"])
@jwt_required()
def create_account():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    account_type = (payload.get("account_type") or "").strip() or None

    if not name:
        return error_response("Account name is required"), 400

    try:
        result = sb.insert("accounts", {"user_id": user_id, "name": name, "account_type": account_type})
    except Exception as e:
        return error_response("Account creation failed", errors={"error": str(e)}), 500

    return success_response(
        message="Account created successfully.",
        data={"account_id": result.get("id") if result else None},
    ), 201


@expenses_bp.route("/scan-receipt", methods=["POST"])
@jwt_required()
def scan_receipt():
    """OCR receipt scanning endpoint."""
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    receipt_file = request.files.get("receipt")
    if not receipt_file or not receipt_file.filename:
        return error_response("No receipt file provided"), 400

    receipt_mime = receipt_file.mimetype
    if receipt_mime not in ALLOWED_RECEIPT_MIMES:
        return error_response("Receipt must be an image (jpg/png/webp) or PDF"), 400

    receipt_size = request.content_length
    if receipt_size and receipt_size > MAX_RECEIPT_SIZE_BYTES:
        return error_response("Receipt file size exceeds limit (5MB)"), 400

    # Save receipt temporarily
    upload_dir = os.path.join(current_app.root_path, "uploads", "receipts", str(user_id), "temp")
    os.makedirs(upload_dir, exist_ok=True)
    ext = os.path.splitext(receipt_file.filename)[1].lower()
    temp_name = f"scan_{user_id}_{int(datetime.now().timestamp())}{ext}"
    temp_path = os.path.join(upload_dir, temp_name)
    receipt_file.save(temp_path)

    # Heuristic-based OCR extraction (simulated)
    import random
    confidence = round(random.uniform(0.75, 0.95), 2)
    filename_lower = receipt_file.filename.lower()

    extracted_data = {
        "merchant": "", "amount": None, "date": None, "tax": None,
        "items": [], "category": "Others", "payment_method": "",
        "currency": "USD", "invoice_number": "", "gst": "",
        "receipt_number": "", "address": "", "confidence": 0.0,
    }

    if "uber" in filename_lower or "taxi" in filename_lower:
        extracted_data.update({
            "merchant": "Uber", "amount": round(random.uniform(15, 80), 2),
            "category": "Travel", "payment_method": "Credit Card", "confidence": confidence,
        })
    elif "pizza" in filename_lower or "food" in filename_lower or "restaurant" in filename_lower:
        extracted_data.update({
            "merchant": "Pizza Hut", "amount": round(random.uniform(20, 60), 2),
            "category": "Food", "payment_method": "Credit Card", "confidence": confidence,
        })
    elif "amazon" in filename_lower or "shopping" in filename_lower:
        extracted_data.update({
            "merchant": "Amazon", "amount": round(random.uniform(10, 200), 2),
            "category": "Shopping", "payment_method": "Credit Card", "confidence": confidence,
        })
    else:
        extracted_data.update({
            "merchant": "Unknown Merchant", "amount": round(random.uniform(10, 100), 2),
            "category": "Others", "confidence": confidence,
        })

    extracted_data["date"] = date.today().isoformat()
    extracted_data["tax"] = round(extracted_data["amount"] * 0.08, 2)
    extracted_data["items"] = [
        {"name": "Item 1", "price": round(extracted_data["amount"] * 0.6, 2)},
        {"name": "Item 2", "price": round(extracted_data["amount"] * 0.4, 2)},
    ]

    try:
        os.remove(temp_path)
    except Exception:
        pass

    return success_response(message="Receipt scanned successfully.", data=extracted_data), 200


@expenses_bp.route("/budgets", methods=["GET"])
@jwt_required()
def get_budgets():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    try:
        budgets = sb.select("budgets", filters={"user_id": user_id, "is_deleted": "false"})
    except Exception:
        budgets = []

    today = date.today()
    month_start = today.replace(day=1)

    try:
        expenses = sb.select("expenses", columns="amount,category,expense_date",
                             filters={"user_id": user_id, "is_deleted": "false"})
    except Exception:
        expenses = []

    budget_data = []
    for budget in (budgets or []):
        cat = budget.get("category")
        spent = sum(
            float(e.get("amount", 0)) for e in (expenses or [])
            if e.get("category") == cat and e.get("expense_date", "") >= month_start.isoformat()
        )
        limit = float(budget.get("limit_amount", 0))
        remaining = limit - spent
        percentage_used = (spent / limit * 100) if limit > 0 else 0

        budget_data.append({
            "id": budget.get("id"),
            "category": cat,
            "limit_amount": str(budget.get("limit_amount")),
            "period": budget.get("period"),
            "spent": str(round(spent, 2)),
            "remaining": str(round(remaining, 2)),
            "percentage_used": round(percentage_used, 1),
            "is_overspending": remaining < 0,
        })

    return success_response(message="Budgets fetched successfully.", data={"budgets": budget_data}), 200


@expenses_bp.route("/budgets", methods=["POST"])
@jwt_required()
def create_budget():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    payload = request.get_json(silent=True) or {}
    category = (payload.get("category") or "").strip()
    limit_amount = payload.get("limit_amount")
    period = (payload.get("period") or "monthly").strip()

    if not category:
        return error_response("Category is required"), 400

    try:
        limit = float(limit_amount)
    except Exception:
        return error_response("Valid limit amount is required"), 400

    if limit <= 0:
        return error_response("Limit amount must be greater than 0"), 400

    try:
        result = sb.insert("budgets", {
            "user_id": user_id, "category": category,
            "limit_amount": limit, "period": period,
        })
    except Exception as e:
        return error_response("Budget creation failed", errors={"error": str(e)}), 500

    return success_response(
        message="Budget created successfully.",
        data={"budget_id": result.get("id") if result else None},
    ), 201


@expenses_bp.route("/budget-check", methods=["GET"])
@jwt_required()
def budget_check():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    category = request.args.get("category", "").strip()
    amount_str = request.args.get("amount", "0")

    try:
        amount = float(amount_str)
    except Exception:
        amount = 0

    if not category:
        return success_response(
            message="No category specified.",
            data={"has_budget": False, "current_budget": 0, "remaining": 0, "after_expense": 0, "percentage_used": 0},
        ), 200

    try:
        budget = sb.select("budgets", filters={
            "user_id": user_id, "category": category, "is_deleted": "false"
        }, limit=1)
    except Exception:
        budget = []

    if not budget:
        return success_response(
            message="No budget set for this category.",
            data={"has_budget": False, "current_budget": 0, "remaining": 0, "after_expense": 0, "percentage_used": 0},
        ), 200

    budget = budget[0]
    today = date.today()
    month_start = today.replace(day=1)

    try:
        expenses = sb.select("expenses", columns="amount",
                             filters={"user_id": user_id, "is_deleted": "false", "category": category})
    except Exception:
        expenses = []

    spent = sum(float(e.get("amount", 0)) for e in (expenses or []))
    limit = float(budget.get("limit_amount", 0))
    remaining = limit - spent
    after_expense = remaining - amount
    percentage_used = (spent / limit * 100) if limit > 0 else 0
    percentage_after = ((spent + amount) / limit * 100) if limit > 0 else 0

    return success_response(
        message="Budget check completed.",
        data={
            "has_budget": True,
            "current_budget": str(budget.get("limit_amount")),
            "spent": str(round(spent, 2)),
            "remaining": str(round(remaining, 2)),
            "after_expense": str(round(after_expense, 2)),
            "percentage_used": round(percentage_used, 1),
            "percentage_after": round(percentage_after, 1),
            "is_overspending": after_expense < 0,
        },
    ), 200


@expenses_bp.route("/ai-suggestions", methods=["GET"])
@jwt_required()
def ai_suggestions():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    title = request.args.get("title", "").strip()
    merchant = request.args.get("merchant", "").strip()
    amount_str = request.args.get("amount", "0")

    try:
        amount = float(amount_str)
    except Exception:
        amount = 0

    suggestions = {
        "suggested_category": None, "suggested_budget": None,
        "monthly_trend": None, "previous_similar": [],
        "average_amount": None, "recurring_suggestion": None, "insight": None,
    }

    suggested_cat = _suggest_category(title, merchant)
    if suggested_cat != "Others":
        suggestions["suggested_category"] = suggested_cat

    if title or merchant:
        search_text = title or merchant
        try:
            all_expenses = sb.select("expenses", columns="id,title,amount,category,merchant_name,expense_date",
                                     filters={"user_id": user_id, "is_deleted": "false"})
        except Exception:
            all_expenses = []

        search_lower = search_text.lower()
        previous = [
            e for e in (all_expenses or [])
            if search_lower in (e.get("title", "")).lower()
            or search_lower in (e.get("merchant_name", "") or "").lower()
        ][:5]

        suggestions["previous_similar"] = [
            {
                "id": e.get("id"), "title": e.get("title"),
                "amount": str(e.get("amount")), "category": e.get("category"),
                "expense_date": e.get("expense_date"),
            }
            for e in previous
        ]

        if previous:
            amounts = [float(e.get("amount", 0)) for e in previous]
            avg = sum(amounts) / len(amounts)
            suggestions["average_amount"] = round(avg, 2)

            if amount > 0 and avg > 0:
                diff_pct = ((amount - avg) / avg) * 100
                if diff_pct > 10:
                    suggestions["insight"] = f"This is {abs(round(diff_pct))}% higher than your average {suggested_cat} expense."
                elif diff_pct < -10:
                    suggestions["insight"] = f"This is {abs(round(diff_pct))}% lower than your average {suggested_cat} expense."

    if suggested_cat:
        today = date.today()
        month_start = today.replace(day=1)
        try:
            all_expenses = sb.select("expenses", columns="amount,category,expense_date",
                                     filters={"user_id": user_id, "is_deleted": "false"})
        except Exception:
            all_expenses = []

        month_amount = sum(
            float(e.get("amount", 0)) for e in (all_expenses or [])
            if e.get("category") == suggested_cat and e.get("expense_date", "") >= month_start.isoformat()
        )
        suggestions["monthly_trend"] = str(round(month_amount, 2))

    if merchant:
        try:
            all_expenses = sb.select("expenses", columns="merchant_name",
                                     filters={"user_id": user_id, "is_deleted": "false"})
        except Exception:
            all_expenses = []

        recurring_count = sum(
            1 for e in (all_expenses or [])
            if merchant.lower() in (e.get("merchant_name", "") or "").lower()
        )
        if recurring_count >= 3:
            suggestions["recurring_suggestion"] = f"You've spent at {merchant} {recurring_count} times. Consider marking this as recurring."

    return success_response(message="AI suggestions fetched successfully.", data=suggestions), 200


@expenses_bp.route("/favorite-merchants", methods=["GET"])
@jwt_required()
def get_favorite_merchants():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    try:
        merchants = sb.select("favorite_merchants", filters={"user_id": user_id},
                              order="usage_count.desc", limit=10)
    except Exception:
        merchants = []

    data = [
        {
            "id": m.get("id"), "merchant_name": m.get("merchant_name"),
            "category": m.get("category"), "default_payment_method": m.get("default_payment_method"),
            "usage_count": m.get("usage_count"),
        }
        for m in (merchants or [])
    ]

    return success_response(message="Favorite merchants fetched successfully.", data={"merchants": data}), 200


@expenses_bp.route("/templates", methods=["GET"])
@jwt_required()
def get_templates():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    try:
        templates = sb.select("expense_templates", filters={"user_id": user_id},
                              order="created_at.desc")
    except Exception:
        templates = []

    data = [
        {"id": t.get("id"), "name": t.get("name"), "template_data": t.get("template_data")}
        for t in (templates or [])
    ]

    return success_response(message="Templates fetched successfully.", data={"templates": data}), 200


@expenses_bp.route("/templates", methods=["POST"])
@jwt_required()
def create_template():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    template_data = payload.get("template_data")

    if not name or not template_data:
        return error_response("Template name and data are required"), 400

    try:
        result = sb.insert("expense_templates", {
            "user_id": user_id, "name": name,
            "template_data": json.dumps(template_data),
        })
    except Exception as e:
        return error_response("Template creation failed", errors={"error": str(e)}), 500

    return success_response(
        message="Template created successfully.",
        data={"template_id": result.get("id") if result else None},
    ), 201


@expenses_bp.route("/drafts", methods=["GET"])
@jwt_required()
def get_draft():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    try:
        drafts = sb.select("expense_drafts", filters={"user_id": user_id},
                           order="updated_at.desc", limit=1)
    except Exception:
        drafts = []

    if not drafts:
        return success_response(message="No draft found.", data={"draft": None}), 200

    return success_response(
        message="Draft fetched successfully.",
        data={"draft": drafts[0].get("draft_data"), "updated_at": drafts[0].get("updated_at")},
    ), 200


@expenses_bp.route("/drafts", methods=["POST"])
@jwt_required()
def save_draft():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    payload = request.get_json(silent=True) or {}
    draft_data = payload.get("draft_data")

    if not draft_data:
        return error_response("Draft data is required"), 400

    try:
        existing = sb.select("expense_drafts", filters={"user_id": user_id}, limit=1)
        if existing and len(existing) > 0:
            sb.update("expense_drafts", {"id": existing[0].get("id")},
                      {"draft_data": json.dumps(draft_data)})
        else:
            sb.insert("expense_drafts", {
                "user_id": user_id, "draft_data": json.dumps(draft_data),
            })
    except Exception as e:
        return error_response("Draft save failed", errors={"error": str(e)}), 500

    return success_response(message="Draft saved successfully."), 200


@expenses_bp.route("/drafts", methods=["DELETE"])
@jwt_required()
def delete_draft():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    try:
        sb.delete("expense_drafts", {"user_id": user_id})
    except Exception as e:
        return error_response("Draft delete failed", errors={"error": str(e)}), 500

    return success_response(message="Draft deleted successfully."), 200


@expenses_bp.route("/recent", methods=["GET"])
@jwt_required()
def get_recent_expenses():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    try:
        recent = sb.select("expenses", columns="id,title,amount,category,merchant_name,expense_date",
                          filters={"user_id": user_id, "is_deleted": "false"},
                          order="created_at.desc", limit=5)
    except Exception:
        recent = []

    data = [
        {
            "id": e.get("id"), "title": e.get("title"),
            "amount": str(e.get("amount")), "category": e.get("category"),
            "merchant_name": e.get("merchant_name"), "expense_date": e.get("expense_date"),
        }
        for e in (recent or [])
    ]

    return success_response(message="Recent expenses fetched successfully.", data={"recent": data}), 200


@expenses_bp.route("/quick-add-amounts", methods=["GET"])
@jwt_required()
def get_quick_add_amounts():
    return success_response(
        message="Quick add amounts fetched successfully.",
        data={"amounts": QUICK_ADD_AMOUNTS, "moods": MOOD_OPTIONS},
    ), 200


@expenses_bp.route("/undo/<int:expense_id>", methods=["POST"])
@jwt_required()
def undo_expense(expense_id: int):
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    try:
        sb.update("expenses", {"id": expense_id, "user_id": user_id}, {
            "is_deleted": True, "deleted_at": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return error_response("Undo failed", errors={"error": str(e)}), 500

    return success_response(message="Expense undone successfully.", data={"expense_id": expense_id}), 200
