import sqlite3

with sqlite3.connect('database.db') as conn:
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS "feeds" (
            "url" TEXT NOT NULL,
            "room" TEXT NOT NULL,
            "author" TEXT,
            "last_updated" DATETIME,
            "last_fetch" TEXT,
            "failures" INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY("url")
        );
    """)

    c.close()