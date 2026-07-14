from datetime import date, datetime
from decimal import Decimal

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy import func

from database.db import db
from models.budget import Budget
from models.expense import Expense
from utils.api_response import success_response, error_response


budgets_bp = Blueprint("budgets", __name__)


def _user_id_from_claims():
    claims = get_jwt()
    user_id = claims.get("sub") or claims.get("user_id") or claims.get("identity")
    if user_id is not None:
        try:
            return int(user_id)
        except (ValueError, TypeError):
            return user_id
    return None


@budgets_bp.route("/", methods=["POST"])
@jwt_required()
def create_budget():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    payload = request.get_json(silent=True) or {}

    category = (payload.get("category") or "").strip()
    amount_raw = payload.get("amount")
    period = (payload.get("period") or "monthly").strip()
    month = payload.get("month")
    year = payload.get("year")
    description = (payload.get("description") or "").strip() or None
    color = (payload.get("color") or "").strip() or None
    icon = (payload.get("icon") or "").strip() or None

    errors = {}

    if not category:
        errors["category"] = "Category is required."

    try:
        budget_amount = float(amount_raw)
    except Exception:
        errors["amount"] = "Amount must be a valid number."
        budget_amount = None

    if budget_amount is None or budget_amount <= 0:
        errors["amount"] = "Amount must be greater than 0."

    if period not in ("monthly", "yearly", "weekly"):
        errors["period"] = "Period must be monthly, yearly, or weekly."

    today = date.today()
    if month is None:
        month = today.month
    if year is None:
        year = today.year

    # Check if budget already exists for this category+period+month+year
    existing = Budget.query.filter_by(
        user_id=user_id, category=category, period=period,
        month=month, year=year, is_deleted=False
    ).first()
    if existing:
        errors["category"] = f"Budget already exists for {category} in this period."

    if errors:
        return error_response("Validation failed", errors=errors), 400

    new_budget = Budget(
        user_id=user_id,
        category=category,
        amount=Decimal(str(budget_amount)),
        period=period,
        month=month,
        year=year,
        description=description,
        color=color,
        icon=icon,
    )

    try:
        db.session.add(new_budget)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return error_response("Budget creation failed", errors={"error": str(e)}), 500

    return success_response(
        message="Budget created successfully.",
        data={"budget_id": new_budget.id},
    ), 201


@budgets_bp.route("/", methods=["GET"])
@jwt_required()
def get_budgets():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    today = date.today()
    month = request.args.get("month", today.month, type=int)
    year = request.args.get("year", today.year, type=int)

    budgets = Budget.query.filter_by(
        user_id=user_id, is_deleted=False,
        month=month, year=year
    ).order_by(Budget.category).all()

    # Get actual expenses for each budget category in this month
    month_start = date(year, month, 1)
    if month == 12:
        month_end = date(year + 1, 1, 1)
    else:
        month_end = date(year, month + 1, 1)

    budget_data = []
    for b in budgets:
        # Sum expenses for this category in the month
        expense_total = db.session.query(func.sum(Expense.amount)).filter(
            Expense.user_id == user_id,
            Expense.is_deleted == False,
            Expense.category == b.category,
            Expense.expense_date >= month_start,
            Expense.expense_date < month_end,
        ).scalar() or 0

        expense_total_f = float(expense_total)
        budget_amount_f = float(b.amount)
        utilization = (expense_total_f / budget_amount_f * 100) if budget_amount_f > 0 else 0
        remaining = budget_amount_f - expense_total_f

        budget_data.append({
            "id": b.id,
            "category": b.category,
            "budget_amount": str(b.amount),
            "spent": str(expense_total),
            "remaining": str(round(remaining, 2)),
            "utilization": round(utilization, 1),
            "period": b.period,
            "month": b.month,
            "year": b.year,
            "description": b.description,
            "color": b.color or _get_category_color(b.category),
            "icon": b.icon or _get_category_icon(b.category),
        })

    # Calculate totals (only from actual budgets, not auto-discovered)
    total_budget = sum(float(b["budget_amount"]) for b in budget_data)
    total_spent = sum(float(b["spent"]) for b in budget_data)
    total_remaining = total_budget - total_spent
    overall_utilization = (total_spent / total_budget * 100) if total_budget > 0 else 0

    return success_response(
        message="Budgets fetched successfully.",
        data={
            "budgets": budget_data,
            "summary": {
                "total_budget": str(round(total_budget, 2)),
                "total_spent": str(round(total_spent, 2)),
                "total_remaining": str(round(total_remaining, 2)),
                "overall_utilization": round(overall_utilization, 1),
                "month": month,
                "year": year,
            }
        },
    ), 200


@budgets_bp.route("/<int:budget_id>", methods=["PUT"])
@jwt_required()
def update_budget(budget_id):
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    budget = Budget.query.filter_by(id=budget_id, user_id=user_id, is_deleted=False).first()
    if not budget:
        return error_response("Budget not found"), 404

    payload = request.get_json(silent=True) or {}

    if "amount" in payload:
        try:
            budget.amount = Decimal(str(float(payload["amount"])))
        except Exception:
            return error_response("Invalid amount"), 400

    if "description" in payload:
        budget.description = payload.get("description")
    if "color" in payload:
        budget.color = payload.get("color")
    if "icon" in payload:
        budget.icon = payload.get("icon")

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return error_response("Budget update failed", errors={"error": str(e)}), 500

    return success_response(message="Budget updated successfully.", data={"budget_id": budget.id}), 200


@budgets_bp.route("/<int:budget_id>", methods=["DELETE"])
@jwt_required()
def delete_budget(budget_id):
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    budget = Budget.query.filter_by(id=budget_id, user_id=user_id, is_deleted=False).first()
    if not budget:
        return error_response("Budget not found"), 404

    budget.is_deleted = True
    budget.deleted_at = datetime.utcnow()

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return error_response("Budget delete failed", errors={"error": str(e)}), 500

    return success_response(message="Budget deleted successfully.", data={"budget_id": budget.id}), 200


def _get_category_color(category):
    colors = {
        "Food": "#ef4444", "Travel": "#f59e0b", "Shopping": "#8b5cf6",
        "Entertainment": "#ec4899", "Healthcare": "#3b82f6", "Bills": "#14b8a6",
        "Fuel": "#f97316", "Education": "#6366f1", "Rent": "#06b6d4",
        "Utilities": "#84cc16", "Subscription": "#a855f7", "Others": "#64748b",
    }
    return colors.get(category, "#64748b")


def _get_category_icon(category):
    icons = {
        "Food": "restaurant", "Travel": "flight", "Shopping": "shopping_cart",
        "Entertainment": "movie", "Healthcare": "local_hospital", "Bills": "receipt_long",
        "Fuel": "local_gas_station", "Education": "school", "Rent": "home",
        "Utilities": "bolt", "Subscription": "subscriptions", "Others": "more_horiz",
    }
    return icons.get(category, "payments")