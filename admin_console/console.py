# admin console entrypoint used by setup.py as 'madmin'
import argparse, sys, subprocess
import sys
from pathlib import Path

# Füge Projekt-Root zum Python-Pfad hinzu
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def main():
    p = argparse.ArgumentParser(prog='madmin')
    p.add_argument('module', nargs='*', help='module path under admin_console.commands or src')
    args = p.parse_args()
    if not args.module:
        print('Usage: madmin admin_console.commands.manage_users create --username ...')
        return 1
    # forward to python -m admin_console.commands.<...>
    cmd = [sys.executable, '-m'] + args.module
    return subprocess.call(cmd)

if __name__ == '__main__':
    raise SystemExit(main())
