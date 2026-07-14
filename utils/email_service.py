"""
Email service for FinSight.
Sends verification and password reset emails.
"""
from flask import current_app, render_template_string
from flask_mail import Message
from extensions import mail


def send_verification_email(email, token):
    """Send email verification link."""
    app_url = current_app.config.get('APP_URL', 'http://localhost:3000')
    verify_url = f"{app_url}/verify-email?token={token}"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; background: #f5f5f5;">
        <div style="max-width: 480px; margin: 40px auto; background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.08);">
            <div style="padding: 32px; text-align: center; background: linear-gradient(135deg, #7c3aed, #a855f7);">
                <div style="width: 48px; height: 48px; background: rgba(255,255,255,0.2); border-radius: 12px; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 12px;">
                    <span style="font-size: 24px;">📊</span>
                </div>
                <h1 style="color: #ffffff; font-size: 22px; margin: 0; font-weight: 700;">FinSight</h1>
            </div>
            <div style="padding: 32px;">
                <h2 style="color: #1a1a2e; font-size: 20px; margin: 0 0 8px 0;">Verify your email address</h2>
                <p style="color: #6b7280; font-size: 15px; line-height: 1.6; margin: 0 0 24px 0;">
                    Thanks for creating your FinSight account! Click the button below to verify your email address.
                </p>
                <div style="text-align: center;">
                    <a href="{verify_url}" style="display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, #7c3aed, #a855f7); color: #ffffff; text-decoration: none; border-radius: 12px; font-size: 16px; font-weight: 600;">Verify Email</a>
                </div>
                <p style="color: #9ca3af; font-size: 13px; margin: 24px 0 0 0; text-align: center;">
                    This link expires in 30 minutes.<br>
                    If you didn't create an account, you can safely ignore this email.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    msg = Message(
        subject="Verify your FinSight account",
        recipients=[email]
    )
    msg.html = html
    mail.send(msg)


def send_reset_email(email, token):
    """Send password reset link."""
    app_url = current_app.config.get('APP_URL', 'http://localhost:3000')
    reset_url = f"{app_url}/reset-password?token={token}"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; background: #f5f5f5;">
        <div style="max-width: 480px; margin: 40px auto; background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.08);">
            <div style="padding: 32px; text-align: center; background: linear-gradient(135deg, #7c3aed, #a855f7);">
                <div style="width: 48px; height: 48px; background: rgba(255,255,255,0.2); border-radius: 12px; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 12px;">
                    <span style="font-size: 24px;">🔐</span>
                </div>
                <h1 style="color: #ffffff; font-size: 22px; margin: 0; font-weight: 700;">FinSight</h1>
            </div>
            <div style="padding: 32px;">
                <h2 style="color: #1a1a2e; font-size: 20px; margin: 0 0 8px 0;">Reset your password</h2>
                <p style="color: #6b7280; font-size: 15px; line-height: 1.6; margin: 0 0 24px 0;">
                    We received a request to reset the password for your FinSight account. Click the button below to set a new password.
                </p>
                <div style="text-align: center;">
                    <a href="{reset_url}" style="display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, #7c3aed, #a855f7); color: #ffffff; text-decoration: none; border-radius: 12px; font-size: 16px; font-weight: 600;">Reset Password</a>
                </div>
                <p style="color: #9ca3af; font-size: 13px; margin: 24px 0 0 0; text-align: center;">
                    This link expires in 15 minutes.<br>
                    If you didn't request a password reset, you can safely ignore this email.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    msg = Message(
        subject="Reset your FinSight password",
        recipients=[email]
    )
    msg.html = html
    mail.send(msg)