<<<<<<< HEAD
from flask import Flask, redirect, jsonify, send_from_directory
import config
from database.db import db
from models.user import User
from extensions import bcrypt, mail, jwt
from routes.auth_routers import auth_bp
from routes.expenses_routers import expenses_bp

from utils.api_response import error_response
=======
>>>>>>> 3b492c6 (Apply local auth and UI updates)
import logging
import os
from datetime import timedelta
from flask import Flask, redirect, jsonify
from sqlalchemy import inspect, text
import config
from database.db import db
from extensions import bcrypt, mail, jwt
from routes.auth_routers import auth_bp
from routes.expenses_routers import expenses_bp
from utils.api_response import error_response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, static_folder='frontend', static_url_path='')
app.config.from_object(config)

# Set Supabase config
app.config['SUPABASE_URL'] = config.SUPABASE_URL
app.config['SUPABASE_ANON_KEY'] = config.SUPABASE_ANON_KEY

# Set JWT configuration
app.config['JWT_SECRET_KEY'] = config.JWT_SECRET_KEY or 'your-secret-key-change-in-production'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=30)

# Initialize extensions
db.init_app(app)
bcrypt.init_app(app)
mail.init_app(app)
jwt.init_app(app)

# Create upload directories
os.makedirs(os.path.join(app.root_path, 'uploads', 'receipts'), exist_ok=True)
os.makedirs(os.path.join(app.root_path, 'uploads', 'profiles'), exist_ok=True)

# Routes
@app.route("/")
def home():
    return redirect("/login.html")

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "message": "FinSight API is running"
    }), 200

@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    """Serve uploaded receipt files."""
    upload_dir = os.path.join(app.root_path, "uploads")
    return send_from_directory(upload_dir, filename)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(expenses_bp, url_prefix="/api/expenses")

# Error handlers
@app.errorhandler(400)
def bad_request_error(err):
    logger.error(f"Bad request: {err}")
    return error_response("Bad request"), 400

@app.errorhandler(404)
def not_found_error(err):
    logger.error(f"Not found: {err}")
    return error_response("Not found"), 404

@app.errorhandler(500)
def internal_error(err):
    logger.error(f"Internal server error: {err}")
    return error_response("Internal server error"), 500

@app.errorhandler(401)
def unauthorized_error(err):
    logger.error(f"Unauthorized: {err}")
    return error_response("Unauthorized"), 401

@app.errorhandler(403)
def forbidden_error(err):
    logger.error(f"Forbidden: {err}")
    return error_response("Forbidden"), 403

# JWT error handlers
@jwt.invalid_token_loader
def invalid_token_callback(err):
    return error_response("Invalid token"), 401

@jwt.unauthorized_loader
def missing_token_callback(err):
    return error_response("Request requires authorization"), 401

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return error_response("Token has expired"), 401

<<<<<<< HEAD

# Run the Flask app
if __name__ == "__main__":
    logger.info("Starting FinSight API server...")
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False,
        use_debugger=True
    )
=======
def initialize_database():
    with app.app_context():
        try:
            from models.user import User
            from models.expense import Expense, ExpenseCategory, Account

            if str(config.SQLALCHEMY_DATABASE_URI).startswith("sqlite"):
                inspector = inspect(db.engine)
                if "users" in inspector.get_table_names():
                    schema_sql = db.session.execute(
                        text("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
                    ).scalar()
                    if schema_sql and "AUTOINCREMENT" not in schema_sql.upper() and "INTEGER" in schema_sql.upper():
                        logger.warning("Detected an older SQLite users table schema. Recreating tables...")
                        db.drop_all()
                        db.create_all()
                        logger.info("Database tables recreated successfully")
                        return

            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise


# Initialize database and run app
if __name__ == "__main__":
    initialize_database()
    logger.info("Starting FinSight API server...")
    app.run(host='0.0.0.0', port=5000, debug=True)
else:
    initialize_database()
>>>>>>> 3b492c6 (Apply local auth and UI updates)
