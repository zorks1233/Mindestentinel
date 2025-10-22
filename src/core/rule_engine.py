"""
rule_engine.py
Regel-Engine für Mindestentinel - Verarbeitet Sicherheitsregeln, Zugriffssteuerung und Validierungslogik
"""

import os
import sys
import logging
import yaml
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

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
                        "max_tokens": 500
                    },
                    "self_learning": {
                        "enabled": True,
                        "learning_rate": 0.01,
                        "memory_size": 1000
                    }
                }
            
            config_loader = load_config

# Initialisiere Logging
logger = logging.getLogger("mindestentinel.rule_engine")
logger.setLevel(logging.INFO)

class RuleEngine:
    """
    Regel-Engine für Mindestentinel
    Verarbeitet Sicherheitsregeln, Zugriffssteuerung und Validierungslogik
    """
    
    def __init__(self, rules_path: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialisiert die Regel-Engine
        
        Args:
            rules_path: Pfad zur Regeldatei (standardmäßig config/rules.yaml)
            config: Optionale Konfiguration
        """
        self.rules_path = rules_path
        self.config = config
        self.rules = []
        self.signature_path = None
        
        # Setze Standard-Regelpfad, wenn keiner angegeben wurde
        if not self.rules_path:
            self.rules_path = os.path.join(PROJECT_ROOT, "config", "rules.yaml")
        
        # Setze Standard-Signaturpfad
        self.signature_path = os.path.join(os.path.dirname(self.rules_path), "rules.sig")
        
        logger.debug(f"RuleEngine initialisiert mit Regelpfad: {self.rules_path}")
        logger.debug(f"Signaturpfad: {self.signature_path}")
        
        # Lade Regeln, wenn der Pfad existiert
        if os.path.exists(self.rules_path):
            self.load_rules()
        else:
            logger.warning(f"Regeldatei nicht gefunden unter: {self.rules_path}")
    
    def calculate_signature(self, rules_content: str) -> str:
        """
        Berechnet die Signatur für die Regeln
        
        Args:
            rules_content: Inhalt der Regeldatei
            
        Returns:
            str: SHA-256-Hash der Regeln
        """
        return hashlib.sha256(rules_content.encode()).hexdigest()
    
    def verify_signature(self) -> bool:
        """
        Überprüft die Signatur der Regeldatei
        
        Returns:
            bool: True, wenn die Signatur gültig ist, sonst False
        """
        if not os.path.exists(self.rules_path):
            logger.error(f"Regeldatei nicht gefunden: {self.rules_path}")
            return False
        
        if not os.path.exists(self.signature_path):
            logger.warning(f"Signaturdatei nicht gefunden: {self.signature_path}")
            return False
        
        try:
            # Lese Regeln
            with open(self.rules_path, 'r') as f:
                rules_content = f.read()
            
            # Berechne aktuelle Signatur
            current_signature = self.calculate_signature(rules_content)
            
            # Lese gespeicherte Signatur
            with open(self.signature_path, 'r') as f:
                stored_signature = f.read().strip()
            
            # Vergleiche Signaturen
            is_valid = current_signature == stored_signature
            
            if is_valid:
                logger.debug("Regel-Signatur ist gültig")
            else:
                logger.error("Regel-Signatur ungültig")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Fehler bei der Signaturüberprüfung: {str(e)}")
            return False
    
    def load_rules(self) -> Dict[str, Any]:
        """
        Lädt die Regeln aus der Regeldatei
        
        Returns:
            dict: Geladene Regeln
            
        Raises:
            FileNotFoundError: Wenn die Regeldatei nicht gefunden wird
            ValueError: Wenn die Signatur ungültig ist
        """
        logger.info(f"Lade Regeln aus: {self.rules_path}")
        
        # Überprüfe, ob die Regeldatei existiert
        if not os.path.exists(self.rules_path):
            logger.error(f"Regeldatei nicht gefunden: {self.rules_path}")
            self.rules = []
            return {"status": "error", "message": f"Regeldatei nicht gefunden: {self.rules_path}"}
        
        # Überprüfe die Signatur
        if not self.verify_signature():
            logger.error("Regel-Signatur ungültig")
            self.rules = []
            return {"status": "error", "message": "Regel-Signatur ungültig"}
        
        try:
            # Lade die Regeln
            with open(self.rules_path, 'r') as f:
                rules_data = yaml.safe_load(f)
            
            # Extrahiere die eigentlichen Regeln
            self.rules = rules_data.get('rules', [])
            
            logger.info(f"{len(self.rules)} Regeln erfolgreich geladen")
            return {"status": "success", "rules_loaded": len(self.rules)}
            
        except Exception as e:
            logger.error(f"Fehler beim Laden der Regeln: {str(e)}")
            self.rules = []
            return {"status": "error", "message": str(e)}
    
    def reload_rules(self) -> Dict[str, Any]:
        """
        Lädt die Regeln neu
        
        Returns:
            dict: Ergebnis des Neuladens
        """
        return self.load_rules()
    
    def apply_rules(self, input_data: Any, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Wendet die Regeln auf die Eingabedaten an
        
        Args:
            input_data: Die zu überprüfenden Daten
            context: Optionaler Kontext für die Regelanwendung
            
        Returns:
            dict: Ergebnis der Regelanwendung mit allowed-Flag und Nachricht
        """
        if context is None:
            context = {}
        
        logger.debug(f"Wende {len(self.rules)} Regeln auf Eingabe an")
        
        # Wenn keine Regeln geladen sind, erlaube alles
        if not self.rules:
            logger.warning("Keine Regeln geladen - erlaube alle Eingaben")
            return {"allowed": True, "message": "Keine Regeln geladen"}
        
        # Durchlaufe alle Regeln
        for rule in self.rules:
            try:
                # Überprüfe, ob die Regel auf diesen Kontext anwendbar ist
                if not self._is_rule_applicable(rule, context):
                    continue
                
                # Wende die Regel an
                result = self._apply_single_rule(rule, input_data, context)
                
                if not result["allowed"]:
                    logger.warning(f"Regel verletzt: {rule.get('name', 'Unbenannte Regel')} - {result['message']}")
                    return result
            
            except Exception as e:
                logger.error(f"Fehler bei der Anwendung der Regel '{rule.get('name', 'Unbenannte Regel')}': {str(e)}")
                # Bei Regel-Fehlern erlauben wir die Eingabe nicht
                return {
                    "allowed": False,
                    "message": f"Systemfehler bei der Regelanwendung: {str(e)}"
                }
        
        # Alle Regeln wurden erfolgreich angewendet
        return {"allowed": True, "message": "Alle Regeln erfüllt"}
    
    def _is_rule_applicable(self, rule: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """
        Überprüft, ob eine Regel auf den gegebenen Kontext anwendbar ist
        
        Args:
            rule: Die Regeldefinition
            context: Der aktuelle Kontext
            
        Returns:
            bool: True, wenn die Regel anwendbar ist, sonst False
        """
        # Wenn keine Bedingungen definiert sind, ist die Regel immer anwendbar
        if "conditions" not in rule:
            return True
        
        conditions = rule["conditions"]
        
        # Überprüfe alle Bedingungen
        for condition_key, condition_value in conditions.items():
            # Überprüfe, ob der Schlüssel im Kontext existiert
            if condition_key not in context:
                return False
            
            # Überprüfe, ob der Wert übereinstimmt
            if context[condition_key] != condition_value:
                return False
        
        return True
    
    def _apply_single_rule(self, rule: Dict[str, Any], input_data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wendet eine einzelne Regel auf die Eingabedaten an
        
        Args:
            rule: Die Regeldefinition
            input_data: Die zu überprüfenden Daten
            context: Der aktuelle Kontext
            
        Returns:
            dict: Ergebnis der Regel mit allowed-Flag und Nachricht
        """
        # Überprüfe den Regeltyp
        rule_type = rule.get("type", "validation")
        
        if rule_type == "validation":
            return self._apply_validation_rule(rule, input_data, context)
        elif rule_type == "transformation":
            return self._apply_transformation_rule(rule, input_data, context)
        else:
            logger.warning(f"Unbekannter Regeltyp: {rule_type}")
            return {"allowed": True, "message": f"Unbekannter Regeltyp: {rule_type}"}
    
    def _apply_validation_rule(self, rule: Dict[str, Any], input_data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wendet eine Validierungsregel an
        
        Args:
            rule: Die Regeldefinition
            input_data: Die zu überprüfenden Daten
            context: Der aktuelle Kontext
            
        Returns:
            dict: Ergebnis der Regel mit allowed-Flag und Nachricht
        """
        # Extrahiere Regelparameter
        rule_name = rule.get("name", "Unbenannte Regel")
        rule_message = rule.get("message", "Eingabe verletzt Regel")
        conditions = rule.get("conditions", {})
        
        # Überprüfe alle Bedingungen
        for condition in conditions:
            condition_type = condition.get("type")
            
            if condition_type == "length":
                min_length = condition.get("min")
                max_length = condition.get("max")
                
                # Überprüfe Länge
                if hasattr(input_data, "__len__"):
                    if min_length is not None and len(input_data) < min_length:
                        return {"allowed": False, "message": f"{rule_message} (Zu kurz: min={min_length})"}
                    if max_length is not None and len(input_data) > max_length:
                        return {"allowed": False, "message": f"{rule_message} (Zu lang: max={max_length})"}
            
            elif condition_type == "pattern":
                pattern = condition.get("pattern")
                # Hier würde eine Musterüberprüfung stattfinden
                # (Für dieses Beispiel überspringen wir die Implementierung)
        
        # Alle Bedingungen erfüllt
        return {"allowed": True, "message": f"Regel '{rule_name}' erfüllt"}
    
    def _apply_transformation_rule(self, rule: Dict[str, Any], input_data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wendet eine Transformationsregel an
        
        Args:
            rule: Die Regeldefinition
            input_data: Die zu transformierenden Daten
            context: Der aktuelle Kontext
            
        Returns:
            dict: Transformiertes Ergebnis
        """
        # Für dieses Beispiel geben wir einfach die Eingabe zurück
        # In einer echten Implementierung würden Transformationen durchgeführt
        return {"allowed": True, "transformed_data": input_data, "message": "Transformation erfolgreich"}
    
    def get_rules(self) -> List[Dict[str, Any]]:
        """
        Gibt die geladenen Regeln zurück
        
        Returns:
            list: Liste der Regeln
        """
        return self.rules
    
    def add_rule(self, rule: Dict[str, Any]) -> None:
        """
        Fügt eine neue Regel hinzu
        
        Args:
            rule: Die neue Regel
        """
        self.rules.append(rule)
        logger.info(f"Neue Regel hinzugefügt: {rule.get('name', 'Unbenannte Regel')}")
    
    def remove_rule(self, rule_name: str) -> bool:
        """
        Entfernt eine Regel nach Namen
        
        Args:
            rule_name: Name der zu entfernenden Regel
            
        Returns:
            bool: True, wenn die Regel entfernt wurde, sonst False
        """
        initial_count = len(self.rules)
        self.rules = [rule for rule in self.rules if rule.get('name') != rule_name]
        removed = len(self.rules) < initial_count
        
        if removed:
            logger.info(f"Regel entfernt: {rule_name}")
        else:
            logger.warning(f"Regel nicht gefunden zum Entfernen: {rule_name}")
        
        return removed
    
    def save_rules(self, path: Optional[str] = None) -> Dict[str, Any]:
        """
        Speichert die Regeln in eine Datei
        
        Args:
            path: Optionaler Pfad zum Speichern (standardmäßig rules_path)
            
        Returns:
            dict: Ergebnis des Speichervorgangs
        """
        save_path = path or self.rules_path
        
        try:
            # Bereite Daten für das Speichern vor
            rules_data = {
                "version": "1.0",
                "timestamp": datetime.now().isoformat(),
                "rules": self.rules
            }
            
            # Speichere die Regeln
            with open(save_path, 'w') as f:
                yaml.dump(rules_data, f, default_flow_style=False)
            
            # Berechne und speichere die Signatur
            with open(save_path, 'r') as f:
                rules_content = f.read()
            
            signature = self.calculate_signature(rules_content)
            with open(self.signature_path, 'w') as f:
                f.write(signature)
            
            logger.info(f"Regeln erfolgreich gespeichert unter: {save_path}")
            return {"status": "success", "path": save_path}
            
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Regeln: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def is_valid(self) -> bool:
        """
        Überprüft, ob die Regel-Engine gültige Regeln hat
        
        Returns:
            bool: True, wenn Regeln geladen sind und gültig sind
        """
        return bool(self.rules) and self.verify_signature()

# Testblock für direkte Ausführung (nur für Tests)
if __name__ == "__main__":
    print("Teste RuleEngine...")
    
    # Erstelle temporäre Regeldatei für den Test
    test_rules_path = os.path.join(PROJECT_ROOT, "config", "test_rules.yaml")
    test_signature_path = os.path.join(PROJECT_ROOT, "config", "test_rules.sig")
    
    try:
        # Erstelle Test-Regeln
        test_rules = {
            "rules": [
                {
                    "name": "Test-Regel 1",
                    "type": "validation",
                    "message": "Testfehler",
                    "conditions": [
                        {
                            "type": "length",
                            "min": 5,
                            "max": 20
                        }
                    ]
                }
            ]
        }
        
        # Speichere Test-Regeln
        os.makedirs(os.path.dirname(test_rules_path), exist_ok=True)
        with open(test_rules_path, 'w') as f:
            yaml.dump(test_rules, f)
        
        # Berechne und speichere Signatur
        with open(test_rules_path, 'r') as f:
            rules_content = f.read()
        signature = hashlib.sha256(rules_content.encode()).hexdigest()
        with open(test_signature_path, 'w') as f:
            f.write(signature)
        
        # Teste RuleEngine
        print("\n1. Test: Initialisierung mit Test-Regeln")
        engine = RuleEngine(rules_path=test_rules_path)
        print(f"  - Regeln geladen: {len(engine.get_rules())}")
        
        print("\n2. Test: Gültige Eingabe (Länge 10)")
        result = engine.apply_rules("0123456789")
        print(f"  - Ergebnis: allowed={result['allowed']}, message='{result['message']}'")
        
        print("\n3. Test: Ungültige Eingabe (zu kurz)")
        result = engine.apply_rules("1234")
        print(f"  - Ergebnis: allowed={result['allowed']}, message='{result['message']}'")
        
        print("\n4. Test: Regelspeicherung")
        save_result = engine.save_rules()
        print(f"  - Speichern erfolgreich: {save_result['status'] == 'success'}")
        
    except Exception as e:
        print(f"Fehler im Test: {str(e)}")
    finally:
        # Bereinige Testdateien
        if os.path.exists(test_rules_path):
            os.remove(test_rules_path)
        if os.path.exists(test_signature_path):
            os.remove(test_signature_path)
    
    print("\nTest abgeschlossen")