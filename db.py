import sqlite3

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row #change tuples to sqlite rows
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS urls (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            short_code  TEXT UNIQUE,
            long_url    TEXT NOT NULL,
            click_count INTEGER DEFAULT 0,
            created_at  TEXT DEFAULT (datetime('now'))
        )
    ''')
    conn.commit()
    conn.close()

