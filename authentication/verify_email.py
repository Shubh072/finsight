from services.auth_service import verify_email as verify_email_service


def verify_email(token):
    return verify_email_service(token)


__all__ = ["verify_email"]
