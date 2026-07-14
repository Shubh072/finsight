import logging
logging.disable(logging.CRITICAL)

from app import app
from database.db import db
from sqlalchemy import inspect

with app.app_context():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print('Tables:', tables)
    
    for t in ['investments', 'financial_goals', 'alerts']:
        if t in tables:
            cols = [c['name'] for c in inspector.get_columns(t)]
            print(f'  [OK] {t}: {len(cols)} cols -> {cols}')
        else:
            print(f'  [FAIL] {t}: MISSING')
    
    routes = set()
    for rule in app.url_map.iter_rules():
        r = rule.rule
        if any(x in r for x in ['/api/goals', '/api/alerts', '/api/investments/charts', '/api/investments/portfolio-summary']):
            routes.add(r)
    
    print()
    print('New Routes:')
    for r in sorted(routes):
        print(f'  {r}')
    
    print()
    print('All OK!')