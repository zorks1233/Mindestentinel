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

Detaillierte README für Mindestentinel-Projekt
 Mindestentinel- Vollständig überarbeitete README
 Projektübersicht
 Mindestentinel ist ein modulares Python-Framework zum Aufbau einer selbstlernenden KI
Plattform (AGI, Autonomes Lernen, Schwarmintelligenz/SI). Ziel von Mindestentinel ist die
 Bereitstellung einer flexiblen, skalierbaren und erweiterten Architektur zur Entwicklung, zum
 Experimentieren und zur Produktivsetzung fortschrittlicher KI-Systeme. Es legt einen
 besonderen Schwerpunkt auf eigenständiges Lernen, adaptives Verhalten, API-basierte
 Erweiterbarkeit und Community-Mitwirkung- mit dem übergeordneten Ziel, eine solide
 Ausgangsbasis zur Realisierung einer echten künstlichen allgemeinen Intelligenz (Artificial
 General Intelligence, AGI) zu schaffen.
 Inhalte der Plattform sind neben Methoden zum autonomen und verstärkenden Lernen
 zahlreiche Werkzeuge für Datenverwaltung, Konfiguration, Monitoring und automatisiertes
 Testen. Alle Komponenten sind darauf ausgelegt, einen hohen Grad an Modularität und
 Anpassbarkeit zu gewährleisten. Sowohl Forscher als auch Entwickler und interessierte
 Community-Mitglieder erhalten so die Möglichkeit, sich direkt am Fortschritt einer offenen AGI
Forschung und-Entwicklung zu beteiligen, eigene Erweiterungen beizusteuern und
 Mindestentinel als Basis für eigene Projekte einzusetzen.
 Features auf einen Blick:
 ▪ Frei kombinierbare, klar getrennte Module für Daten, Lernen, APIs, Evaluation, etc.
 ▪ Flexibles Konfigurationssystem (YAML, ENV, Aufrufparameter)
 ▪ Fähigkeit zum autonomen Lernen über verschiedene Ansätze (inkl.
 Schwarmmechanismen/SI)
 ▪ REST-API und CLI-Schnittstelle für die Integration in andere Systeme
 ▪ Umfassender Test- und Experimentier-Workflow auf Basis von pytest
 ▪ Strukturierte Architektur für Skalierbarkeit und Community-Extensibilität
 1.
 Inhaltsverzeichnis
 ▪ Projektübersicht
 ▪ Projektstruktur & Architektur
 ▪ Installation & Abhängigkeiten
 ▪ Erste Schritte und Quickstart
 1
 Copilot may make mistakes
▪ Nutzung&Startbefehle
 ▪ Wichtige Module und Kernfunktionen
 ▪ API-Spezifikation
 ▪ Konfiguration & Umgebungsvariablen
 ▪ Erweiterungen & optionale Features
 ▪ Selbstlernende KI-Komponenten
 ▪ Testframework & Testanleitungen
 ▪ Beispielanwendungen
 ▪ Mitwirken & Community-Richtlinien
 ▪ Lizenz und rechtliche Hinweise
 1.
 Projektstruktur & Architektur
 Die Architektur von Mindestentinel basiert auf den Prinzipien modularen, objektorientierten
 Designs und folgt etablierten Entwurfsmustern, um Flexibilität, Wartbarkeit und Erweiterbarkeit
 zu gewährleisten[2]. Die Projektverzeichnisstruktur ist logisch gegliedert, um eine klare Trennung
 von Kernfunktionen, Nutzungsschnittstellen, Konfiguration und Test zu schaffen.
 Projektverzeichnisstruktur
 Die typische Projektstruktur gliedert sich wie folgt:
 Mindestentinel/
 api/ # REST-API und API-Logik
 config/ # Standard-Konfigurationsdateien (YAML, JSON, ENV)
 core/ # Zentrale Komponenten (KI-Algorithmen, Agenten, Schwarm-Logik)
 data/ # Datenmanagement, Datensätze, Preprocessing, Persistenz
 extensions/ # Erweiterungs- und Plug-in-System
 tests/ # Unit-Tests, Integrations- und Systemtests (pytest)
 utils/ # Hilfsfunktionen, Werkzeuge, Logging, Monitoring
 scripts/ # CLI-Kommandos und Hilfsskripte
 requirements.txt # Python-Abhängigkeiten (pip-kompatibel)
 2
 Copilot may make mistakes
main.py # Einstiegspunkt für den Start als Anwendung
 README.md #Dokumentation (dieses Dokument)
 Hinweise zur Struktur:
 ▪ DieTrennungder Module ist konsequent. Erweiterungen (z.B. für API, UI oder spezielle
 Algorithmen) werden in extensions/ abgelegt, sodass Upgrades und Feature-Add-ons einfach
 möglich sind.
 ▪ Konfigurationsdateien können sowohl lokal im Projekt (config/) als auch global im System
 platziert werden und unterstützen verschiedene Formate (insb. YAML, ENV).
 ▪ Alle Skripte und CLIs befinden sich in scripts/ für einen schnellen Zugriff und automatisierte
 Prozesse.
 ▪ Diezentrale Kernintelligenz und Lernlogik findet sich im core/-Verzeichnis.
 1.
 Mit diesem Aufbau wird das Prinzip einer klaren, nutzerorientierten Projekthierarchie
 umgesetzt, die sowohl für Einzelentwickler als auch für größere Teams geeignet ist[4][5].
 Installation & Abhängigkeiten
 Voraussetzungen
 ▪ Python3.8oderneuer(empfohlen: 3.10+)
 ▪ Unterstützung für UNIX- und Windows-Plattformen (getestet auf Ubuntu 22.04 LTS, Windows
 10/11)
 ▪ Empfohlen: Virtuelle Umgebung für isolierte Installation (venv oder virtualenv)[7]
 1.
 Installation über pip
 Das Projekt folgt den Python-Standards für Distribution und kann direkt via pip installiert
 werden.
 Schnellstart mit virtueller Umgebung:
 # 1. Virtuelle Umgebung anlegen (empfohlen)
 python3-m venv .venv
 # oder: python-m venv .venv (unter Windows)
 # 2. Aktivieren der Umgebung
 source .venv/bin/activate # Linux/MacOS
 .\.venv\Scripts\activate # Windows
 # 3. Projekt klonen
 git clone https://github.com/zorks1233/Mindestentinel.git
 3
 Copilot may make mistakes
cd Mindestentinel
 # 4. Abhängigkeiten installieren
 pip install-r requirements.txt
 Hinweis: Wenn die Standard-Module bereits installiert sind, können auch einzelne Module
 installiert oder aktualisiert werden. Bei Bedarf können Minimum- und Maximum-Versionen wie
 folgt gesetzt werden:
 numpy>=1.18,<1.25
 requests~=2.31
 (im requirements.txt gemäß [PEP 440] und Pip-Syntax)[8]
 Alle Standardabhängigkeiten beinhalten (Stand: Oktober 2025):
 Paket
 numpy
 pandas
 scikit-learn
 requests
 pyyaml
 fastapi
 pytest
 uvicorn
 loguru
 Typ
 Basis-Lib
 Basis-Lib
 ML-Framework
 HTTP/Netzwerk
 Konfiguration
 Web-API
 Test
 ASGI-Server
 Logging
 Zweck
 Numerische Berechnungen, Vektoroperationen
 Datenmanipulation und-analyse
 Klassische Algorithmen, Preprocessing
 REST-Kommunikation, Datenabruf
 YAML-basierte Konfigs einlesen/schreiben
 REST-Endpunkte und API-Definitionen
 Unit- und System-Testing
 FastAPI-Server für API
 Fortgeschrittenes Logging/Monitoring
 Je nach Bedarf können zusätzliche Pakete (z. B. für Deep Learning, wie TensorFlow oder PyTorch)
 integriert werden.
 Erste Schritte und Quickstart
 1. Initiale Konfiguration generieren
 Beim ersten Start kann das Setup die Grundkonfiguration (YAML) erzeugen:
 python main.py--init-config
 2. Projekt starten (CLI-Modus):
 Für den Standardbetrieb via Kommandozeile und API:
 python main.py--mode=train--config=config/default.yaml
 Optionen wie Modus (train, inference, api), Konfig-Datei und Log-Level sind individuell
 einstellbar.
 3. REST-API lokal starten
 4
 Copilot may make mistakes
# Start via Uvicorn (FastAPI)
 uvicorn api.main:app--reload
 Standardmäßig erreichbar unter http://localhost:8000.
 4. Testlauf (Unit-/Integrationstests):
 pytest tests/
 Dies prüft alle Kernfunktionen sowie Integrität von Daten- und Lernmodulen.
 Nutzung & Startbefehle (CLI)
 Die Steuerung von Mindestentinel erfolgt über ein zentrales CLI (Command Line Interface)
 und/oder GUI (bei Integration entsprechender Erweiterungen).
 Allgemeiner Aufruf:
 python main.py [OPTIONS]
 Wichtige Parameter:
 Parameter--mode--config--api-port--log-level--init-config--help
 Beispiel:
 Bedeutung
 Ausführungsmodus (train, inference,
 api)
 Pfad zur Konfigurationsdatei
 Port für die API
 Logging-Verbosity
 Erstellt eine neue Basis-Konfiguration
 Hilfestellung anfordern
 Beispiel--mode=train--config=config/custom.yaml--api-port=8080--log-level=DEBUG--init-config--help
 python main.py--mode=api--config=config/demo.yaml--api-port=9090
 Das System wird samt REST-API mit den Parametern aus "demo.yaml" unter Port 9090
 bereitgestellt.
 Wichtige Module und Kernfunktionen
 Die Funktionalität von Mindestentinel ist in logisch getrennte, wiederverwendbare Python
Module gegliedert[10][11]. Hier ein Überblick über die wichtigsten Komponenten:
 Kernmodule (core/)
 ▪ Agenten&Schwarm-Intelligenz: Klassen, Funktionen zu Multi-Agenten-Systemen,
 Schwarmmechanismen, emergentes Verhalten ("Swarm Coordination", "Agent",
 "CollectiveLearning").
 5
 Copilot may make mistakes
▪ Lernalgorithmen: Implementierungen klassischer wie fortgeschrittener Verfahren: Q
Learning, Deep RL, Genetische Algorithmen, Clustering, Ensemble-Techniken.
 ▪ Datenmanagement:Verwaltung, Preprocessing, Persistenz und Wiederherstellung von
 Trainings- und Testdaten. Schnittstellen zu lokalen Datenspeichern, S3 oder Datenbank
Backends.
 ▪ Evaluation: Vergleich und Auswertung verschiedener Ansätze (Metriken, Cross Validation,
 Reward-Bewertung).
 1.
 REST-API (api/)
 ▪ FastAPI-basierte REST-Schnittstelle: Endpunkte zum Trainieren, Steuern und Beobachten
 von Agenten, Statusabfrage, Datenimport/-export.
 ▪ API-Modelle: Standardisierte Schemata für Requests/Responses (OpenAPI 3).
 ▪ Authentifizierung: Token-basierte Security, API-Key-Support (optional).
 1.
 Erweiterungen (extensions/)
 ▪ Plug-in-System: API für neue Datenquellen, zusätzliche Algorithmen oder UI-Elemente.
 ▪ Third-Party-Integrationen: Anbindung an externe Monitoring-Tools, Metrikdienste,
 Messaging-Anbieter.
 1.
 Hilfsfunktionen (utils/)
 ▪ Logging&Monitoring: Erweiterte Logausgaben, Performance- und Status-Tracking.
 ▪ Fehlerbehandlung: Exception-Handling, strukturierte Rückmeldungen.
 ▪ Werkzeuge:Datenvalidierung, Schnittstellen- und Formatstandardisierung.
 1.
 Tests (tests/)
 ▪ pytest-kompatible Unit- und Feature-Tests: Automatisiertes Testen nahezu aller
 Kernmodule und Workflow-Szenarien.
 1.
 API-Spezifikation
 Mindestentinel stellt eine eigene, OpenAPI-kompatible REST-Schnittstelle bereit[13][14].
 Endpunkte (Beispiele)
 Methode
 POST
 Pfad
 /api/agent/train
 Beschreibung
 Starte Trainingslauf mit übergebenen
 Parametern
 6
 Copilot may make mistakes
GET
 /api/agent/status
 POST
 GET
 /api/data/import
 /api/evaluate/results
 Statusabfrage (Trainingsfortschritt,
 Agentenzustand)
 Aufnahme und Validierung neuer
 Trainingsdaten
 Abfrage von Evaluationsergebnissen
 Beispielanfrage zum Starten eines Trainings:
 POST /api/agent/train HTTP/1.1
 Content-Type: application/json
 {
 "episodes": 1000,
 "env": "CartPole",
 "learning_rate": 0.001,
 "reward_threshold": 450
 }
 Die API-Dokumentation ist automatisch verfügbar (in FastAPI über /docs erreichbar).
 Eigene Endpunkte hinzufügen: Durch das Plug-in-System können Teams neue Schnittstellen
 als Python-Modul bereitstellen, welche über ein API-Register dynamisch eingebunden werden.
 Authentifizierung
 Standardmäßig ist die API offen für die lokale Entwicklung. Für den Produktivbetrieb muss
 Authentifizierung (Token, API-Key) ausdrücklich aktiviert und konfiguriert werden.
 Konfiguration & Umgebungsvariablen
 Mindestentinel nutzt ein flexibles, mehrstufiges Konfigurationssystem, das Werte aus YAML
Dateien, ENV-Variablen und zur Laufzeit via CLI einlesen und überschreiben kann.
 Typische Konfigurationsdatei (YAML):
 # config/default.yaml
 api:
 port: 8000
 auth_mode: "api-key"
 log_level: "info"
 learning:
 episode_count: 1000
 batch_size: 32
 optimizer: "adam"
 learning_rate: 0.001
 7
 Copilot may make mistakes
reward_threshold: 450
 env:
 name: "CartPole"
 seed: 42
 Parameter sind im CLI wie folgt überschreibbar:
 python main.py--config=config/custom.yaml--log-level=DEBUG
 Umgebungsvariablen
 Häufig genutzte Parameter (API-Key, Datenbank-Passwörter, Betriebsmodi) dürfen explizit
 durch ENV-Variablen gesetzt werden. Typisch:
 ▪ MINDESENTINEL_CONFIG_PATH
 ▪ MINDESENTINEL_API_KEY
 ▪ MINDESENTINEL_DATA_DIR
 1.
 Systematische Namensgebung und zentrale Ablage werden empfohlen, um Sicherungen,
 Containerisierung und Cloud-Deployment zu vereinfachen[16].
 Erweiterungen & optionale Features
 Mindestentinel ist auf Erweiterbarkeit und Anpassbarkeit ausgelegt. Neben den Kernmodulen
 können zusätzliche Features als Plug-in-Pakete in das Verzeichnis extensions/ eingebunden
 werden.
 Beispiele für optionale Features:
 ▪ NeueLernalgorithmen: Einbinden zusätzlicher Algorithmen als eigenes Python-Modul,
 Integration über Factory-Pattern.
 ▪ UI/Visualisierung: Integration von Dashboards (bspw. mit Streamlit oder Dash), um
 Trainingsfortschritt grafisch darzustellen.
 ▪ Cloud-Deployment: Automatische Bereitstellung auf Azure, Google Cloud, AWS über
 Deployment-Skripte.
 ▪ Benutzerdefinierte Datenquellen: Anbindung externer APIs oder Datenbanken für
 Input/Output.
 1.
 Aktivierung: Erweiterungen werden in der Konfigurationsdatei gelistet- sodass diese beim
 Systemstart automatisch geladen werden.
 Beispiel (YAML):
 extensions:- name: "custom_optimizer"
 path: "extensions/optimizers/adamw.py"
 auto_activate: true
 8
 Copilot may make mistakes
Dies vereinfacht auch Projekt- und Team-spezifische Konfigurationen.
 Selbstlernende KI-Komponenten & Algorithmen
 Ein zentraler Fokus von Mindestentinel liegt auf dem Bereich des autonomen, verstärkenden
 sowie kollektiven Lernens[18][19]. Das Framework erlaubt Forschern und Entwicklern,
 verschiedene Paradigmen experimentell zu vergleichen und zu kombinieren.
 Funktionale KI-Elemente im Überblick:
 ▪ Agentenmodellierung: Implementierungen für einzelne und multiple Agenten mit
 orchestriertem Schwarmverhalten.
 ▪ Lernstrategien: Unterstützung für Value-based, Policy-based und Evolutionäre Algorithmen.
 ▪ Selbstadaptation: Automatische Modellauswahl und Hyperparameter-Tuning (z.B. durch
 RandomSearch, Grid Search, Reinforcement Learning selbst).
 ▪ Schwarmintelligenz (SI): Mechanismen zur Informationsverteilung, kollektivem
 Belohnungslernen und konsensbasierten Entscheidungsprozessen.
 1.
 Weiterhin werden best practices für die Entwicklung solcher Systeme direkt im Framework
 abgebildet, wie etwa:
 ▪ Kapselung des Agentenverhaltens
 ▪ API-basierte Überwachung und Steuerung
 ▪ Isolierung von Trainings- und Testdaten
 ▪ LoggingundReproduzierbarkeit von Experimenten
 1.
 Testframework & Testanleitungen
 Softwarequalität ist ein integraler Bestandteil von Mindestentinel. Dafür wird umfassend auf das
 populäre Python-Testframework [pytest] gesetzt[21].
 Teststrategie
 ▪ Unit-Tests: Einzelne Funktionen und Klassen werden auf Korrektheit, Stabilität und
 Fehlerrobustheit geprüft.
 ▪ Integrationstests: Zusammenspiel von Komponenten (z.B. Agent ↔ Datenmanager ↔ API)
 wird automatisiert evaluiert.
 ▪ APITests: REST-Endpoints werden mit Beispieldaten getestet (u.a. Response-Validierung,
 Fehler-Handling).
 ▪ Systemtests: End-to-End-Tests beliebiger Konfigurationen, auch in verschiedenen
 Umgebungen (lokal, Docker, CI/CD).
 1.
 Testbefehle:
 9
 Copilot may make mistakes
pytest # führt alle Tests aus
 pytest-k "test_agent" # führt Tests zu Agentenmodulen aus
 pytest--cov=core # misst und reportet die Testabdeckung
 Eigene Tests einbinden: Neue Features müssen mit mindestens einem Test-Skript im tests/
Verzeichnis geliefert werden. Pytest erkennt und integriert diese automatisch anhand der
 Namenskonvention (Prefix/Suffix test_).
 Hinweise für Contributors:
 ▪ Schreibe reproduzierbare Beispielanwendungen für neue Features.
 ▪ Liefere möglichst ein vollständiges, minimales Beispiel mit, welches die Nutzung verdeutlicht
 [22].
 1.
 Beispielanwendungen & Quickstart
 UmdenEinstieg zu erleichtern, sind in examples/ Musterprojekte enthalten, die verschiedene
 Kernfunktionen demonstrieren:
 Beispiellauf- Klassisches AGI-Szenario
 python main.py--mode=train--config=examples/cartpole_config.yaml
 Hierbei wird ein Standard-Environment (z.B. CartPole) mithilfe von Q-Learning trainiert und die
 Entwicklung des Agenten aufgezeichnet.
 REST-API-Demo
 uvicorn api.main:app--reload
 Besuche anschließend [http://localhost:8000/docs] um interaktiv Endpunkte zu testen.
 Mitwirken & Community-Richtlinien
 Mindestentinel ist ein Open-Source-Projekt und ausdrücklich auf eine aktive Community
 angewiesen.
 Mitwirkungsmöglichkeiten:
 ▪ Feature-Entwicklung: Implementiere neue Module (z.B. Agent-Arten, Optimierer), reiche Plug
ins ein.
 ▪ Bugfixes: Melde und behebe Fehler, verbessere bestehende Komponenten.
 ▪ Dokumentation: Pflege und erweitere README, Add-ons, Tutorials, API-Beschreibungen.
 ▪ Diskussion: Nutze und leite Issues auf GitHub, nimm an Community-Calls teil.
 1.
 10
 Copilot may make mistakes
Beiträge einreichen (Contribution Guide):
 1. Fork auf GitHub →neuenBranch anlegen (z.B. feature/optimization-x)
 2. Feature/Verbesserung implementieren
 3. Passende Unit- und/oder Integrationstests schreiben
 4. Dokumentation (README & ggf. API/Examples) aktualisieren
 5. Pull Request (PR) mit Beschreibung und Referenz zu ggf. betroffenen Issues öffnen
 1.
 Hinweise:
 ▪ Haltedich an die Coding-Standards (PEP8 u.a.)
 ▪ Schreibe lesbare, modularisierte und testbare Funktionen/Klassen
 ▪ Definiere in PRs klar, welche Änderungen vorgenommen wurden (Change-Log)
 ▪ Ermutige Reviewer explizit zu Feedback und Verbesserungsvorschlägen
 1.
 Empfehlung: Ziehe stets vor PR-Abschicken den Hauptstand (main-Branch) und führe
 automatisch alle Tests aus.
 Lizenz und rechtliche Hinweise
 Mindestentinel wird unter der MIT-Lizenz bereitgestellt:
 MIT License
 Copyright (c) [aktuelles Jahr] [zorks1233]
 Hiermit wird unentgeltlich jeder Person, die eine Kopie der Software und der zugehörigen
 Dokumentationsdateien erhält, die Erlaubnis erteilt, uneingeschränkt mit der Software zu
 arbeiten, einschließlich uneingeschränkter Rechte zur Nutzung, Kopie, Änderung,
 Zusammenführung, Veröffentlichung, Verteilung, Unterlizenzierung und/oder zum Verkauf von
 Kopien der Software, unter den folgenden Bedingungen:
 [...]
 Bitte lies die ausführliche Lizenz im LICENSE-File im Projektverzeichnis.
 Achtung: Die Nutzung von Mindestentinel und sämtlicher Erweiterungen erfolgt auf eigene
 Verantwortung. Für Schäden, Fehlfunktionen, Datenverluste oder sicherheitsrelevante Aspekte
 übernimmt der Urheber keine Haftung. Für Aspekte der KI-Ethik, Datenschutz und
 verantwortungsbewusste KI-Nutzung wird ausdrücklich auf die Einhaltung entsprechender
 gesetzlicher und gesellschaftlicher Normen verwiesen.
 Fragen, Vorschläge oder Feedback?
 Nutze Issues im GitHub-Repository oder kontaktiere das Entwicklerteam über die im Profil
 hinterlegten Kanäle.
 Viel Erfolg und Freude beim Entwickeln, Forschen, Testen und Mitwirken mit Mindestentinel!
 11
 Copilot may make mistakes
References (22)
 1. Whento Use Which Design Pattern?- GeeksforGeeks. https://www.geeksforgeeks.org/system
design/design-patterns-cheat-sheet-when-to-use-which-design-pattern/
 2. Ideale Ordnerstruktur: Dateiablage mit dem 7-Ordner-System. https://www.buero
kaizen.de/ordnerstruktur/
 3. Verzeichnisstruktur- Wikipedia. https://de.wikipedia.org/wiki/Verzeichnisstruktur
 4. venv & virtualenv: Virtual Environments in Python erklärt.
 https://www.computerwoche.de/article/2826499/virtual-environments-in-python
erklaert.html
 5. Howto pip install a package with min and max version range?.
 https://stackoverflow.com/questions/8795617/how-to-pip-install-a-package-with-min-and
max-version-range
 6. start . https://learn.microsoft.com/de-de/windows-server/administration/windows
commands/start
 7. Python Module Tutorial: Sie importieren, schreiben und verwenden- DataCamp.
 https://www.datacamp.com/de/tutorial/modules-in-python
 8. Online API Dokumentation erstellen: Der komplette Leitfaden.
 https://apidog.com/de/blog/online-api-documentation-guide-de/
 9. RESTful APIs dokumentieren- so geht’s!- API Conference. https://apiconference.net/blog/restful
apis-dokumentieren-so-gehts/
 10.Config-Dateien in Linux bearbeiten- so geht's- PC-WELT.
 https://www.pcwelt.de/article/1177812/know-how-konfigurationsdateien-unter-linux.html
 11.Machine Learning Architekturen für Entscheidende. https://digitales-kompetenzzentrum
stuttgart.de/wp-content/uploads/2022/03/Leitfaden-Machine_Learning_Architekturen.pdf
 12.Lernerautonomie- Wikipedia. https://de.wikipedia.org/wiki/Lernerautonomie
 13.Pytest Tutorial- Unit Testing in Python using Pytest Framework.
 https://www.geeksforgeeks.org/python/pytest-tutorial-testing-python-application-using
pytest/
 14.How to create a Minimal, Reproducible Example- Help Center.
 https://stackoverflow.com/help/minimal-reproducible-example
 12
 Copilot may make mistakes
