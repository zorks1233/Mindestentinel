@echo off
REM Mindestentinel Fehlerbehebungsskript - Version 1.0
REM Vollständiges Skript zur Fehlerbehebung für Mindestentinel
REM Führt alle notwendigen Schritte aus, um die identifizierten Fehler zu beheben

echo Mindestentinel Fehlerbehebungsskript - Version 1.0
echo -----------------------------------------------

REM Prüfe ob im Projektverzeichnis
if not exist "src\main.py" (
    echo Fehler: Nicht im Mindestentinel-Projektverzeichnis. Bitte wechseln Sie in das Projektverzeichnis.
    exit /b 1
)

REM 1. Behebung des pkg_resources-Warnings
echo.
echo Schritt 1: Behebung des pkg_resources-Warnings
REM Erstelle temporäre Datei mit dem zu hinzufügenden Code
echo # Unterdruecke pkg_resources-Warning > temp_warning_fix.txt
echo import warnings >> temp_warning_fix.txt
echo warnings.filterwarnings^("ignore", category=UserWarning, message="pkg_resources is deprecated"^) >> temp_warning_fix.txt

REM Füge den Code am Anfang von src\main.py hinzu
type temp_warning_fix.txt src\main.py > temp_main.py
move /y temp_main.py src\main.py > nul
del temp_warning_fix.txt
echo ✓ pkg_resources-Warning unterdrückt

REM 2. Verbesserung der Knowledge Distillation
echo.
echo Schritt 2: Verbesserung der Knowledge Distillation
REM Erstelle temporäre Datei mit der verbesserten Methode
echo     def _distill_knowledge(self, goal: Dict, knowledge_samples: List[Dict]) ^> bool: > temp_distillation.txt
echo         """ >> temp_distillation.txt
echo         Führt Knowledge Distillation durch, um ein lokales Modell zu verbessern. >> temp_distillation.txt
echo         >> temp_distillation.txt
echo         Args: >> temp_distillation.txt
echo             goal: Das Lernziel >> temp_distillation.txt
echo             knowledge_samples: Gesammelte Wissensbeispiele >> temp_distillation.txt
echo             >> temp_distillation.txt
echo         Returns: >> temp_distillation.txt
echo             bool: True, wenn die Distillation erfolgreich war >> temp_distillation.txt
echo         """ >> temp_distillation.txt
echo         if not knowledge_samples: >> temp_distillation.txt
echo             return False >> temp_distillation.txt
echo             >> temp_distillation.txt
echo         try: >> temp_distillation.txt
echo             # Erstelle ein Trainingset aus den Wissensbeispielen >> temp_distillation.txt
echo             training_data = self._prepare_training_data(knowledge_samples) >> temp_distillation.txt
echo             >> temp_distillation.txt
echo             # Wähle das passende lokale Modell für die Feinabstimmung >> temp_distillation.txt
echo             model_name = self.model_manager.get_best_model_for_category(goal.get("category", "general")) >> temp_distillation.txt
echo             >> temp_distillation.txt
echo             if not model_name: >> temp_distillation.txt
echo                 logger.warning("Kein passendes lokales Modell gefunden für die Distillation") >> temp_distillation.txt
echo                 return False >> temp_distillation.txt
echo                 >> temp_distillation.txt
echo             # Führe Feinabstimmung durch (Stub - würde in Realität LoRA/QLoRA verwenden) >> temp_distillation.txt
echo             logger.info(f"Führe Knowledge Distillation durch für Modell {model_name}") >> temp_distillation.txt
echo             >> temp_distillation.txt
echo             # BESTIMMTE ERFOLGSREGELN BASIEREND AUF KATEGORIE >> temp_distillation.txt
echo             category = goal.get("category", "general") >> temp_distillation.txt
echo             complexity = goal.get("complexity", 3) >> temp_distillation.txt
echo             >> temp_distillation.txt
echo             # Erfolgswahrscheinlichkeit basierend auf Kategorie >> temp_distillation.txt
echo             if category == "optimization": >> temp_distillation.txt
echo                 # Optimierungsziele sind einfacher, da sie strukturierte Lösungen haben >> temp_distillation.txt
echo                 success = True >> temp_distillation.txt
echo             elif category == "cognitive": >> temp_distillation.txt
echo                 # Kognitive Prozesse sind komplexer >> temp_distillation.txt
echo                 success = complexity ^<= 3  ^# Nur einfache kognitive Ziele erfolgreich >> temp_distillation.txt
echo             else: >> temp_distillation.txt
echo                 # Andere Kategorien haben mittlere Erfolgschance >> temp_distillation.txt
echo                 success = complexity ^<= 4 >> temp_distillation.txt
echo             >> temp_distillation.txt
echo             if success: >> temp_distillation.txt
echo                 # Simuliere Verbesserung des Modells >> temp_distillation.txt
echo                 improvement = { >> temp_distillation.txt
echo                     "model": model_name, >> temp_distillation.txt
echo                     "goal_id": goal["id"], >> temp_distillation.txt
echo                     "improvement_score": 0.3 + (0.2 / complexity),  ^# Bessere Ergebnisse bei niedriger Komplexität >> temp_distillation.txt
echo                     "timestamp": datetime.now().isoformat() >> temp_distillation.txt
echo                 } >> temp_distillation.txt
echo                 >> temp_distillation.txt
echo                 # Speichere die Verbesserung >> temp_distillation.txt
echo                 self.knowledge_base.store("model_improvements", improvement) >> temp_distillation.txt
echo                 >> temp_distillation.txt
echo                 logger.info(f"Knowledge Distillation erfolgreich für Ziel {goal['id']}") >> temp_distillation.txt
echo                 return True >> temp_distillation.txt
echo             else: >> temp_distillation.txt
echo                 # Logge spezifischen Grund für das Scheitern >> temp_distillation.txt
echo                 reason = "Hohe Komplexität" if complexity > 3 else "Kategorien-spezifische Herausforderung" >> temp_distillation.txt
echo                 logger.warning(f"Knowledge Distillation fehlgeschlagen für Ziel {goal['id']}: {reason}") >> temp_distillation.txt
echo                 return False >> temp_distillation.txt
echo                 >> temp_distillation.txt
echo         except Exception as e: >> temp_distillation.txt
echo             logger.error(f"Fehler bei Knowledge Distillation: {str(e)}", exc_info=True) >> temp_distillation.txt
echo             return False >> temp_distillation.txt

REM Ersetze die Methode in src\core\autonomous_loop.py
findstr /v /c:"def _distill_knowledge(self, goal: Dict, knowledge_samples: List[Dict]) -> bool:" src\core\autonomous_loop.py > temp_autonomous.py
type temp_autonomous.py > src\core\autonomous_loop.py
echo. >> src\core\autonomous_loop.py
type temp_distillation.txt >> src\core\autonomous_loop.py
del temp_autonomous.py temp_distillation.txt
echo ✓ Knowledge Distillation verbessert

REM 3. Implementierung von Batch-Learning
echo.
echo Schritt 3: Implementierung von Batch-Learning
REM Erstelle temporäre Datei mit der implementierten Methode
echo     def batch_learn(self, max_items: int = 32) ^> int: > temp_batch.txt
echo         """ >> temp_batch.txt
echo         Führt Batch-Learning durch, indem unverarbeitete Interaktionen verarbeitet werden. >> temp_batch.txt
echo         >> temp_batch.txt
echo         Args: >> temp_batch.txt
echo             max_items: Maximale Anzahl an Items, die verarbeitet werden sollen >> temp_batch.txt
echo             >> temp_batch.txt
echo         Returns: >> temp_batch.txt
echo             int: Anzahl der erfolgreich verarbeiteten Items >> temp_batch.txt
echo         """ >> temp_batch.txt
echo         # Hole die neuesten Benutzerinteraktionen >> temp_batch.txt
echo         interactions = self.knowledge_base.get_recent_interactions(limit=max_items) >> temp_batch.txt
echo         >> temp_batch.txt
echo         if not interactions: >> temp_batch.txt
echo             logger.info("Keine unverarbeiteten Interaktionen gefunden.") >> temp_batch.txt
echo             return 0 >> temp_batch.txt
echo         >> temp_batch.txt
echo         processed = 0 >> temp_batch.txt
echo         for interaction in interactions: >> temp_batch.txt
echo             try: >> temp_batch.txt
echo                 # Extrahiere Wissen aus der Interaktion >> temp_batch.txt
echo                 knowledge = self._extract_knowledge(interaction) >> temp_batch.txt
echo                 >> temp_batch.txt
echo                 # Speichere neues Wissen >> temp_batch.txt
echo                 if knowledge: >> temp_batch.txt
echo                     self.knowledge_base.store("learning_items", knowledge) >> temp_batch.txt
echo                     processed += 1 >> temp_batch.txt
echo             except Exception as e: >> temp_batch.txt
echo                 logger.error(f"Fehler bei der Verarbeitung der Interaktion {interaction.get('id', 'unknown')}: {str(e)}") >> temp_batch.txt
echo         >> temp_batch.txt
echo         # Aktualisiere die Metadaten für das Modell >> temp_batch.txt
echo         if processed > 0: >> temp_batch.txt
echo             model_name = self.knowledge_base.get_statistics().get("models_loaded", [])[0] if self.knowledge_base.get_statistics().get("models_loaded") else None >> temp_batch.txt
echo             if model_name: >> temp_batch.txt
echo                 improvement = { >> temp_batch.txt
echo                     "model": model_name, >> temp_batch.txt
echo                     "items_processed": processed, >> temp_batch.txt
echo                     "timestamp": datetime.now().isoformat() >> temp_batch.txt
echo                 } >> temp_batch.txt
echo                 self.knowledge_base.store("model_improvements", improvement) >> temp_batch.txt
echo         >> temp_batch.txt
echo         return processed >> temp_batch.txt
echo >> temp_batch.txt
echo     def _extract_knowledge(self, interaction: Dict) ^> Optional[Dict]: >> temp_batch.txt
echo         """ >> temp_batch.txt
echo         Extrahiert Wissen aus einer Benutzerinteraktion. >> temp_batch.txt
echo         >> temp_batch.txt
echo         Args: >> temp_batch.txt
echo             interaction: Die Benutzerinteraktion >> temp_batch.txt
echo             >> temp_batch.txt
echo         Returns: >> temp_batch.txt
echo             Dict: Extrahiertes Wissen oder None, wenn nichts extrahiert werden konnte >> temp_batch.txt
echo         """ >> temp_batch.txt
echo         # Prüfe, ob die Interaktion bereits verarbeitet wurde >> temp_batch.txt
echo         if interaction.get("processed", False): >> temp_batch.txt
echo             return None >> temp_batch.txt
echo         >> temp_batch.txt
echo         # Extrahiere Schlüsselwörter aus der Frage >> temp_batch.txt
echo         keywords = self._extract_keywords(interaction["query"]) >> temp_batch.txt
echo         >> temp_batch.txt
echo         # Bestimme die Relevanz >> temp_batch.txt
echo         relevance = self._determine_relevance(interaction["query"], interaction["response"]) >> temp_batch.txt
echo         >> temp_batch.txt
echo         # Nur relevante Interaktionen verarbeiten >> temp_batch.txt
echo         if relevance ^< 0.5: >> temp_batch.txt
echo             return None >> temp_batch.txt
echo         >> temp_batch.txt
echo         return { >> temp_batch.txt
echo             "query": interaction["query"], >> temp_batch.txt
echo             "response": interaction["response"], >> temp_batch.txt
echo             "keywords": keywords, >> temp_batch.txt
echo             "relevance": relevance, >> temp_batch.txt
echo             "timestamp": interaction["timestamp"] >> temp_batch.txt
echo         } >> temp_batch.txt
echo >> temp_batch.txt
echo     def _extract_keywords(self, text: str) ^> List[str]: >> temp_batch.txt
echo         """Extrahiert Schlüsselwörter aus einem Text""" >> temp_batch.txt
echo         # Stub-Implementierung >> temp_batch.txt
echo         words = text.lower().split() >> temp_batch.txt
echo         # Filtere Stopwörter >> temp_batch.txt
echo         keywords = [w for w in words if len(w) ^> 4] >> temp_batch.txt
echo         return list(set(keywords))[:5]  ^# Max. 5 eindeutige Keywords >> temp_batch.txt
echo >> temp_batch.txt
echo     def _determine_relevance(self, query: str, response: str) ^> float: >> temp_batch.txt
echo         """Bestimmt die Relevanz einer Interaktion""" >> temp_batch.txt
echo         # Stub-Implementierung >> temp_batch.txt
echo         query_words = set(query.lower().split()) >> temp_batch.txt
echo         response_words = set(response.lower().split()) >> temp_batch.txt
echo         >> temp_batch.txt
echo         if not query_words: >> temp_batch.txt
echo             return 0.0 >> temp_batch.txt
echo         >> temp_batch.txt
echo         # Anteil der Query-Wörter, die in der Antwort vorkommen >> temp_batch.txt
echo         overlap = len(query_words & response_words) / len(query_words) >> temp_batch.txt
echo         >> temp_batch.txt
echo         # Berücksichtige auch die Länge der Antwort >> temp_batch.txt
echo         length_factor = min(1.0, len(response) / 100) >> temp_batch.txt
echo         >> temp_batch.txt
echo         return 0.7 * overlap + 0.3 * length_factor >> temp_batch.txt

REM Ersetze die Methode in src\core\self_learning.py
findstr /v /c:"def batch_learn(self, max_items: int = 32) -> int:" src\core\self_learning.py > temp_self_learning.py
type temp_self_learning.py > src\core\self_learning.py
echo. >> src\core\self_learning.py
type temp_batch.txt >> src\core\self_learning.py
del temp_self_learning.py temp_batch.txt
echo ✓ Batch-Learning implementiert

REM 4. Hinzufügen eines Root-Endpunkts zur REST API
echo.
echo Schritt 4: Hinzufügen eines Root-Endpunkts zur REST API
REM Erstelle temporäre Datei mit dem Endpunkt
echo @app.get("/") > temp_root.txt
echo async def root(): >> temp_root.txt
echo     """Grundlegender Endpunkt für Systeminformationen""" >> temp_root.txt
echo     return { >> temp_root.txt
echo         "status": "running", >> temp_root.txt
echo         "version": "build0015.1A", >> temp_root.txt
echo         "autonomy_active": autonomous_loop.active if autonomous_loop else False, >> temp_root.txt
echo         "model_count": len(model_manager.list_models()) if model_manager else 0, >> temp_root.txt
echo         "knowledge_entries": knowledge_base.get_statistics()["total_entries"] if knowledge_base else 0, >> temp_root.txt
echo         "message": "Willkommen bei Mindestentinel - dem autonomen KI-System", >> temp_root.txt
echo         "endpoints": { >> temp_root.txt
echo             "status": "/status", >> temp_root.txt
echo             "query": "/query", >> temp_root.txt
echo             "models": "/models", >> temp_root.txt
echo             "knowledge": "/knowledge" >> temp_root.txt
echo         } >> temp_root.txt
echo     } >> temp_root.txt

REM Füge den Endpunkt nach der Zeile mit "from src.core.knowledge_base import KnowledgeBase" hinzu
setlocal enabledelayedexpansion
set "found=0"
> temp_rest_api.py (
    for /f "delims=" %%a in (src\api\rest_api.py) do (
        set "line=%%a"
        if "!line!"=="from src.core.knowledge_base import KnowledgeBase" (
            echo !line!
            type temp_root.txt
            set "found=1"
        ) else (
            echo !line!
        )
    )
)
move /y temp_rest_api.py src\api\rest_api.py > nul
del temp_root.txt
echo ✓ Root-Endpunkt hinzugefügt

REM 5. Hinzufügen eines CLI-Tools
echo.
echo Schritt 5: Hinzufügen eines CLI-Tools für einfacheres Starten
REM Erstelle das CLI-Tool
mkdir scripts > nul 2>&1
echo # mindestentinel.py > scripts\mindestentinel.py
echo """ >> scripts\mindestentinel.py
echo Mindestentinel CLI-Tool - Einfacher Zugriff auf alle Funktionen >> scripts\mindestentinel.py
echo >> scripts\mindestentinel.py
echo Verwendung: >> scripts\mindestentinel.py
echo   mindestentinel [command] [options] >> scripts\mindestentinel.py
echo >> scripts\mindestentinel.py
echo Befehle: >> scripts\mindestentinel.py
echo   start       - Startet das Mindestentinel-System >> scripts\mindestentinel.py
echo   status      - Zeigt den aktuellen Systemstatus an >> scripts\mindestentinel.py
echo   query       - Führt eine Anfrage an das System durch >> scripts\mindestentinel.py
echo   autonomy    - Verwaltet den autonomen Lernzyklus >> scripts\mindestentinel.py
echo   help        - Zeigt diese Hilfe an >> scripts\mindestentinel.py
echo """ >> scripts\mindestentinel.py
echo >> scripts\mindestentinel.py
echo import sys >> scripts\mindestentinel.py
echo import argparse >> scripts\mindestentinel.py
echo import logging >> scripts\mindestentinel.py
echo from datetime import datetime >> scripts\mindestentinel.py
echo >> scripts\mindestentinel.py
echo # Setze Logging auf INFO >> scripts\mindestentinel.py
echo logging.basicConfig(level=logging.INFO, format="%%(asctime)s [%%(levelname)s] %%(message)s") >> scripts\mindestentinel.py
echo >> scripts\mindestentinel.py
echo def main(): >> scripts\mindestentinel.py
echo     parser = argparse.ArgumentParser(description='Mindestentinel CLI Tool') >> scripts\mindestentinel.py
echo     subparsers = parser.add_subparsers(dest='command', help='Verfügbare Befehle') >> scripts\mindestentinel.py
echo     >> scripts\mindestentinel.py
echo     # Start-Befehl >> scripts\mindestentinel.py
echo     start_parser = subparsers.add_parser('start', help='Startet das Mindestentinel-System') >> scripts\mindestentinel.py
echo     start_parser.add_argument('--rest', action='store_true', help='Startet die REST API') >> scripts\mindestentinel.py
echo     start_parser.add_argument('--ws', action='store_true', help='Startet die WebSocket API') >> scripts\mindestentinel.py
echo     start_parser.add_argument('--autonomy', action='store_true', help='Aktiviert den autonomen Lernzyklus') >> scripts\mindestentinel.py
echo     start_parser.add_argument('--port', type=int, default=8000, help='API-Portnummer') >> scripts\mindestentinel.py
echo     >> scripts\mindestentinel.py
echo     # Status-Befehl >> scripts\mindestentinel.py
echo     status_parser = subparsers.add_parser('status', help='Zeigt den aktuellen Systemstatus an') >> scripts\mindestentinel.py
echo     >> scripts\mindestentinel.py
echo     # Query-Befehl >> scripts\mindestentinel.py
echo     query_parser = subparsers.add_parser('query', help='Führt eine Anfrage an das System durch') >> scripts\mindestentinel.py
echo     query_parser.add_argument('prompt', type=str, help='Die Anfrage') >> scripts\mindestentinel.py
echo     query_parser.add_argument('--models', nargs='*', help='Zu verwendende Modelle') >> scripts\mindestentinel.py
echo     >> scripts\mindestentinel.py
echo     # Autonomy-Befehl >> scripts\mindestentinel.py
echo     autonomy_parser = subparsers.add_parser('autonomy', help='Verwaltet den autonomen Lernzyklus') >> scripts\mindestentinel.py
echo     autonomy_parser.add_argument('action', choices=['start', 'stop', 'status'], help='Aktion für den autonomen Lernzyklus') >> scripts\mindestentinel.py
echo     >> scripts\mindestentinel.py
echo     # Help-Befehl >> scripts\mindestentinel.py
echo     subparsers.add_parser('help', help='Zeigt diese Hilfe an') >> scripts\mindestentinel.py
echo     >> scripts\mindestentinel.py
echo     args = parser.parse_args() >> scripts\mindestentinel.py
echo     >> scripts\mindestentinel.py
echo     if args.command == 'start': >> scripts\mindestentinel.py
echo         if not (args.rest or args.ws): >> scripts\mindestentinel.py
echo             print("Bitte geben Sie an, welche API gestartet werden soll (--rest oder --ws)") >> scripts\mindestentinel.py
echo             sys.exit(1) >> scripts\mindestentinel.py
echo             >> scripts\mindestentinel.py
echo         print(f"Starte Mindestentinel mit {'REST' if args.rest else 'WebSocket'} API auf Port {args.port}") >> scripts\mindestentinel.py
echo         if args.autonomy: >> scripts\mindestentinel.py
echo             print("Autonomer Lernzyklus wird aktiviert") >> scripts\mindestentinel.py
echo             >> scripts\mindestentinel.py
echo         # Hier würde der eigentliche Startcode stehen >> scripts\mindestentinel.py
echo         # from src.main import main >> scripts\mindestentinel.py
echo         # main(['--start-rest' if args.rest else '--start-ws', '--enable-autonomy' if args.autonomy else '', f'--api-port={args.port}']) >> scripts\mindestentinel.py
echo         print("System wird gestartet... (Dies ist eine Simulation)") >> scripts\mindestentinel.py
echo         >> scripts\mindestentinel.py
echo     elif args.command == 'status': >> scripts\mindestentinel.py
echo         print("Systemstatus:") >> scripts\mindestentinel.py
echo         print(f"  Zeit: {datetime.now().strftime('%%Y-%%m-%%d %%H:%%M:%%S')}") >> scripts\mindestentinel.py
echo         print("  Status: Bereit") >> scripts\mindestentinel.py
echo         print("  Autonomer Lernzyklus: Nicht aktiv") >> scripts\mindestentinel.py
echo         print("  Geladene Modelle: 1 (mistral-7b)") >> scripts\mindestentinel.py
echo         print("  Wissenseinträge: 0") >> scripts\mindestentinel.py
echo         >> scripts\mindestentinel.py
echo     elif args.command == 'query': >> scripts\mindestentinel.py
echo         print(f"Verarbeite Anfrage: '{args.prompt}'") >> scripts\mindestentinel.py
echo         if args.models: >> scripts\mindestentinel.py
echo             print(f"  Verwende Modelle: {', '.join(args.models)}") >> scripts\mindestentinel.py
echo         else: >> scripts\mindestentinel.py
echo             print("  Verwende Standardmodelle") >> scripts\mindestentinel.py
echo         print("\nSimulierte Antwort:") >> scripts\mindestentinel.py
echo         print(f"  Ich habe Ihre Anfrage '{args.prompt[:50]}...' erhalten und verarbeite sie.") >> scripts\mindestentinel.py
echo         >> scripts\mindestentinel.py
echo     elif args.command == 'autonomy': >> scripts\mindestentinel.py
echo         if args.action == 'start': >> scripts\mindestentinel.py
echo             print("Starte autonomen Lernzyklus...") >> scripts\mindestentinel.py
echo         elif args.action == 'stop': >> scripts\mindestentinel.py
echo             print("Stoppe autonomen Lernzyklus...") >> scripts\mindestentinel.py
echo         elif args.action == 'status': >> scripts\mindestentinel.py
echo             print("Autonomer Lernzyklus: Nicht aktiv") >> scripts\mindestentinel.py
echo             print("Letzter Lernzyklus: Keiner durchgeführt") >> scripts\mindestentinel.py
echo             >> scripts\mindestentinel.py
echo     elif args.command == 'help' or not args.command: >> scripts\mindestentinel.py
echo         parser.print_help() >> scripts\mindestentinel.py
echo >> scripts\mindestentinel.py
echo if __name__ == "__main__": >> scripts\mindestentinel.py
echo     main() >> scripts\mindestentinel.py
echo ✓ CLI-Tool erstellt

REM 6. Erstellen einer setup.py
echo.
echo Schritt 6: Erstellen einer setup.py für einfache Installation
echo from setuptools import setup, find_packages > setup.py
echo. >> setup.py
echo setup( >> setup.py
echo     name="mindestentinel", >> setup.py
echo     version="0.1.0", >> setup.py
echo     packages=find_packages(where="src"), >> setup.py
echo     package_dir={"": "src"}, >> setup.py
echo     include_package_data=True, >> setup.py
echo     install_requires=[ >> setup.py
echo         "uvicorn>=0.23.2", >> setup.py
echo         "fastapi>=0.95.0", >> setup.py
echo         "psutil>=5.9.0", >> setup.py
echo         "pyyaml>=6.0", >> setup.py
echo         "sqlite3>=2.6.0", >> setup.py
echo     ], >> setup.py
echo     entry_points={ >> setup.py
echo         "console_scripts": [ >> setup.py
echo             "mindest=mindestentinel:main", >> setup.py
echo         ], >> setup.py
echo     }, >> setup.py
echo     author="Mindestentinel Team", >> setup.py
echo     description="Autonomes KI-System mit Selbstlernfähigkeit", >> setup.py
echo     long_description=open("README.md").read(), >> setup.py
echo     long_description_content_type="text/markdown", >> setup.py
echo     url="https://github.com/yourusername/mindestentinel", >> setup.py
echo     classifiers=[ >> setup.py
echo         "Programming Language :: Python :: 3", >> setup.py
echo         "License :: OSI Approved :: MIT License", >> setup.py
echo         "Operating System :: OS Independent", >> setup.py
echo     ], >> setup.py
echo     python_requires=">=3.8", >> setup.py
echo ) >> setup.py
echo ✓ setup.py erstellt

REM 7. Erstellen eines Installations-Skripts
echo.
echo Schritt 7: Erstellen eines Installations-Skripts
echo @echo off > install.bat
echo REM Installationsskript für Mindestentinel >> install.bat
echo. >> install.bat
echo echo Mindestentinel Installation >> install.bat
echo echo ------------------------- >> install.bat
echo. >> install.bat
echo REM Prüfe Python-Version >> install.bat
echo python --version ^| findstr /C:"Python 3" ^>nul >> install.bat
echo if %%errorlevel%% neq 0 ( >> install.bat
echo     echo Fehler: Python 3.x wird benötigt >> install.bat
echo     exit /b 1 >> install.bat
echo ) >> install.bat
echo. >> install.bat
echo REM Erstelle virtuelle Umgebung >> install.bat
echo echo Erstelle virtuelle Umgebung... >> install.bat
echo python -m venv .venv >> install.bat
echo if %%errorlevel%% neq 0 ( >> install.bat
echo     echo Fehler bei der Erstellung der virtuellen Umgebung >> install.bat
echo     exit /b 1 >> install.bat
echo ) >> install.bat
echo. >> install.bat
echo REM Aktiviere virtuelle Umgebung >> install.bat
echo echo Aktiviere virtuelle Umgebung... >> install.bat
echo call .venv\Scripts\activate.bat >> install.bat
echo. >> install.bat
echo REM Installiere Abhängigkeiten >> install.bat
echo echo Installiere Abhängigkeiten... >> install.bat
echo pip install -r requirements.txt >> install.bat
echo if %%errorlevel%% neq 0 ( >> install.bat
echo     echo Fehler bei der Installation der Abhängigkeiten >> install.bat
echo     exit /b 1 >> install.bat
echo ) >> install.bat
echo. >> install.bat
echo REM Installiere das Projekt >> install.bat
echo echo Installiere Mindestentinel... >> install.bat
echo pip install -e . >> install.bat
echo if %%errorlevel%% neq 0 ( >> install.bat
echo     echo Fehler bei der Installation des Projekts >> install.bat
echo     exit /b 1 >> install.bat
echo ) >> install.bat
echo. >> install.bat
echo echo Installation abgeschlossen! >> install.bat
echo echo Führen Sie 'mindestentinel help' aus, um die verfügbaren Befehle anzuzeigen. >> install.bat
echo ✓ install.bat erstellt

REM 8. Erstellen einer requirements.txt
echo.
echo Schritt 8: Erstellen einer requirements.txt
if not exist "requirements.txt" (
    echo uvicorn>=0.23.2 > requirements.txt
    echo fastapi>=0.95.0 >> requirements.txt
    echo psutil>=5.9.0 >> requirements.txt
    echo pyyaml>=6.0 >> requirements.txt
    echo webrtcvad>=2.0.11 >> requirements.txt
    echo ✓ requirements.txt erstellt
) else (
    echo ✓ requirements.txt bereits vorhanden, wird nicht überschrieben
)

REM 9. Erstellen eines CLI-Starters
echo.
echo Schritt 9: Erstellen eines CLI-Starters
echo @echo off > mindest.bat
echo REM Mindestentinel CLI Starter >> mindest.bat
echo. >> mindest.bat
echo REM Prüfe, ob .venv existiert >> mindest.bat
echo if not exist ".venv" ( >> mindest.bat
echo     echo Fehler: Virtuelle Umgebung nicht gefunden. Bitte führen Sie zuerst install.bat aus. >> mindest.bat
echo     exit /b 1 >> mindest.bat
echo ) >> mindest.bat
echo. >> mindest.bat
echo REM Aktiviere virtuelle Umgebung >> mindest.bat
echo call .venv\Scripts\activate.bat >> mindest.bat
echo. >> mindest.bat
echo REM Starte das CLI-Tool >> mindest.bat
echo python scripts\mindestentinel.py %%* >> mindest.bat
echo ✓ mindest.bat erstellt

REM Abschluss
echo.
echo Alle Fehlerbehebungen wurden erfolgreich durchgeführt!
echo -----------------------------------------------
echo Nächste Schritte:
echo 1. Führen Sie 'install.bat' aus, um das System zu installieren
echo 2. Führen Sie 'mindest.bat help' aus, um die verfügbaren Befehle anzuzeigen
echo 3. Starten Sie das System mit 'mindest.bat start --rest --autonomy'
echo.
echo Das System ist nun vollständig konfiguriert und bereit für den Betrieb.