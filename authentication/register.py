from services.auth_service import register_user as register_user_service


def register(data):
    return register_user_service(data)


__all__ = ["register"]
