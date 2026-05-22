from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from psycopg2.extras import RealDictCursor
from db import get_db, init_db, connection_pool
from base62 import encode


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up: Initializing database...")
    init_db()
    
    yield
    
    print("Shutting down: Closing database connection pool...")
    if connection_pool:
        connection_pool.closeall()

app = FastAPI(lifespan=lifespan)

# define form of POST request
class ShortenRequest(BaseModel):
    url : str

# LONG URL -> SHORT URL
@app.post('/shorten')
def shorten_url(request: ShortenRequest, conn = Depends(get_db)):
    url = request.url

    # simple valid url validation for now
    if not url.startswith('http'):
        raise HTTPException(status_code=400, detail='Invalid URL')

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute('SELECT * FROM urls WHERE long_url = %s', (url,))
        existing = cursor.fetchone()
        
        # check if given URL has already been converted
        if existing:
            return { 'short_url': f'http://localhost:8000/{existing["short_code"]}' }

        # insert and get the id
        cursor.execute(
            'INSERT INTO urls (long_url) VALUES (%s) RETURNING id', (url,)
        )
        row_id = cursor.fetchone()['id']
        
        # generate short code
        short_code = encode(row_id)
        cursor.execute(
            'UPDATE urls SET short_code = %s WHERE id = %s', (short_code, row_id)
        )
        conn.commit()

    return { 'short_url': f'http://localhost:8000/{short_code}' }

# SHORT URL -> LONG URL
@app.get('/{short_code}')
def redirect(short_code: str, conn = Depends(get_db)):
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute('SELECT * FROM urls WHERE short_code = %s', (short_code,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail='Short code not found')
        
        cursor.execute(
            'UPDATE urls SET click_count = click_count + 1 WHERE short_code = %s', (short_code, )
        )
        conn.commit()

    return RedirectResponse(url=row['long_url'], status_code=302)


# STATS OF URL
@app.get('/{short_code}/stats')
def stats(short_code: str, conn = Depends(get_db)):
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute('SELECT * FROM urls WHERE short_code = %s', (short_code,))
        row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail='Short code not found')

    return {
        'short_code': row['short_code'],
        'long_url': row['long_url'],
        'click_count': row['click_count'],
        'created_at': row['created_at'].isoformat() if row['created_at'] else None
    }
