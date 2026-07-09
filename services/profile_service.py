from utils.api_response import error_response, success_response
from utils import supabase_client as sb


def get_me_service(claims):
    """Return current user profile summary."""
    user_id = claims.get("sub") or claims.get("user_id") or claims.get("identity")
    if not user_id:
        return error_response("Unauthorized"), 401

    try:
        user = sb.select("users", filters={"user_id": user_id}, single=True)
    except Exception:
        return error_response("User not found"), 404

    if not user:
        return error_response("User not found"), 404

    return success_response(
        message="Profile fetched successfully.",
        data={
            "user_id": user.get("user_id"),
            "full_name": user.get("full_name"),
            "username": user.get("username"),
            "email": user.get("email"),
            "phone": user.get("phone"),
            "profile_photo": user.get("profile_photo"),
            "role": user.get("role"),
            "account_status": user.get("account_status"),
            "email_verified": user.get("email_verified"),
        },
    ), 200
