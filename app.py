"""
FinSight - Unified Application Server
Serves both frontend static files and backend API routes directly.
No separate backend process required.
"""
import logging
import os
from datetime import timedelta
from pathlib import Path

from flask import Flask, redirect, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- App Factory ---
def create_app():
    app = Flask(__name__,
        static_folder='frontend',
        static_url_path='',
        template_folder='frontend/templates'
    )

    # --- Config ---
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'finsight-dev-secret-key-change-in-production')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'finsight-jwt-secret-key-change-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=30)
    app.config['APP_URL'] = os.getenv('APP_URL', 'http://localhost:3000')
    app.config['APP_NAME'] = 'FinSight'

    # Database (SQLite for local dev)
    instance_dir = Path(__file__).parent / 'instance'
    instance_dir.mkdir(exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL') or f"sqlite:///{instance_dir / 'finsight.db'}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Email config
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    app.config['MAIL_USE_SSL'] = False
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

    # Upload config
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
    os.makedirs(os.path.join(app.root_path, 'uploads', 'receipts'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'uploads', 'profiles'), exist_ok=True)

    CORS(app)

    # --- Init extensions ---
    from extensions import bcrypt, mail, jwt
    bcrypt.init_app(app)
    mail.init_app(app)
    jwt.init_app(app)

    from database.db import db
    db.init_app(app)

    # --- Register Blueprints ---
    from routes.auth_routers import auth_bp
    from routes.expenses_routers import expenses_bp
    from routes.analytics_routers import analytics_bp
    from routes.budgets_routers import budgets_bp
    from routes.goals_routers import goals_bp
    from routes.incomes_routers import incomes_bp
    from routes.investments_routers import investments_bp
    from routes.alerts_routers import alerts_bp
    from routes.investment_analytics_routers import investment_analytics_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(expenses_bp, url_prefix='/api/expenses')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(budgets_bp, url_prefix='/api/budgets')
    app.register_blueprint(goals_bp, url_prefix='/api/goals')
    app.register_blueprint(incomes_bp, url_prefix='/api/incomes')
    app.register_blueprint(investments_bp, url_prefix='/api/investments')
    app.register_blueprint(alerts_bp, url_prefix='/api/alerts')
    app.register_blueprint(investment_analytics_bp, url_prefix='/api/investments')

    # --- Health Check ---
    @app.route('/api/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'message': 'FinSight API is running',
            'version': '1.0.0'
        }), 200

    # --- Serve Static HTML Pages ---
    # Pages that exist at root level
    STATIC_PAGES = {
        'login': 'login.html',
        'register': 'create_account.html',
        'create_account': 'create_account.html',
        'forgot-password': 'forgot_password.html',
        'reset-password': 'reset_password.html',
        'verify-email': 'verify_email.html',
        'dashboard': 'dashboard.html',
        'expenses': 'expense.html',
        'budget': 'budget.html',
        'investments': 'investment.html',
        'goals': 'goal.html',
        'analytics': 'analytics.html',
        'reports': 'report_document.html',
        'notifications': 'notification.html',
        'settings': 'setting.html',
        'income': 'income.html',
        'landing': 'landing.html',
    }

    def _make_static_route(filename):
        return lambda: send_from_directory(app.static_folder, filename)

    for route, filename in STATIC_PAGES.items():
        endpoint = route.replace('-', '_')
        app.add_url_rule(f'/{route}', endpoint=f'serve_{endpoint}', 
                         view_func=_make_static_route(filename))

    @app.route('/')
    def home():
        return send_from_directory(app.static_folder, 'landing.html')

    # --- Error Handlers ---
    @app.errorhandler(400)
    def bad_request(err):
        return jsonify({'success': False, 'message': 'Bad request'}), 400

    @app.errorhandler(404)
    def not_found(err):
        return send_from_directory(app.static_folder, '404.html') if os.path.exists(os.path.join(app.static_folder, '404.html')) else (jsonify({'success': False, 'message': 'Not found'}), 404)

    @app.errorhandler(500)
    def internal_error(err):
        logger.error(f"Internal error: {err}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

    # --- JWT Error handlers ---
    @jwt.invalid_token_loader
    def invalid_token(err):
        return jsonify({'success': False, 'message': 'Invalid token'}), 401

    @jwt.unauthorized_loader
    def missing_token(err):
        return jsonify({'success': False, 'message': 'Authorization required'}), 401

    @jwt.expired_token_loader
    def expired_token(jwt_header, jwt_payload):
        return jsonify({'success': False, 'message': 'Token has expired'}), 401

    # --- Create Tables ---
    with app.app_context():
        try:
            from models.user import User
            from models.expense import Expense, ExpenseCategory, Account
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Database init error: {e}")

    return app


# --- Main ---
if __name__ == '__main__':
    app = create_app()
    logger.info("Starting FinSight server on http://localhost:3000")
    app.run(host='0.0.0.0', port=3000, debug=True)