from pathlib import Path
from app import app, initialize_database

path = Path('instance/finsight.db')
if path.exists():
    path.unlink()
    print('removed existing database')

with app.app_context():
    initialize_database()
    print('database initialized successfully')
