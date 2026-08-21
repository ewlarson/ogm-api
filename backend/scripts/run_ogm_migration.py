#!/usr/bin/env python3
"""
Script to run the OGM Aardvark migration.

This script adds the OGM-specific fields to the resources table
to support OGM flavored OGM Aardvark records.
"""

import sys
from pathlib import Path

# Add the project root directory to Python path
sys.path.append(str(Path(__file__).parent))

from db.migrations.add_ogm_fields import add_ogm_fields


def main():
    """Run the OGM migration."""
    print("Starting OGM Aardvark migration...")

    try:
        add_ogm_fields()
        print("✅ OGM migration completed successfully!")
    except Exception as e:
        print(f"❌ OGM migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
