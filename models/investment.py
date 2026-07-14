from sqlalchemy.sql import func
from decimal import Decimal
from database.db import db


class Investment(db.Model):
    __tablename__ = "investments"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.user_id"), nullable=False, index=True)
    
    # Core fields
    name = db.Column(db.String(200), nullable=False)
    investment_type = db.Column(db.String(60), nullable=False, index=True)  # Stocks, Mutual Funds, ETFs, Bonds, Crypto, Gold, FD, Real Estate, Other
    amount = db.Column(db.Numeric(18, 2), nullable=False)
    units = db.Column(db.Numeric(18, 4), nullable=True)
    purchase_price = db.Column(db.Numeric(18, 2), nullable=True)
    current_price = db.Column(db.Numeric(18, 2), nullable=True)
    investment_date = db.Column(db.Date, nullable=False, index=True)
    
    # Optional fields
    ticker = db.Column(db.String(20), nullable=True)
    broker = db.Column(db.String(120), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    currency = db.Column(db.String(10), nullable=True, default='INR')
    
    # Risk level
    risk_level = db.Column(db.String(20), nullable=True, default='medium')  # low, medium, high
    
    # Status
    status = db.Column(db.String(30), default="active", nullable=False)  # active, sold, dividend
    
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Soft delete
    is_deleted = db.Column(db.Boolean, default=False, nullable=False, index=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Investment {self.id}: {self.name}>'
    
    @property
    def investment_cost(self):
        """Total cost = units * purchase_price, or fallback to amount"""
        if self.units and self.purchase_price:
            return float(self.units) * float(self.purchase_price)
        return float(self.amount)
    
    @property
    def current_value(self):
        """Current value = units * current_price, or fallback to amount"""
        if self.units and self.current_price:
            return float(self.units) * float(self.current_price)
        return float(self.amount)
    
    @property
    def profit_loss(self):
        return self.current_value - self.investment_cost
    
    @property
    def roi_percentage(self):
        if self.investment_cost > 0:
            return (self.profit_loss / self.investment_cost) * 100
        return 0.0
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'investment_type': self.investment_type,
            'amount': str(self.amount),
            'units': str(self.units) if self.units else None,
            'purchase_price': str(self.purchase_price) if self.purchase_price else None,
            'current_price': str(self.current_price) if self.current_price else None,
            'investment_date': self.investment_date.isoformat() if self.investment_date else None,
            'ticker': self.ticker,
            'broker': self.broker,
            'notes': self.notes,
            'currency': self.currency,
            'risk_level': self.risk_level,
            'status': self.status,
            'investment_cost': round(self.investment_cost, 2),
            'current_value': round(self.current_value, 2),
            'profit_loss': round(self.profit_loss, 2),
            'roi_percentage': round(self.roi_percentage, 2),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
