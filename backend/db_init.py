import sys


def main() -> int:
    print("[DEPRECATED] backend/db_init.py should not create/alter schema anymore.")
    print("Use: python mysql_data/migrate.py --all")
    print("Use mysql_data scripts for seed data and maintenance tasks.")
    return 1


if __name__ == '__main__':
    sys.exit(main())