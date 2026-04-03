"""
Create the earthquakes SQLite database and ensure the schema is correct.
Run this script once before starting data acquisition.
"""

import pathlib
import sqlite3

DATABASE = pathlib.Path("./earthquakes.sqlite")
SCHEMA = pathlib.Path("./schema.sql")
DATABASE.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(DATABASE)
conn.executescript(SCHEMA.read_text())
conn.commit()
conn.close()

print(f"Database ready at {DATABASE.resolve()}")
