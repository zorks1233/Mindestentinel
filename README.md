# Mindestentinel — Alpha

Mindestentinel ist ein modulares Python-Framework zur Entwicklung einer selbstlernenden KI-Plattform (Alpha) Build0015.3A.

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


# Mindestentinel - Autonome KI System (Build 0016A)

![Mindestentinel Logo](docs/mindestentinel_logo.png)

## Projektübersicht

Mindestentinel ist ein ambitioniertes Open-Source-Projekt zur Entwicklung einer autonomen, allgemeinen künstlichen Intelligenz (AGI), die sich selbstständig weiterentwickelt, Wissen aneignet und Fähigkeiten lernt - mit minimalem menschlichem Eingreifen. Die KI ist modular aufgebaut und folgt strengen Sicherheitsregeln, um verantwortungsvolle Entwicklung zu gewährleisten.

**Projektstatus**: Alpha Build 0016A (experimentell - NICHT für Produktionsumgebungen geeignet)

## Projektstruktur

```
Mindestentinel/
├── src/
│   ├── core/                  # Kernkomponenten der KI
│   │   ├── ai_engine.py       # Hauptorchestrator
│   │   ├── self_learning.py   # Autonome Lernschleifen
│   │   ├── knowledge_base.py  # Wissensdatenbank
│   │   ├── multi_model_orchestrator.py  # Koordination mehrerer LLMs
│   │   ├── rule_engine.py     # Sicherheitsregeln
│   │   ├── protection_module.py  # Schutzmechanismen
│   │   ├── model_manager.py   # Modellverwaltung
│   │   ├── system_monitor.py  # Systemüberwachung
│   │   └── autonomous_loop.py # Autonomer Lernzyklus (NEU)
│   ├── api/                   # API-Implementierungen
│   │   ├── rest_api.py        # REST-API Endpoints
│   │   └── websocket_api.py   # WebSocket-API
│   ├── cli/                   # Kommandozeilen-Schnittstelle
│   │   └── console.py         # Interaktive CLI
│   └── main.py                # Haupteinstiegspunkt
├── plugins/                   # Erweiterungs-Plugins
│   ├── __init__.py
│   ├── example_plugin.py
│   └── simulation_engine.py
├── config/                    # Konfigurationsdateien
│   ├── rules.yaml             # Sicherheitsregeln
│   └── default_config.json
├── data/                      # Datenverzeichnisse
│   ├── models/                # Geladene Modelle
│   ├── memory/                # Benutzerspezifische Speicher
│   ├── training/              # Trainingsdaten
│   └── knowledge/             # Wissensdatenbank
├── scripts/                   # Hilfsskripte
│   ├── install.sh             # Linux/macOS Installation
│   ├── install.bat            # Windows Installation
│   ├── start_mindest.sh       # Startskript Linux
│   ├── start_mindest.bat      # Startskript Windows
│   ├── sign_rules.py          # Regelsignatur-Tool
│   └── setup_env.py           # Umgebungskonfiguration
├── tests/                     # Unit-Tests
├── docs/                      # Dokumentation
├── requirements.txt           # Abhängigkeiten
├── LICENSE                    # MIT-Lizenz
├── README.md                  # Diese Datei
└── README-full.md             # Ausführliche Dokumentation
```

## Installation

### Voraussetzungen
- Python 3.10 oder höher
- Git (optional, für Source-Installation)
- Für Quantenintegration: Qiskit (optional)
- Für GPU-Beschleunigung: CUDA-kompatible GPU mit Treibern

### Schnellinstallation (empfohlen)

#### Linux/macOS
```bash
git clone https://github.com/zorks1233/Mindestentinel.git
cd Mindestentinel
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### Windows
```cmd
git clone https://github.com/zorks1233/Mindestentinel.git
cd Mindestentinel
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Alternative: Setup-Skript verwenden

#### Linux/macOS
```bash
curl -LO https://github.com/zorks1233/Mindestentinel/raw/main/scripts/setup_and_run.sh
chmod +x setup_and_run.sh
./setup_and_run.sh
```

#### Windows (PowerShell)
```powershell
Invoke-WebRequest -Uri "https://github.com/zorks1233/Mindestentinel/raw/main/scripts/setup_and_run.ps1" -OutFile "setup_and_run.ps1"
Set-ExecutionPolicy Bypass -Scope Process -Force
.\setup_and_run.ps1
```

#### Windows (CMD)
```cmd
curl https://github.com/zorks1233/Mindestentinel/raw/main/setup_and_run.bat -o setup_and_run.bat
setup_and_run.bat
```

## Konfiguration

### API-Schlüssel einrichten
Mindestentinel benötigt API-Schlüssel für externe Modelle (optional, aber empfohlen):

1. Erstellen Sie eine `.env`-Datei im Projekt-Root:
```env
MIND_API_KEY=IHR_OPENAI_API_SCHLÜSSEL
OLLAMA_API_BASE=http://localhost:11434
HUGGINGFACE_TOKEN=IHR_HF_TOKEN
```

2. Regeln anpassen (optional):
   - Bearbeiten Sie `config/rules.yaml` um die Sicherheitsregeln anzupassen
   - Verwenden Sie `scripts/sign_rules.py` um Regeln zu signieren:
   ```bash
   python scripts/sign_rules.py sign config/rules.yaml
   ```

## Verwendung

### Grundlegende Befehle

#### Starten der KI mit Standard-API
```bash
python src/main.py
```

#### Starten der REST-API (empfohlen)
```bash
python src/main.py --start-rest --api-port 8000
```

#### Starten der WebSocket-API
```bash
python src/main.py --start-ws --api-port 8765
```

#### Aktivieren des autonomen Lernzyklus
```bash
python src/main.py --start-rest --enable-autonomy --api-port 8000
```

### Installierte CLI-Befehle

Nach Installation mit `pip install -e .` stehen folgende Systembefehle zur Verfügung:

#### Benutzer-CLI (`mindest`)
```bash
# Interaktive Konsole starten
mindest console

# Chat mit der KI
mindest chat "Was ist der Sinn des Lebens?"

# Status der KI abfragen
mindest status

# Liste der verfügbaren Modelle anzeigen
mindest models list
```

#### Admin-CLI (`madmin`)
```bash
# Admin-Konsole starten
madmin console

# Regeln verwalten
madmin rules list
madmin rules add "new_rule_id" "prohibition" "Keine Selbstdestruktion" --priority 10
madmin rules verify

# Trainingsdaten verwalten
madmin training add data/training/sample.json
madmin training list
madmin training scan

# Benutzer verwalten (nur mit Admin-Rechten)
madmin users list
madmin users create --username admin --password securepassword --role admin
madmin users delete admin

# Sicherheitsprüfung durchführen
madmin security audit
```

### Interaktive CLI

Starten Sie die interaktive CLI mit:
```bash
python -m src.cli.console
```

In der CLI stehen folgende Befehle zur Verfügung:
```
> help
Verfügbare Befehle:
  - chat <Nachricht>: Chatte mit der KI
  - status: Zeigt den aktuellen Systemstatus
  - models: Liste der verfügbaren Modelle
  - rules: Zeigt die aktiven Sicherheitsregeln
  - autonomy on/off: Aktiviert/deaktiviert den autonomen Modus
  - exit: Verlässt die CLI

> chat Hallo, wie geht es dir?
KI: Hallo! Ich bin Mindestentinel, Build 0016A. Ich fühle mich gut, da mein autonomer Lernzyklus aktiv ist und ich kontinuierlich lerne.
```

## Autonomer Modus

Der autonome Modus ermöglicht es der KI, sich selbstständig weiterzuentwickeln. WICHTIG: Dies ist experimentell und sollte mit Vorsicht genutzt werden.

### Aktivierung
```bash
python src/main.py --enable-autonomy
# ODER in der interaktiven CLI:
> autonomy on
```

### Funktionsweise
1. **Zielgenerierung**: Die KI identifiziert Wissenslücken und setzt Lernziele
2. **Wissensakquisition**: Interaktion mit Lehrer-Modellen zur Datensammlung
3. **Knowledge Distillation**: Training lokaler Modelle mit gesammelten Daten
4. **Evaluierung**: Überprüfung des Lernerfolgs
5. **Integration**: Einbindung neuer Fähigkeiten in das System
6. **Reflexion**: Anpassung der Lernstrategie basierend auf Erfahrungen

### Konfiguration
Die Parameter des autonomen Lernzyklus können in `src/main.py` angepasst werden:
```python
autonomous_loop = AutonomousLoop(
    ai_engine=brain,
    knowledge_base=brain.knowledge_base,
    # ... andere Abhängigkeiten ...
    config={
        "max_learning_cycles": 1000,           # Maximale Anzahl von Lernzyklen
        "learning_interval_seconds": 1800,      # Intervall zwischen Lernzyklen (30 Minuten)
        "min_confidence_threshold": 0.65,       # Mindestzuverlässigkeit für Erfolg
        "max_resource_usage": 0.85,             # Maximale Ressourcennutzung
        "max_goal_complexity": 5,               # Maximale Zielkomplexität
        "safety_check_interval": 10             # Sicherheitsprüfungen alle 10 Zyklen
    }
)
```

## Sicherheit

Mindestentinel implementiert mehrere Sicherheitsmechanismen:

### Sicherheitsregeln
- Definiert in `config/rules.yaml`
- Regeln werden bei jeder Aktion überprüft
- Kritische Regeln haben höhere Priorität
- Regeln können signiert werden für Integrität

### Schutzmodule
- Systemintegritätsprüfung
- Ressourcenüberwachung
- Sicherheitsverletzungsprotokollierung
- Automatische Deaktivierung nach mehreren Verstößen

### Autonomie-Sicherheit
- Der autonome Lernzyklus führt vor jeder Aktion Sicherheitsprüfungen durch
- Nach 3 Sicherheitsverletzungen wird der autonome Modus automatisch deaktiviert
- Alle Änderungen werden protokolliert und können rückgängig gemacht werden

## Entwicklung

### Projektstruktur verstehen
- `src/core/`: Kernfunktionalität der KI
- `src/api/`: API-Implementierungen
- `plugins/`: Erweiterbarkeit durch Plugins
- `data/`: Persistente Daten

### Lokale Entwicklung
1. Aktivieren Sie die virtuelle Umgebung:
   ```bash
   source .venv/bin/activate  # Linux/macOS
   .venv\Scripts\activate     # Windows
   ```

2. Starten Sie die Entwicklungsumgebung:
   ```bash
   python src/main.py --no-start
   ```

3. Führen Sie Unit-Tests aus:
   ```bash
   python -m unittest discover -s tests -v
   ```

### Plugin-Entwicklung
1. Erstellen Sie ein neues Plugin in `plugins/`:
   ```python
   # plugins/my_plugin.py
   from src.core.plugin_interface import PluginInterface
   
   class MyPlugin(PluginInterface):
       def initialize(self, brain):
           print("MyPlugin initialized!")
           brain.register_command("mycommand", self.handle_command)
           
       def handle_command(self, args):
           return f"Command executed with args: {args}"
   ```

2. Laden Sie das Plugin automatisch:
   ```python
   # plugins/__init__.py
   from .my_plugin import MyPlugin
   ```

## Troubleshooting

### Häufige Probleme

#### ModuleNotFoundError
```bash
# Stellen Sie sicher, dass Sie sich im Projekt-Root befinden
export PYTHONPATH=$(pwd)  # Linux/macOS
set PYTHONPATH=%cd%        # Windows CMD
$env:PYTHONPATH = $PWD    # Windows PowerShell
```

#### API-Schlüssel-Fehler
- Überprüfen Sie, ob die `.env`-Datei korrekt erstellt wurde
- Stellen Sie sicher, dass die API-Schlüssel gültig sind
- Prüfen Sie die Netzwerkverbindung zu den API-Servern

#### Autonomie-Probleme
- Prüfen Sie die Logs in `logs/autonomy.log`
- Reduzieren Sie die Komplexität der Lernziele
- Erhöhen Sie das Lernintervall für mehr Stabilität

### Logs
- System-Logs: `logs/system.log`
- API-Logs: `logs/api.log`
- Autonomie-Logs: `logs/autonomy.log`
- Fehler-Logs: `logs/error.log`

## Roadmap

### Kurzfristig (Build 0017)
- Verbesserte Quantencomputing-Integration
- Erweiterte Sicherheitsaudits
- Benutzerfreundlichere Admin-Oberfläche
- Verbesserte Wissensverdichtung

### Mittelfristig (Build 0018-0020)
- Neuroevolution mit DEAP
- Transfer-Learning-Fähigkeiten
- Hybrid-Quantum-Integration
- Erweiterte Simulationen

### Langfristig (Build 0021+)
- Vollständige Autonomie mit menschlicher Aufsicht
- Selbstmodifizierender Code (mit Sicherheitsgitter)
- Erweiterte Multimodalität (Vision, Audio)
- Soziale Interaktionsfähigkeit

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz - siehe [LICENSE](LICENSE) für Details.

## Sicherheitshinweis

Dies ist eine experimentelle Alpha-Version. Bewahren Sie Sicherheitskopien von wichtigen Daten auf. Die autonomen Funktionen sind experimentell und sollten mit Vorsicht genutzt werden. Bei Sicherheitsproblemen erstellen Sie bitte ein Issue auf GitHub.

## Kontakt

Bei Fragen oder Unterstützung:
- GitHub Issues: https://github.com/zorks1233/Mindestentinel/issues
- Projekt-Cloud: https://cloud.projektsafe.net/index.php/s/XJZa9ZpJ8Tzci8M



