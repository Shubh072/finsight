import pymysql

DB = {
    "host": "localhost",
    "user": "root",
    "password": "2005",
    "database": "finsight_db",
}

def main():
    conn = pymysql.connect(**DB)
    cur = conn.cursor()

    # users.user_id
    cur.execute(
        """
        SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY, EXTRA
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA=%s AND TABLE_NAME='users' AND COLUMN_NAME='user_id'
        """,
        (DB["database"],),
    )
    print("users.user_id:", cur.fetchone())

    # accounts.user_id (table might not exist yet)
    cur.execute(
        """
        SELECT TABLE_NAME
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA=%s AND TABLE_NAME='accounts'
        """,
        (DB["database"],),
    )
    print("accounts exists:", cur.fetchone())

    cur.execute(
        """
        SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY, EXTRA
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA=%s AND TABLE_NAME='accounts' AND COLUMN_NAME='user_id'
        """,
        (DB["database"],),
    )
    print("accounts.user_id:", cur.fetchone())

    conn.close()

if __name__ == "__main__":
    main()

