"""
One-off migration: adds name and phone columns to the users table.
Connects directly to Neon Postgres via DATABASE_URL from .env.

Usage:
    python migrate_add_user_profile_fields.py
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect

load_dotenv()

db_url = os.environ.get('DATABASE_URL')

if not db_url:
    raise SystemExit(
        "[Migrate] DATABASE_URL not found in environment.\n"
        "[Migrate] Make sure .env exists in this folder with DATABASE_URL=postgresql://..."
    )

if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)

print(f"[Migrate] Connecting to: {db_url.split('@')[-1]}")

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