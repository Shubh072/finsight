import os
import hashlib
from datetime import date, datetime, timedelta
from decimal import Decimal

from flask import Blueprint, request, current_app, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Query


from database.db import db
from models.expense import Expense, ExpenseCategory, Account
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
    ("cafe", "Food"),
    ("coffee", "Food"),
    ("uber", "Travel"),
    ("ola", "Travel"),
    ("taxi", "Travel"),
    ("bus", "Travel"),
    ("flight", "Travel"),
    ("hotel", "Travel"),
    ("amazon", "Shopping"),
    ("flipkart", "Shopping"),
    ("netflix", "Entertainment"),
    ("spotify", "Entertainment"),
    ("gym", "Health"),
    ("medical", "Health"),
    ("hospital", "Health"),
    ("fuel", "Transportation"),
    ("petrol", "Transportation"),
    ("electricity", "Bills"),
    ("water", "Bills"),
    ("internet", "Bills"),
    ("phone", "Bills"),
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
        if isinstance(value, date):
            return value
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
    return "Other"


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
    currency = (payload.get("currency") or "USD").strip() or "USD"
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
        safe_name = f"expense_{user_id}_{int(datetime.now().timestamp())}_{hashlib.sha256(receipt_file.filename.encode('utf-8')).hexdigest()[:16]}{ext}"
        file_path = os.path.join(upload_dir, safe_name)
        receipt_file.save(file_path)

        receipt_filename = safe_name
        # Since static serving for uploads isn't implemented in this milestone,
        # keep a relative URL-like path for frontend preview and future endpoints.
        receipt_url = f"/uploads/receipts/{user_id}/{safe_name}"

    fingerprint = _fingerprint_for_duplicate(title, amount, str(expense_date), merchant_name, currency)

    new_expense = Expense(
        user_id=user_id,
        title=title,
        category=category_final,
        amount=Decimal(str(amount)),
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


@expenses_bp.route("/", methods=["GET"])
@jwt_required()
def get_expenses():
    """
    Get all expenses with filtering, searching, sorting, and pagination.
    
    Query params:
    - search: search in title, merchant, description
    - category: filter by category
    - payment_method: filter by payment method
    - status: filter by status
    - date_from: YYYY-MM-DD
    - date_to: YYYY-MM-DD
    - amount_min: minimum amount
    - amount_max: maximum amount
    - merchant: filter by merchant
    - tags: comma-separated tags
    - sort: field to sort by (created_at, amount, expense_date, title)
    - order: asc or desc
    - page: page number (default 1)
    - per_page: entries per page (default 20)
    """
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    # Base query
    query = Expense.query.filter_by(user_id=user_id, is_deleted=False)

    # Search
    search_term = request.args.get("search", "").strip()
    if search_term:
        query = query.filter(
            or_(
                Expense.title.ilike(f"%{search_term}%"),
                Expense.merchant_name.ilike(f"%{search_term}%"),
                Expense.description.ilike(f"%{search_term}%"),
            )
        )

    # Filters
    category = request.args.get("category", "").strip()
    if category:
        query = query.filter_by(category=category)

    payment_method = request.args.get("payment_method", "").strip()
    if payment_method:
        query = query.filter_by(payment_method=payment_method)

    status = request.args.get("status", "").strip()
    if status:
        query = query.filter_by(status=status)

    merchant = request.args.get("merchant", "").strip()
    if merchant:
        query = query.filter(Expense.merchant_name.ilike(f"%{merchant}%"))

    # Date range
    date_from_str = request.args.get("date_from", "").strip()
    date_to_str = request.args.get("date_to", "").strip()
    if date_from_str:
        date_from = _parse_date(date_from_str)
        if date_from:
            query = query.filter(Expense.expense_date >= date_from)
    if date_to_str:
        date_to = _parse_date(date_to_str)
        if date_to:
            query = query.filter(Expense.expense_date <= date_to)

    # Amount range
    try:
        amount_min = float(request.args.get("amount_min", 0))
        if amount_min > 0:
            query = query.filter(Expense.amount >= amount_min)
    except:
        pass

    try:
        amount_max = float(request.args.get("amount_max", float('inf')))
        if amount_max < float('inf'):
            query = query.filter(Expense.amount <= amount_max)
    except:
        pass

    # Sorting
    sort_by = request.args.get("sort", "created_at").strip()
    order = request.args.get("order", "desc").strip().lower()

    if sort_by == "created_at":
        sort_col = Expense.created_at
    elif sort_by == "amount":
        sort_col = Expense.amount
    elif sort_by == "expense_date":
        sort_col = Expense.expense_date
    elif sort_by == "title":
        sort_col = Expense.title
    else:
        sort_col = Expense.created_at

    if order == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    # Pagination
    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = max(1, min(100, int(request.args.get("per_page", 20))))
    except:
        page = 1
        per_page = 20

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    expenses_data = [
        {
            "id": exp.id,
            "title": exp.title,
            "category": exp.category,
            "amount": str(exp.amount),
            "expense_date": exp.expense_date.isoformat(),
            "payment_method": exp.payment_method,
            "merchant_name": exp.merchant_name,
            "status": exp.status,
            "receipt_url": exp.receipt_url,
            "created_at": exp.created_at.isoformat() if exp.created_at else None,
        }
        for exp in paginated.items
    ]

    return success_response(
        message="Expenses fetched successfully.",
        data={
            "expenses": expenses_data,
            "pagination": {
                "total": paginated.total,
                "page": page,
                "per_page": per_page,
                "pages": paginated.pages,
            },
        },
    ), 200


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
            "status": exp.status,
            "created_at": exp.created_at.isoformat() if exp.created_at else None,
            "updated_at": exp.updated_at.isoformat() if exp.updated_at else None,
        },
    ), 200


@expenses_bp.route("/<int:expense_id>", methods=["PUT"])
@jwt_required()
def update_expense(expense_id: int):
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
    exp.amount = Decimal(str(amount_f))
    exp.expense_date = expense_date
    exp.payment_method = payment_method
    exp.description = description
    exp.merchant_name = payload.get("merchant_name", exp.merchant_name)
    exp.location = payload.get("location", exp.location)
    exp.status = payload.get("status", exp.status)

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
    exp.deleted_at = datetime.utcnow()

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return error_response("Expense delete failed", errors={"error": str(e)}), 500

    return success_response(message="Expense deleted successfully.", data={"expense_id": exp.id}), 200


@expenses_bp.route("/<int:expense_id>/duplicate", methods=["POST"])
@jwt_required()
def duplicate_expense(expense_id: int):
    """Duplicate an existing expense with optional modifications."""
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    exp = Expense.query.filter_by(id=expense_id, user_id=user_id, is_deleted=False).first()
    if not exp:
        return error_response("Expense not found"), 404

    payload = request.get_json(silent=True) or {}

    # Create a copy with any modifications
    new_expense = Expense(
        user_id=user_id,
        title=payload.get("title", exp.title),
        category=payload.get("category", exp.category),
        amount=Decimal(str(payload.get("amount", exp.amount))),
        expense_date=_parse_date(payload.get("expense_date", exp.expense_date.isoformat())),
        payment_method=payload.get("payment_method", exp.payment_method),
        account_id=payload.get("account_id", exp.account_id),
        merchant_name=payload.get("merchant_name", exp.merchant_name),
        location=payload.get("location", exp.location),
        description=payload.get("description", exp.description),
        tags_json=payload.get("tags_json", exp.tags_json),
        recurring=payload.get("recurring", exp.recurring),
        currency=payload.get("currency", exp.currency),
        priority=payload.get("priority", exp.priority),
        mood=payload.get("mood", exp.mood),
        status="active",
        is_deleted=False,
    )

    try:
        db.session.add(new_expense)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return error_response("Expense duplication failed", errors={"error": str(e)}), 500

    return success_response(
        message="Expense duplicated successfully.",
        data={"expense_id": new_expense.id},
    ), 201


@expenses_bp.route("/statistics", methods=["GET"])
@jwt_required()
def get_statistics():
    """Get expense statistics."""
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    # Get date range
    date_from_str = request.args.get("date_from", "").strip()
    date_to_str = request.args.get("date_to", "").strip()

    today = date.today()
    if not date_from_str:
        date_from = today - timedelta(days=30)
    else:
        date_from = _parse_date(date_from_str) or today - timedelta(days=30)

    if not date_to_str:
        date_to = today
    else:
        date_to = _parse_date(date_to_str) or today

    # Base query
    query = Expense.query.filter(
        Expense.user_id == user_id,
        Expense.is_deleted == False,
        Expense.expense_date >= date_from,
        Expense.expense_date <= date_to,
    )

    # Calculate statistics
    total_expenses = query.count()
    total_amount = db.session.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user_id,
        Expense.is_deleted == False,
        Expense.expense_date >= date_from,
        Expense.expense_date <= date_to,
    ).scalar() or 0

    avg_amount = float(total_amount) / total_expenses if total_expenses > 0 else 0

    # Highest spending category
    category_stats = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label("total")
    ).filter(
        Expense.user_id == user_id,
        Expense.is_deleted == False,
        Expense.expense_date >= date_from,
        Expense.expense_date <= date_to,
    ).group_by(Expense.category).order_by(func.sum(Expense.amount).desc()).first()

    highest_category = category_stats[0] if category_stats else "N/A"
    highest_category_amount = str(category_stats[1]) if category_stats else "0"

    # Most used payment method
    payment_stats = db.session.query(
        Expense.payment_method,
        func.count(Expense.id).label("count")
    ).filter(
        Expense.user_id == user_id,
        Expense.is_deleted == False,
        Expense.expense_date >= date_from,
        Expense.expense_date <= date_to,
    ).group_by(Expense.payment_method).order_by(func.count(Expense.id).desc()).first()

    most_used_payment = payment_stats[0] if payment_stats else "N/A"

    # Top merchant
    merchant_stats = db.session.query(
        Expense.merchant_name,
        func.sum(Expense.amount).label("total")
    ).filter(
        Expense.user_id == user_id,
        Expense.is_deleted == False,
        Expense.expense_date >= date_from,
        Expense.expense_date <= date_to,
        Expense.merchant_name != None,
    ).group_by(Expense.merchant_name).order_by(func.sum(Expense.amount).desc()).first()

    top_merchant = merchant_stats[0] if merchant_stats else "N/A"

    return success_response(
        message="Statistics fetched successfully.",
        data={
            "total_expenses": total_expenses,
            "total_amount": str(total_amount),
            "average_amount": str(round(avg_amount, 2)),
            "highest_spending_category": highest_category,
            "highest_category_amount": highest_category_amount,
            "most_used_payment_method": most_used_payment,
            "top_merchant": top_merchant,
            "date_range": {
                "from": date_from.isoformat(),
                "to": date_to.isoformat(),
            },
        },
    ), 200


@expenses_bp.route("/chart-data", methods=["GET"])
@jwt_required()
def get_chart_data():
    """Get data for charts."""
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    # Get date range
    date_from_str = request.args.get("date_from", "").strip()
    date_to_str = request.args.get("date_to", "").strip()

    today = date.today()
    if not date_from_str:
        date_from = today - timedelta(days=30)
    else:
        date_from = _parse_date(date_from_str) or today - timedelta(days=30)

    if not date_to_str:
        date_to = today
    else:
        date_to = _parse_date(date_to_str) or today

    # Expense by category (Pie Chart)
    category_data = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label("total"),
        func.count(Expense.id).label("count")
    ).filter(
        Expense.user_id == user_id,
        Expense.is_deleted == False,
        Expense.expense_date >= date_from,
        Expense.expense_date <= date_to,
    ).group_by(Expense.category).order_by(func.sum(Expense.amount).desc()).all()

    category_chart = [
        {
            "name": cat[0],
            "value": float(cat[1]),
            "count": cat[2],
        }
        for cat in category_data
    ]

    # Monthly expense trend (Bar Chart)
    monthly_data = db.session.query(
        func.date_format(Expense.expense_date, "%Y-%m").label("month"),
        func.sum(Expense.amount).label("total")
    ).filter(
        Expense.user_id == user_id,
        Expense.is_deleted == False,
        Expense.expense_date >= date_from,
        Expense.expense_date <= date_to,
    ).group_by(func.date_format(Expense.expense_date, "%Y-%m")).order_by(
        func.date_format(Expense.expense_date, "%Y-%m")
    ).all()

    monthly_chart = [
        {
            "month": month[0],
            "total": float(month[1]),
        }
        for month in monthly_data
    ]

    # Payment method breakdown (Donut Chart)
    payment_data = db.session.query(
        Expense.payment_method,
        func.sum(Expense.amount).label("total"),
        func.count(Expense.id).label("count")
    ).filter(
        Expense.user_id == user_id,
        Expense.is_deleted == False,
        Expense.expense_date >= date_from,
        Expense.expense_date <= date_to,
    ).group_by(Expense.payment_method).order_by(func.sum(Expense.amount).desc()).all()

    payment_chart = [
        {
            "name": pm[0],
            "value": float(pm[1]),
            "count": pm[2],
        }
        for pm in payment_data
    ]

    # Daily expense trend (Line Chart)
    daily_data = db.session.query(
        Expense.expense_date,
        func.sum(Expense.amount).label("total"),
        func.count(Expense.id).label("count")
    ).filter(
        Expense.user_id == user_id,
        Expense.is_deleted == False,
        Expense.expense_date >= date_from,
        Expense.expense_date <= date_to,
    ).group_by(Expense.expense_date).order_by(Expense.expense_date).all()

    daily_chart = [
        {
            "date": d[0].isoformat(),
            "total": float(d[1]),
            "count": d[2],
        }
        for d in daily_data
    ]

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
    """Get dashboard statistics cards."""
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    today = date.today()

    # Total expenses (all time)
    total_expenses = Expense.query.filter_by(user_id=user_id, is_deleted=False).count()
    total_amount = db.session.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user_id,
        Expense.is_deleted == False,
    ).scalar() or 0

    # Today's expenses
    today_expenses = Expense.query.filter_by(
        user_id=user_id,
        is_deleted=False,
        expense_date=today,
    ).count()
    today_amount = db.session.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user_id,
        Expense.is_deleted == False,
        Expense.expense_date == today,
    ).scalar() or 0

    # This month expenses
    month_start = today.replace(day=1)
    month_expenses = Expense.query.filter(
        Expense.user_id == user_id,
        Expense.is_deleted == False,
        Expense.expense_date >= month_start,
        Expense.expense_date <= today,
    ).count()
    month_amount = db.session.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user_id,
        Expense.is_deleted == False,
        Expense.expense_date >= month_start,
        Expense.expense_date <= today,
    ).scalar() or 0

    # This week expenses
    week_start = today - timedelta(days=today.weekday())
    week_expenses = Expense.query.filter(
        Expense.user_id == user_id,
        Expense.is_deleted == False,
        Expense.expense_date >= week_start,
        Expense.expense_date <= today,
    ).count()
    week_amount = db.session.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user_id,
        Expense.is_deleted == False,
        Expense.expense_date >= week_start,
        Expense.expense_date <= today,
    ).scalar() or 0

    # Average expense
    avg_amount = float(total_amount) / total_expenses if total_expenses > 0 else 0

    # Largest expense
    largest = Expense.query.filter_by(user_id=user_id, is_deleted=False).order_by(
        Expense.amount.desc()
    ).first()
    largest_amount = str(largest.amount) if largest else "0"

    return success_response(
        message="Dashboard stats fetched successfully.",
        data={
            "total_expenses": total_expenses,
            "total_amount": str(total_amount),
            "today_expenses": today_expenses,
            "today_amount": str(today_amount),
            "month_expenses": month_expenses,
            "month_amount": str(month_amount),
            "week_expenses": week_expenses,
            "week_amount": str(week_amount),
            "average_amount": str(round(avg_amount, 2)),
            "largest_amount": largest_amount,
        },
    ), 200


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
        return success_response(
            message="Duplicate check skipped (missing fields).",
            data={"possible_duplicate": False, "duplicates": []},
        ), 200

    amount_f = None
    try:
        amount_f = float(amount)
    except Exception:
        amount_f = None

    if amount_f is None:
        return success_response(
            message="Duplicate check skipped (invalid amount).",
            data={"possible_duplicate": False, "duplicates": []},
        ), 200

    normalized = _normalize_title(title)

    possible = (
        Expense.query.filter(
            Expense.user_id == user_id,
            Expense.is_deleted == False,
            Expense.normalized_title == normalized,
            Expense.amount == Decimal(str(amount_f)),
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


@expenses_bp.route("/categories", methods=["GET"])
@jwt_required()
def get_categories():
    """Get all categories for the user or predefined categories."""
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    # Return predefined categories + user custom ones if any
    categories = list(set([cat[1] for cat in CATEGORY_AUTOSUGGESTION_RULES]))
    categories.sort()

    return success_response(
        message="Categories fetched successfully.",
        data={"categories": categories},
    ), 200


@expenses_bp.route("/payment-methods", methods=["GET"])
@jwt_required()
def get_payment_methods():
    """Get all payment methods."""
    methods = [
        "Credit Card",
        "Debit Card",
        "Cash",
        "Bank Transfer",
        "Digital Wallet",
        "Cheque",
        "Other",
    ]

    return success_response(
        message="Payment methods fetched successfully.",
        data={"payment_methods": methods},
    ), 200


@expenses_bp.route("/accounts", methods=["GET"])
@jwt_required()
def get_accounts():
    """Get all accounts for the user."""
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    accounts = Account.query.filter_by(user_id=user_id, is_deleted=False).all()

    accounts_data = [
        {
            "id": acc.id,
            "name": acc.name,
            "account_type": acc.account_type,
        }
        for acc in accounts
    ]

    return success_response(
        message="Accounts fetched successfully.",
        data={"accounts": accounts_data},
    ), 200
