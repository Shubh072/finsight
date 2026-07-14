from sqlalchemy.sql import func
from decimal import Decimal
from database.db import db


class Income(db.Model):
    __tablename__ = "incomes"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.user_id"), nullable=False, index=True)
    
    # Core fields
    title = db.Column(db.String(200), nullable=False)
    source = db.Column(db.String(80), nullable=False, index=True)  # Salary, Freelance, Business, Investment, Rental, Other
    amount = db.Column(db.Numeric(18, 2), nullable=False)
    income_date = db.Column(db.Date, nullable=False, index=True)
    payment_method = db.Column(db.String(60), nullable=True)
    
    # Optional fields
    description = db.Column(db.Text, nullable=True)
    is_recurring = db.Column(db.Boolean, default=False, nullable=False)
    recurring_frequency = db.Column(db.String(30), nullable=True)  # monthly, yearly, weekly
    currency = db.Column(db.String(10), nullable=True, default='INR')
    
    # Status
    status = db.Column(db.String(30), default="received", nullable=False)  # received, pending, expected
    
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Soft delete
    is_deleted = db.Column(db.Boolean, default=False, nullable=False, index=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Income {self.id}: {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'source': self.source,
            'amount': str(self.amount),
            'income_date': self.income_date.isoformat() if self.income_date else None,
            'payment_method': self.payment_method,
            'description': self.description,
            'is_recurring': self.is_recurring,
            'recurring_frequency': self.recurring_frequency,
            'currency': self.currency,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }