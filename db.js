const Database = require('better-sqlite3')

const db = new Database('database.db');

// create table
db.exec(`
  CREATE TABLE IF NOT EXISTS urls (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    short_code  TEXT UNIQUE,
    long_url    TEXT NOT NULL,
    click_count INTEGER DEFAULT 0,
    created_at  TEXT DEFAULT (datetime('now'))
  )
`);

module.exports = db;