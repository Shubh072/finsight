from itsdangerous import URLSafeTimedSerializer
from flask import current_app

def generate_reset_token(email):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return serializer.dumps(email, salt="password-reset")

def verify_reset_token(token):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        email = serializer.loads(
            token,
            salt="password-reset",
            max_age=900
        )
        return email
    except Exception:
        return None
