from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel
from psycopg2.extras import RealDictCursor
from db import get_db, init_db, connection_pool
from base62 import encode
import os

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


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

# landing page UI
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>URL Shortener</title>
    </head>
    <body>
        <h2>URL Shortener</h2>

        <input id="url" type="text" placeholder="Enter URL" style="width:300px;" />
        <button onclick="shorten()">Shorten</button>

        <p id="result"></p>

        <script>
            async function shorten() {
                const url = document.getElementById("url").value;

                const res = await fetch("/shorten", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ url })
                });

                const data = await res.json();

                document.getElementById("result").innerHTML =
                    `<a href="${data.short_url}" target="_blank">${data.short_url}</a>`;
            }
        </script>
    </body>
    </html>
    """

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
            return { 'short_url': f'{BASE_URL}/{existing["short_code"]}' }

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

    return { 'short_url': f'{BASE_URL}/{short_code}' }

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
@app.get('/{short_code}/stats', response_class=HTMLResponse)
def stats(short_code: str, conn = Depends(get_db)):
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute('SELECT * FROM urls WHERE short_code = %s', (short_code,))
        row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail='Short code not found')

    short_url = f"{BASE_URL}/{row['short_code']}"
    created = row['created_at'].strftime('%b %d, %Y') if row['created_at'] else '—'

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Stats – {row['short_code']}</title>
    </head>
    <body>
        <h2>Stats – {row['short_code']}</h2>
        <p><b>Short URL:</b> <a href="{short_url}">{short_url}</a></p>
        <p><b>Original URL:</b> {row['long_url']}</p>
        <p><b>Clicks:</b> {row['click_count']}</p>
        <p><b>Created:</b> {created}</p>
        <br/>
        <a href="/">← Back</a>
    </body>
    </html>
    """