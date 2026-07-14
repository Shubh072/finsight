"""
Investment Analytics routes for FinSight.
Generates Matplotlib charts for portfolio analysis.
"""
import io
import os
from datetime import date, datetime, timedelta
from decimal import Decimal

from flask import Blueprint, request, send_file
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy import func, and_, or_

from database.db import db
from models.investment import Investment
from utils.api_response import success_response, error_response

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np


investment_analytics_bp = Blueprint("investment_analytics", __name__)


def _user_id_from_claims():
    claims = get_jwt()
    user_id = claims.get("sub") or claims.get("user_id") or claims.get("identity")
    if user_id is not None:
        try:
            return int(user_id)
        except (ValueError, TypeError):
            return user_id
    return None


# Style configuration for dark theme charts
plt.style.use('dark_background')
CHART_COLORS = ['#8B5CF6', '#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#EC4899', '#14B8A6', '#6366F1', '#F97316', '#84CC16']


def _apply_dark_theme(ax, title, xlabel=None, ylabel=None):
    """Apply dark theme styling to a chart axes."""
    ax.set_facecolor('#0b1326')
    ax.figure.patch.set_facecolor('#0b1326')
    ax.tick_params(colors='#94a3b8', labelsize=8)
    ax.spines['bottom'].set_color('#334155')
    ax.spines['top'].set_color('#334155')
    ax.spines['left'].set_color('#334155')
    ax.spines['right'].set_color('#334155')
    ax.set_title(title, color='#f8fafc', fontsize=14, fontweight='bold', pad=15)
    if xlabel:
        ax.set_xlabel(xlabel, color='#94a3b8', fontsize=10)
    if ylabel:
        ax.set_ylabel(ylabel, color='#94a3b8', fontsize=10)
    ax.grid(True, alpha=0.1, color='#475569')


def _format_currency(value):
    """Format value as Indian currency string."""
    return f'₹{value:,.2f}'


@investment_analytics_bp.route("/charts/asset-allocation", methods=["GET"])
@jwt_required()
def asset_allocation_chart():
    """Generate asset allocation pie chart."""
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    investments = Investment.query.filter_by(
        user_id=user_id, is_deleted=False, status="active"
    ).all()

    if not investments:
        return error_response("No investment data available"), 404

    # Aggregate by type
    type_values = {}
    for inv in investments:
        inv_type = inv.investment_type or "Other"
        type_values[inv_type] = type_values.get(inv_type, 0) + inv.current_value

    labels = list(type_values.keys())
    sizes = list(type_values.values())
    colors = CHART_COLORS[:len(labels)]

    fig, ax = plt.subplots(figsize=(8, 6))
    _apply_dark_theme(ax, 'Asset Allocation')

    wedges, texts, autotexts = ax.pie(
        sizes, labels=None, autopct='%1.1f%%',
        colors=colors, startangle=90,
        textprops={'color': '#f8fafc', 'fontsize': 9},
        wedgeprops={'linewidth': 1, 'edgecolor': '#0b1326'},
        pctdistance=0.75,
    )
    for t in autotexts:
        t.set_color('#f8fafc')
        t.set_fontsize(8)

    # Legend
    legend_labels = [f'{l} ({_format_currency(s)})' for l, s in zip(labels, sizes)]
    ax.legend(
        wedges, legend_labels,
        loc='center left', bbox_to_anchor=(1, 0.5),
        fontsize=8, facecolor='#1e293b', edgecolor='#334155',
        labelcolor='#f8fafc'
    )

    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', transparent=False)
    buf.seek(0)
    plt.close(fig)

    return send_file(buf, mimetype='image/png'), 200


@investment_analytics_bp.route("/charts/portfolio-performance", methods=["GET"])
@jwt_required()
def portfolio_performance_chart():
    """Generate portfolio performance line chart showing investment cost vs current value."""
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    investments = Investment.query.filter_by(
        user_id=user_id, is_deleted=False, status="active"
    ).order_by(Investment.investment_date).all()

    if not investments:
        return error_response("No investment data available"), 404

    names = [inv.name[:15] for inv in investments]
    costs = [inv.investment_cost for inv in investments]
    values = [inv.current_value for inv in investments]

    x = np.arange(len(names))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    _apply_dark_theme(ax, 'Portfolio Performance', xlabel='Investments', ylabel='Amount (₹)')

    bars1 = ax.bar(x - width/2, costs, width, label='Investment Cost', color='#3B82F6', alpha=0.8)
    bars2 = ax.bar(x + width/2, values, width, label='Current Value', color='#10B981', alpha=0.8)

    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=45, ha='right', fontsize=7, color='#94a3b8')
    ax.legend(
        fontsize=10, facecolor='#1e293b', edgecolor='#334155',
        labelcolor='#f8fafc'
    )

    # Format y-axis as currency
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'₹{x:,.0f}'))

    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', transparent=False)
    buf.seek(0)
    plt.close(fig)

    return send_file(buf, mimetype='image/png'), 200


@investment_analytics_bp.route("/charts/type-distribution", methods=["GET"])
@jwt_required()
def investment_type_distribution_chart():
    """Generate horizontal bar chart showing investment distribution by type."""
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    investments = Investment.query.filter_by(
        user_id=user_id, is_deleted=False, status="active"
    ).all()

    if not investments:
        return error_response("No investment data available"), 404

    # Aggregate by type
    type_data = {}
    for inv in investments:
        inv_type = inv.investment_type or "Other"
        if inv_type not in type_data:
            type_data[inv_type] = {'cost': 0, 'value': 0, 'count': 0}
        type_data[inv_type]['cost'] += inv.investment_cost
        type_data[inv_type]['value'] += inv.current_value
        type_data[inv_type]['count'] += 1

    types = list(type_data.keys())
    costs = [type_data[t]['cost'] for t in types]
    values = [type_data[t]['value'] for t in types]
    counts = [type_data[t]['count'] for t in types]

    y = np.arange(len(types))
    height = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    _apply_dark_theme(ax, 'Investment Type Distribution', xlabel='Amount (₹)', ylabel='Investment Type')

    bars1 = ax.barh(y + height/2, costs, height, label='Cost', color='#3B82F6', alpha=0.8)
    bars2 = ax.barh(y - height/2, values, height, label='Current Value', color='#10B981', alpha=0.8)

    ax.set_yticks(y)
    ax.set_yticklabels([f'{t} ({c})' for t, c in zip(types, counts)], fontsize=9, color='#94a3b8')
    ax.legend(
        fontsize=10, facecolor='#1e293b', edgecolor='#334155',
        labelcolor='#f8fafc'
    )
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'₹{x:,.0f}'))

    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', transparent=False)
    buf.seek(0)
    plt.close(fig)

    return send_file(buf, mimetype='image/png'), 200


@investment_analytics_bp.route("/charts/risk-distribution", methods=["GET"])
@jwt_required()
def risk_distribution_chart():
    """Generate risk distribution chart showing allocation by risk level."""
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    investments = Investment.query.filter_by(
        user_id=user_id, is_deleted=False, status="active"
    ).all()

    if not investments:
        return error_response("No investment data available"), 404

    # Aggregate by risk level
    risk_data = {'Low': 0, 'Medium': 0, 'High': 0}
    risk_counts = {'Low': 0, 'Medium': 0, 'High': 0}
    for inv in investments:
        level = (inv.risk_level or 'medium').capitalize()
        if level not in risk_data:
            level = 'Medium'
        risk_data[level] += inv.current_value
        risk_counts[level] += 1

    risk_labels = list(risk_data.keys())
    risk_values = list(risk_data.values())
    risk_colors = ['#10B981', '#F59E0B', '#EF4444']  # Green, Yellow, Red

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Pie chart
    _apply_dark_theme(ax1, 'Risk Allocation')
    wedges, texts, autotexts = ax1.pie(
        risk_values, labels=None, autopct='%1.1f%%',
        colors=risk_colors[:len(risk_labels)], startangle=90,
        textprops={'color': '#f8fafc', 'fontsize': 9},
        wedgeprops={'linewidth': 1, 'edgecolor': '#0b1326'},
    )
    for t in autotexts:
        t.set_color('#f8fafc')
        t.set_fontsize(8)
    legend_labels = [f'{l} ({_format_currency(v)})' for l, v in zip(risk_labels, risk_values)]
    ax1.legend(
        wedges, legend_labels,
        loc='center left', bbox_to_anchor=(1, 0.5),
        fontsize=8, facecolor='#1e293b', edgecolor='#334155',
        labelcolor='#f8fafc'
    )

    # Bar chart
    _apply_dark_theme(ax2, 'Risk Level Distribution')
    x = np.arange(len(risk_labels))
    bars = ax2.bar(x, risk_values, color=risk_colors[:len(risk_labels)], alpha=0.8, width=0.5)
    ax2.set_xticks(x)
    ax2.set_xticklabels(risk_labels, fontsize=10, color='#94a3b8')
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'₹{x:,.0f}'))

    # Add value labels on bars
    for bar, val in zip(bars, risk_values):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                f'{_format_currency(val)}', ha='center', va='bottom',
                fontsize=8, color='#f8fafc')

    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', transparent=False)
    buf.seek(0)
    plt.close(fig)

    return send_file(buf, mimetype='image/png'), 200


@investment_analytics_bp.route("/charts/monthly-trend", methods=["GET"])
@jwt_required()
def monthly_investment_trend_chart():
    """Generate monthly investment trend line chart."""
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    investments = Investment.query.filter_by(
        user_id=user_id, is_deleted=False, status="active"
    ).order_by(Investment.investment_date).all()

    if not investments:
        return error_response("No investment data available"), 404

    # Aggregate by month
    monthly_data = {}
    for inv in investments:
        month_key = inv.investment_date.strftime('%Y-%m')
        if month_key not in monthly_data:
            monthly_data[month_key] = {'cost': 0, 'value': 0, 'count': 0}
        monthly_data[month_key]['cost'] += inv.investment_cost
        monthly_data[month_key]['value'] += inv.current_value
        monthly_data[month_key]['count'] += 1

    months = sorted(monthly_data.keys())
    costs = [monthly_data[m]['cost'] for m in months]
    values = [monthly_data[m]['value'] for m in months]
    counts = [monthly_data[m]['count'] for m in months]

    fig, ax = plt.subplots(figsize=(10, 6))
    _apply_dark_theme(ax, 'Monthly Investment Trend', xlabel='Month', ylabel='Amount (₹)')

    x = np.arange(len(months))
    line1 = ax.plot(x, costs, 'o-', color='#3B82F6', label='Investment Cost', linewidth=2, markersize=6)
    line2 = ax.plot(x, values, 's-', color='#10B981', label='Current Value', linewidth=2, markersize=6)
    ax.fill_between(x, costs, values, alpha=0.1, color='#8B5CF6')

    ax.set_xticks(x)
    ax.set_xticklabels(months, rotation=45, ha='right', fontsize=8, color='#94a3b8')
    ax.legend(
        fontsize=10, facecolor='#1e293b', edgecolor='#334155',
        labelcolor='#f8fafc'
    )
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'₹{x:,.0f}'))

    # Add count annotations
    for i, (m, c) in enumerate(zip(months, counts)):
        ax.annotate(f'n={c}', (i, costs[i]), xytext=(5, 5),
                   textcoords='offset points', fontsize=7, color='#94a3b8')

    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', transparent=False)
    buf.seek(0)
    plt.close(fig)

    return send_file(buf, mimetype='image/png'), 200


@investment_analytics_bp.route("/portfolio-summary", methods=["GET"])
@jwt_required()
def portfolio_summary():
    """Get comprehensive portfolio summary with analytics."""
    user_id = _user_id_from_claims()
    if not user_id:
        return error_response("Unauthorized"), 401

    investments = Investment.query.filter_by(
        user_id=user_id, is_deleted=False, status="active"
    ).all()

    if not investments:
        return success_response(
            message="Portfolio summary fetched successfully.",
            data={
                "total_investment": 0,
                "current_portfolio_value": 0,
                "overall_profit_loss": 0,
                "average_roi": 0,
                "total_investments_count": 0,
                "type_breakdown": [],
                "risk_breakdown": [],
            },
        ), 200

    total_investment = sum(inv.investment_cost for inv in investments)
    current_value = sum(inv.current_value for inv in investments)
    overall_pl = current_value - total_investment
    avg_roi = (overall_pl / total_investment * 100) if total_investment > 0 else 0

    # Type breakdown
    type_data = {}
    for inv in investments:
        inv_type = inv.investment_type or "Other"
        if inv_type not in type_data:
            type_data[inv_type] = {'cost': 0, 'value': 0, 'count': 0, 'pl': 0, 'roi': 0}
        type_data[inv_type]['cost'] += inv.investment_cost
        type_data[inv_type]['value'] += inv.current_value
        type_data[inv_type]['count'] += 1
        type_data[inv_type]['pl'] += inv.profit_loss

    type_breakdown = []
    for inv_type, data in type_data.items():
        roi = (data['pl'] / data['cost'] * 100) if data['cost'] > 0 else 0
        alloc_pct = (data['value'] / current_value * 100) if current_value > 0 else 0
        type_breakdown.append({
            "type": inv_type,
            "count": data['count'],
            "total_cost": round(data['cost'], 2),
            "current_value": round(data['value'], 2),
            "profit_loss": round(data['pl'], 2),
            "roi": round(roi, 2),
            "allocation_percentage": round(alloc_pct, 1),
        })

    # Risk breakdown
    risk_data = {'Low': {'cost': 0, 'value': 0, 'count': 0},
                 'Medium': {'cost': 0, 'value': 0, 'count': 0},
                 'High': {'cost': 0, 'value': 0, 'count': 0}}
    for inv in investments:
        level = (inv.risk_level or 'medium').capitalize()
        if level not in risk_data:
            level = 'Medium'
        risk_data[level]['cost'] += inv.investment_cost
        risk_data[level]['value'] += inv.current_value
        risk_data[level]['count'] += 1

    risk_breakdown = []
    for level, data in risk_data.items():
        alloc_pct = (data['value'] / current_value * 100) if current_value > 0 else 0
        risk_breakdown.append({
            "level": level,
            "count": data['count'],
            "total_cost": round(data['cost'], 2),
            "current_value": round(data['value'], 2),
            "allocation_percentage": round(alloc_pct, 1),
        })

    return success_response(
        message="Portfolio summary fetched successfully.",
        data={
            "total_investment": round(total_investment, 2),
            "current_portfolio_value": round(current_value, 2),
            "overall_profit_loss": round(overall_pl, 2),
            "average_roi": round(avg_roi, 2),
            "total_investments_count": len(investments),
            "type_breakdown": sorted(type_breakdown, key=lambda x: x['current_value'], reverse=True),
            "risk_breakdown": risk_breakdown,
        },
    ), 200