import os
from datetime import date, datetime, timedelta
from decimal import Decimal

from flask import Blueprint, request, current_app, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy import func, and_, or_

from database.db import db
from models.investment import Investment
from utils.api_response import success_response, error_response


investments_bp = Blueprint("investments", __name__)


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


@investments_bp.route("/", methods=["POST"])
@jwt_required()
def create_investment():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    payload = request.get_json(silent=True) or {}

    name = (payload.get("name") or "").strip()
    investment_type = (payload.get("investment_type") or "").strip()
    amount_raw = payload.get("amount")
    investment_date_raw = payload.get("investment_date")
    units_raw = payload.get("units")
    purchase_price_raw = payload.get("purchase_price")
    current_price_raw = payload.get("current_price")
    ticker = (payload.get("ticker") or "").strip() or None
    broker = (payload.get("broker") or "").strip() or None
    notes = (payload.get("notes") or "").strip() or None
    currency = (payload.get("currency") or "INR").strip() or "INR"
    risk_level = (payload.get("risk_level") or "medium").strip()
    if risk_level not in ("low", "medium", "high"):
        risk_level = "medium"

    errors = {}

    if not name or len(name) < 2:
        errors["name"] = "Name must be at least 2 characters."

    if not investment_type:
        errors["investment_type"] = "Investment type is required."

    try:
        amount = float(amount_raw)
    except Exception:
        errors["amount"] = "Amount must be a valid number."
        amount = None

    if amount is None or amount <= 0:
        errors["amount"] = "Amount must be greater than 0."

    investment_date = _parse_date(investment_date_raw)
    if not investment_date:
        errors["investment_date"] = "Investment date is invalid or missing."
    else:
        if investment_date > date.today():
            errors["investment_date"] = "Date cannot be in the future."

    units = None
    if units_raw not in (None, "", "null"):
        try:
            units = float(units_raw)
            if units <= 0:
                errors["units"] = "Units must be greater than 0."
        except Exception:
            errors["units"] = "Units must be a valid number."

    purchase_price = None
    if purchase_price_raw not in (None, "", "null"):
        try:
            purchase_price = float(purchase_price_raw)
        except Exception:
            errors["purchase_price"] = "Purchase price must be a valid number."

    current_price = None
    if current_price_raw not in (None, "", "null"):
        try:
            current_price = float(current_price_raw)
        except Exception:
            errors["current_price"] = "Current price must be a valid number."

    if errors:
        return error_response("Validation failed", errors=errors), 400

    new_investment = Investment(
        user_id=user_id,
        name=name,
        investment_type=investment_type,
        amount=Decimal(str(amount)),
        units=Decimal(str(units)) if units else None,
        purchase_price=Decimal(str(purchase_price)) if purchase_price else None,
        current_price=Decimal(str(current_price)) if current_price else None,
        investment_date=investment_date,
        ticker=ticker,
        broker=broker,
        notes=notes,
        currency=currency,
        risk_level=risk_level,
        status="active",
        is_deleted=False,
    )

    try:
        db.session.add(new_investment)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return error_response("Investment creation failed", errors={"error": str(e)}), 500

    return success_response(
        message="Investment added successfully.",
        data={"investment_id": new_investment.id},
    ), 201


@investments_bp.route("/", methods=["GET"])
@jwt_required()
def get_investments():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    query = Investment.query.filter_by(user_id=user_id, is_deleted=False)

    # Filters
    investment_type = request.args.get("investment_type", "").strip()
    if investment_type:
        query = query.filter_by(investment_type=investment_type)

    status = request.args.get("status", "").strip()
    if status:
        query = query.filter_by(status=status)

    # Search
    search = request.args.get("search", "").strip()
    if search:
        query = query.filter(
            or_(
                Investment.name.ilike(f"%{search}%"),
                Investment.ticker.ilike(f"%{search}%"),
                Investment.broker.ilike(f"%{search}%"),
            )
        )

    # Sorting
    sort_by = request.args.get("sort", "created_at").strip()
    order = request.args.get("order", "desc").strip().lower()

    if sort_by == "created_at":
        sort_col = Investment.created_at
    elif sort_by == "amount":
        sort_col = Investment.amount
    elif sort_by == "investment_date":
        sort_col = Investment.investment_date
    elif sort_by == "name":
        sort_col = Investment.name
    else:
        sort_col = Investment.created_at

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

    investments_data = [inv.to_dict() for inv in paginated.items]

    return success_response(
        message="Investments fetched successfully.",
        data={
            "investments": investments_data,
            "pagination": {
                "total": paginated.total,
                "page": page,
                "per_page": per_page,
                "pages": paginated.pages,
            },
        },
    ), 200


@investments_bp.route("/<int:investment_id>", methods=["GET"])
@jwt_required()
def get_investment(investment_id):
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    inv = Investment.query.filter_by(id=investment_id, user_id=user_id, is_deleted=False).first()
    if not inv:
        return error_response("Investment not found"), 404

    return success_response(
        message="Investment fetched successfully.",
        data=inv.to_dict(),
    ), 200


@investments_bp.route("/<int:investment_id>", methods=["PUT"])
@jwt_required()
def update_investment(investment_id):
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    inv = Investment.query.filter_by(id=investment_id, user_id=user_id, is_deleted=False).first()
    if not inv:
        return error_response("Investment not found"), 404

    payload = request.get_json(silent=True) or {}

    inv.name = (payload.get("name", inv.name) or "").strip()
    inv.investment_type = payload.get("investment_type", inv.investment_type)
    
    amount_raw = payload.get("amount", inv.amount)
    try:
        inv.amount = Decimal(str(float(amount_raw)))
    except Exception:
        pass

    date_raw = payload.get("investment_date", inv.investment_date.isoformat())
    parsed_date = _parse_date(date_raw)
    if parsed_date:
        inv.investment_date = parsed_date

    inv.ticker = payload.get("ticker", inv.ticker)
    inv.broker = payload.get("broker", inv.broker)
    inv.notes = payload.get("notes", inv.notes)
    inv.currency = payload.get("currency", inv.currency)
    inv.status = payload.get("status", inv.status)

    units_raw = payload.get("units", inv.units)
    if units_raw:
        try:
            inv.units = Decimal(str(float(units_raw)))
        except Exception:
            pass

    price_raw = payload.get("current_price", inv.current_price)
    if price_raw:
        try:
            inv.current_price = Decimal(str(float(price_raw)))
        except Exception:
            pass

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return error_response("Investment update failed", errors={"error": str(e)}), 500

    return success_response(message="Investment updated successfully.", data={"investment_id": inv.id}), 200


@investments_bp.route("/<int:investment_id>", methods=["DELETE"])
@jwt_required()
def delete_investment(investment_id):
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    inv = Investment.query.filter_by(id=investment_id, user_id=user_id, is_deleted=False).first()
    if not inv:
        return error_response("Investment not found"), 404

    inv.is_deleted = True
    inv.deleted_at = datetime.utcnow()

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return error_response("Investment delete failed", errors={"error": str(e)}), 500

    return success_response(message="Investment deleted successfully.", data={"investment_id": inv.id}), 200


@investments_bp.route("/dashboard-stats", methods=["GET"])
@jwt_required()
def get_dashboard_stats():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    # Total investments
    total_investments = Investment.query.filter_by(user_id=user_id, is_deleted=False).count()
    total_amount = db.session.query(func.sum(Investment.amount)).filter(
        Investment.user_id == user_id,
        Investment.is_deleted == False,
    ).scalar() or 0

    # By type breakdown
    type_stats = db.session.query(
        Investment.investment_type,
        func.sum(Investment.amount).label("total"),
        func.count(Investment.id).label("count")
    ).filter(
        Investment.user_id == user_id,
        Investment.is_deleted == False,
    ).group_by(Investment.investment_type).order_by(func.sum(Investment.amount).desc()).all()

    type_breakdown = [
        {"type": t[0], "total": str(t[1]), "count": t[2]}
        for t in type_stats
    ]

    return success_response(
        message="Investment dashboard stats fetched successfully.",
        data={
            "total_investments": total_investments,
            "total_amount": str(total_amount),
            "type_breakdown": type_breakdown,
        },
    ), 200


@investments_bp.route("/types", methods=["GET"])
@jwt_required()
def get_investment_types():
    types = ["Stocks", "Mutual Funds", "ETFs", "Bonds", "Crypto", "Real Estate", "Fixed Deposit", "Gold", "Other"]
    return success_response(
        message="Investment types fetched successfully.",
        data={"types": types},
    ), 200