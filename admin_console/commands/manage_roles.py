#!/usr/bin/env python3
"""
admin_console/commands/manage_roles.py
Simple role assignment CLI that edits src/core/auth_roles.json
"""
import argparse, json, os, sys
import sys
from pathlib import Path

# Füge Projekt-Root zum Python-Pfad hinzu
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ROLES_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'core', 'auth_roles.json'))

def load():
    if not os.path.exists(ROLES_PATH):
        return {}
    return json.load(open(ROLES_PATH, 'r', encoding='utf-8'))

def save(data):
    os.makedirs(os.path.dirname(ROLES_PATH), exist_ok=True)
    json.dump(data, open(ROLES_PATH, 'w', encoding='utf-8'), indent=2)

def cmd_list(args):
    data = load()
    for user, roles in data.items():
        print(user, roles)

def cmd_set(args):
    data = load()
    data[args.user] = args.roles.split(',')
    save(data)
    print("Set roles for", args.user)

def cmd_remove(args):
    data = load()
    if args.user in data:
        del data[args.user]
        save(data)
        print("Removed roles for", args.user)
    else:
        print("User not found")

def main():
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest='cmd')
    p_list = sp.add_parser('list'); p_list.set_defaults(func=cmd_list)
    p_set = sp.add_parser('set'); p_set.add_argument('--user', required=True); p_set.add_argument('--roles', required=True); p_set.set_defaults(func=cmd_set)
    p_rm = sp.add_parser('remove'); p_rm.add_argument('--user', required=True); p_rm.set_defaults(func=cmd_remove)
    args = p.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        p.print_help()

if __name__ == '__main__':
    main()
