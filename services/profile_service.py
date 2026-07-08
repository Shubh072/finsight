from models.user import User
from utils.api_response import error_response, success_response


def get_me_service(claims):
    """Return current user profile summary (Phase 1 auth support for Phase 4)."""
    user_id = claims.get("sub") or claims.get("user_id") or claims.get("identity")
    if not user_id:
        return error_response("Unauthorized"), 401

    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return error_response("User not found"), 404

    return success_response(
        message="Profile fetched successfully.",
        data={
            "user_id": user.user_id,
            "full_name": user.full_name,
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "profile_photo": user.profile_photo,
            "role": user.role,
            "account_status": user.account_status,
            "email_verified": user.email_verified,
        },
    ), 200

