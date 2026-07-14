from database.db import db
from sqlalchemy.sql import func

class Device(db.Model):
    __tablename__ = "devices"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    device_fingerprint = db.Column(db.String(255), nullable=False)
    device_name = db.Column(db.String(100))
    trusted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=func.now())
    last_used = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

    user = db.relationship('User', backref=db.backref('devices', lazy=True))
