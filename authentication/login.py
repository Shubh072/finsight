from services.auth_service import login_user as login_user_service


def login(data):
    return login_user_service(data)


__all__ = ["login"]
