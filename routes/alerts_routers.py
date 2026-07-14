"""
Centralized Alert System routes for FinSight.
Generates and manages budget, goal, and investment alerts automatically.
"""
from datetime import date, datetime, timedelta
from decimal import Decimal

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy import func, and_, or_

from database.db import db
from models.alert import Alert
from models.budget import Budget
from models.expense import Expense
from models.financial_goal import FinancialGoal
from models.investment import Investment
from utils.api_response import success_response, error_response


alerts_bp = Blueprint("alerts", __name__)


def _user_id_from_claims():
    claims = get_jwt()
    user_id = claims.get("sub") or claims.get("user_id") or claims.get("identity")
    if user_id is not None:
        try:
            return int(user_id)
        except (ValueError, TypeError):
            return user_id
    return None


def _create_alert(user_id, alert_type, severity, title, message, ref_type=None, ref_id=None):
    """Helper to create a new alert."""
    try:
        alert = Alert(
            user_id=user_id,
            alert_type=alert_type,
            alert_severity=severity,
            alert_title=title,
            alert_message=message,
            reference_type=ref_type,
            reference_id=ref_id,
        )
        db.session.add(alert)
        db.session.commit()
        return alert
    except Exception:
        db.session.rollback()
        return None


def _dismiss_old_alerts(user_id, alert_type, ref_type=None, ref_id=None):
    """Dismiss old alerts of the same type to avoid duplicates."""
    try:
        query = Alert.query.filter_by(
            user_id=user_id, alert_type=alert_type, is_dismissed=False
        )
        if ref_type:
            query = query.filter_by(reference_type=ref_type)
        if ref_id:
            query = query.filter_by(reference_id=ref_id)
        for alert in query.all():
            alert.is_dismissed = True
        db.session.commit()
    except Exception:
        db.session.rollback()


# ──────────────────────────────────────────────
# Alert Generation Endpoints
# ──────────────────────────────────────────────

@alerts_bp.route("/generate", methods=["POST"])
@jwt_required()
def generate_alerts():
    """
    Generate all alerts for the current user.
    This endpoint is called to refresh alerts after data changes.
    """
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    generated = {
        "budget_alerts": 0,
        "goal_alerts": 0,
        "investment_alerts": 0,
    }

    # 1. Budget Alerts
    generated["budget_alerts"] = _generate_budget_alerts(user_id)

    # 2. Goal Alerts
    generated["goal_alerts"] = _generate_goal_alerts(user_id)

    # 3. Investment Alerts
    generated["investment_alerts"] = _generate_investment_alerts(user_id)

    return success_response(
        message="Alerts generated successfully.",
        data=generated,
    ), 200


def _generate_budget_alerts(user_id):
    """Compare monthly expenses with monthly budget and generate alerts."""
    today = date.today()
    month_start = today.replace(day=1)
    if today.month == 12:
        month_end = date(today.year + 1, 1, 1)
    else:
        month_end = date(today.year, today.month + 1, 1)

    budgets = Budget.query.filter_by(
        user_id=user_id, is_deleted=False,
        month=today.month, year=today.year
    ).all()

    count = 0
    for budget in budgets:
        # Get actual spending for this category this month
        spent = db.session.query(func.sum(Expense.amount)).filter(
            Expense.user_id == user_id,
            Expense.is_deleted == False,
            Expense.category == budget.category,
            Expense.expense_date >= month_start,
            Expense.expense_date < month_end,
        ).scalar() or 0

        spent_f = float(spent)
        budget_f = float(budget.amount)
        utilization = (spent_f / budget_f * 100) if budget_f > 0 else 0

        # Dismiss old alerts for this budget
        _dismiss_old_alerts(user_id, "budget", "budget_id", budget.id)

        if utilization > 100:
            _create_alert(
                user_id, "budget", "danger",
                "Budget Exceeded",
                f"You exceeded your {budget.category} budget by ₹{spent_f - budget_f:,.2f}. Budget: ₹{budget_f:,.2f}, Spent: ₹{spent_f:,.2f}.",
                "budget_id", budget.id
            )
            count += 1
        elif utilization >= 80:
            _create_alert(
                user_id, "budget", "warning",
                "Budget Warning",
                f"You have used {utilization:.1f}% of your {budget.category} budget (₹{spent_f:,.2f} of ₹{budget_f:,.2f}).",
                "budget_id", budget.id
            )
            count += 1
        else:
            _create_alert(
                user_id, "budget", "success",
                "Budget Healthy",
                f"Your {budget.category} budget is on track. Used {utilization:.1f}% (₹{spent_f:,.2f} of ₹{budget_f:,.2f}).",
                "budget_id", budget.id
            )
            count += 1

    return count


def _generate_goal_alerts(user_id):
    """Generate alerts for financial goals."""
    today = date.today()
    goals = FinancialGoal.query.filter_by(
        user_id=user_id, is_deleted=False
    ).filter(
        FinancialGoal.status != "completed"
    ).all()

    count = 0
    for goal in goals:
        _dismiss_old_alerts(user_id, "goal", "goal_id", goal.id)

        target = float(goal.target_amount)
        current = float(goal.current_savings)
        remaining = target - current
        days_remaining = (goal.target_date - today).days

        # Goal deadline within 30 days
        if 0 < days_remaining <= 30 and remaining > 0:
            monthly_needed = remaining / max(1, days_remaining / 30.44)
            _create_alert(
                user_id, "goal", "warning",
                "Goal Deadline Approaching",
                f"Your goal '{goal.name}' is due in {days_remaining} days. You need to save ₹{monthly_needed:,.2f}/month to reach ₹{target:,.2f}.",
                "goal_id", goal.id
            )
            count += 1

        # User is saving below recommended
        if goal.created_at:
            created_date = goal.created_at.date() if hasattr(goal.created_at, 'date') else today
            days_since = max(1, (today - created_date).days)
            savings_rate = current / (days_since / 30.44) if days_since > 0 else 0
            months_remaining = max(1, days_remaining / 30.44) if days_remaining > 0 else 1
            monthly_required = remaining / months_remaining if remaining > 0 else 0

            if savings_rate > 0 and monthly_required > 0 and savings_rate < monthly_required * 0.5:
                _create_alert(
                    user_id, "goal", "warning",
                    "Below Recommended Savings",
                    f"You're saving ₹{savings_rate:,.2f}/month for '{goal.name}', but need ₹{monthly_required:,.2f}/month to reach your target.",
                    "goal_id", goal.id
                )
                count += 1

        # Goal completed
        if current >= target:
            _create_alert(
                user_id, "goal", "success",
                "Goal Completed!",
                f"Congratulations! You've completed your goal '{goal.name}' by saving ₹{current:,.2f} of ₹{target:,.2f}.",
                "goal_id", goal.id
            )
            count += 1

    return count


def _generate_investment_alerts(user_id):
    """Generate alerts for investment portfolio."""
    investments = Investment.query.filter_by(
        user_id=user_id, is_deleted=False, status="active"
    ).all()

    if not investments:
        return 0

    count = 0
    _dismiss_old_alerts(user_id, "investment")

    # Calculate portfolio metrics
    total_cost = sum(inv.investment_cost for inv in investments)
    total_value = sum(inv.current_value for inv in investments)
    total_pl = total_value - total_cost
    overall_roi = (total_pl / total_cost * 100) if total_cost > 0 else 0

    # Portfolio loss exceeds 10%
    if overall_roi < -10:
        _create_alert(
            user_id, "investment", "danger",
            "Portfolio Loss Alert",
            f"Your portfolio has lost {abs(overall_roi):.1f}% (₹{abs(total_pl):,.2f}). Consider reviewing your investment strategy.",
            "portfolio", None
        )
        count += 1

    # ROI becomes negative
    if overall_roi < 0:
        _create_alert(
            user_id, "investment", "warning",
            "Negative Portfolio Return",
            f"Your overall portfolio ROI is {overall_roi:.1f}%. Total loss: ₹{abs(total_pl):,.2f}.",
            "portfolio", None
        )
        count += 1

    # One investment category exceeds 60% of portfolio
    type_totals = {}
    for inv in investments:
        inv_type = inv.investment_type or "Other"
        type_totals[inv_type] = type_totals.get(inv_type, 0) + inv.current_value

    for inv_type, type_value in type_totals.items():
        if total_value > 0 and (type_value / total_value * 100) > 60:
            pct = (type_value / total_value * 100)
            _create_alert(
                user_id, "investment", "warning",
                "High Concentration Risk",
                f"{inv_type} makes up {pct:.1f}% of your portfolio (₹{type_value:,.2f}). Consider diversifying.",
                "portfolio", None
            )
            count += 1

    # High-risk investments exceed 50% of portfolio
    high_risk_value = sum(
        inv.current_value for inv in investments
        if inv.risk_level == "high"
    )
    if total_value > 0 and (high_risk_value / total_value * 100) > 50:
        pct = (high_risk_value / total_value * 100)
        _create_alert(
            user_id, "investment", "warning",
            "High Risk Exposure",
            f"High-risk investments make up {pct:.1f}% of your portfolio (₹{high_risk_value:,.2f}). Consider rebalancing.",
            "portfolio", None
        )
        count += 1

    return count


# ──────────────────────────────────────────────
# Alert CRUD Endpoints
# ──────────────────────────────────────────────

@alerts_bp.route("/", methods=["GET"])
@jwt_required()
def get_alerts():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    query = Alert.query.filter_by(user_id=user_id, is_dismissed=False)

    # Filters
    alert_type = request.args.get("alert_type", "").strip()
    if alert_type:
        query = query.filter_by(alert_type=alert_type)

    severity = request.args.get("severity", "").strip()
    if severity:
        query = query.filter_by(alert_severity=severity)

    is_read = request.args.get("is_read")
    if is_read in ("true", "false"):
        query = query.filter_by(is_read=(is_read == "true"))

    # Sort by newest first
    query = query.order_by(Alert.created_at.desc())

    # Pagination
    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = max(1, min(100, int(request.args.get("per_page", 20))))
    except:
        page = 1
        per_page = 20

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    alerts_data = [alert.to_dict() for alert in paginated.items]

    # Count unread
    unread_count = Alert.query.filter_by(
        user_id=user_id, is_dismissed=False, is_read=False
    ).count()

    return success_response(
        message="Alerts fetched successfully.",
        data={
            "alerts": alerts_data,
            "unread_count": unread_count,
            "pagination": {
                "total": paginated.total,
                "page": page,
                "per_page": per_page,
                "pages": paginated.pages,
            },
        },
    ), 200


@alerts_bp.route("/<int:alert_id>/read", methods=["PUT"])
@jwt_required()
def mark_alert_read(alert_id):
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    alert = Alert.query.filter_by(id=alert_id, user_id=user_id).first()
    if not alert:
        return error_response("Alert not found"), 404

    alert.is_read = True
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return error_response("Failed to mark alert as read", errors={"error": str(e)}), 500

    return success_response(message="Alert marked as read."), 200


@alerts_bp.route("/<int:alert_id>/dismiss", methods=["PUT"])
@jwt_required()
def dismiss_alert(alert_id):
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    alert = Alert.query.filter_by(id=alert_id, user_id=user_id).first()
    if not alert:
        return error_response("Alert not found"), 404

    alert.is_dismissed = True
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return error_response("Failed to dismiss alert", errors={"error": str(e)}), 500

    return success_response(message="Alert dismissed."), 200


@alerts_bp.route("/read-all", methods=["PUT"])
@jwt_required()
def mark_all_read():
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    try:
        Alert.query.filter_by(user_id=user_id, is_dismissed=False, is_read=False).update(
            {"is_read": True}
        )
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return error_response("Failed to mark all as read", errors={"error": str(e)}), 500

    return success_response(message="All alerts marked as read."), 200


@alerts_bp.route("/recent", methods=["GET"])
@jwt_required()
def get_recent_alerts():
    """Get recent alerts for dashboard display."""
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    try:
        limit = min(50, int(request.args.get("limit", 10)))
    except:
        limit = 10

    alerts = Alert.query.filter_by(
        user_id=user_id, is_dismissed=False
    ).order_by(
        Alert.created_at.desc()
    ).limit(limit).all()

    return success_response(
        message="Recent alerts fetched successfully.",
        data={
            "alerts": [a.to_dict() for a in alerts],
            "unread_count": Alert.query.filter_by(
                user_id=user_id, is_dismissed=False, is_read=False
            ).count(),
        },
    ), 200