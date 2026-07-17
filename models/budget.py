from sqlalchemy.sql import func
from decimal import Decimal
from database.db import db


class Budget(db.Model):
    __tablename__ = "budgets"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.user_id"), nullable=False, index=True)
    
    # Core fields
    category = db.Column(db.String(80), nullable=False, index=True)
    amount = db.Column(db.Numeric(18, 2), nullable=True)  # Budget limit (some schemas use amount)
    limit_amount = db.Column(db.Numeric(18, 2), nullable=True)  # Budget limit (some schemas use limit_amount)
    period = db.Column(db.String(20), default="monthly", nullable=False)  # monthly, yearly, weekly
    month = db.Column(db.Integer, nullable=True)  # Month (1-12) for monthly budgets
    year = db.Column(db.Integer, nullable=True)   # Year
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    
    # Optional
    description = db.Column(db.Text, nullable=True)
    color = db.Column(db.String(50), nullable=True)
    icon = db.Column(db.String(50), nullable=True)
    
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Soft delete
    is_deleted = db.Column(db.Boolean, default=False, nullable=False, index=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Budget {self.id}: {self.category} - {self.amount or self.limit_amount}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'amount': str(self.amount) if self.amount is not None else None,
            'limit_amount': str(self.limit_amount) if self.limit_amount is not None else None,
            'period': self.period,
            'month': self.month,
            'year': self.year,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'description': self.description,
            'color': self.color,
            'icon': self.icon,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }