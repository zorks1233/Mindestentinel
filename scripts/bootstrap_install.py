#!/usr/bin/env python3
"""
scripts/bootstrap_install.py
Checks for Python 3.13.6 and provides instructions / download stubs.
This script does NOT automatically install system Python without privileges.
It downloads installers to ./installers if possible.
"""
import sys, os, platform, subprocess, urllib.request, shutil

TARGET_VERSION = (3,13,6)

def python_version_ok():
    v = sys.version_info
    return (v.major, v.minor, v.micro) >= TARGET_VERSION

def download(url, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    try:
        print("Downloading:", url)
        urllib.request.urlretrieve(url, dest)
        print("Saved to", dest)
        return True
    except Exception as e:
        print("Download failed:", e)
        return False

def main():
    print("Bootstrap installer for Mindestentinel (build0016A)")
    if python_version_ok():
        print("Python version OK:", sys.version)
        return 0
    print("Detected Python:", sys.version)
    system = platform.system().lower()
    installers_dir = os.path.join(os.getcwd(), 'installers')
    os.makedirs(installers_dir, exist_ok=True)
    if system == 'windows':
        url = "https://www.python.org/ftp/python/3.13.6/python-3.13.6-amd64.exe"
        dest = os.path.join(installers_dir, 'python-3.13.6-amd64.exe')
        download(url, dest)
        print("Please run the downloaded installer as Administrator to install Python 3.13.6.")
    elif system == 'linux':
        url = "https://www.python.org/ftp/python/3.13.6/Python-3.13.6.tgz"
        dest = os.path.join(installers_dir, 'Python-3.13.6.tgz')
        download(url, dest)
        print("Extract and build from source, e.g.: tar xzf Python-3.13.6.tgz && cd Python-3.13.6 && ./configure && make -j && sudo make altinstall")
    elif system == 'darwin':
        url = "https://www.python.org/ftp/python/3.13.6/python-3.13.6-macos11.pkg"
        dest = os.path.join(installers_dir, 'python-3.13.6-macos11.pkg')
        download(url, dest)
        print("Open the downloaded .pkg to install Python 3.13.6.")
    else:
        print("Unsupported system:", system)
    return 0

if __name__ == '__main__':
    main()
