import sqlite3

conn = sqlite3.connect("instance/finsight.db")
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS expenses")

conn.commit()
conn.close()

print("Expenses table deleted successfully.")