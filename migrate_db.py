"""
Database migration script to add new columns to existing tables.
Run this once to update the existing database schema.
"""
import logging
logging.disable(logging.CRITICAL)

from app import app
from database.db import db
from sqlalchemy import inspect, text

with app.app_context():
    inspector = inspect(db.engine)
    print("Running database migrations...")

    # Add risk_level column to investments table if missing
    inv_cols = [c['name'] for c in inspector.get_columns('investments')]
    if 'risk_level' not in inv_cols:
        print("  Adding risk_level column to investments...")
        db.session.execute(text("ALTER TABLE investments ADD COLUMN risk_level VARCHAR(20) DEFAULT 'medium'"))
        db.session.commit()
        print("  ✓ risk_level column added")
    else:
        print("  ✓ risk_level column already exists")

    # Ensure financial_goals table exists
    tables = inspector.get_table_names()
    if 'financial_goals' not in tables:
        print("  Creating financial_goals table...")
        from models.financial_goal import FinancialGoal
        db.create_all()
        print("  ✓ financial_goals table created")
    else:
        print("  ✓ financial_goals table exists")

    if 'alerts' not in tables:
        print("  Creating alerts table...")
        from models.alert import Alert
        db.create_all()
        print("  ✓ alerts table created")
    else:
        print("  ✓ alerts table exists")

    print("\nMigration completed successfully!")
    print("\nFinal table schemas:")
    for table_name in ['investments', 'financial_goals', 'alerts']:
        if table_name in inspector.get_table_names():
            cols = [c['name'] for c in inspector.get_columns(table_name)]
            print(f"  {table_name}: {cols}")