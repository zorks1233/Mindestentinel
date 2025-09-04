# simple CLI entrypoint for the project
import argparse
import subprocess, sys

def main():
    p = argparse.ArgumentParser(prog='mindest')
    p.add_argument('cmd', nargs='*', help='Command to forward to python -m ...')
    args = p.parse_args()
    if not args.cmd:
        print('Usage: mindest <module> [args]  e.g. mindest src.main --start-rest')
        return 0
    # forward to python -m <...>
    module = args.cmd[0]
    rest = args.cmd[1:]
    cmd = [sys.executable, '-m', module] + rest
    return subprocess.call(cmd)

if __name__ == '__main__':
    raise SystemExit(main())
