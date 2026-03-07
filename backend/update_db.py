#!/usr/bin/env python
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import app, db
from models import User, Dataset, Image, Annotation

def update_db():
    """Update the database with new table structure"""
    try:
        with app.app_context():
            # Create all tables (this will add new columns if they don't exist)
            db.create_all()
            print("Database tables updated successfully!")

            # Check current table structure
            from sqlalchemy import inspect
            inspector = inspect(db.engine)

            print("\nDataset table columns:")
            columns = inspector.get_columns('datasets')
            for col in columns:
                print(f"  - {col['name']}: {col['type']}")

            return True
    except Exception as e:
        print(f"Database update failed: {str(e)}")
        return False

if __name__ == '__main__':
    success = update_db()
    if not success:
        print("Failed to update database.")
        sys.exit(1)