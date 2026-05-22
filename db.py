import os
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor


db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")

try:
    connection_pool = pool.SimpleConnectionPool(1, 10, dsn=db_url)
except psycopg2.DatabaseError as e:
    print(f'Error connecting to database: {e}')
    connection_pool = None

def get_db():
    if not connection_pool:
        raise Exception('Database connection pool is not initialized.')
    
    conn = connection_pool.getconn()
    try:
        yield conn
    finally:
        connection_pool.putconn(conn) #return connection to pool after use is done

def init_db():
    if not connection_pool:
        return 
    
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS urls (
                    id          SERIAL PRIMARY KEY,
                    short_code  TEXT UNIQUE,
                    long_url    TEXT NOT NULL,
                    click_count INTEGER DEFAULT 0,
                    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
    finally:
        connection_pool.putconn(conn)
    

