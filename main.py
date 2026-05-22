from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from db import get_db, init_db
from base62 import encode, decode
import os

app = FastAPI()
init_db()

class ShortenRequest(BaseModel):
    url : str


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
