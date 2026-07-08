from flask import current_app
from flask_mail import Message
from extensions import mail

def send_verification_email(email, token):
    verify_url = f"{current_app.config['APP_URL']}/api/auth/verify-email/{token}"
    msg = Message(
        subject="Verify your FinSight Account",
        recipients=[email]
    )
    msg.body = f"""
Hi,

Welcome to FinSight.

Please verify your email by clicking the link below.

{verify_url}

This link expires in 30 minutes.

Thank you.
"""
    mail.send(msg)

def send_reset_email(email, token):
    reset_url = f"{current_app.config['APP_URL']}/api/auth/reset-password/{token}"
    msg = Message(
        subject="Reset Your FinSight Password",
        recipients=[email]
    )
    msg.body = f"""
Hi,

Click the link below to reset your password.

{reset_url}

This link expires in 15 minutes.
"""
    mail.send(msg)