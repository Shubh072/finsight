"""
Alert model for FinSight.
Centralized alert system for budget, goal, and investment alerts.
"""
from sqlalchemy.sql import func
from database.db import db


class Alert(db.Model):
    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.user_id"), nullable=False, index=True)

    # Alert categorization
    alert_type = db.Column(db.String(30), nullable=False, index=True)  # budget, goal, investment
    alert_severity = db.Column(db.String(20), nullable=False, default="info")  # success, warning, danger, info
    alert_title = db.Column(db.String(200), nullable=False)
    alert_message = db.Column(db.Text, nullable=False)

    # Related entity (optional FK)
    reference_type = db.Column(db.String(30), nullable=True)  # e.g., budget_id, goal_id, investment_id
    reference_id = db.Column(db.Integer, nullable=True)

    # Status
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    is_dismissed = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False, index=True)

    def __repr__(self):
        return f'<Alert {self.id}: {self.alert_type} - {self.alert_title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'alert_type': self.alert_type,
            'alert_severity': self.alert_severity,
            'alert_title': self.alert_title,
            'alert_message': self.alert_message,
            'reference_type': self.reference_type,
            'reference_id': self.reference_id,
            'is_read': self.is_read,
            'is_dismissed': self.is_dismissed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }