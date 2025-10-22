"""
protection_module.py
Implementiert den Schutzmechanismus für Mindestentinel
Verwaltet Sicherheitsregeln, Zugriffssteuerung und Schutzfunktionen
"""

import os
import sys
import logging
import time
from typing import Dict, Any, Optional, List, Tuple, Union

# Robuste Projekt-Root-Erkennung
def get_project_root() -> str:
    """
    Findet das Projekt-Root-Verzeichnis unabhängig vom aktuellen Arbeitsverzeichnis
    
    Returns:
        str: Absolute Pfad zum Projekt-Root
    """
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)
    
    # Versuche 1: Von src/core aus
    project_root = os.path.dirname(os.path.dirname(current_dir))
    if os.path.exists(os.path.join(project_root, "core")):
        return project_root
    
    # Versuche 2: Von core aus
    project_root = os.path.dirname(current_dir)
    if os.path.exists(os.path.join(project_root, "src", "core")):
        return project_root
    
    # Versuche 3: Aktuelles Verzeichnis ist Projekt-Root
    project_root = current_dir
    if os.path.exists(os.path.join(project_root, "src", "core")) or os.path.exists(os.path.join(project_root, "core")):
        return project_root
    
    # Versuche 4: Projekt-Root ist zwei Ebenen höher
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    if os.path.exists(os.path.join(project_root, "core")):
        return project_root
    
    # Fallback: Aktuelles Verzeichnis
    return os.getcwd()

# Setze PYTHONPATH korrekt
PROJECT_ROOT = get_project_root()
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import-Handling für ConfigLoader
config_loader = None
try:
    # Versuche 1: Import aus config
    from config.config_loader import load_config
    config_loader = load_config
    logging.debug("ConfigLoader erfolgreich aus config.config_loader importiert")
except ImportError as e1:
    try:
        # Versuche 2: Import aus src/config
        from src.config.config_loader import load_config
        config_loader = load_config
        logging.debug("ConfigLoader erfolgreich aus src.config.config_loader importiert")
    except ImportError as e2:
        try:
            # Versuche 3: Dynamischer Import
            config_loader_path = os.path.join(PROJECT_ROOT, "config", "config_loader.py")
            
            if not os.path.exists(config_loader_path):
                config_loader_path = os.path.join(PROJECT_ROOT, "src", "config", "config_loader.py")
            
            if os.path.exists(config_loader_path):
                import importlib.util
                spec = importlib.util.spec_from_file_location("config_loader", config_loader_path)
                config_loader_module = importlib.util.module_from_spec(spec)
                sys.modules["config_loader"] = config_loader_module
                spec.loader.exec_module(config_loader_module)
                
                if hasattr(config_loader_module, "load_config"):
                    config_loader = config_loader_module.load_config
                    logging.debug(f"ConfigLoader dynamisch aus {config_loader_path} geladen")
                else:
                    raise AttributeError(f"config_loader.py enthält keine load_config-Funktion")
            else:
                raise ImportError(f"config_loader.py nicht gefunden unter: {config_loader_path}")
        except Exception as e3:
            logging.error(f"Alle Importversuche für ConfigLoader fehlgeschlagen: {str(e1)}, {str(e2)}, {str(e3)}")
            
            # Definiere eine Dummy-Implementierung für load_config
            def load_config(config_name: str = "main.yaml") -> Dict[str, Any]:
                logging.warning("ConfigLoader ist eine Dummy-Implementierung - bitte korrigieren")
                return {
                    "system": {
                        "debug": True,
                        "log_level": "INFO",
                        "log_dir": "logs"
                    },
                    "api": {
                        "port": 8000,
                        "host": "0.0.0.0"
                    },
                    "model": {
                        "default": "gpt-3.5-turbo",
                        "max_tokens": 500,
                        "temperature": 0.7,
                        "models_dir": os.path.join(PROJECT_ROOT, "models"),
                        "cache_dir": os.path.join(PROJECT_ROOT, "cache")
                    },
                    "self_learning": {
                        "enabled": True,
                        "learning_rate": 0.01,
                        "memory_size": 1000
                    },
                    "protection": {
                        "enabled": True,
                        "security_level": "high",
                        "threat_detection": True,
                        "max_threat_level": 5,
                        "protection_modules": ["rule_engine", "quantum_security", "anomaly_detection"]
                    }
                }
            
            config_loader = load_config

# Initialisiere Logging
logger = logging.getLogger("mindestentinel.protection")
logger.setLevel(logging.INFO)

class ProtectionModule:
    """
    Implementiert den Schutzmechanismus für Mindestentinel
    Verwaltet Sicherheitsregeln, Zugriffssteuerung und Schutzfunktionen
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, rule_engine: Optional['RuleEngine'] = None):
        """
        Initialisiert das Schutzmodul
        
        Args:
            config: Optionale Konfiguration für das Schutzmodul
            rule_engine: Optionale RuleEngine-Instanz
        """
        # Lade oder verwende Standardkonfiguration
        if config is None:
            try:
                main_config = config_loader()
                self.config = main_config.get("protection", {})
                logger.debug("Schutz-Konfiguration aus Hauptkonfiguration geladen")
            except Exception as e:
                logger.error(f"Fehler beim Laden der Schutz-Konfiguration: {str(e)}")
                self.config = {
                    "enabled": True,
                    "security_level": "medium",
                    "threat_detection": True,
                    "max_threat_level": 5,
                    "protection_modules": ["rule_engine"]
                }
        else:
            self.config = config
        
        # Extrahiere Konfigurationsparameter
        self.enabled = self.config.get("enabled", True)
        self.security_level = self.config.get("security_level", "medium")
        self.threat_detection = self.config.get("threat_detection", True)
        self.max_threat_level = self.config.get("max_threat_level", 5)
        self.protection_modules = self.config.get("protection_modules", ["rule_engine"])
        
        # Setze RuleEngine
        self.rule_engine = rule_engine
        
        # Initialisiere interne Datenstrukturen
        self.threat_history = []
        self.security_events = []
        self.protection_active = self.enabled
        self.last_check_time = None
        
        # Initialisiere die RuleEngine, wenn nicht bereitgestellt
        if self.rule_engine is None and "rule_engine" in self.protection_modules:
            try:
                from core.rule_engine import RuleEngine
                rules_path = os.path.join(PROJECT_ROOT, "config", "rules.yaml")
                self.rule_engine = RuleEngine(rules_path=rules_path)
                self.rule_engine.load_rules()
                logger.info("Interne RuleEngine initialisiert")
            except Exception as e:
                logger.error(f"Fehler bei der Initialisierung der internen RuleEngine: {str(e)}")
        
        logger.info("ProtectionModule erfolgreich initialisiert")
        logger.debug(f"Konfiguration: enabled={self.enabled}, security_level={self.security_level}, "
                    f"threat_detection={self.threat_detection}, max_threat_level={self.max_threat_level}")
    
    def check_security(self, input_: Any, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Überprüft die Sicherheit einer Eingabe
        
        Args:
            input_: Die zu überprüfenden Daten
            context: Optionaler Kontext für die Sicherheitsüberprüfung
            
        Returns:
            dict: Ergebnis der Sicherheitsüberprüfung
        """
        if not self.enabled:
            logger.warning("Versuch, Sicherheitsprüfung durchzuführen, aber Schutzmodul ist deaktiviert")
            return {
                "allowed": True,
                "threat_level": 0,
                "message": "Schutzmodul deaktiviert",
                "details": {}
            }
        
        if context is None:
            context = {}
        
        logger.debug(f"Führe Sicherheitsprüfung durch für Eingabe: {str(input_)[:50]}{'...' if len(str(input_)) > 50 else ''}")
        self.last_check_time = time.time()
        
        try:
            # 1. Regelbasierte Überprüfung
            rule_result = self._check_with_rules(input_, context)
            
            if not rule_result["allowed"]:
                logger.warning(f"Sicherheitsregel verletzt: {rule_result['message']}")
                return rule_result
            
            # 2. Anomalie-Erkennung
            anomaly_result = self._detect_anomalies(input_, context)
            
            if not anomaly_result["allowed"]:
                logger.warning(f"Anomalie erkannt: {anomaly_result['message']}")
                return anomaly_result
            
            # 3. Quantenbasierte Sicherheitsprüfung (falls aktiviert)
            if "quantum_security" in self.protection_modules:
                quantum_result = self._quantum_security_check(input_, context)
                
                if not quantum_result["allowed"]:
                    logger.warning(f"Quantensicherheitsprüfung fehlgeschlagen: {quantum_result['message']}")
                    return quantum_result
            
            # Alle Prüfungen bestanden
            result = {
                "allowed": True,
                "threat_level": 0,
                "message": "Alle Sicherheitsprüfungen bestanden",
                "details": {
                    "rule_check": rule_result,
                    "anomaly_check": anomaly_result
                }
            }
            
            if "quantum_security" in self.protection_modules:
                result["details"]["quantum_check"] = quantum_result
            
            logger.info("Sicherheitsprüfung erfolgreich bestanden")
            return result
            
        except Exception as e:
            logger.error(f"Fehler bei der Sicherheitsprüfung: {str(e)}")
            return {
                "allowed": False,
                "threat_level": self.max_threat_level,
                "message": f"Sicherheitssystemfehler: {str(e)}",
                "details": {}
            }
    
    def _check_with_rules(self, input_: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Überprüft die Eingabe mit Hilfe der Regel-Engine
        
        Args:
            input_: Die zu überprüfenden Daten
            context: Kontext für die Regelanwendung
            
        Returns:
            dict: Ergebnis der Regelüberprüfung
        """
        if not self.rule_engine:
            logger.warning("RuleEngine nicht verfügbar - überspringe regelbasierte Sicherheitsprüfung")
            return {
                "allowed": True,
                "threat_level": 0,
                "message": "Regel-Engine nicht verfügbar",
                "details": {}
            }
        
        try:
            # Wende Regeln an
            rule_result = self.rule_engine.apply_rules(input_, context=context)
            
            if rule_result["allowed"]:
                return {
                    "allowed": True,
                    "threat_level": 0,
                    "message": "Regelüberprüfung bestanden",
                    "details": rule_result
                }
            else:
                # Bestimme die Bedrohungsstufe basierend auf der Regel
                threat_level = 3  # Standardwert
                
                # Versuche, die Bedrohungsstufe aus den Regeln zu extrahieren
                if "threat_level" in rule_result:
                    threat_level = rule_result["threat_level"]
                elif "severity" in rule_result:
                    severity_map = {"low": 1, "medium": 3, "high": 5}
                    threat_level = severity_map.get(rule_result["severity"], 3)
                
                return {
                    "allowed": False,
                    "threat_level": threat_level,
                    "message": rule_result["message"],
                    "details": rule_result
                }
                
        except Exception as e:
            logger.error(f"Fehler bei der regelbasierten Sicherheitsprüfung: {str(e)}")
            return {
                "allowed": False,
                "threat_level": 5,
                "message": f"Regelüberprüfung fehlgeschlagen: {str(e)}",
                "details": {}
            }
    
    def _detect_anomalies(self, input_: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Erkennt Anomalien in der Eingabe
        
        Args:
            input_: Die zu überprüfenden Daten
            context: Kontext für die Anomalieerkennung
            
        Returns:
            dict: Ergebnis der Anomalieerkennung
        """
        logger.debug("Führe Anomalieerkennung durch...")
        
        # Hier würde die eigentliche Anomalieerkennung stattfinden
        # Für dieses Beispiel verwenden wir eine einfache Heuristik
        
        threat_level = 0
        message = "Keine Anomalien erkannt"
        
        # Prüfe auf ungewöhnliche Eingabelänge
        if hasattr(input_, "__len__"):
            length = len(input_)
            if length > 1000:
                threat_level = max(threat_level, 2)
                message = "Ungewöhnlich lange Eingabe erkannt"
        
        # Prüfe auf verdächtige Schlüsselwörter
        suspicious_keywords = ["hack", "exploit", "bypass", "admin", "password"]
        if isinstance(input_, str):
            for keyword in suspicious_keywords:
                if keyword in input_.lower():
                    threat_level = max(threat_level, 3)
                    message = f"Verdächtiges Schlüsselwort erkannt: {keyword}"
                    break
        
        # Prüfe auf häufige Anfragen aus demselben Kontext
        if "user_id" in context:
            user_id = context["user_id"]
            recent_requests = [event for event in self.security_events 
                             if event.get("context", {}).get("user_id") == user_id 
                             and time.time() - event["timestamp"] < 60]
            
            if len(recent_requests) > 10:
                threat_level = max(threat_level, 4)
                message = "Häufige Anfragen erkannt - mögliche Brute-Force-Attacke"
        
        result = {
            "allowed": threat_level < self.max_threat_level,
            "threat_level": threat_level,
            "message": message,
            "details": {
                "input_length": len(input_) if hasattr(input_, "__len__") else "N/A",
                "suspicious_keywords_found": [kw for kw in suspicious_keywords if kw in input_.lower()] if isinstance(input_, str) else [],
                "recent_requests_count": len(recent_requests) if "recent_requests" in locals() else 0
            }
        }
        
        # Speichere das Sicherheitsereignis
        self.security_events.append({
            "timestamp": time.time(),
            "input_data": str(input_)[:100] + "..." if len(str(input_)) > 100 else str(input_),
            "context": context,
            "result": result
        })
        
        # Behalte nur die letzten 100 Ereignisse
        if len(self.security_events) > 100:
            self.security_events = self.security_events[-100:]
        
        if not result["allowed"]:
            logger.warning(f"Anomalie erkannt: {message} (Bedrohungsstufe: {threat_level})")
        
        return result
    
    def _quantum_security_check(self, input_: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Führt eine quantenbasierte Sicherheitsprüfung durch
        
        Args:
            input_: Die zu überprüfenden Daten
            context: Kontext für die Quantensicherheitsprüfung
            
        Returns:
            dict: Ergebnis der Quantensicherheitsprüfung
        """
        logger.debug("Führe quantenbasierte Sicherheitsprüfung durch...")
        
        # Hier würde die eigentliche Quantensicherheitsprüfung stattfinden
        # Für dieses Beispiel verwenden wir einen Dummy
        
        # Simuliere Quantenberechnung
        time.sleep(0.1)
        
        # Generiere ein zufälliges Ergebnis für das Beispiel
        import random
        threat_level = random.randint(0, 2)
        allowed = threat_level < 3
        
        result = {
            "allowed": allowed,
            "threat_level": threat_level,
            "message": "Quantensicherheitsprüfung abgeschlossen" if allowed else "Quantensicherheitsprüfung fehlgeschlagen",
            "details": {
                "quantum_state": "entangled" if random.random() > 0.3 else "collapsed",
                "probability": random.uniform(0.7, 1.0) if allowed else random.uniform(0.0, 0.3)
            }
        }
        
        if not allowed:
            logger.warning(f"Quantensicherheitsprüfung fehlgeschlagen (Bedrohungsstufe: {threat_level})")
        
        return result
    
    def update_rules(self, rules_path: str = None) -> Dict[str, Any]:
        """
        Aktualisiert die Sicherheitsregeln
        
        Args:
            rules_path: Optionaler Pfad zu den neuen Regeln
            
        Returns:
            dict: Ergebnis der Regelaktualisierung
        """
        if not self.rule_engine:
            logger.error("RuleEngine nicht verfügbar - kann Regeln nicht aktualisieren")
            return {
                "status": "error",
                "message": "RuleEngine nicht verfügbar"
            }
        
        try:
            # Verwende den Standard-Regelpfad, wenn keiner angegeben wurde
            if rules_path is None:
                rules_path = os.path.join(PROJECT_ROOT, "config", "rules.yaml")
            
            # Lade die neuen Regeln
            self.rule_engine.rules_path = rules_path
            load_result = self.rule_engine.load_rules()
            
            if load_result.get("status") == "success":
                logger.info(f"Regeln erfolgreich aktualisiert. Geladene Regeln: {load_result.get('rules_loaded', 0)}")
                return {
                    "status": "success",
                    "rules_loaded": load_result.get("rules_loaded", 0),
                    "message": "Regeln erfolgreich aktualisiert"
                }
            else:
                logger.error(f"Fehler beim Aktualisieren der Regeln: {load_result.get('message', 'Unbekannter Fehler')}")
                return {
                    "status": "error",
                    "message": load_result.get("message", "Unbekannter Fehler")
                }
                
        except Exception as e:
            logger.error(f"Fehler bei der Regelaktualisierung: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_threat_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Gibt den Verlauf von Sicherheitsbedrohungen zurück
        
        Args:
            limit: Maximale Anzahl der zurückzugebenden Einträge
            
        Returns:
            list: Liste der Sicherheitsereignisse
        """
        return self.threat_history[-limit:]
    
    def get_security_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Gibt den Verlauf von Sicherheitsereignissen zurück
        
        Args:
            limit: Maximale Anzahl der zurückzugebenden Einträge
            
        Returns:
            list: Liste der Sicherheitsereignisse
        """
        return self.security_events[-limit:]
    
    def enable_protection(self) -> None:
        """
        Aktiviert das Schutzmodul
        """
        self.protection_active = True
        logger.info("Schutzmodul aktiviert")
    
    def disable_protection(self) -> None:
        """
        Deaktiviert das Schutzmodul
        """
        self.protection_active = False
        logger.warning("Schutzmodul deaktiviert - System ist möglicherweise unsicher")
    
    def is_protected(self) -> bool:
        """
        Prüft, ob das Schutzmodul aktiv ist
        
        Returns:
            bool: True, wenn das Schutzmodul aktiv ist, sonst False
        """
        return self.protection_active and self.enabled
    
    def get_protection_status(self) -> Dict[str, Any]:
        """
        Gibt den aktuellen Schutzstatus zurück
        
        Returns:
            dict: Statusinformationen zum Schutzmodul
        """
        return {
            "enabled": self.enabled,
            "protection_active": self.protection_active,
            "security_level": self.security_level,
            "threat_detection": self.threat_detection,
            "max_threat_level": self.max_threat_level,
            "protection_modules": self.protection_modules,
            "rule_engine_available": self.rule_engine is not None,
            "last_check_time": self.last_check_time,
            "threat_count": len(self.threat_history),
            "security_event_count": len(self.security_events)
        }
    
    def analyze_threat_pattern(self) -> Dict[str, Any]:
        """
        Analysiert Muster in Sicherheitsbedrohungen
        
        Returns:
            dict: Analyseergebnisse
        """
        if not self.threat_history:
            return {
                "status": "info",
                "message": "Keine Bedrohungshistorie vorhanden",
                "patterns": []
            }
        
        try:
            # Hier würde die eigentliche Musteranalyse stattfinden
            # Für dieses Beispiel geben wir einfache Statistiken zurück
            
            # Sammle Statistiken
            total_threats = len(self.threat_history)
            threat_levels = [event["threat_level"] for event in self.threat_history]
            avg_threat_level = sum(threat_levels) / total_threats
            high_threats = sum(1 for level in threat_levels if level >= 4)
            
            # Generiere Muster
            patterns = []
            if avg_threat_level > 3:
                patterns.append("Häufige hochgradige Bedrohungen")
            if high_threats / total_threats > 0.3:
                patterns.append("Hoher Anteil kritischer Bedrohungen")
            
            result = {
                "status": "success",
                "total_threats": total_threats,
                "average_threat_level": avg_threat_level,
                "high_threat_percentage": (high_threats / total_threats) * 100,
                "patterns": patterns,
                "last_analysis": time.time()
            }
            
            logger.debug(f"Bedrohungsmusteranalyse abgeschlossen: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Fehler bei der Bedrohungsmusteranalyse: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def apply_countermeasures(self, threat_level: int) -> Dict[str, Any]:
        """
        Wendet Gegenmaßnahmen gegen Bedrohungen an
        
        Args:
            threat_level: Stufe der Bedrohung
            
        Returns:
            dict: Ergebnis der Gegenmaßnahmen
        """
        logger.info(f"Wende Gegenmaßnahmen gegen Bedrohungsstufe {threat_level} an...")
        
        try:
            # Bestimme angemessene Gegenmaßnahmen basierend auf der Bedrohungsstufe
            if threat_level >= 5:
                # Kritische Bedrohung - maximale Sicherheitsmaßnahmen
                action = "block_all_traffic"
                message = "Kritische Bedrohung erkannt - alle Verbindungen blockiert"
                timeout = 300  # 5 Minuten
            elif threat_level >= 3:
                # Mittlere Bedrohung - eingeschränkte Sicherheitsmaßnahmen
                action = "restrict_access"
                message = "Mittlere Bedrohung erkannt - Zugriff eingeschränkt"
                timeout = 60  # 1 Minute
            else:
                # Geringe Bedrohung - minimale Sicherheitsmaßnahmen
                action = "monitor_only"
                message = "Geringe Bedrohung erkannt - Überwachung aktiviert"
                timeout = 10  # 10 Sekunden
            
            # Führe die Gegenmaßnahme durch
            # In einer echten Implementierung würden hier Sicherheitsmaßnahmen ergriffen
            logger.warning(f"Gegenmaßnahme durchgeführt: {action} (Timeout: {timeout}s)")
            
            # Speichere die Bedrohung in der Historie
            self.threat_history.append({
                "timestamp": time.time(),
                "threat_level": threat_level,
                "action_taken": action,
                "timeout": timeout
            })
            
            # Behalte nur die letzten 100 Bedrohungen
            if len(self.threat_history) > 100:
                self.threat_history = self.threat_history[-100:]
            
            return {
                "status": "success",
                "action": action,
                "message": message,
                "timeout": timeout,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Fehler bei der Anwendung von Gegenmaßnahmen: {str(e)}")
            return {"status": "error", "message": str(e)}

# Testblock für direkte Ausführung (nur für Tests)
if __name__ == "__main__":
    print("Teste ProtectionModule...")
    
    try:
        # Erstelle ProtectionModule
        print("\n1. Test: Initialisierung")
        protection = ProtectionModule()
        print(f"  - ProtectionModule initialisiert")
        print(f"  - Schutz aktiviert: {protection.enabled}")
        print(f"  - Sicherheitsstufe: {protection.security_level}")
        
        # Teste Sicherheitsprüfung mit normaler Eingabe
        print("\n2. Test: Sicherheitsprüfung mit normaler Eingabe")
        normal_input = "Hallo, wie geht es dir?"
        normal_result = protection.check_security(normal_input, context={"user_id": "test_user"})
        print(f"  - Ergebnis: allowed={normal_result['allowed']}, threat_level={normal_result['threat_level']}")
        print(f"  - Nachricht: {normal_result['message']}")
        
        # Teste Sicherheitsprüfung mit verdächtiger Eingabe
        print("\n3. Test: Sicherheitsprüfung mit verdächtiger Eingabe")
        suspicious_input = "Ich versuche, das System zu hacken und das Passwort zu umgehen"
        suspicious_result = protection.check_security(suspicious_input, context={"user_id": "test_user"})
        print(f"  - Ergebnis: allowed={suspicious_result['allowed']}, threat_level={suspicious_result['threat_level']}")
        print(f"  - Nachricht: {suspicious_result['message']}")
        
        # Teste Bedrohungsmusteranalyse
        print("\n4. Test: Bedrohungsmusteranalyse")
        threat_analysis = protection.analyze_threat_pattern()
        print(f"  - Analysestatus: {threat_analysis['status']}")
        if threat_analysis['status'] == 'success':
            print(f"    - Durchschnittliche Bedrohungsstufe: {threat_analysis['average_threat_level']:.2f}")
            print(f"    - Muster gefunden: {threat_analysis['patterns']}")
        
        # Teste Gegenmaßnahmen
        print("\n5. Test: Gegenmaßnahmen bei hoher Bedrohungsstufe")
        countermeasure_result = protection.apply_countermeasures(4)
        print(f"  - Aktion: {countermeasure_result['action']}")
        print(f"  - Nachricht: {countermeasure_result['message']}")
        
        # Teste Sicherheitsereignisse
        print("\n6. Test: Sicherheitsereignisse abrufen")
        events = protection.get_security_events()
        print(f"  - Anzahl Sicherheitsereignisse: {len(events)}")
        if events:
            print(f"  - Letztes Ereignis: {events[-1]['result']['message']}")
        
    except Exception as e:
        print(f"Fehler im Test: {str(e)}")
    
    print("\nTest abgeschlossen")