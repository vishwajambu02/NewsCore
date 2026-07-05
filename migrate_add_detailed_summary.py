"""
One-off migration: adds the detailed_summary column to the articles table.
Does NOT import app.py / create_app() — connects to the DB directly.

Flask-SQLAlchemy resolves relative sqlite:/// paths against the app's
instance/ folder, not the current working directory, so we replicate
that here explicitly instead of using Config.SQLALCHEMY_DATABASE_URI as-is.

Usage:
    python migrate_add_detailed_summary.py
"""

import os
from sqlalchemy import create_engine, text, inspect

# Point directly at the instance folder, same as Flask does by default.
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
columns = [col['name'] for col in inspector.get_columns('articles')]

if 'detailed_summary' in columns:
    print("[Migrate] Column 'detailed_summary' already exists — nothing to do.")
else:
    with engine.connect() as conn:
        conn.execute(text('ALTER TABLE articles ADD COLUMN detailed_summary TEXT'))
        conn.commit()
    print("[Migrate] Added 'detailed_summary' column to articles table.")