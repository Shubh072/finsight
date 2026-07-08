from flask import Blueprint, request, jsonify, redirect
from flask_jwt_extended import jwt_required, get_jwt

from services.auth_service import (
    register_user,
    verify_email,
    login_user,
    forgot_password,
    reset_password,
)
from services.profile_service import get_me_service
from utils.api_response import error_response

auth_bp = Blueprint("auth", __name__)


def _jsonify(response, status):
    # Enforce API response contract shape here if services already follow it.
    if not isinstance(response, dict):
        return jsonify(error_response("Unexpected response type")), 500
    return jsonify(response), status


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    response, status = register_user(data)
    return _jsonify(response, status)


@auth_bp.route("/verify-email/<token>", methods=["GET"])
def verify(token):
    response, status = verify_email(token)
    success_str = "true" if status == 200 else "false"
    message_escaped = response.get("message", "")
    return redirect(f"/verify_email.html?success={success_str}&message={message_escaped}")


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    response, status = login_user(data)
    return _jsonify(response, status)


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_pw():
    data = request.get_json() or {}
    response, status = forgot_password(data)
    return _jsonify(response, status)


@auth_bp.route("/reset-password/<token>", methods=["POST"])
def reset_pw(token):
    data = request.get_json() or {}
    response, status = reset_password(token, data)
    return _jsonify(response, status)


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    claims = get_jwt()
    response, status = get_me_service(claims)
    return _jsonify(response, status)
