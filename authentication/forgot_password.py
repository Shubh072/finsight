from services.auth_service import forgot_password as forgot_password_service


def forgot_password(data):
    return forgot_password_service(data)


__all__ = ["forgot_password"]
