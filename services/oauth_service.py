import requests
from models.user import User
from database.db import db
from extensions import bcrypt
from flask_jwt_extended import create_access_token
from datetime import datetime
import os


def google_login(google_token):
    """
    Handle Google OAuth login
    """
    try:
        # Get user info from Google
        response = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {google_token}"}
        )
        
        if not response.ok:
            return {
                "success": False,
                "message": "Invalid Google token"
            }, 400

        user_data = response.json()
        email = user_data.get("email")
        full_name = user_data.get("name", "")
        google_id = user_data.get("id")

        # Check if user already exists
        user = User.query.filter_by(email=email).first()

        if not user:
            # Create new user
            username = email.split("@")[0]
            # Check if username already exists
            existing_username = User.query.filter_by(username=username).first()
            if existing_username:
                username = f"{username}_{google_id[:8]}"

            user = User(
                full_name=full_name,
                username=username,
                email=email,
                phone="0000000000",
                password_hash=bcrypt.generate_password_hash(os.urandom(16).hex()).decode("utf-8"),
                role="user",
                account_status="active",
                email_verified=True,
                failed_login_attempts=0,
                google_id=google_id
            )
            db.session.add(user)
            db.session.commit()
        else:
            # Update last login
            user.last_login = datetime.utcnow()
            if not user.google_id:
                user.google_id = google_id
            db.session.commit()

        # Create JWT token
        access_token = create_access_token(
            identity=str(user.user_id),
            additional_claims={
                "email": user.email,
                "role": user.role
            }
        )

        return {
            "success": True,
            "message": "Login successful!",
            "access_token": access_token,
            "user": {
                "user_id": user.user_id,
                "full_name": user.full_name,
                "email": user.email,
                "role": user.role
            }
        }, 200

    except Exception as e:
        return {
            "success": False,
            "message": "Google login failed",
            "error": str(e)
        }, 500


def apple_login(apple_token):
    """
    Handle Apple OAuth login
    """
    try:
        return {
            "success": False,
            "message": "Apple login coming soon!"
        }, 501

    except Exception as e:
        return {
            "success": False,
            "message": "Apple login failed",
            "error": str(e)
        }, 500
