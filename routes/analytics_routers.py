"""
Analytics routes for FinSight.
Provides comprehensive financial analytics with JWT authentication.
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy import func, and_
from database.db import db
from models.expense import Expense
from models.income import Income
from models.budget import Budget
from models.investment import Investment
from utils.api_response import success_response, error_response

analytics_bp = Blueprint("analytics", __name__)


def _user_id_from_claims():
    """Extract user_id from JWT claims."""
    claims = get_jwt()
    user_id = claims.get("sub") or claims.get("user_id") or claims.get("identity")
    if user_id is not None:
        try:
            return int(user_id)
        except (ValueError, TypeError):
            return user_id
    return None


def _get_date_range(filter_type, custom_start=None, custom_end=None):
    """Calculate date range based on filter type."""
    today = date.today()
    
    if filter_type == "today":
        return today, today
    elif filter_type == "last_7_days":
        return today - timedelta(days=6), today
    elif filter_type == "last_30_days":
        return today - timedelta(days=29), today
    elif filter_type == "current_month":
        return today.replace(day=1), today
    elif filter_type == "last_month":
        first_of_this_month = today.replace(day=1)
        last_of_last_month = first_of_this_month - timedelta(days=1)
        return last_of_last_month.replace(day=1), last_of_last_month
    elif filter_type == "last_3_months":
        return today - timedelta(days=90), today
    elif filter_type == "last_6_months":
        return today - timedelta(days=180), today
    elif filter_type == "last_12_months":
        return today - timedelta(days=365), today
    elif filter_type == "custom" and custom_start and custom_end:
        return custom_start, custom_end
    else:
        return today - timedelta(days=30), today


@analytics_bp.route("/dashboard", methods=["GET"])
@jwt_required()
def get_dashboard():
    """Get all dashboard data: cards, charts, and insights in one call."""
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401
    
    # Get filter parameters
    filter_type = request.args.get("filter", "last_30_days")
    date_from_str = request.args.get("date_from", "").strip()
    date_to_str = request.args.get("date_to", "").strip()
    
    # Calculate date range
    if filter_type == "custom":
        date_from = _parse_date(date_from_str) or date.today() - timedelta(days=30)
        date_to = _parse_date(date_to_str) or date.today()
    else:
        date_from, date_to = _get_date_range(filter_type)
    
    try:
        # Get all data
        dashboard_data = {
            "cards": _get_dashboard_cards(user_id, date_from, date_to),
            "charts": _get_all_charts(user_id, date_from, date_to),
            "insights": _get_financial_insights(user_id, date_from, date_to),
        }
        
        return success_response(
            message="Dashboard data fetched successfully.",
            data=dashboard_data,
        ), 200
    except Exception as e:
        return error_response(f"Failed to fetch dashboard data: {str(e)}"), 500


def _parse_date(value):
    """Parse date string to date object."""
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


def _get_dashboard_cards(user_id, date_from, date_to):
    """Calculate dashboard summary cards."""
    # Total Income
    total_income = db.session.query(func.sum(Income.amount)).filter(
        Income.user_id == user_id,
        Income.is_deleted == False,
    ).scalar() or 0
    
    # Total Expense
    total_expense = db.session.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user_id,
        Expense.is_deleted == False,
    ).scalar() or 0
    
    # Current Balance (Income - Expense)
    current_balance = float(total_income) - float(total_expense)
    
    # Monthly Savings (filtered period)
    month_income = db.session.query(func.sum(Income.amount)).filter(
        Income.user_id == user_id,
        Income.is_deleted == False,
        Income.income_date >= date_from,
        Income.income_date <= date_to,
    ).scalar() or 0
    
    month_expense = db.session.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user_id,
        Expense.is_deleted == False,
        Expense.expense_date >= date_from,
        Expense.expense_date <= date_to,
    ).scalar() or 0
    
    monthly_savings = float(month_income) - float(month_expense)
    
    # Budget Utilization
    total_budget = db.session.query(func.sum(Budget.amount)).filter(
        Budget.user_id == user_id,
        Budget.is_deleted == False,
    ).scalar() or 0
    
    budget_utilization = (float(month_expense) / float(total_budget) * 100) if float(total_budget) > 0 else 0
    
# Total Investments (use amount as the column, current_value is a property)
    total_investments = db.session.query(func.sum(Investment.amount)).filter(
        Investment.user_id == user_id,
        Investment.is_deleted == False,
        Investment.status == "active",
    ).scalar() or 0
    
    # Total Budgets
    total_budgets = Budget.query.filter_by(
        user_id=user_id, is_deleted=False
    ).count()
    
    # Total Transactions
    total_transactions = (
        Income.query.filter_by(user_id=user_id, is_deleted=False).count() +
        Expense.query.filter_by(user_id=user_id, is_deleted=False).count()
    )
    
    # Financial Health Score
    health_score = _calculate_financial_health(
        float(total_income), float(total_expense), 
        float(total_investments), float(current_balance),
        float(budget_utilization)
    )
    
    return {
        "total_income": round(float(total_income), 2),
        "total_expense": round(float(total_expense), 2),
        "current_balance": round(current_balance, 2),
        "monthly_savings": round(monthly_savings, 2),
        "budget_utilization": round(budget_utilization, 1),
        "total_investments": round(float(total_investments), 2),
        "total_budgets": total_budgets,
        "total_transactions": total_transactions,
        "financial_health_score": health_score,
    }


def _calculate_financial_health(total_income, total_expense, total_investments, current_balance, budget_utilization):
    """Calculate financial health score (0-100)."""
    score = 50  # Base score
    
    # Income vs Expense ratio (positive balance is good)
    if total_income > 0:
        savings_ratio = (total_income - total_expense) / total_income
        if savings_ratio > 0.2:
            score += 20
        elif savings_ratio > 0:
            score += 10
        elif savings_ratio < -0.2:
            score -= 20
        else:
            score -= 10
    
    # Investment diversity (more investments = better)
    if total_investments > 0:
        if total_investments > total_income:
            score += 15
        elif total_investments > total_income * 0.5:
            score += 10
        else:
            score += 5
    
    # Budget utilization (under budget is good)
    if budget_utilization < 80:
        score += 10
    elif budget_utilization < 100:
        score += 5
    elif budget_utilization < 120:
        score -= 10
    else:
        score -= 20
    
    # Balance health
    if current_balance > 0:
        score += 15
    elif current_balance < 0:
        score -= 15
    
    return max(0, min(100, score))


def _get_all_charts(user_id, date_from, date_to):
    """Get all chart data."""
    return {
        "expense_by_category": _get_expense_by_category(user_id, date_from, date_to),
        "income_vs_expense": _get_income_vs_expense(user_id, date_from, date_to),
        "monthly_expense_trend": _get_monthly_expense_trend(user_id, date_from, date_to),
        "monthly_income_trend": _get_monthly_income_trend(user_id, date_from, date_to),
        "budget_vs_expense": _get_budget_vs_expense(user_id, date_from, date_to),
        "payment_method_distribution": _get_payment_method_distribution(user_id, date_from, date_to),
        "top_spending_categories": _get_top_spending_categories(user_id, date_from, date_to),
        "monthly_savings_trend": _get_monthly_savings_trend(user_id, date_from, date_to),
        "investment_allocation": _get_investment_allocation(user_id),
        "daily_expense_trend": _get_daily_expense_trend(user_id, date_from, date_to),
    }


def _get_expense_by_category(user_id, date_from, date_to):
    """Get expense by category for doughnut chart."""
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
    
    if not category_data:
        return {"labels": [], "data": [], "colors": []}
    
    colors = ["#8B5CF6", "#10B981", "#3B82F6", "#F59E0B", "#EF4444", "#EC4899", "#14B8A6", "#6366F1", "#F97316", "#84CC16"]
    
    return {
        "labels": [cat[0] for cat in category_data],
        "data": [float(cat[1]) for cat in category_data],
        "colors": colors[:len(category_data)],
    }


def _get_income_vs_expense(user_id, date_from, date_to):
    """Get income vs expense for bar chart (monthly)."""
    # Monthly income
    income_data = db.session.query(
        func.strftime("%Y-%m", Income.income_date).label("month"),
        func.sum(Income.amount).label("total")
    ).filter(
        Income.user_id == user_id,
        Income.is_deleted == False,
        Income.income_date >= date_from,
        Income.income_date <= date_to,
    ).group_by(func.strftime("%Y-%m", Income.income_date)).all()
    
    # Monthly expense
    expense_data = db.session.query(
        func.strftime("%Y-%m", Expense.expense_date).label("month"),
        func.sum(Expense.amount).label("total")
    ).filter(
        Expense.user_id == user_id,
        Expense.is_deleted == False,
        Expense.expense_date >= date_from,
        Expense.expense_date <= date_to,
    ).group_by(func.strftime("%Y-%m", Expense.expense_date)).all()
    
    # Combine data
    months = sorted(set([i[0] for i in income_data] + [e[0] for e in expense_data]))
    
    income_map = {i[0]: float(i[1]) for i in income_data}
    expense_map = {e[0]: float(e[1]) for e in expense_data}
    
    return {
        "labels": months,
        "income": [income_map.get(m, 0) for m in months],
        "expense": [expense_map.get(m, 0) for m in months],
    }


def _get_monthly_expense_trend(user_id, date_from, date_to):
    """Get monthly expense trend for line chart."""
    monthly_data = db.session.query(
        func.strftime("%Y-%m", Expense.expense_date).label("month"),
        func.sum(Expense.amount).label("total"),
        func.count(Expense.id).label("count")
    ).filter(
        Expense.user_id == user_id,
        Expense.is_deleted == False,
        Expense.expense_date >= date_from,
        Expense.expense_date <= date_to,
    ).group_by(func.strftime("%Y-%m", Expense.expense_date)).order_by(
        func.strftime("%Y-%m", Expense.expense_date)
    ).all()
    
    return {
        "labels": [m[0] for m in monthly_data],
        "data": [float(m[1]) for m in monthly_data],
        "counts": [m[2] for m in monthly_data],
    }


def _get_monthly_income_trend(user_id, date_from, date_to):
    """Get monthly income trend for line chart."""
    monthly_data = db.session.query(
        func.strftime("%Y-%m", Income.income_date).label("month"),
        func.sum(Income.amount).label("total"),
        func.count(Income.id).label("count")
    ).filter(
        Income.user_id == user_id,
        Income.is_deleted == False,
        Income.income_date >= date_from,
        Income.income_date <= date_to,
    ).group_by(func.strftime("%Y-%m", Income.income_date)).order_by(
        func.strftime("%Y-%m", Income.income_date)
    ).all()
    
    return {
        "labels": [m[0] for m in monthly_data],
        "data": [float(m[1]) for m in monthly_data],
        "counts": [m[2] for m in monthly_data],
    }


def _get_budget_vs_expense(user_id, date_from, date_to):
    """Get budget vs expense for grouped bar chart."""
    # Get budgets
    budgets = Budget.query.filter_by(
        user_id=user_id, is_deleted=False
    ).all()
    
    # Get expenses by category
    expense_by_category = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label("total")
    ).filter(
        Expense.user_id == user_id,
        Expense.is_deleted == False,
        Expense.expense_date >= date_from,
        Expense.expense_date <= date_to,
    ).group_by(Expense.category).all()
    
    expense_map = {e[0]: float(e[1]) for e in expense_by_category}
    
    categories = []
    budget_amounts = []
    expense_amounts = []
    
    for budget in budgets:
        categories.append(budget.category)
        budget_amounts.append(float(budget.amount))
        expense_amounts.append(expense_map.get(budget.category, 0))
    
    return {
        "labels": categories,
        "budget": budget_amounts,
        "expense": expense_amounts,
    }


def _get_payment_method_distribution(user_id, date_from, date_to):
    """Get payment method distribution for pie chart."""
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
    
    if not payment_data:
        return {"labels": [], "data": [], "colors": []}
    
    colors = ["#8B5CF6", "#10B981", "#3B82F6", "#F59E0B", "#EF4444", "#EC4899", "#14B8A6"]
    
    return {
        "labels": [p[0] for p in payment_data],
        "data": [float(p[1]) for p in payment_data],
        "colors": colors[:len(payment_data)],
    }


def _get_top_spending_categories(user_id, date_from, date_to):
    """Get top spending categories for horizontal bar chart."""
    category_data = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label("total"),
        func.count(Expense.id).label("count")
    ).filter(
        Expense.user_id == user_id,
        Expense.is_deleted == False,
        Expense.expense_date >= date_from,
        Expense.expense_date <= date_to,
    ).group_by(Expense.category).order_by(func.sum(Expense.amount).desc()).limit(10).all()
    
    return {
        "labels": [c[0] for c in category_data],
        "data": [float(c[1]) for c in category_data],
        "counts": [c[2] for c in category_data],
    }


def _get_monthly_savings_trend(user_id, date_from, date_to):
    """Get monthly savings trend for area chart."""
    # Get all months in range
    months_income = db.session.query(
        func.strftime("%Y-%m", Income.income_date).label("month"),
        func.sum(Income.amount).label("total")
    ).filter(
        Income.user_id == user_id,
        Income.is_deleted == False,
        Income.income_date >= date_from,
        Income.income_date <= date_to,
    ).group_by(func.strftime("%Y-%m", Income.income_date)).all()
    
    months_expense = db.session.query(
        func.strftime("%Y-%m", Expense.expense_date).label("month"),
        func.sum(Expense.amount).label("total")
    ).filter(
        Expense.user_id == user_id,
        Expense.is_deleted == False,
        Expense.expense_date >= date_from,
        Expense.expense_date <= date_to,
    ).group_by(func.strftime("%Y-%m", Expense.expense_date)).all()
    
    income_map = {m[0]: float(m[1]) for m in months_income}
    expense_map = {m[0]: float(m[1]) for m in months_expense}
    
    all_months = sorted(set(income_map.keys()) | set(expense_map.keys()))
    
    savings = []
    for m in all_months:
        savings.append(income_map.get(m, 0) - expense_map.get(m, 0))
    
    return {
        "labels": all_months,
        "data": savings,
    }


def _get_investment_allocation(user_id):
    """Get investment allocation for doughnut chart."""
    investments = Investment.query.filter_by(
        user_id=user_id, is_deleted=False, status="active"
    ).all()
    
    if not investments:
        return {"labels": [], "data": [], "colors": []}
    
    type_data = {}
    for inv in investments:
        inv_type = inv.investment_type or "Other"
        type_data[inv_type] = type_data.get(inv_type, 0) + inv.current_value
    
    colors = ["#8B5CF6", "#10B981", "#3B82F6", "#F59E0B", "#EF4444", "#EC4899", "#14B8A6", "#6366F1", "#F97316", "#84CC16"]
    
    return {
        "labels": list(type_data.keys()),
        "data": [float(v) for v in type_data.values()],
        "colors": colors[:len(type_data)],
    }


def _get_daily_expense_trend(user_id, date_from, date_to):
    """Get daily expense trend for line chart."""
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
    
    return {
        "labels": [d[0].isoformat() for d in daily_data],
        "data": [float(d[1]) for d in daily_data],
        "counts": [d[2] for d in daily_data],
    }


def _get_financial_insights(user_id, date_from, date_to):
    """Generate AI financial insights."""
    insights = []
    
    # Highest spending category
    highest_category = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label("total")
    ).filter(
        Expense.user_id == user_id,
        Expense.is_deleted == False,
        Expense.expense_date >= date_from,
        Expense.expense_date <= date_to,
    ).group_by(Expense.category).order_by(func.sum(Expense.amount).desc()).first()
    
    if highest_category:
        insights.append({
            "type": "highest_spending",
            "title": "Highest Spending Category",
            "value": highest_category[0],
            "amount": float(highest_category[1]),
            "icon": "trending_up",
            "color": "error",
        })
    
    # Highest spending month
    highest_month = db.session.query(
        func.strftime("%Y-%m", Expense.expense_date).label("month"),
        func.sum(Expense.amount).label("total")
    ).filter(
        Expense.user_id == user_id,
        Expense.is_deleted == False,
    ).group_by(func.strftime("%Y-%m", Expense.expense_date)).order_by(
        func.sum(Expense.amount).desc()
    ).first()
    
    if highest_month:
        insights.append({
            "type": "highest_month",
            "title": "Highest Spending Month",
            "value": highest_month[0],
            "amount": float(highest_month[1]),
            "icon": "calendar_month",
            "color": "secondary",
        })
    
    # Average monthly expense
    monthly_avg = db.session.query(
        func.strftime("%Y-%m", Expense.expense_date).label("month"),
        func.sum(Expense.amount).label("total")
    ).filter(
        Expense.user_id == user_id,
        Expense.is_deleted == False,
    ).group_by(func.strftime("%Y-%m", Expense.expense_date)).all()
    
    if monthly_avg:
        avg_expense = sum(float(m[1]) for m in monthly_avg) / len(monthly_avg)
        insights.append({
            "type": "avg_monthly",
            "title": "Average Monthly Expense",
            "value": f"₹{avg_expense:,.2f}",
            "amount": avg_expense,
            "icon": "analytics",
            "color": "primary",
        })
    
    # Budget exceeded warning
    budgets = Budget.query.filter_by(
        user_id=user_id, is_deleted=False
    ).all()
    
    exceeded_budgets = []
    for budget in budgets:
        month_start = date.today().replace(day=1)
        if date.today().month == 12:
            month_end = date(date.today().year + 1, 1, 1)
        else:
            month_end = date(date.today().year, date.today().month + 1, 1)
        
        spent = db.session.query(func.sum(Expense.amount)).filter(
            Expense.user_id == user_id,
            Expense.is_deleted == False,
            Expense.category == budget.category,
            Expense.expense_date >= month_start,
            Expense.expense_date < month_end,
        ).scalar() or 0
        
        if float(spent) > float(budget.amount):
            exceeded_budgets.append({
                "category": budget.category,
                "budget": float(budget.amount),
                "spent": float(spent),
            })
    
    if exceeded_budgets:
        insights.append({
            "type": "budget_warning",
            "title": "Budget Exceeded",
            "value": f"{len(exceeded_budgets)} category(ies)",
            "details": exceeded_budgets,
            "icon": "warning",
            "color": "error",
        })
    
    # Savings rate
    total_income = db.session.query(func.sum(Income.amount)).filter(
        Income.user_id == user_id,
        Income.is_deleted == False,
    ).scalar() or 0
    
    total_expense = db.session.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user_id,
        Expense.is_deleted == False,
    ).scalar() or 0
    
    if float(total_income) > 0:
        savings_rate = (float(total_income) - float(total_expense)) / float(total_income) * 100
        insights.append({
            "type": "savings_rate",
            "title": "Savings Rate",
            "value": f"{savings_rate:.1f}%",
            "amount": savings_rate,
            "icon": "savings",
            "color": "secondary" if savings_rate > 0 else "error",
        })
    
    # Investment summary
    investments = Investment.query.filter_by(
        user_id=user_id, is_deleted=False, status="active"
    ).all()
    
    if investments:
        total_invested = sum(inv.investment_cost for inv in investments)
        total_value = sum(inv.current_value for inv in investments)
        total_pl = total_value - total_invested
        
        insights.append({
            "type": "investment_summary",
            "title": "Investment Performance",
            "value": f"₹{total_value:,.2f}",
            "invested": total_invested,
            "profit_loss": total_pl,
            "icon": "trending_up",
            "color": "secondary" if total_pl >= 0 else "error",
        })
    
    # Get total investments for recommendations (use amount column since current_value is a property)
    total_investments = db.session.query(func.sum(Investment.amount)).filter(
        Investment.user_id == user_id,
        Investment.is_deleted == False,
        Investment.status == "active",
    ).scalar() or 0
    
    # Personalized recommendations
    recommendations = _generate_recommendations(user_id, float(total_income), float(total_expense), float(total_investments))
    insights.append({
        "type": "recommendations",
        "title": "AI Recommendations",
        "value": recommendations[0] if recommendations else "Keep up the good work!",
        "details": recommendations,
        "icon": "auto_awesome",
        "color": "primary",
    })
    
    return insights


def _generate_recommendations(user_id, total_income, total_expense, total_investments):
    """Generate personalized financial recommendations."""
    recommendations = []
    
    if total_income > 0:
        savings_rate = (total_income - total_expense) / total_income
        if savings_rate < 0.1:
            recommendations.append("Your savings rate is low. Consider reducing discretionary spending.")
        elif savings_rate < 0.2:
            recommendations.append("Good savings rate! Try to increase it to 20% for better financial security.")
        else:
            recommendations.append("Excellent savings rate! You're on track for strong financial health.")
    
    if total_investments < total_income * 0.5:
        recommendations.append("Consider increasing your investment contributions for long-term wealth building.")
    
    # Check for high spending categories
    high_spending = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label("total")
    ).filter(
        Expense.user_id == user_id,
        Expense.is_deleted == False,
    ).group_by(Expense.category).order_by(func.sum(Expense.amount).desc()).limit(3).all()
    
    if high_spending and len(high_spending) > 0 and total_expense > 0 and float(high_spending[0][1]) > total_expense * 0.3:
        recommendations.append(f"Review your spending on {high_spending[0][0]} - it's your largest expense category.")
    
    if not recommendations:
        recommendations.append("Your finances look healthy! Keep maintaining your current habits.")
    
    return recommendations


# Individual chart endpoints for direct access
@analytics_bp.route("/category", methods=["GET"])
@jwt_required()
def get_category():
    """Get expense by category data."""
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401
    
    date_from_str = request.args.get("date_from", "").strip()
    date_to_str = request.args.get("date_to", "").strip()
    filter_type = request.args.get("filter", "last_30_days")
    
    if filter_type == "custom":
        date_from = _parse_date(date_from_str) or date.today() - timedelta(days=30)
        date_to = _parse_date(date_to_str) or date.today()
    else:
        date_from, date_to = _get_date_range(filter_type)
    
    data = _get_expense_by_category(user_id, date_from, date_to)
    return success_response(message="Category data fetched.", data=data), 200


@analytics_bp.route("/monthly", methods=["GET"])
@jwt_required()
def get_monthly():
    """Get monthly trend data."""
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401
    
    date_from_str = request.args.get("date_from", "").strip()
    date_to_str = request.args.get("date_to", "").strip()
    filter_type = request.args.get("filter", "last_12_months")
    
    if filter_type == "custom":
        date_from = _parse_date(date_from_str) or date.today() - timedelta(days=365)
        date_to = _parse_date(date_to_str) or date.today()
    else:
        date_from, date_to = _get_date_range(filter_type)
    
    return success_response(
        message="Monthly data fetched.",
        data={
            "expense_trend": _get_monthly_expense_trend(user_id, date_from, date_to),
            "income_trend": _get_monthly_income_trend(user_id, date_from, date_to),
        },
    ), 200


@analytics_bp.route("/income-expense", methods=["GET"])
@jwt_required()
def get_income_expense():
    """Get income vs expense data."""
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401
    
    date_from_str = request.args.get("date_from", "").strip()
    date_to_str = request.args.get("date_to", "").strip()
    filter_type = request.args.get("filter", "last_12_months")
    
    if filter_type == "custom":
        date_from = _parse_date(date_from_str) or date.today() - timedelta(days=365)
        date_to = _parse_date(date_to_str) or date.today()
    else:
        date_from, date_to = _get_date_range(filter_type)
    
    data = _get_income_vs_expense(user_id, date_from, date_to)
    return success_response(message="Income vs expense data fetched.", data=data), 200


@analytics_bp.route("/payment-method", methods=["GET"])
@jwt_required()
def get_payment_method():
    """Get payment method distribution."""
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401
    
    date_from_str = request.args.get("date_from", "").strip()
    date_to_str = request.args.get("date_to", "").strip()
    filter_type = request.args.get("filter", "last_30_days")
    
    if filter_type == "custom":
        date_from = _parse_date(date_from_str) or date.today() - timedelta(days=30)
        date_to = _parse_date(date_to_str) or date.today()
    else:
        date_from, date_to = _get_date_range(filter_type)
    
    data = _get_payment_method_distribution(user_id, date_from, date_to)
    return success_response(message="Payment method data fetched.", data=data), 200


@analytics_bp.route("/budget", methods=["GET"])
@jwt_required()
def get_budget():
    """Get budget vs expense data."""
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401
    
    date_from_str = request.args.get("date_from", "").strip()
    date_to_str = request.args.get("date_to", "").strip()
    filter_type = request.args.get("filter", "current_month")
    
    if filter_type == "custom":
        date_from = _parse_date(date_from_str) or date.today()
        date_to = _parse_date(date_to_str) or date.today()
    else:
        date_from, date_to = _get_date_range(filter_type)
    
    data = _get_budget_vs_expense(user_id, date_from, date_to)
    return success_response(message="Budget data fetched.", data=data), 200


@analytics_bp.route("/investments", methods=["GET"])
@jwt_required()
def get_investments():
    """Get investment allocation data."""
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401
    
    data = _get_investment_allocation(user_id)
    return success_response(message="Investment data fetched.", data=data), 200


@analytics_bp.route("/financial-health", methods=["GET"])
@jwt_required()
def get_financial_health():
    """Get financial health score and details."""
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401
    
    date_from_str = request.args.get("date_from", "").strip()
    date_to_str = request.args.get("date_to", "").strip()
    filter_type = request.args.get("filter", "last_30_days")
    
    if filter_type == "custom":
        date_from = _parse_date(date_from_str) or date.today() - timedelta(days=30)
        date_to = _parse_date(date_to_str) or date.today()
    else:
        date_from, date_to = _get_date_range(filter_type)
    
    cards = _get_dashboard_cards(user_id, date_from, date_to)
    
    return success_response(
        message="Financial health data fetched.",
        data={
            "score": cards["financial_health_score"],
            "breakdown": {
                "income": cards["total_income"],
                "expense": cards["total_expense"],
                "balance": cards["current_balance"],
                "savings": cards["monthly_savings"],
                "investments": cards["total_investments"],
            },
        },
    ), 200


@analytics_bp.route("/export", methods=["GET"])
@jwt_required()
def export_analytics():
    """Export analytics data as PDF, Excel, or CSV."""
    from flask import Response
    import csv
    import io
    
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401
    
    format_type = request.args.get("format", "csv").lower()
    filter_type = request.args.get("filter", "last_30_days")
    date_from_str = request.args.get("date_from", "").strip()
    date_to_str = request.args.get("date_to", "").strip()
    
    if filter_type == "custom":
        date_from = _parse_date(date_from_str) or date.today() - timedelta(days=30)
        date_to = _parse_date(date_to_str) or date.today()
    else:
        date_from, date_to = _get_date_range(filter_type)
    
    try:
        # Get all data
        cards = _get_dashboard_cards(user_id, date_from, date_to)
        charts = _get_all_charts(user_id, date_from, date_to)
        
        if format_type == "csv":
            return _export_csv(cards, charts)
        elif format_type == "excel":
            return _export_excel(cards, charts)
        elif format_type == "pdf":
            return _export_pdf(cards, charts)
        else:
            return error_response("Invalid format. Use pdf, excel, or csv."), 400
    except Exception as e:
        return error_response(f"Export failed: {str(e)}"), 500


def _export_csv(cards, charts):
    """Export data as CSV."""
    from flask import Response
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write summary cards
    writer.writerow(["=== Dashboard Summary ==="])
    writer.writerow(["Metric", "Value"])
    writer.writerow(["Total Income", cards["total_income"]])
    writer.writerow(["Total Expense", cards["total_expense"]])
    writer.writerow(["Current Balance", cards["current_balance"]])
    writer.writerow(["Monthly Savings", cards["monthly_savings"]])
    writer.writerow(["Budget Utilization %", cards["budget_utilization"]])
    writer.writerow(["Total Investments", cards["total_investments"]])
    writer.writerow(["Total Budgets", cards["total_budgets"]])
    writer.writerow(["Total Transactions", cards["total_transactions"]])
    writer.writerow(["Financial Health Score", cards["financial_health_score"]])
    writer.writerow([])
    
    # Write expense by category
    writer.writerow(["=== Expense by Category ==="])
    writer.writerow(["Category", "Amount"])
    for i, label in enumerate(charts["expense_by_category"]["labels"]):
        writer.writerow([label, charts["expense_by_category"]["data"][i]])
    writer.writerow([])
    
    # Write income vs expense
    writer.writerow(["=== Income vs Expense ==="])
    writer.writerow(["Month", "Income", "Expense"])
    for i, label in enumerate(charts["income_vs_expense"]["labels"]):
        writer.writerow([label, charts["income_vs_expense"]["income"][i], charts["income_vs_expense"]["expense"][i]])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=analytics_report.csv"}
    )


def _export_excel(cards, charts):
    """Export data as Excel (CSV format for simplicity)."""
    from flask import Response
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write summary cards
    writer.writerow(["=== Dashboard Summary ==="])
    writer.writerow(["Metric", "Value"])
    writer.writerow(["Total Income", cards["total_income"]])
    writer.writerow(["Total Expense", cards["total_expense"]])
    writer.writerow(["Current Balance", cards["current_balance"]])
    writer.writerow(["Monthly Savings", cards["monthly_savings"]])
    writer.writerow(["Budget Utilization %", cards["budget_utilization"]])
    writer.writerow(["Total Investments", cards["total_investments"]])
    writer.writerow(["Total Budgets", cards["total_budgets"]])
    writer.writerow(["Total Transactions", cards["total_transactions"]])
    writer.writerow(["Financial Health Score", cards["financial_health_score"]])
    writer.writerow([])
    
    # Write all chart data
    writer.writerow(["=== Expense by Category ==="])
    writer.writerow(["Category", "Amount"])
    for i, label in enumerate(charts["expense_by_category"]["labels"]):
        writer.writerow([label, charts["expense_by_category"]["data"][i]])
    writer.writerow([])
    
    writer.writerow(["=== Monthly Expense Trend ==="])
    writer.writerow(["Month", "Amount"])
    for i, label in enumerate(charts["monthly_expense_trend"]["labels"]):
        writer.writerow([label, charts["monthly_expense_trend"]["data"][i]])
    writer.writerow([])
    
    writer.writerow(["=== Monthly Income Trend ==="])
    writer.writerow(["Month", "Amount"])
    for i, label in enumerate(charts["monthly_income_trend"]["labels"]):
        writer.writerow([label, charts["monthly_income_trend"]["data"][i]])
    writer.writerow([])
    
    writer.writerow(["=== Payment Method Distribution ==="])
    writer.writerow(["Method", "Amount"])
    for i, label in enumerate(charts["payment_method_distribution"]["labels"]):
        writer.writerow([label, charts["payment_method_distribution"]["data"][i]])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment;filename=analytics_report.xlsx"}
    )


def _export_pdf(cards, charts):
    """Export data as PDF (HTML format for simplicity)."""
    from flask import Response
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><title>FinSight Analytics Report</title></head>
    <body>
        <h1>FinSight Analytics Report</h1>
        <h2>Dashboard Summary</h2>
        <ul>
            <li>Total Income: ₹{cards["total_income"]}</li>
            <li>Total Expense: ₹{cards["total_expense"]}</li>
            <li>Current Balance: ₹{cards["current_balance"]}</li>
            <li>Monthly Savings: ₹{cards["monthly_savings"]}</li>
            <li>Budget Utilization: {cards["budget_utilization"]}%</li>
            <li>Total Investments: ₹{cards["total_investments"]}</li>
            <li>Financial Health Score: {cards["financial_health_score"]}</li>
        </ul>
        <h2>Expense by Category</h2>
        <ul>
            {''.join(f'<li>{label}: ₹{amount}</li>' for label, amount in zip(charts["expense_by_category"]["labels"], charts["expense_by_category"]["data"]))}
        </ul>
    </body>
    </html>
    """
    
    return Response(
        html_content,
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment;filename=analytics_report.pdf"}
    )
