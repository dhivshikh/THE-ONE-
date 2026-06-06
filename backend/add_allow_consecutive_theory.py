"""
Migration: Add allow_consecutive_theory column to subjects table.

This column controls whether a theory subject can be scheduled in
consecutive periods on the same day.
- Default: False (consecutive NOT allowed)
- Set True for special subjects (Placement Training, Seminar, etc.)

Usage:
    python add_allow_consecutive_theory.py

Idempotent: Safe to run multiple times.
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import inspect, text
from app.db.session import engine


def migrate():
    """Add allow_consecutive_theory column if it doesn't exist."""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('subjects')]
    
    if 'allow_consecutive_theory' in columns:
        print("[OK] Column 'allow_consecutive_theory' already exists in 'subjects' table. Nothing to do.")
        return
    
    with engine.begin() as conn:
        conn.execute(text(
            "ALTER TABLE subjects ADD COLUMN allow_consecutive_theory BOOLEAN DEFAULT 0"
        ))
    
    print("[OK] Added 'allow_consecutive_theory' column to 'subjects' table (default: False).")
    print("     All existing subjects will default to NOT allowing consecutive theory periods.")
    print("     To enable for specific subjects, update them via API or SQL:")
    print("       UPDATE subjects SET allow_consecutive_theory = 1 WHERE code = 'PT101';")


if __name__ == "__main__":
    migrate()
