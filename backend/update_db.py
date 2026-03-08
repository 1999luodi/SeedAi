#!/usr/bin/env python
"""Deprecated schema updater.

Use mysql_data/migrate.py to apply schema changes.
"""

import sys


def main() -> int:
    print("[DEPRECATED] backend/update_db.py is no longer used for schema changes.")
    print("Use: python mysql_data/migrate.py --status")
    print("Use: python mysql_data/migrate.py --all")
    return 1


if __name__ == '__main__':
    sys.exit(main())