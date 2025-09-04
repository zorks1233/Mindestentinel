# README Full — Mindestentinel Build0015A (detailliert)

Diese Datei enthält die detaillierten Änderungen, Installationshinweise, Admin-Befehle und die Roadmap.

## Änderungen / neue Module
- core/rule_engine.py: HMAC-signature support and enforcement toggle.
- admin_console/commands/manage_rules.py: list/add/sign/verify rules
- admin_console/commands/manage_training.py: manage training_data folder
- scripts/sign_rules.py: sign/verify rules file using HMAC-SHA256
- training_data/: folder for training datasets
- scripts/bootstrap_install.py: helper to check/install Python 3.13.6 or provide platform hints
- setup.py & src/entrypoints: provide `mindest` and `madmin` CLI shortcuts when installed editable.

## Installation (Kurz)
1. Unzip full project.
2. Create and activate virtualenv, install requirements: `python -m pip install -r requirements.txt`
3. (Optional) `pip install -e .` to install entrypoints
4. Sign rules: `python scripts/sign_rules.py sign`
5. Start system: `python -m src.main --start-rest --api-port 8000`

## Admin-CLI Beispiele
- `python -m admin_console.commands.manage_rules list`
- `python -m admin_console.commands.manage_rules add --id myrule --action "do.x" --type prohibition --message "..."`
- `python -m admin_console.commands.manage_training add mydata.csv`
- `python -m admin_console.commands.manage_users create --username benni --password "..." --admin`

## Sicherheit & Empfehlungen
- Backups von config/, training_data/ und models/ sind wichtig.
- Signiere die Regeln, aktiviere enforcement in Produktionsumgebung.
- Audit logs für Admin-Commands einrichten (kann ergänzt werden).

## Roadmap (Vorschläge)
- Integrate sign-enforcement in src/main on startup
- Add role-based access control for admin_console
- Add interactive KI-only REPL sandbox with permission checks


---
build: build0016A
date: 2025-08-23
summary:
  - Added admin CLI commands: manage_rules, manage_training, manage_roles
  - Added integrity signature check at startup (config/signatures.json)
  - Added scripts/bootstrap_install.py to facilitate Python 3.13.6 setup (download stubs)
  - Added training data folder management via admin CLI
  - Updated project structure and documentation

