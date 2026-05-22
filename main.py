from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from db import get_db, init_db
from base62 import encode, decode
import os

app = FastAPI()
init_db()

class ShortenRequest(BaseModel):
    url : str

# LONG URL -> SHORT URL
@app.post('/shorten')
def shorten_url(request: ShortenRequest):
    url = request.url

    # simple valid url validation for now
    if not url.startswith('http'):
        raise HTTPException(status_code=400, detail='Invalid URL')
    
    conn = get_db()

    # insert url into db to get ID
    cursor = conn.execute(
        'INSERT INTO urls (long_url) VALUES (?)', (url,)
    )
    conn.commit()
    row_id = cursor.lastrowid

    # get updated short URL and save back into DB
    short_code = encode(row_id)
    conn.execute(
        'UPDATE urls SET short_code = ? WHERE id = ?', (short_code, row_id)
    )
    conn.commit()
    conn.close()

    return { 'short_url': f'http://localhost:8000/{short_code}' }

# SHORT URL -> LONG URL
@app.get('/{short_code}')
def redirect(short_code: str):
    conn = get_db()

    row = conn.execute(
        'SELECT * FROM urls WHERE short_code = ?', (short_code,)
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail='Short code not found')
    
    conn.execute(
        'UPDATE urls SET click_count = click_count + 1 WHERE short_code = ?', (short_code, )
    )
    conn.commit()
    conn.close()

    return RedirectResponse(url=row['long_url'], status_code=302)

@app.get('/{short_code}/stats')
def stats(short_code: str):
    conn = get_db()

    row = conn.execute(
        'SELECT * FROM urls WHERE short_code = ?', (short_code,)
    ).fetchone()

    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail='Short code not found')

    return {
        'short_code': row['short_code'],
        'long_url': row['long_url'],
        'click_count': row['click_count'],
        'created_at': row['created_at']
    }
