import os
from datetime import date, datetime, timedelta
from decimal import Decimal

from flask import Blueprint, request, current_app, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy import func, and_, or_

from database.db import db
from models.income import Income
from utils.api_response import success_response, error_response


incomes_bp = Blueprint("incomes", __name__)


def _user_id_from_claims():
    claims = get_jwt()
    user_id = claims.get("sub") or claims.get("user_id") or claims.get("identity")
    if user_id is not None:
        try:
            return int(user_id)
        except (ValueError, TypeError):
            return user_id
    return None


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


@incomes_bp.route("/", methods=["POST"])
@jwt_required()
def create_income():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    payload = request.get_json(silent=True) or {}

    title = (payload.get("title") or "").strip()
    source = (payload.get("source") or "").strip()
    amount_raw = payload.get("amount")
    income_date_raw = payload.get("income_date")
    payment_method = (payload.get("payment_method") or "").strip() or None
    description = (payload.get("description") or "").strip() or None
    is_recurring = payload.get("is_recurring", False) in (True, "true", "1", 1, "yes")
    recurring_frequency = (payload.get("recurring_frequency") or "").strip() or None
    currency = (payload.get("currency") or "INR").strip() or "INR"
    status = (payload.get("status") or "received").strip()

    errors = {}

    if not title or len(title) < 2:
        errors["title"] = "Title must be at least 2 characters."

    if not source:
        errors["source"] = "Income source is required."

    try:
        amount = float(amount_raw)
    except Exception:
        errors["amount"] = "Amount must be a valid number."
        amount = None

    if amount is None or amount <= 0:
        errors["amount"] = "Amount must be greater than 0."

    income_date = _parse_date(income_date_raw)
    if not income_date:
        errors["income_date"] = "Income date is invalid or missing."
    else:
        if income_date > date.today():
            errors["income_date"] = "Date cannot be in the future."

    if errors:
        return error_response("Validation failed", errors=errors), 400

    new_income = Income(
        user_id=user_id,
        title=title,
        source=source,
        amount=Decimal(str(amount)),
        income_date=income_date,
        payment_method=payment_method,
        description=description,
        is_recurring=is_recurring,
        recurring_frequency=recurring_frequency,
        currency=currency,
        status=status,
        is_deleted=False,
    )

    try:
        db.session.add(new_income)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return error_response("Income creation failed", errors={"error": str(e)}), 500

    return success_response(
        message="Income added successfully.",
        data={"income_id": new_income.id},
    ), 201


@incomes_bp.route("/", methods=["GET"])
@jwt_required()
def get_incomes():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    query = Income.query.filter_by(user_id=user_id, is_deleted=False)

    # Filters
    source = request.args.get("source", "").strip()
    if source:
        query = query.filter_by(source=source)

    status = request.args.get("status", "").strip()
    if status:
        query = query.filter_by(status=status)

    # Search
    search = request.args.get("search", "").strip()
    if search:
        query = query.filter(
            or_(
                Income.title.ilike(f"%{search}%"),
                Income.description.ilike(f"%{search}%"),
            )
        )

    # Date range
    date_from_str = request.args.get("date_from", "").strip()
    date_to_str = request.args.get("date_to", "").strip()
    if date_from_str:
        date_from = _parse_date(date_from_str)
        if date_from:
            query = query.filter(Income.income_date >= date_from)
    if date_to_str:
        date_to = _parse_date(date_to_str)
        if date_to:
            query = query.filter(Income.income_date <= date_to)

    # Sorting
    sort_by = request.args.get("sort", "created_at").strip()
    order = request.args.get("order", "desc").strip().lower()

    if sort_by == "created_at":
        sort_col = Income.created_at
    elif sort_by == "amount":
        sort_col = Income.amount
    elif sort_by == "income_date":
        sort_col = Income.income_date
    elif sort_by == "title":
        sort_col = Income.title
    else:
        sort_col = Income.created_at

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

    incomes_data = [inc.to_dict() for inc in paginated.items]

    return success_response(
        message="Incomes fetched successfully.",
        data={
            "incomes": incomes_data,
            "pagination": {
                "total": paginated.total,
                "page": page,
                "per_page": per_page,
                "pages": paginated.pages,
            },
        },
    ), 200


@incomes_bp.route("/<int:income_id>", methods=["GET"])
@jwt_required()
def get_income(income_id):
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    inc = Income.query.filter_by(id=income_id, user_id=user_id, is_deleted=False).first()
    if not inc:
        return error_response("Income not found"), 404

    return success_response(
        message="Income fetched successfully.",
        data=inc.to_dict(),
    ), 200


@incomes_bp.route("/<int:income_id>", methods=["PUT"])
@jwt_required()
def update_income(income_id):
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    inc = Income.query.filter_by(id=income_id, user_id=user_id, is_deleted=False).first()
    if not inc:
        return error_response("Income not found"), 404

    payload = request.get_json(silent=True) or {}

    inc.title = (payload.get("title", inc.title) or "").strip()
    inc.source = payload.get("source", inc.source)
    
    amount_raw = payload.get("amount", inc.amount)
    try:
        inc.amount = Decimal(str(float(amount_raw)))
    except Exception:
        pass

    date_raw = payload.get("income_date", inc.income_date.isoformat())
    parsed_date = _parse_date(date_raw)
    if parsed_date:
        inc.income_date = parsed_date

    inc.payment_method = payload.get("payment_method", inc.payment_method)
    inc.description = payload.get("description", inc.description)
    inc.is_recurring = payload.get("is_recurring", inc.is_recurring) in (True, "true", "1", 1, "yes")
    inc.recurring_frequency = payload.get("recurring_frequency", inc.recurring_frequency)
    inc.currency = payload.get("currency", inc.currency)
    inc.status = payload.get("status", inc.status)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return error_response("Income update failed", errors={"error": str(e)}), 500

    return success_response(message="Income updated successfully.", data={"income_id": inc.id}), 200


@incomes_bp.route("/<int:income_id>", methods=["DELETE"])
@jwt_required()
def delete_income(income_id):
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    inc = Income.query.filter_by(id=income_id, user_id=user_id, is_deleted=False).first()
    if not inc:
        return error_response("Income not found"), 404

    inc.is_deleted = True
    inc.deleted_at = datetime.utcnow()

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return error_response("Income delete failed", errors={"error": str(e)}), 500

    return success_response(message="Income deleted successfully.", data={"income_id": inc.id}), 200


@incomes_bp.route("/dashboard-stats", methods=["GET"])
@jwt_required()
def get_dashboard_stats():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    today = date.today()

    # Total income (all time)
    total_incomes = Income.query.filter_by(user_id=user_id, is_deleted=False).count()
    total_amount = db.session.query(func.sum(Income.amount)).filter(
        Income.user_id == user_id,
        Income.is_deleted == False,
    ).scalar() or 0

    # This month income
    month_start = today.replace(day=1)
    month_amount = db.session.query(func.sum(Income.amount)).filter(
        Income.user_id == user_id,
        Income.is_deleted == False,
        Income.income_date >= month_start,
        Income.income_date <= today,
    ).scalar() or 0
    month_incomes = Income.query.filter(
        Income.user_id == user_id,
        Income.is_deleted == False,
        Income.income_date >= month_start,
        Income.income_date <= today,
    ).count()

    # By source breakdown
    source_stats = db.session.query(
        Income.source,
        func.sum(Income.amount).label("total"),
        func.count(Income.id).label("count")
    ).filter(
        Income.user_id == user_id,
        Income.is_deleted == False,
    ).group_by(Income.source).order_by(func.sum(Income.amount).desc()).all()

    source_breakdown = [
        {"source": s[0], "total": str(s[1]), "count": s[2]}
        for s in source_stats
    ]

    return success_response(
        message="Income dashboard stats fetched successfully.",
        data={
            "total_incomes": total_incomes,
            "total_amount": str(total_amount),
            "month_amount": str(month_amount),
            "month_incomes": month_incomes,
            "source_breakdown": source_breakdown,
        },
    ), 200


@incomes_bp.route("/comparison", methods=["GET"])
@jwt_required()
def get_comparison():
    """Get income vs expenses comparison for dashboard."""
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    today = date.today()
    month_start = today.replace(day=1)

    # This month income
    month_income = db.session.query(func.sum(Income.amount)).filter(
        Income.user_id == user_id,
        Income.is_deleted == False,
        Income.income_date >= month_start,
        Income.income_date <= today,
    ).scalar() or 0

    # This month expenses
    from models.expense import Expense
    month_expense = db.session.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user_id,
        Expense.is_deleted == False,
        Expense.expense_date >= month_start,
        Expense.expense_date <= today,
    ).scalar() or 0

    # Budget (estimated as 70% of income)
    month_income_f = float(month_income)
    month_expense_f = float(month_expense)
    savings = month_income_f - month_expense_f
    savings_rate = (savings / month_income_f * 100) if month_income_f > 0 else 0
    budget_utilization = (month_expense_f / month_income_f * 100) if month_income_f > 0 else 0

    return success_response(
        message="Comparison data fetched successfully.",
        data={
            "month_income": str(month_income),
            "month_expense": str(month_expense),
            "savings": str(round(savings, 2)),
            "savings_rate": round(savings_rate, 1),
            "budget_utilization": round(budget_utilization, 1),
        },
    ), 200


@incomes_bp.route("/sources", methods=["GET"])
@jwt_required()
def get_sources():
    sources = ["Salary", "Freelance", "Business", "Investment", "Rental", "Dividend", "Interest", "Gift", "Refund", "Bonus", "Commission", "Other"]
    return success_response(
        message="Income sources fetched successfully.",
        data={"sources": sources},
    ), 200