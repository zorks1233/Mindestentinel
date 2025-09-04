# setup.py (Projekt-Root)
from setuptools import setup, find_packages
setup(
    name="mindestentinel",
    version="0.0.1",
    packages=find_packages("src"),
    package_dir={"":"src"},
    entry_points={
        "console_scripts": [
            "mindest=main:cli_entrypoint",          # Beispiel
            "madmin=admin_console.console:main",    # Admin CLI
        ]
    }
)
