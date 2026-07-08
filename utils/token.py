from itsdangerous import URLSafeTimedSerializer
from config import SECRET_KEY


serializer = URLSafeTimedSerializer(SECRET_KEY)


def generate_verification_token(email):
    return serializer.dumps(email, salt="email-verification")


def verify_verification_token(token, expiration=1800):
    try:
        email = serializer.loads(
            token,
            salt="email-verification",
            max_age=expiration
        )
        return email
    except Exception:
        return None