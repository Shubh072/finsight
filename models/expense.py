from sqlalchemy.sql import func
from decimal import Decimal
from database.db import db


def _bigint_unsigned():
    return db.BigInteger


class ExpenseCategory(db.Model):
    __tablename__ = "expense_categories"
    __table_args__ = ({"mysql_engine": "InnoDB"},)

    id = db.Column(_bigint_unsigned(), primary_key=True, autoincrement=True)
    user_id = db.Column(_bigint_unsigned(), db.ForeignKey("users.user_id"), nullable=False, index=True)
    name = db.Column(db.String(80), nullable=False)
    icon = db.Column(db.String(120), nullable=True)
    color = db.Column(db.String(50), nullable=True)
    category_image = db.Column(db.String(500), nullable=True)

    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)


class Account(db.Model):
    __tablename__ = "accounts"

    id = db.Column(_bigint_unsigned(), primary_key=True, autoincrement=True)
    user_id = db.Column(_bigint_unsigned(), db.ForeignKey("users.user_id"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    account_type = db.Column(db.String(50), nullable=True)

    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)


class Expense(db.Model):
    __tablename__ = "expenses"
    __table_args__ = ({"mysql_engine": "InnoDB"},)

    id = db.Column(_bigint_unsigned(), primary_key=True, autoincrement=True)
    user_id = db.Column(_bigint_unsigned(), db.ForeignKey("users.user_id"), nullable=False, index=True)

    # Core fields
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(80), nullable=False, index=True)
    amount = db.Column(db.Numeric(18, 2), nullable=False)
    expense_date = db.Column(db.Date, nullable=False, index=True)
    payment_method = db.Column(db.String(60), nullable=False)

    account_id = db.Column(db.BigInteger, db.ForeignKey("accounts.id"), nullable=True, index=True)
    merchant_name = db.Column(db.String(180), nullable=True, index=True)
    location = db.Column(db.String(180), nullable=True)
    description = db.Column(db.Text, nullable=True)

    # Tags stored as JSON
    tags_json = db.Column(db.JSON, nullable=True)

    recurring = db.Column(db.Boolean, default=False, nullable=False)
    currency = db.Column(db.String(10), nullable=True, default='USD')
    priority = db.Column(db.Integer, nullable=True)
    mood = db.Column(db.String(80), nullable=True)

    # Status
    status = db.Column(db.String(30), default="active", nullable=False, index=True)

    # Duplicate handling
    normalized_title = db.Column(db.String(255), nullable=True, index=True)
    fingerprint = db.Column(db.String(64), nullable=True, index=True)

    # Receipt storage
    receipt_filename = db.Column(db.String(255), nullable=True)
    receipt_url = db.Column(db.String(500), nullable=True)
    receipt_mime = db.Column(db.String(120), nullable=True)
    receipt_size = db.Column(_bigint_unsigned(), nullable=True)

    # OCR-ready structure
    receipt_ocr_text = db.Column(db.Text, nullable=True)
    receipt_ocr_confidence = db.Column(db.Numeric(5, 2), nullable=True)
    ocr_ready = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Soft delete
    is_deleted = db.Column(db.Boolean, default=False, nullable=False, index=True)
    deleted_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Expense {self.id}: {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'category': self.category,
            'amount': str(self.amount),
            'expense_date': self.expense_date.isoformat() if self.expense_date else None,
            'payment_method': self.payment_method,
            'account_id': self.account_id,
            'merchant_name': self.merchant_name,
            'location': self.location,
            'description': self.description,
            'tags': self.tags_json,
            'recurring': self.recurring,
            'currency': self.currency,
            'priority': self.priority,
            'mood': self.mood,
            'receipt_url': self.receipt_url,
            'receipt_filename': self.receipt_filename,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
