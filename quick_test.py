import sqlite3
conn = sqlite3.connect(r'instance\finsight.db')
c = conn.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = [r[0] for r in c.fetchall()]
c2 = conn.execute('SELECT COUNT(*) FROM users')
users = c2.fetchone()[0]
c3 = conn.execute('SELECT COUNT(*) FROM expenses')
expenses = c3.fetchone()[0]
conn.close()
print(f'Tables: {tables}')
print(f'Users: {users}')
print(f'Expenses: {expenses}')