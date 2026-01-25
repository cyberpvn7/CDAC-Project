#!/usr/bin/env python3
"""
Database Migration Script
Upgrades existing databases with missing columns from schema updates
"""

import sqlite3
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import CONFIG

def migrate_database():
    """Add missing columns to existing database tables"""
    db_path = CONFIG["database"]["path"]
    
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get existing columns in findings table
        cursor.execute("PRAGMA table_info(findings)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        
        # Define new columns to add
        new_columns = {
            'semantic_classification': 'TEXT',
            'semantic_cvss': 'REAL',
            'attack_capability': 'TEXT',
            'mitre_tactic': 'TEXT',
            'mitre_technique': 'TEXT'
        }
        
        # Add missing columns
        migrations_applied = 0
        for column_name, column_type in new_columns.items():
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"""
                        ALTER TABLE findings
                        ADD COLUMN {column_name} {column_type}
                    """)
                    print(f"✅ Added column: {column_name}")
                    migrations_applied += 1
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        print(f"⚠️  Column already exists: {column_name}")
                    else:
                        raise
        
        conn.commit()
        conn.close()
        
        if migrations_applied > 0:
            print(f"\n✅ Applied {migrations_applied} migrations")
            return True
        else:
            print("✅ Database schema is up-to-date")
            return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


if __name__ == "__main__":
    import sys
    success = migrate_database()
    sys.exit(0 if success else 1)
