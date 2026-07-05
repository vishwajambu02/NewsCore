"""
One-off migration: adds name and phone columns to the users table
in the LOCAL SQLite database (instance/newscore.db).

Usage:
    python migrate_add_user_profile_fields_sqlite.py
"""

import os
from sqlalchemy import create_engine, text, inspect

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'instance', 'newscore.db')

if not os.path.exists(db_path):
    print(f"[Migrate] No file at: {db_path}")
    print("[Migrate] Searching for newscore.db under the project folder...")
    for root, dirs, files in os.walk(BASE_DIR):
        if 'venv' in root or '.git' in root:
            continue
        for f in files:
            if f == 'newscore.db':
                found = os.path.join(root, f)
                print(f"[Migrate] Found: {found}")
    raise SystemExit("Update db_path above to the correct location shown, then re-run.")

db_url = f"sqlite:///{db_path}"
print(f"[Migrate] Connecting to: {db_url}")

engine = create_engine(db_url)
inspector = inspect(engine)
columns = [col['name'] for col in inspector.get_columns('users')]

with engine.connect() as conn:
    if 'name' not in columns:
        conn.execute(text('ALTER TABLE users ADD COLUMN name VARCHAR(200)'))
        conn.commit()
        print("[Migrate] Added 'name' column to users table.")
    else:
        print("[Migrate] Column 'name' already exists — skipping.")

    if 'phone' not in columns:
        conn.execute(text('ALTER TABLE users ADD COLUMN phone VARCHAR(30)'))
        conn.commit()
        print("[Migrate] Added 'phone' column to users table.")
    else:
        print("[Migrate] Column 'phone' already exists — skipping.")

print("[Migrate] Done.")