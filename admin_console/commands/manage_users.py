#!/usr/bin/env python3
# admin_console/commands/manage_users.py
"""
Manage users: create, list, regen-backup
Usage:
  python admin_console/commands/manage_users.py create --username USER --password PASS [--admin]
  python admin_console/commands/manage_users.py list
  python admin_console/commands/manage_users.py regen --username USER
"""
import sys, os

import argparse
from src.core import auth

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

def parse_args():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create")
    c.add_argument("--username", required=True)
    c.add_argument("--password", required=True)
    c.add_argument("--admin", action="store_true")
    sub.add_parser("list")
    r = sub.add_parser("regen")
    r.add_argument("--username", required=True)
    return p.parse_args()

def main():
    args = parse_args()
    if args.cmd == "create":
        res = auth.create_user(args.username, args.password, is_admin=args.admin)
        print("Created user:", res["username"])
        if res.get("totp_secret"):
            print("TOTP secret (show in authenticator app):", res["totp_secret"])
        print("Backup codes (show once):")
        for c in res["backup_codes"]:
            print(" -", c)
    elif args.cmd == "list":
        users = auth.list_users()
        for u in users:
            print(u)
    elif args.cmd == "regen":
        new = auth.regenerate_backup_codes(args.username)
        print("New backup codes for", args.username)
        for c in new:
            print(" -", c)

if __name__ == '__main__':
    main()
