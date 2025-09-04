# admin_console/commands/manage_training.py
import argparse
from pathlib import Path
import shutil

TRAIN_DIR = Path('training_data')
TRAIN_DIR.mkdir(parents=True, exist_ok=True)

def main():
    p = argparse.ArgumentParser(prog='manage_training')
    sub = p.add_subparsers(dest='cmd')
    sub_list = sub.add_parser('list')
    sub_add = sub.add_parser('add')
    sub_add.add_argument('file', help='Path to file to add to training_data')
    sub_rm = sub.add_parser('remove')
    sub_rm.add_argument('name', help='Filename in training_data')
    sub_clear = sub.add_parser('clear')
    args = p.parse_args()
    if args.cmd == 'list':
        for f in TRAIN_DIR.iterdir():
            print(f.name)
    elif args.cmd == 'add':
        src = Path(args.file)
        if not src.exists():
            print('Source file not found')
            return
        dest = TRAIN_DIR / src.name
        shutil.copy2(src, dest)
        print('Added', dest)
    elif args.cmd == 'remove':
        t = TRAIN_DIR / args.name
        if t.exists():
            t.unlink()
            print('Removed', args.name)
        else:
            print('Not found')
    elif args.cmd == 'clear':
        for f in TRAIN_DIR.iterdir():
            f.unlink()
        print('Cleared training_data')
    else:
        p.print_help()

if __name__ == '__main__':
    main()
