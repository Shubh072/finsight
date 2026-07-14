"""
Financial Goal Planning routes for FinSight.
Manages short-term and long-term financial goals with progress tracking.
"""
from datetime import date, datetime, timedelta
from decimal import Decimal

from flask import Blueprint, request, send_file
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy import func, or_, and_

from database.db import db
from models.financial_goal import FinancialGoal
from utils.api_response import success_response, error_response

import io
import csv


goals_bp = Blueprint("goals", __name__)


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


def _calculate_goal_progress(goal):
    """
    Calculate goal metrics:
    - remaining_amount: target - current_savings
    - progress_percentage: (current_savings / target) * 100
    - monthly_savings_required: remaining / months_remaining
    - estimated_completion: projected date based on current savings rate
    """
    target = float(goal.target_amount)
    current = float(goal.current_savings)
    remaining = target - current
    progress_pct = (current / target * 100) if target > 0 else 0

    # Days remaining until target date
    today = date.today()
    target_date = goal.target_date
    days_remaining = (target_date - today).days

    # Monthly savings required
    months_remaining = max(1, days_remaining / 30.44) if days_remaining > 0 else 1
    monthly_required = max(0, remaining / months_remaining) if remaining > 0 else 0

    # Estimated completion date (assuming current savings rate continues)
    # If goal has been active for some time, calculate savings rate
    created_date = goal.created_at.date() if goal.created_at else today
    days_since_creation = max(1, (today - created_date).days)
    savings_rate = current / (days_since_creation / 30.44) if days_since_creation > 0 else 0

    estimated_completion = None
    if savings_rate > 0 and remaining > 0:
        months_to_complete = remaining / savings_rate
        estimated_days = int(months_to_complete * 30.44)
        estimated_completion = (today + timedelta(days=estimated_days)).isoformat()
    elif remaining <= 0:
        estimated_completion = today.isoformat()

    # Auto-update status
    if current >= target:
        new_status = "completed"
    elif current > 0:
        new_status = "in_progress"
    else:
        new_status = "not_started"

    if goal.status != new_status:
        goal.status = new_status

    return {
        "remaining_amount": round(max(0, remaining), 2),
        "progress_percentage": round(min(100, progress_pct), 1),
        "monthly_savings_required": round(monthly_required, 2),
        "estimated_completion_date": estimated_completion,
        "days_remaining": max(0, days_remaining),
    }


@goals_bp.route("/", methods=["POST"])
@jwt_required()
def create_goal():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    payload = request.get_json(silent=True) or {}

    name = (payload.get("name") or "").strip()
    goal_type = (payload.get("goal_type") or "short_term").strip()
    target_amount_raw = payload.get("target_amount")
    current_savings_raw = payload.get("current_savings", 0)
    target_date_raw = payload.get("target_date")
    priority = (payload.get("priority") or "medium").strip()
    notes = (payload.get("notes") or "").strip() or None
    category = (payload.get("category") or "").strip() or None
    savings_allocation_raw = payload.get("savings_allocation", 0)

    errors = {}

    if not name or len(name) < 2:
        errors["name"] = "Goal name must be at least 2 characters."

    if goal_type not in ("short_term", "long_term"):
        errors["goal_type"] = "Goal type must be short_term or long_term."

    if priority not in ("low", "medium", "high"):
        errors["priority"] = "Priority must be low, medium, or high."

    try:
        target_amount = float(target_amount_raw)
    except Exception:
        errors["target_amount"] = "Target amount must be a valid number."
        target_amount = None

    if target_amount is None or target_amount <= 0:
        errors["target_amount"] = "Target amount must be greater than 0."

    try:
        current_savings = float(current_savings_raw)
    except Exception:
        current_savings = 0

    target_date = _parse_date(target_date_raw)
    if not target_date:
        errors["target_date"] = "Target date is invalid."
    else:
        if target_date <= date.today():
            errors["target_date"] = "Target date must be in the future."

    if errors:
        return error_response("Validation failed", errors=errors), 400

    new_goal = FinancialGoal(
        user_id=user_id,
        name=name,
        goal_type=goal_type,
        target_amount=Decimal(str(target_amount)),
        current_savings=Decimal(str(current_savings)),
        target_date=target_date,
        priority=priority,
        notes=notes,
        category=category,
        status="not_started" if current_savings <= 0 else "in_progress",
    )

    try:
        db.session.add(new_goal)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return error_response("Goal creation failed", errors={"error": str(e)}), 500

    return success_response(
        message="Financial goal created successfully.",
        data={"goal_id": new_goal.id},
    ), 201


@goals_bp.route("/", methods=["GET"])
@jwt_required()
def get_goals():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    query = FinancialGoal.query.filter_by(user_id=user_id, is_deleted=False)

    # Filters
    goal_type = request.args.get("goal_type", "").strip()
    if goal_type:
        query = query.filter_by(goal_type=goal_type)

    status = request.args.get("status", "").strip()
    if status:
        query = query.filter_by(status=status)

    priority = request.args.get("priority", "").strip()
    if priority:
        query = query.filter_by(priority=priority)

    # Search
    search = request.args.get("search", "").strip()
    if search:
        query = query.filter(
            or_(
                FinancialGoal.name.ilike(f"%{search}%"),
                FinancialGoal.notes.ilike(f"%{search}%"),
            )
        )

    # Sorting
    sort_by = request.args.get("sort", "created_at").strip()
    order = request.args.get("order", "desc").strip().lower()

    sort_map = {
        "created_at": FinancialGoal.created_at,
        "target_amount": FinancialGoal.target_amount,
        "target_date": FinancialGoal.target_date,
        "name": FinancialGoal.name,
        "priority": FinancialGoal.priority,
        "progress": FinancialGoal.current_savings,
    }
    sort_col = sort_map.get(sort_by, FinancialGoal.created_at)

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

    goals_data = []
    for goal in paginated.items:
        goal_dict = goal.to_dict()
        progress = _calculate_goal_progress(goal)
        goal_dict.update(progress)
        goals_data.append(goal_dict)

    # Commit any status updates
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()

    return success_response(
        message="Goals fetched successfully.",
        data={
            "goals": goals_data,
            "pagination": {
                "total": paginated.total,
                "page": page,
                "per_page": per_page,
                "pages": paginated.pages,
            },
        },
    ), 200


@goals_bp.route("/<int:goal_id>", methods=["GET"])
@jwt_required()
def get_goal(goal_id):
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    goal = FinancialGoal.query.filter_by(id=goal_id, user_id=user_id, is_deleted=False).first()
    if not goal:
        return error_response("Goal not found"), 404

    goal_dict = goal.to_dict()
    progress = _calculate_goal_progress(goal)
    goal_dict.update(progress)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()

    return success_response(
        message="Goal fetched successfully.",
        data=goal_dict,
    ), 200


@goals_bp.route("/<int:goal_id>", methods=["PUT"])
@jwt_required()
def update_goal(goal_id):
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    goal = FinancialGoal.query.filter_by(id=goal_id, user_id=user_id, is_deleted=False).first()
    if not goal:
        return error_response("Goal not found"), 404

    payload = request.get_json(silent=True) or {}

    if "name" in payload:
        goal.name = (payload["name"] or "").strip()
    if "goal_type" in payload:
        goal.goal_type = payload["goal_type"]
    if "target_amount" in payload:
        try:
            goal.target_amount = Decimal(str(float(payload["target_amount"])))
        except Exception:
            return error_response("Invalid target amount"), 400
    if "current_savings" in payload:
        try:
            goal.current_savings = Decimal(str(float(payload["current_savings"])))
        except Exception:
            return error_response("Invalid current savings"), 400
    if "target_date" in payload:
        parsed = _parse_date(payload["target_date"])
        if parsed:
            goal.target_date = parsed
    if "priority" in payload:
        goal.priority = payload["priority"]
    if "notes" in payload:
        goal.notes = (payload["notes"] or "").strip() or None
    if "category" in payload:
        goal.category = (payload["category"] or "").strip() or None

    # Recalculate status
    current = float(goal.current_savings)
    target = float(goal.target_amount)
    if current >= target:
        goal.status = "completed"
    elif current > 0:
        goal.status = "in_progress"
    else:
        goal.status = "not_started"

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return error_response("Goal update failed", errors={"error": str(e)}), 500

    return success_response(message="Goal updated successfully.", data={"goal_id": goal.id}), 200


@goals_bp.route("/<int:goal_id>", methods=["DELETE"])
@jwt_required()
def delete_goal(goal_id):
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    goal = FinancialGoal.query.filter_by(id=goal_id, user_id=user_id, is_deleted=False).first()
    if not goal:
        return error_response("Goal not found"), 404

    goal.is_deleted = True
    goal.deleted_at = datetime.utcnow()

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return error_response("Goal delete failed", errors={"error": str(e)}), 500

    return success_response(message="Goal deleted successfully.", data={"goal_id": goal.id}), 200


@goals_bp.route("/dashboard-stats", methods=["GET"])
@jwt_required()
def get_dashboard_stats():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    # Total goals
    total_goals = FinancialGoal.query.filter_by(user_id=user_id, is_deleted=False).count()

    # Completed goals
    completed_goals = FinancialGoal.query.filter_by(
        user_id=user_id, is_deleted=False, status="completed"
    ).count()

    # Active (in_progress) goals
    active_goals = FinancialGoal.query.filter_by(
        user_id=user_id, is_deleted=False, status="in_progress"
    ).count()

    # Total saved across all goals
    total_saved = db.session.query(func.sum(FinancialGoal.current_savings)).filter(
        FinancialGoal.user_id == user_id,
        FinancialGoal.is_deleted == False,
    ).scalar() or 0

    # Overall progress: sum(current_savings) / sum(target_amount) * 100
    total_target = db.session.query(func.sum(FinancialGoal.target_amount)).filter(
        FinancialGoal.user_id == user_id,
        FinancialGoal.is_deleted == False,
    ).scalar() or 0
    overall_progress = (float(total_saved) / float(total_target) * 100) if float(total_target) > 0 else 0

    return success_response(
        message="Goal dashboard stats fetched successfully.",
        data={
            "total_goals": total_goals,
            "completed_goals": completed_goals,
            "active_goals": active_goals,
            "total_saved": str(total_saved),
            "overall_progress": round(overall_progress, 1),
        },
    ), 200


@goals_bp.route("/export/csv", methods=["GET"])
@jwt_required()
def export_goals_csv():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    goals = FinancialGoal.query.filter_by(user_id=user_id, is_deleted=False).order_by(
        FinancialGoal.created_at.desc()
    ).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Name", "Type", "Target Amount", "Current Savings",
        "Target Date", "Priority", "Status", "Remaining",
        "Progress (%)", "Monthly Required", "Notes"
    ])

    for goal in goals:
        progress = _calculate_goal_progress(goal)
        writer.writerow([
            goal.name, goal.goal_type, str(goal.target_amount),
            str(goal.current_savings), goal.target_date.isoformat(),
            goal.priority, goal.status,
            progress["remaining_amount"], progress["progress_percentage"],
            progress["monthly_savings_required"], goal.notes or "",
        ])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"goals_export_{date.today().isoformat()}.csv",
    ), 200