# Mindestentinel — Alpha

Mindestentinel ist ein modulares Python-Framework zur Entwicklung einer selbstlernenden KI-Plattform (Alpha).

## Quickstart

1. Python >= 3.12 (du hast 3.13.6) empfohlen.
2. Projektverzeichnis anlegen (du hast die Batch-Datei `setup_project.bat` genutzt).
3. Virtuelle Umgebung:
```bash
python -m venv .venv
# linux/mac
source .venv/bin/activate
# windows powershell
.venv\Scripts\Activate.ps1
Installiere Basis-Abhängigkeiten (siehe requirements.txt am Projektende).

Setze API-Key (für REST/WebSocket):

bash
Kopieren
Bearbeiten
export MIND_API_KEY="dein_secret"
# windows powershell:
setx MIND_API_KEY "dein_secret"
Starte den Service:

bash
Kopieren
Bearbeiten
# über python
python src/main.py --start-rest --api-port 8000
# oder über script (Linux)
./scripts/start_ai.sh
Ordnerstruktur (Alpha)
(siehe Projekt-Root, enthält src/, plugins/, data/, config/)

Wichtige Hinweise
Viele optionale Features (HuggingFace, FAISS, Qiskit, PennyLane, OpenCV, cryptography) sind optional — es gibt klare Fehlermeldungen, wenn Abhängigkeiten fehlen.

Die RuleEngine liest config/rules.yaml — passe dort deine Gesetze an (Admin).

ModelManager kann lokale HF-Modelle oder externe Plugins verwalten.

Entwicklung & Tests
bash
Kopieren
Bearbeiten
# venv aktivieren
python -m unittest discover -s tests
