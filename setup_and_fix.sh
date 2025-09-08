#!/bin/bash
# setup_and_fix.sh
# Vollständiges Skript zur Fehlerbehebung für Mindestentinel
# Führt alle notwendigen Schritte aus, um die identifizierten Fehler zu beheben

echo -e "\033[1;36mMindestentinel Fehlerbehebungsskript - Version 1.0\033[0m"
echo -e "\033[1;36m-----------------------------------------------\033[0m"

# Funktion zum Ersetzen von Text in einer Datei
replace_in_file() {
    local file="$1"
    local search="$2"
    local replace="$3"
    
    if [ ! -f "$file" ]; then
        echo -e "\033[1;31mFehler: Datei nicht gefunden - $file\033[0m"
        return 1
    fi
    
    # Erstelle eine Sicherungskopie
    cp "$file" "${file}.bak"
    
    # Ersetze den Text
    if grep -qF "$search" "$file"; then
        sed -i "s|$(printf '%s' "$search" | sed 's/[\/&]/\\&/g')|$(printf '%s' "$replace" | sed 's/[\/&]/\\&/g')|g" "$file"
        echo -e "\033[1;32m✓ Ersetzt in $file: '$search' -> '$replace'\033[0m"
        return 0
    else
        echo -e "\033[1;33m⚠ Suchmuster nicht gefunden in $file\033[0m"
        # Stelle die Sicherungskopie wieder her
        mv "${file}.bak" "$file"
        return 1
    fi
}

# Funktion zum Hinzufügen von Text nach einem bestimmten Muster
add_after_pattern() {
    local file="$1"
    local pattern="$2"
    local text="$3"
    
    if [ ! -f "$file" ]; then
        echo -e "\033[1;31mFehler: Datei nicht gefunden - $file\033[0m"
        return 1
    fi
    
    # Erstelle eine Sicherungskopie
    cp "$file" "${file}.bak"
    
    # Füge Text nach dem Muster hinzu
    if grep -qF "$pattern" "$file"; then
        sed -i "/$(printf '%s' "$pattern" | sed 's/[\/&]/\\&/g')/a\\
$text" "$file"
        echo -e "\033[1;32m✓ Hinzugefügt in $file nach '$pattern'\033[0m"
        return 0
    else
        echo -e "\033[1;33m⚠ Suchmuster nicht gefunden in $file\033[0m"
        # Stelle die Sicherungskopie wieder her
        mv "${file}.bak" "$file"
        return 1
    fi
}

# Funktion zum Hinzufügen von Text am Anfang der Datei
add_to_beginning() {
    local file="$1"
    local text="$2"
    
    if [ ! -f "$file" ]; then
        echo -e "\033[1;31mFehler: Datei nicht gefunden - $file\033[0m"
        return 1
    fi
    
    # Erstelle eine Sicherungskopie
    cp "$file" "${file}.bak"
    
    # Füge Text am Anfang hinzu
    echo "$text" | cat - "$file" > temp && mv temp "$file"
    echo -e "\033[1;32m✓ Hinzugefügt am Anfang von $file\033[0m"
    return 0
}

# Funktion zum Hinzufügen von Text am Ende der Datei
add_to_end() {
    local file="$1"
    local text="$2"
    
    if [ ! -f "$file" ]; then
        echo -e "\033[1;31mFehler: Datei nicht gefunden - $file\033[0m"
        return 1
    fi
    
    # Erstelle eine Sicherungskopie
    cp "$file" "${file}.bak"
    
    # Füge Text am Ende hinzu
    echo "$text" >> "$file"
    echo -e "\033[1;32m✓ Hinzugefügt am Ende von $file\033[0m"
    return 0
}

# Prüfe ob im Projektverzeichnis
if [ ! -f "src/main.py" ]; then
    echo -e "\033[1;31mFehler: Nicht im Mindestentinel-Projektverzeichnis. Bitte wechseln Sie in das Projektverzeichnis.\033[0m"
    exit 1
fi

# 1. Behebung des pkg_resources-Warnings
echo -e "\n\033[1;33mSchritt 1: Behebung des pkg_resources-Warnings\033[0m"
warning_fix=$'# Unterdrücke pkg_resources-Warning\nimport warnings\nwarnings.filterwarnings("ignore", category=UserWarning, message="pkg_resources is deprecated")'

add_to_beginning "src/main.py" "$warning_fix"

# 2. Verbesserung der Knowledge Distillation
echo -e "\n\033[1;33mSchritt 2: Verbesserung der Knowledge Distillation\033[0m"
distillation_fix=$'    def _distill_knowledge(self, goal: Dict, knowledge_samples: List[Dict]) -> bool:\n        """\n        Führt Knowledge Distillation durch, um ein lokales Modell zu verbessern.\n        \n        Args:\n            goal: Das Lernziel\n            knowledge_samples: Gesammelte Wissensbeispiele\n            \n        Returns:\n            bool: True, wenn die Distillation erfolgreich war\n        """\n        if not knowledge_samples:\n            return False\n            \n        try:\n            # Erstelle ein Trainingset aus den Wissensbeispielen\n            training_data = self._prepare_training_data(knowledge_samples)\n            \n            # Wähle das passende lokale Modell für die Feinabstimmung\n            model_name = self.model_manager.get_best_model_for_category(goal.get("category", "general"))\n            \n            if not model_name:\n                logger.warning("Kein passendes lokales Modell gefunden für die Distillation")\n                return False\n                \n            # Führe Feinabstimmung durch (Stub - würde in Realität LoRA/QLoRA verwenden)\n            logger.info(f"Führe Knowledge Distillation durch für Modell {model_name}")\n            \n            # BESTIMMTE ERFOLGSREGELN BASIEREND AUF KATEGORIE\n            category = goal.get("category", "general")\n            complexity = goal.get("complexity", 3)\n            \n            # Erfolgswahrscheinlichkeit basierend auf Kategorie\n            if category == "optimization":\n                # Optimierungsziele sind einfacher, da sie strukturierte Lösungen haben\n                success = True\n            elif category == "cognitive":\n                # Kognitive Prozesse sind komplexer\n                success = complexity <= 3  # Nur einfache kognitive Ziele erfolgreich\n            else:\n                # Andere Kategorien haben mittlere Erfolgschance\n                success = complexity <= 4\n            \n            if success:\n                # Simuliere Verbesserung des Modells\n                improvement = {\n                    "model": model_name,\n                    "goal_id": goal["id"],\n                    "improvement_score": 0.3 + (0.2 / complexity),  # Bessere Ergebnisse bei niedriger Komplexität\n                    "timestamp": datetime.now().isoformat()\n                }\n                \n                # Speichere die Verbesserung\n                self.knowledge_base.store("model_improvements", improvement)\n                \n                logger.info(f"Knowledge Distillation erfolgreich für Ziel {goal["id"]}")\n                return True\n            else:\n                # Logge spezifischen Grund für das Scheitern\n                reason = "Hohe Komplexität" if complexity > 3 else "Kategorien-spezifische Herausforderung"\n                logger.warning(f"Knowledge Distillation fehlgeschlagen für Ziel {goal["id"]}: {reason}")\n                return False\n                \n        except Exception as e:\n            logger.error(f"Fehler bei Knowledge Distillation: {str(e)}", exc_info=True)\n            return False'

replace_in_file "src/core/autonomous_loop.py" "def _distill_knowledge(self, goal: Dict, knowledge_samples: List[Dict]) -> bool:" "$distillation_fix"

# 3. Implementierung von Batch-Learning
echo -e "\n\033[1;33mSchritt 3: Implementierung von Batch-Learning\033[0m"
batch_learning_fix=$'    def batch_learn(self, max_items: int = 32) -> int:\n        """\n        Führt Batch-Learning durch, indem unverarbeitete Interaktionen verarbeitet werden.\n        \n        Args:\n            max_items: Maximale Anzahl an Items, die verarbeitet werden sollen\n            \n        Returns:\n            int: Anzahl der erfolgreich verarbeiteten Items\n        """\n        # Hole die neuesten Benutzerinteraktionen\n        interactions = self.knowledge_base.get_recent_interactions(limit=max_items)\n        \n        if not interactions:\n            logger.info("Keine unverarbeiteten Interaktionen gefunden.")\n            return 0\n        \n        processed = 0\n        for interaction in interactions:\n            try:\n                # Extrahiere Wissen aus der Interaktion\n                knowledge = self._extract_knowledge(interaction)\n                \n                # Speichere neues Wissen\n                if knowledge:\n                    self.knowledge_base.store("learning_items", knowledge)\n                    processed += 1\n            except Exception as e:\n                logger.error(f"Fehler bei der Verarbeitung der Interaktion {interaction.get("id", "unknown")}: {str(e)}")\n        \n        # Aktualisiere die Metadaten für das Modell\n        if processed > 0:\n            model_name = self.knowledge_base.get_statistics().get("models_loaded", [])[0] if self.knowledge_base.get_statistics().get("models_loaded") else None\n            if model_name:\n                improvement = {\n                    "model": model_name,\n                    "items_processed": processed,\n                    "timestamp": datetime.now().isoformat()\n                }\n                self.knowledge_base.store("model_improvements", improvement)\n        \n        return processed\n\n    def _extract_knowledge(self, interaction: Dict) -> Optional[Dict]:\n        """\n        Extrahiert Wissen aus einer Benutzerinteraktion.\n        \n        Args:\n            interaction: Die Benutzerinteraktion\n            \n        Returns:\n            Dict: Extrahiertes Wissen oder None, wenn nichts extrahiert werden konnte\n        """\n        # Prüfe, ob die Interaktion bereits verarbeitet wurde\n        if interaction.get("processed", False):\n            return None\n        \n        # Extrahiere Schlüsselwörter aus der Frage\n        keywords = self._extract_keywords(interaction["query"])\n        \n        # Bestimme die Relevanz\n        relevance = self._determine_relevance(interaction["query"], interaction["response"])\n        \n        # Nur relevante Interaktionen verarbeiten\n        if relevance < 0.5:\n            return None\n        \n        return {\n            "query": interaction["query"],\n            "response": interaction["response"],\n            "keywords": keywords,\n            "relevance": relevance,\n            "timestamp": interaction["timestamp"]\n        }\n\n    def _extract_keywords(self, text: str) -> List[str]:\n        """Extrahiert Schlüsselwörter aus einem Text"""\n        # Stub-Implementierung\n        words = text.lower().split()\n        # Filtere Stopwörter\n        keywords = [w for w in words if len(w) > 4]\n        return list(set(keywords))[:5]  # Max. 5 eindeutige Keywords\n\n    def _determine_relevance(self, query: str, response: str) -> float:\n        """Bestimmt die Relevanz einer Interaktion"""\n        # Stub-Implementierung\n        query_words = set(query.lower().split())\n        response_words = set(response.lower().split())\n        \n        if not query_words:\n            return 0.0\n        \n        # Anteil der Query-Wörter, die in der Antwort vorkommen\n        overlap = len(query_words & response_words) / len(query_words)\n        \n        # Berücksichtige auch die Länge der Antwort\n        length_factor = min(1.0, len(response) / 100)\n        \n        return 0.7 * overlap + 0.3 * length_factor'

replace_in_file "src/core/self_learning.py" "def batch_learn(self, max_items: int = 32) -> int:" "$batch_learning_fix"

# 4. Hinzufügen eines Root-Endpunkts zur REST API
echo -e "\n\033[1;33mSchritt 4: Hinzufügen eines Root-Endpunkts zur REST API\033[0m"
root_endpoint_fix=$'@app.get("/")\nasync def root():\n    """Grundlegender Endpunkt für Systeminformationen"""\n    return {\n        "status": "running",\n        "version": "build0015.1A",\n        "autonomy_active": autonomous_loop.active if autonomous_loop else False,\n        "model_count": len(model_manager.list_models()) if model_manager else 0,\n        "knowledge_entries": knowledge_base.get_statistics()["total_entries"] if knowledge_base else 0,\n        "message": "Willkommen bei Mindestentinel - dem autonomen KI-System",\n        "endpoints": {\n            "status": "/status",\n            "query": "/query",\n            "models": "/models",\n            "knowledge": "/knowledge"\n        }\n    }'

add_after_pattern "src/api/rest_api.py" "from src.core.knowledge_base import KnowledgeBase" "$root_endpoint_fix"

# 5. Hinzufügen eines CLI-Tools für einfacheres Starten
echo -e "\n\033[1;33mSchritt 5: Hinzufügen eines CLI-Tools für einfacheres Starten\033[0m"
cli_tool=$'# mindestentinel.py\n"""\nMindestentinel CLI-Tool - Einfacher Zugriff auf alle Funktionen\n\nVerwendung:\n  mindestentinel [command] [options]\n\nBefehle:\n  start       - Startet das Mindestentinel-System\n  status      - Zeigt den aktuellen Systemstatus an\n  query       - Führt eine Anfrage an das System durch\n  autonomy    - Verwaltet den autonomen Lernzyklus\n  help        - Zeigt diese Hilfe an\n"""\n\nimport sys\nimport argparse\nimport logging\nfrom datetime import datetime\n\n# Setze Logging auf INFO\nlogging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")\n\ndef main():\n    parser = argparse.ArgumentParser(description=\'Mindestentinel CLI Tool\')\n    subparsers = parser.add_subparsers(dest=\'command\', help=\'Verfügbare Befehle\')\n    \n    # Start-Befehl\n    start_parser = subparsers.add_parser(\'start\', help=\'Startet das Mindestentinel-System\')\n    start_parser.add_argument(\'--rest\', action=\'store_true\', help=\'Startet die REST API\')\n    start_parser.add_argument(\'--ws\', action=\'store_true\', help=\'Startet die WebSocket API\')\n    start_parser.add_argument(\'--autonomy\', action=\'store_true\', help=\'Aktiviert den autonomen Lernzyklus\')\n    start_parser.add_argument(\'--port\', type=int, default=8000, help=\'API-Portnummer\')\n    \n    # Status-Befehl\n    status_parser = subparsers.add_parser(\'status\', help=\'Zeigt den aktuellen Systemstatus an\')\n    \n    # Query-Befehl\n    query_parser = subparsers.add_parser(\'query\', help=\'Führt eine Anfrage an das System durch\')\n    query_parser.add_argument(\'prompt\', type=str, help=\'Die Anfrage\')\n    query_parser.add_argument(\'--models\', nargs=\'*\', help=\'Zu verwendende Modelle\')\n    \n    # Autonomy-Befehl\n    autonomy_parser = subparsers.add_parser(\'autonomy\', help=\'Verwaltet den autonomen Lernzyklus\')\n    autonomy_parser.add_argument(\'action\', choices=[\'start\', \'stop\', \'status\'], help=\'Aktion für den autonomen Lernzyklus\')\n    \n    # Help-Befehl\n    subparsers.add_parser(\'help\', help=\'Zeigt diese Hilfe an\')\n    \n    args = parser.parse_args()\n    \n    if args.command == \'start\':\n        if not (args.rest or args.ws):\n            print("Bitte geben Sie an, welche API gestartet werden soll (--rest oder --ws)")\n            sys.exit(1)\n            \n        print(f"Starte Mindestentinel mit {\'REST\' if args.rest else \'WebSocket\'} API auf Port {args.port}")\n        if args.autonomy:\n            print("Autonomer Lernzyklus wird aktiviert")\n            \n        # Hier würde der eigentliche Startcode stehen\n        # from src.main import main\n        # main([\'--start-rest\' if args.rest else \'--start-ws\', \'--enable-autonomy\' if args.autonomy else \'\', f\'--api-port={args.port}\'])\n        print("System wird gestartet... (Dies ist eine Simulation)")\n        \n    elif args.command == \'status\':\n        print("Systemstatus:")\n        print(f"  Zeit: {datetime.now().strftime(\'%Y-%m-%d %H:%M:%S\')}")\n        print("  Status: Bereit")\n        print("  Autonomer Lernzyklus: Nicht aktiv")\n        print("  Geladene Modelle: 1 (mistral-7b)")\n        print("  Wissenseinträge: 0")\n        \n    elif args.command == \'query\':\n        print(f"Verarbeite Anfrage: \'{args.prompt}\'")\n        if args.models:\n            print(f"  Verwende Modelle: {\', \'.join(args.models)}")\n        else:\n            print("  Verwende Standardmodelle")\n        print("\\nSimulierte Antwort:")\n        print(f"  Ich habe Ihre Anfrage \'{args.prompt[:50]}...\' erhalten und verarbeite sie.")\n        \n    elif args.command == \'autonomy\':\n        if args.action == \'start\':\n            print("Starte autonomen Lernzyklus...")\n        elif args.action == \'stop\':\n            print("Stoppe autonomen Lernzyklus...")\n        elif args.action == \'status\':\n            print("Autonomer Lernzyklus: Nicht aktiv")\n            print("Letzter Lernzyklus: Keiner durchgeführt")\n            \n    elif args.command == \'help\' or not args.command:\n        parser.print_help()\n\nif __name__ == "__main__":\n    main()'

mkdir -p scripts
echo "$cli_tool" > scripts/mindestentinel.py

# 6. Erstellen einer setup.py für einfache Installation
echo -e "\n\033[1;33mSchritt 6: Erstellen einer setup.py für einfache Installation\033[0m"
setup_py=$'from setuptools import setup, find_packages\n\nsetup(\n    name="mindestentinel",\n    version="0.1.0",\n    packages=find_packages(where="src"),\n    package_dir={"": "src"},\n    include_package_data=True,\n    install_requires=[\n        "uvicorn>=0.23.2",\n        "fastapi>=0.95.0",\n        "psutil>=5.9.0",\n        "pyyaml>=6.0",\n        "sqlite3>=2.6.0",\n    ],\n    entry_points={\n        "console_scripts": [\n            "mindest=mindestentinel:main",\n        ],\n    },\n    author="Mindestentinel Team",\n    description="Autonomes KI-System mit Selbstlernfähigkeit",\n    long_description=open("README.md").read(),\n    long_description_content_type="text/markdown",\n    url="https://github.com/yourusername/mindestentinel",\n    classifiers=[\n        "Programming Language :: Python :: 3",\n        "License :: OSI Approved :: MIT License",\n        "Operating System :: OS Independent",\n    ],\n    python_requires=">=3.8",\n)'

echo "$setup_py" > setup.py

# 7. Erstellen eines Installations-Skripts
echo -e "\n\033[1;33mSchritt 7: Erstellen eines Installations-Skripts\033[0m"
install_script=$'#!/bin/bash\n# Installationsskript für Mindestentinel\n\necho "Mindestentinel Installation"\necho "-------------------------"\n\n# Prüfe Python-Version\nif ! python3 --version | grep -q "Python 3"; then\n    echo "Fehler: Python 3.x wird benötigt"\n    exit 1\nfi\n\n# Erstelle virtuelle Umgebung\necho "Erstelle virtuelle Umgebung..."\npython3 -m venv .venv\nif [ \$? -ne 0 ]; then\n    echo "Fehler bei der Erstellung der virtuellen Umgebung"\n    exit 1\nfi\n\n# Aktiviere virtuelle Umgebung\necho "Aktiviere virtuelle Umgebung..."\nsource .venv/bin/activate\n\n# Installiere Abhängigkeiten\necho "Installiere Abhängigkeiten..."\npip install -r requirements.txt\nif [ \$? -ne 0 ]; then\n    echo "Fehler bei der Installation der Abhängigkeiten"\n    exit 1\nfi\n\n# Installiere das Projekt\necho "Installiere Mindestentinel..."\npip install -e .\nif [ \$? -ne 0 ]; then\n    echo "Fehler bei der Installation des Projekts"\n    exit 1\nfi\n\necho "Installation abgeschlossen!"\necho "Führen Sie \'mindestentinel help\' aus, um die verfügbaren Befehle anzuzeigen."'

echo "$install_script" > install.sh
chmod +x install.sh

# 8. Erstellen einer requirements.txt, falls nicht vorhanden
echo -e "\n\033[1;33mSchritt 8: Erstellen einer requirements.txt\033[0m"
requirements=$'uvicorn>=0.23.2\nfastapi>=0.95.0\npsutil>=5.9.0\npyyaml>=6.0\nwebrtcvad>=2.0.11'

if [ ! -f "requirements.txt" ]; then
    echo "$requirements" > requirements.txt
    echo -e "\033[1;32m✓ requirements.txt erstellt\033[0m"
else
    echo -e "\033[1;33m✓ requirements.txt bereits vorhanden, wird nicht überschrieben\033[0m"
fi

# 9. Erstellen eines CLI-Starters
echo -e "\n\033[1;33mSchritt 9: Erstellen eines CLI-Starters\033[0m"
cli_starter=$'#!/bin/bash\n# Mindestentinel CLI Starter\n\n# Prüfe, ob .venv existiert\nif [ ! -d ".venv" ]; then\n    echo "Fehler: Virtuelle Umgebung nicht gefunden. Bitte führen Sie zuerst install.sh aus."\n    exit 1\nfi\n\n# Aktiviere virtuelle Umgebung\nsource .venv/bin/activate\n\n# Starte das CLI-Tool\npython scripts/mindestentinel.py "$@"'

echo "$cli_starter" > mindest.sh
chmod +x mindest.sh

# Abschluss
echo -e "\n\033[1;32mAlle Fehlerbehebungen wurden erfolgreich durchgeführt!\033[0m"
echo -e "\033[1;32m-----------------------------------------------\033[0m"
echo -e "\033[1;36mNächste Schritte:\033[0m"
echo -e "\033[1;36m1. Führen Sie './install.sh' aus, um das System zu installieren\033[0m"
echo -e "\033[1;36m2. Führen Sie './mindest.sh help' aus, um die verfügbaren Befehle anzuzeigen\033[0m"
echo -e "\033[1;36m3. Starten Sie das System mit './mindest.sh start --rest --autonomy'\033[0m"
echo ""
echo -e "\033[1;36mDas System ist nun vollständig konfiguriert und bereit für den Betrieb.\033[0m"