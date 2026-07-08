from flask import Flask, redirect
import config
from database.db import db
from models.user import User
from extensions import bcrypt, mail, jwt
from routes.auth_routers import auth_bp
from routes.expenses_routers import expenses_bp

from utils.api_response import error_response

app = Flask(__name__, static_folder='frontend', static_url_path='')
app.config.from_object(config)

db.init_app(app)
bcrypt.init_app(app)
mail.init_app(app)
jwt.init_app(app)

@app.route("/")
def home():
    return redirect("/login.html")

app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(expenses_bp, url_prefix="/api/expenses")


@app.errorhandler(400)
def bad_request_error(_err):
    return error_response("Bad request"), 400


@app.errorhandler(404)
def not_found_error(_err):
    return error_response("Not found"), 404


@app.errorhandler(500)
def internal_error(_err):
    return error_response("Internal server error"), 500


if __name__ == "__main__":
    with app.app_context():
        # Ensure all models (including new expense models) are registered.
        from models import expense  # noqa: F401
        db.create_all()

    app.run(debug=True)

