# mindestentinel.py 
Mindestentinel CLI-Tool - Einfacher Zugriff auf alle Funktionen 
ECHO ist ausgeschaltet (OFF).
Verwendung: 
  mindestentinel [command] [options] 
ECHO ist ausgeschaltet (OFF).
Befehle: 
  start       - Startet das Mindestentinel-System 
  status      - Zeigt den aktuellen Systemstatus an 
  query       - Führt eine Anfrage an das System durch 
  autonomy    - Verwaltet den autonomen Lernzyklus 
  help        - Zeigt diese Hilfe an 
ECHO ist ausgeschaltet (OFF).
import sys 
import argparse 
import logging 
from datetime import datetime 
ECHO ist ausgeschaltet (OFF).
# Setze Logging auf INFO 
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s") 
ECHO ist ausgeschaltet (OFF).
def main(): 
    parser = argparse.ArgumentParser(description='Mindestentinel CLI Tool') 
    subparsers = parser.add_subparsers(dest='command', help='Verfügbare Befehle') 
ECHO ist ausgeschaltet (OFF).
    # Start-Befehl 
    start_parser = subparsers.add_parser('start', help='Startet das Mindestentinel-System') 
    start_parser.add_argument('--rest', action='store_true', help='Startet die REST API') 
    start_parser.add_argument('--ws', action='store_true', help='Startet die WebSocket API') 
    start_parser.add_argument('--autonomy', action='store_true', help='Aktiviert den autonomen Lernzyklus') 
    start_parser.add_argument('--port', type=int, default=8000, help='API-Portnummer') 
ECHO ist ausgeschaltet (OFF).
    # Status-Befehl 
    status_parser = subparsers.add_parser('status', help='Zeigt den aktuellen Systemstatus an') 
ECHO ist ausgeschaltet (OFF).
    # Query-Befehl 
    query_parser = subparsers.add_parser('query', help='Führt eine Anfrage an das System durch') 
    query_parser.add_argument('prompt', type=str, help='Die Anfrage') 
    query_parser.add_argument('--models', nargs='*', help='Zu verwendende Modelle') 
ECHO ist ausgeschaltet (OFF).
    # Autonomy-Befehl 
    autonomy_parser = subparsers.add_parser('autonomy', help='Verwaltet den autonomen Lernzyklus') 
    autonomy_parser.add_argument('action', choices=['start', 'stop', 'status'], help='Aktion für den autonomen Lernzyklus') 
ECHO ist ausgeschaltet (OFF).
    # Help-Befehl 
    subparsers.add_parser('help', help='Zeigt diese Hilfe an') 
ECHO ist ausgeschaltet (OFF).
    args = parser.parse_args() 
ECHO ist ausgeschaltet (OFF).
    if args.command == 'start': 
        if not (args.rest or args.ws): 
            print("Bitte geben Sie an, welche API gestartet werden soll (--rest oder --ws)") 
            sys.exit(1) 
ECHO ist ausgeschaltet (OFF).
        print(f"Starte Mindestentinel mit {'REST' if args.rest else 'WebSocket'} API auf Port {args.port}") 
        if args.autonomy: 
            print("Autonomer Lernzyklus wird aktiviert") 
ECHO ist ausgeschaltet (OFF).
        # Hier würde der eigentliche Startcode stehen 
        # from src.main import main 
        # main(['--start-rest' if args.rest else '--start-ws', '--enable-autonomy' if args.autonomy else '', f'--api-port={args.port}']) 
        print("System wird gestartet... (Dies ist eine Simulation)") 
ECHO ist ausgeschaltet (OFF).
    elif args.command == 'status': 
        print("Systemstatus:") 
        print(f"  Zeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}") 
        print("  Status: Bereit") 
        print("  Autonomer Lernzyklus: Nicht aktiv") 
        print("  Geladene Modelle: 1 (mistral-7b)") 
        print("  Wissenseinträge: 0") 
ECHO ist ausgeschaltet (OFF).
    elif args.command == 'query': 
        print(f"Verarbeite Anfrage: '{args.prompt}'") 
        if args.models: 
            print(f"  Verwende Modelle: {', '.join(args.models)}") 
        else: 
            print("  Verwende Standardmodelle") 
        print("\nSimulierte Antwort:") 
        print(f"  Ich habe Ihre Anfrage '{args.prompt[:50]}...' erhalten und verarbeite sie.") 
ECHO ist ausgeschaltet (OFF).
    elif args.command == 'autonomy': 
        if args.action == 'start': 
            print("Starte autonomen Lernzyklus...") 
        elif args.action == 'stop': 
            print("Stoppe autonomen Lernzyklus...") 
        elif args.action == 'status': 
            print("Autonomer Lernzyklus: Nicht aktiv") 
            print("Letzter Lernzyklus: Keiner durchgeführt") 
ECHO ist ausgeschaltet (OFF).
    elif args.command == 'help' or not args.command: 
        parser.print_help() 
ECHO ist ausgeschaltet (OFF).
if __name__ == "__main__": 
    main() 
