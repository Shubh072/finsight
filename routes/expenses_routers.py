import os
import json
import hashlib
import re
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
    if user_id is not None:
        try:
            return int(user_id)
        except (ValueError, TypeError):
            return user_id
    return None


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


@expenses_bp.route("/scan-receipt", methods=["POST"])
@jwt_required()
def scan_receipt():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401
    if "receipt" not in request.files:
        return error_response("Receipt file is required", errors={"receipt": "Receipt file is required"}), 400
    receipt_file = request.files["receipt"]
    if not receipt_file.filename:
        return error_response("Receipt file is required", errors={"receipt": "Receipt file is required"}), 400
    # Simulated receipt scan
    return success_response("Receipt scanned successfully", data={
        "merchant_name": None, "amount": None, "expense_date": date.today().isoformat(),
        "category": "Others", "confidence_score": 0.5, "currency": "INR", "payment_method": "UPI",
        "title": "Receipt Expense", "description": "Receipt uploaded",
    }), 200


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
        "user_id": user_id, "title": title, "category": category_final, "sub_category": sub_category,
        "amount": amount, "expense_date": str(expense_date), "payment_method": payment_method,
        "account_id": account_id, "merchant_name": merchant_name, "location": location,
        "description": description, "tags_json": json.dumps(tags) if tags else None,
        "recurring": recurring, "recurring_frequency": recurring_frequency, "currency": currency,
        "priority": priority, "mood": mood, "receipt_filename": receipt_filename, "receipt_url": receipt_url,
        "receipt_mime": receipt_mime, "receipt_size": receipt_size, "ocr_ready": False,
        "tax_included": tax_included, "invoice_number": invoice_number, "receipt_number": receipt_number,
        "gst": gst, "budget_id": budget_id, "notes": notes,
        "normalized_title": _normalize_title(title), "fingerprint": fingerprint,
        "status": "active", "is_deleted": False,
    }
    try:
        result = sb.insert("expenses", expense_data)
        expense_id = result.get("id") if result else None
        if splits and isinstance(splits, list) and expense_id:
            for split in splits:
                sb.insert("expense_splits", {"expense_id": expense_id, "user_id": user_id, **split})
        if merchant_name:
            existing_fav = sb.select("favorite_merchants", filters={"user_id": user_id, "merchant_name": merchant_name}, limit=1)
            if existing_fav and len(existing_fav) > 0:
                sb.update("favorite_merchants", {"user_id": user_id, "merchant_name": merchant_name},
                          {"usage_count": (existing_fav[0].get("usage_count", 0) or 0) + 1})
            else:
                sb.insert("favorite_merchants", {"user_id": user_id, "merchant_name": merchant_name, "category": category_final, "usage_count": 1})
    except Exception as e:
        return error_response("Expense creation failed", errors={"error": str(e)}), 500
    return success_response(message="Expense added successfully.", data={"expense_id": expense_id}), 201


@expenses_bp.route("/", methods=["GET"])
@jwt_required()
def get_expenses():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401
    filters = {"user_id": user_id, "is_deleted": "false"}
    search_term = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    payment_method = request.args.get("payment_method", "").strip()
    status = request.args.get("status", "").strip()
    if category: filters["category"] = category
    if payment_method: filters["payment_method"] = payment_method
    if status: filters["status"] = status
    sort_by = request.args.get("sort", "created_at").strip()
    order = request.args.get("order", "desc").strip().lower()
    order_param = f"{sort_by}.{order}"
    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = max(1, min(100, int(request.args.get("per_page", 20))))
    except Exception:
        page, per_page = 1, 20
    all_expenses = sb.select("expenses", columns="id", filters=filters)
    total = len(all_expenses) if all_expenses else 0
    offset = (page - 1) * per_page
    expenses = sb.select("expenses", columns="*", filters=filters, order=order_param, limit=per_page)
    if expenses and len(expenses) > offset:
        expenses = expenses[offset:offset + per_page]
    else:
        expenses = []
    if search_term and expenses:
        search_lower = search_term.lower()
        expenses = [e for e in expenses if search_lower in (e.get("title", "")).lower() or search_lower in (e.get("merchant_name", "") or "").lower()]
    expenses_data = [{"id": e.get("id"), "title": e.get("title"), "category": e.get("category"), "amount": str(e.get("amount", 0)), "expense_date": e.get("expense_date")} for e in expenses]
    return success_response(message="Expenses fetched successfully.", data={"expenses": expenses_data, "pagination": {"total": total, "page": page, "per_page": per_page}}), 200


@expenses_bp.route("/<int:expense_id>", methods=["GET"])
@jwt_required()
def get_expense(expense_id: int):
    user_id = _user_id_from_claims()
    if not user_id: return error_response("Unauthorized"), 401
    try:
        exp = sb.select("expenses", filters={"id": expense_id, "user_id": user_id, "is_deleted": "false"}, single=True)
    except Exception:
        exp = None
    if not exp: return error_response("Expense not found"), 404
    return success_response(message="Expense fetched successfully.", data=exp), 200


@expenses_bp.route("/<int:expense_id>", methods=["PUT"])
@jwt_required()
def update_expense(expense_id: int):
    user_id = _user_id_from_claims()
    if not user_id: return error_response("Unauthorized"), 401
    try:
        exp = sb.select("expenses", filters={"id": expense_id, "user_id": user_id, "is_deleted": "false"}, single=True)
    except Exception:
        exp = None
    if not exp: return error_response("Expense not found"), 404
    payload = request.get_json(silent=True) or {}
    update_data = {}
    for field in ["title", "category", "sub_category", "amount", "expense_date", "payment_method", "merchant_name", "description", "status"]:
        if field in payload: update_data[field] = payload[field]
    try:
        sb.update("expenses", {"id": expense_id, "user_id": user_id}, update_data)
    except Exception as e:
        return error_response("Expense update failed", errors={"error": str(e)}), 500
    return success_response(message="Expense updated successfully.", data={"expense_id": expense_id}), 200


@expenses_bp.route("/<int:expense_id>", methods=["DELETE"])
@jwt_required()
def delete_expense(expense_id: int):
    user_id = _user_id_from_claims()
    if not user_id: return error_response("Unauthorized"), 401
    try:
        sb.update("expenses", {"id": expense_id, "user_id": user_id}, {"is_deleted": True, "deleted_at": datetime.utcnow().isoformat()})
    except Exception as e:
        return error_response("Expense delete failed", errors={"error": str(e)}), 500
    return success_response(message="Expense deleted successfully.", data={"expense_id": expense_id}), 200


@expenses_bp.route("/statistics", methods=["GET"])
@jwt_required()
def get_statistics():
    user_id = _user_id_from_claims()
    if not user_id: return error_response("Unauthorized"), 401
    date_from_str = request.args.get("date_from", "").strip()
    date_to_str = request.args.get("date_to", "").strip()
    today = date.today()
    date_from = _parse_date(date_from_str) or today - timedelta(days=30)
    date_to = _parse_date(date_to_str) or today
    try:
        all_expenses = sb.select("expenses", columns="amount,category,payment_method,merchant_name,expense_date", filters={"user_id": user_id, "is_deleted": "false"})
    except Exception:
        all_expenses = []
    filtered = [e for e in (all_expenses or []) if date_from.isoformat() <= (e.get("expense_date") or "") <= date_to.isoformat()]
    total_expenses = len(filtered)
    total_amount = sum(float(e.get("amount", 0)) for e in filtered)
    avg_amount = total_amount / total_expenses if total_expenses > 0 else 0
    cat_totals = {}
    for e in filtered:
        cat = e.get("category", "Others")
        cat_totals[cat] = cat_totals.get(cat, 0) + float(e.get("amount", 0))
    highest_category = max(cat_totals, key=cat_totals.get) if cat_totals else "N/A"
    return success_response(message="Statistics fetched successfully.", data={
        "total_expenses": total_expenses, "total_amount": str(round(total_amount, 2)),
        "average_amount": str(round(avg_amount, 2)), "highest_spending_category": highest_category,
    }), 200


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
        all_expenses = sb.select("expenses", columns="amount,category,payment_method,expense_date", filters={"user_id": user_id, "is_deleted": "false"})
    except Exception:
        all_expenses = []
    filtered = [e for e in (all_expenses or []) if date_from.isoformat() <= (e.get("expense_date") or "") <= date_to.isoformat()]
    cat_data = {}
    for e in filtered:
        cat = e.get("category", "Others")
        if cat not in cat_data: cat_data[cat] = {"value": 0, "count": 0}
        cat_data[cat]["value"] += float(e.get("amount", 0))
        cat_data[cat]["count"] += 1
    category_chart = [{"name": k, "value": v["value"], "count": v["count"]} for k, v in cat_data.items()]
    month_data = {}
    for e in filtered:
        d = e.get("expense_date", "")
        if d:
            month = d[:7]
            month_data[month] = month_data.get(month, 0) + float(e.get("amount", 0))
    monthly_chart = [{"month": k, "total": v} for k, v in sorted(month_data.items())]
    pm_data = {}
    for e in filtered:
        pm = e.get("payment_method", "Unknown")
        if pm not in pm_data: pm_data[pm] = {"value": 0, "count": 0}
        pm_data[pm]["value"] += float(e.get("amount", 0))
        pm_data[pm]["count"] += 1
    payment_chart = [{"name": k, "value": v["value"], "count": v["count"]} for k, v in pm_data.items()]
    day_data = {}
    for e in filtered:
        d = e.get("expense_date", "")
        if d:
            day_data[d] = {"total": day_data.get(d, {}).get("total", 0) + float(e.get("amount", 0)), "count": day_data.get(d, {}).get("count", 0) + 1}
    daily_chart = [{"date": k, "total": v["total"], "count": v["count"]} for k, v in sorted(day_data.items())]
    return success_response(message="Chart data fetched successfully.", data={
        "category_chart": category_chart, "monthly_chart": monthly_chart, "payment_chart": payment_chart, "daily_chart": daily_chart,
    }), 200


@expenses_bp.route("/dashboard-stats", methods=["GET"])
@jwt_required()
def get_dashboard_stats():
    user_id = _user_id_from_claims()
    if not user_id: return error_response("Unauthorized"), 401
    today = date.today()
    month_start = today.replace(day=1)
    week_start = today - timedelta(days=today.weekday())
    try:
        all_expenses = sb.select("expenses", columns="amount,expense_date", filters={"user_id": user_id, "is_deleted": "false"})
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
    return success_response(message="Dashboard stats fetched successfully.", data={
        "total_expenses": total_expenses, "total_amount": str(round(total_amount, 2)),
        "today_expenses": len(today_expenses), "today_amount": str(round(today_amount, 2)),
        "month_expenses": len(month_expenses), "month_amount": str(round(month_amount, 2)),
        "week_expenses": len(week_expenses), "week_amount": str(round(week_amount, 2)),
        "average_amount": str(round(avg_amount, 2)), "largest_amount": str(round(largest_amount, 2)),
    }), 200


@expenses_bp.route("/categories", methods=["GET"])
@jwt_required()
def get_categories():
    categories = [{"name": name, "icon": meta["icon"], "color": meta["color"]} for name, meta in CATEGORY_METADATA.items()]
    return success_response(message="Categories fetched successfully.", data={"categories": categories}), 200


@expenses_bp.route("/payment-methods", methods=["GET"])
@jwt_required()
def get_payment_methods():
    return success_response(message="Payment methods fetched successfully.", data={"payment_methods": PAYMENT_METHODS}), 200


@expenses_bp.route("/budgets", methods=["GET"])
@jwt_required()
def get_budgets():
    user_id = _user_id_from_claims()
    if not user_id: return error_response("Unauthorized"), 401
    try:
        budgets = sb.select("budgets", filters={"user_id": user_id, "is_deleted": "false"})
    except Exception:
        budgets = []
    today = date.today()
    month_start = today.replace(day=1)
    try:
        expenses = sb.select("expenses", columns="amount,category,expense_date", filters={"user_id": user_id, "is_deleted": "false"})
    except Exception:
        expenses = []
    budget_data = []
    for budget in (budgets or []):
        cat = budget.get("category")
        spent = sum(float(e.get("amount", 0)) for e in (expenses or []) if e.get("category") == cat and e.get("expense_date", "") >= month_start.isoformat())
        limit = float(budget.get("limit_amount", 0))
        remaining = limit - spent
        percentage_used = (spent / limit * 100) if limit > 0 else 0
        budget_data.append({"id": budget.get("id"), "category": cat, "limit_amount": str(budget.get("limit_amount")), "period": budget.get("period"), "spent": str(round(spent, 2)), "remaining": str(round(remaining, 2)), "percentage_used": round(percentage_used, 1), "is_overspending": remaining < 0})
    return success_response(message="Budgets fetched successfully.", data={"budgets": budget_data}), 200


@expenses_bp.route("/budgets", methods=["POST"])
@jwt_required()
def create_budget():
    user_id = _user_id_from_claims()
    if not user_id: return error_response("Unauthorized"), 401
    payload = request.get_json(silent=True) or {}
    category = (payload.get("category") or "").strip()
    limit_amount = payload.get("limit_amount")
    period = (payload.get("period") or "monthly").strip()
    if not category: return error_response("Category is required"), 400
    try:
        limit = float(limit_amount)
    except Exception:
        return error_response("Valid limit amount is required"), 400
    if limit <= 0: return error_response("Limit amount must be greater than 0"), 400
    try:
        result = sb.insert("budgets", {"user_id": user_id, "category": category, "limit_amount": limit, "period": period})
    except Exception as e:
        return error_response("Budget creation failed", errors={"error": str(e)}), 500
    return success_response(message="Budget created successfully.", data={"budget_id": result.get("id") if result else None}), 201


@expenses_bp.route("/favorite-merchants", methods=["GET"])
@jwt_required()
def get_favorite_merchants():
    user_id = _user_id_from_claims()
    if not user_id: return error_response("Unauthorized"), 401
    try:
        merchants = sb.select("favorite_merchants", filters={"user_id": user_id}, order="usage_count.desc", limit=10)
    except Exception:
        merchants = []
    data = [{"id": m.get("id"), "merchant_name": m.get("merchant_name"), "category": m.get("category"), "usage_count": m.get("usage_count")} for m in (merchants or [])]
    return success_response(message="Favorite merchants fetched successfully.", data={"merchants": data}), 200


@expenses_bp.route("/quick-add-amounts", methods=["GET"])
@jwt_required()
def get_quick_add_amounts():
    return success_response(message="Quick add amounts fetched successfully.", data={"amounts": QUICK_ADD_AMOUNTS, "moods": MOOD_OPTIONS}), 200