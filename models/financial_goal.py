"""
Financial Goal model for FinSight.
Tracks short-term and long-term financial goals with progress monitoring.
"""
from sqlalchemy.sql import func
from decimal import Decimal
from database.db import db


class FinancialGoal(db.Model):
    __tablename__ = "financial_goals"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.user_id"), nullable=False, index=True)

    # Core fields
    name = db.Column(db.String(200), nullable=False)
    goal_type = db.Column(db.String(30), nullable=False, default="short_term")  # short_term, long_term
    target_amount = db.Column(db.Numeric(18, 2), nullable=False)
    current_savings = db.Column(db.Numeric(18, 2), nullable=False, default=0)
    target_date = db.Column(db.Date, nullable=False)
    priority = db.Column(db.String(20), nullable=False, default="medium")  # low, medium, high

    # Optional
    notes = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(60), nullable=True)  # Optional grouping
    savings_allocation = db.Column(db.Numeric(5, 2), nullable=True, default=0)  # % of savings allocated to this goal (0-100)

    # Auto-updated status
    status = db.Column(db.String(20), default="not_started", nullable=False)  # not_started, in_progress, completed

    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Soft delete
    is_deleted = db.Column(db.Boolean, default=False, nullable=False, index=True)
    deleted_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<FinancialGoal {self.id}: {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'goal_type': self.goal_type,
            'target_amount': str(self.target_amount),
            'current_savings': str(self.current_savings),
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'priority': self.priority,
            'notes': self.notes,
            'category': self.category,
            'status': self.status,
            'savings_allocation': float(self.savings_allocation) if self.savings_allocation else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
