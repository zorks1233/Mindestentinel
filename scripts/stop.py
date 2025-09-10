# src/scripts/stop.py
"""
Stoppt das Mindestentinel-System sauber.

Dieses Skript sendet eine Shutdown-Anfrage an die REST-API des laufenden Systems.
Falls die API nicht erreichbar ist, wird versucht, den Prozess zu finden und zu beenden.

Verwendung:
    python src/scripts/stop.py [--port PORT] [--timeout SECONDS]

Beispiele:
    python src/scripts/stop.py          # Nutzt Standard-Port 8000
    python src/scripts/stop.py --port 8080
"""

import sys
import time
import argparse
import logging
import requests
import psutil
import os

# Setze Logging-Konfiguration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("mindestentinel.stop")

def shutdown_via_api(port=8000, timeout=10):
    """Versucht, das System über die REST-API herunterzufahren"""
    url = f"http://localhost:{port}/shutdown"
    logger.info(f"Versuche, das System über {url} herunterzufahren...")
    
    try:
        response = requests.post(
            url,
            json={"reason": "Shutdown requested via stop.py"},
            timeout=timeout
        )
        
        if response.status_code == 200:
            logger.info("API Shutdown erfolgreich. Warte auf Beendigung...")
            return True
        else:
            logger.warning(f"API Shutdown fehlgeschlagen. Status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.debug(f"API Shutdown nicht möglich: {str(e)}")
        return False

def find_and_terminate_process():
    """Versucht, den Mindestentinel-Prozess zu finden und zu beenden"""
    current_pid = os.getpid()
    logger.info(f"Suche nach Mindestentinel-Prozessen (ausgenommen PID {current_pid})...")
    
    found = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Prüfe, ob es sich um einen Python-Prozess handelt
            if 'python' in proc.info['name'].lower():
                # Prüfe, ob es Mindestentinel ist
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                if 'mindestentinel' in cmdline.lower() or 'src.main' in cmdline.lower():
                    pid = proc.info['pid']
                    if pid != current_pid:
                        logger.info(f"Gefundener Prozess: PID {pid}, Befehl: {cmdline}")
                        proc.terminate()
                        found = True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    if not found:
        logger.info("Kein laufender Mindestentinel-Prozess gefunden.")
        return False
    
    # Warte auf Beendigung
    logger.info("Warte auf Beendigung der Prozesse...")
    for i in range(10):
        time.sleep(1)
        all_terminated = True
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'python' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    if 'mindestentinel' in cmdline.lower() or 'src.main' in cmdline.lower():
                        all_terminated = False
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        if all_terminated:
            logger.info("Alle Prozesse wurden beendet.")
            return True
    
    # Force terminate remaining processes
    logger.warning("Einige Prozesse laufen noch. Versuche forcieren...")
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                if 'mindestentinel' in cmdline.lower() or 'src.main' in cmdline.lower():
                    proc.kill()
                    logger.info(f"Prozess {proc.info['pid']} wurde gezwungen zu beenden.")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Stoppt das Mindestentinel-System')
    parser.add_argument('--port', type=int, default=8000, help='API-Portnummer (Standard: 8000)')
    parser.add_argument('--timeout', type=int, default=15, help='Timeout für API-Aufruf in Sekunden (Standard: 15)')
    args = parser.parse_args()
    
    logger.info("Starte Shutdown-Prozess für Mindestentinel...")
    
    # Versuche erst über die API zu stoppen
    if shutdown_via_api(args.port, args.timeout):
        # Warte auf vollständige Beendigung
        time.sleep(2)
        # Prüfe, ob noch Prozesse laufen
        if find_and_terminate_process():
            logger.info("Mindestentinel wurde erfolgreich heruntergefahren.")
            return 0
        else:
            logger.info("Mindestentinel wurde über die API heruntergefahren.")
            return 0
    
    # Wenn API nicht verfügbar, suche und beende Prozesse direkt
    if find_and_terminate_process():
        logger.info("Mindestentinel wurde erfolgreich heruntergefahren.")
        return 0
    else:
        logger.info("Kein laufendes Mindestentinel-System gefunden.")
        return 0

if __name__ == "__main__":
    sys.exit(main())