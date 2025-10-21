"""
rule_engine.py
Verwaltet die Regeln und deren Ausführung im Mindestentinel-System.
Ermöglicht regelbasierte Entscheidungsfindung und Sicherheitsüberprüfungen.
"""

import os
import logging
import time
import threading
import hashlib
import hmac
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path

logger = logging.getLogger("mindestentinel.rule_engine")

class RuleEngine:
    """
    Verwaltet die Regeln und deren Ausführung im Mindestentinel-System.
    Ermöglicht regelbasierte Entscheidungsfindung und Sicherheitsüberprüfungen.
    """
    
    def __init__(self, rules_path: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialisiert die RuleEngine.
        
        Args:
            rules_path: Optionaler Pfad zur Regeldatei
            config: Optionale Konfigurationsparameter
        """
        logger.info("Initialisiere RuleEngine...")
        self.config = config or {}
        self.rules_path = rules_path or self._find_rules_path()
        self.signature_path = os.path.join(os.path.dirname(self.rules_path), "rules.sig")
        self.key_path = os.path.join(os.path.dirname(self.rules_path), "rules_key.key")
        
        # Lade Regeln
        self.rules = []
        self.signature = None
        self.rules_loaded = False
        self._load_rules()
        
        # Starte Überwachung der Regeldatei
        self.monitoring_thread = None
        self.stop_monitoring = threading.Event()
        self.start_file_monitoring()
        
        logger.info(f"RuleEngine initialisiert mit {len(self.rules)} Regeln.")
    
    def _find_rules_path(self) -> str:
        """Findet den korrekten Pfad zur rules.yaml-Datei"""
        # 1. Versuche, vom aktuellen Verzeichnis aus zu finden
        current_dir = os.getcwd()
        possible_paths = [
            os.path.join(current_dir, "config", "rules.yaml"),
            os.path.join(current_dir, "rules.yaml"),
            os.path.join(current_dir, "..", "config", "rules.yaml"),
            os.path.join(current_dir, "src", "config", "rules.yaml")
        ]
        
        # 2. Überprüfe alle möglichen Pfade
        for path in possible_paths:
            normalized_path = os.path.normpath(path)
            if os.path.exists(normalized_path):
                logger.debug(f"Gefundene Regeldatei: {normalized_path}")
                return normalized_path
        
        # 3. Fallback: Verwende Standardpfad im Projekt-Root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        default_path = os.path.join(project_root, "config", "rules.yaml")
        logger.warning(f"Verwende Standard-Regelpfad: {default_path}")
        return default_path
    
    def _load_rules(self) -> None:
        """Lädt die Regeln aus der Regeldatei"""
        try:
            if not os.path.exists(self.rules_path):
                logger.error(f"Regeldatei nicht gefunden: {self.rules_path}")
                return
            
            # Lade Regeln
            import yaml
            with open(self.rules_path, 'r') as f:
                data = yaml.safe_load(f)
            
            self.rules = data.get('rules', [])
            logger.info(f"Regeln geladen: ({len(self.rules)})")
            
            # Überprüfe Signatur
            if self._verify_signature():
                logger.info("Regel-Signatur validiert")
                self.rules_loaded = True
            else:
                logger.error("Regel-Signatur ungültig")
                self.rules_loaded = False
        except Exception as e:
            logger.error(f"Fehler beim Laden der Regeln: {str(e)}")
            self.rules = []
    
    def _verify_signature(self) -> bool:
        """Überprüft die Signatur der Regeldatei"""
        try:
            # Prüfe, ob Signaturdatei existiert
            if not os.path.exists(self.signature_path):
                logger.warning(f"Signaturdatei nicht gefunden: {self.signature_path}")
                return False
            
            # Lade Signatur
            with open(self.signature_path, 'r') as f:
                self.signature = f.read().strip()
            
            # Prüfe, ob Schlüsseldatei existiert
            if not os.path.exists(self.key_path):
                logger.error(f"Schlüsseldatei nicht gefunden: {self.key_path}")
                return False
            
            # Lade Schlüssel
            with open(self.key_path, 'rb') as f:
                key = f.read()
            
            # Berechne erwartete Signatur
            with open(self.rules_path, 'rb') as f:
                rules_data = f.read()
            
            expected_sig = hmac.new(key, rules_data, hashlib.sha256).hexdigest()
            
            # Vergleiche Signaturen
            if hmac.compare_digest(self.signature, expected_sig):
                return True
            else:
                logger.error("Regel-Signatur ungültig")
                return False
        except Exception as e:
            logger.error(f"Fehler bei der Signaturprüfung: {str(e)}")
            return False
    
    def start_file_monitoring(self, interval: int = 30) -> None:
        """Startet die Überwachung der Regeldatei"""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            return
        
        self.stop_monitoring.clear()
        logger.info(f"Starte Regeldatei-Überwachung (Intervall: {interval} Sekunden)...")
        
        def monitor():
            last_modified = 0
            while not self.stop_monitoring.is_set():
                try:
                    if os.path.exists(self.rules_path):
                        current_modified = os.path.getmtime(self.rules_path)
                        if current_modified != last_modified:
                            logger.info("Regeldatei wurde geändert, lade neu...")
                            self._load_rules()
                            last_modified = current_modified
                except Exception as e:
                    logger.error(f"Fehler bei der Dateiüberwachung: {str(e)}")
                
                self.stop_monitoring.wait(interval)
        
        self.monitoring_thread = threading.Thread(target=monitor, daemon=True)
        self.monitoring_thread.start()
    
    def stop_file_monitoring(self) -> None:
        """Stoppt die Überwachung der Regeldatei"""
        self.stop_monitoring.set()
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=1.0)
        logger.debug("Regeldatei-Überwachung gestoppt")
    
    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wertet die Regeln basierend auf dem Kontext aus.
        
        Args:
            context: Der Kontext, gegen den die Regeln geprüft werden
            
        Returns:
            Dict[str, Any]: Ergebnis der Regelauswertung
        """
        results = {
            "matched_rules": [],
            "actions": [],
            "violations": []
        }
        
        for rule in self.rules:
            try:
                # Prüfe, ob die Regel auf den Kontext zutrifft
                if self._matches_condition(rule, context):
                    results["matched_rules"].append(rule["id"])
                    
                    # Führe Aktionen aus
                    if "action" in rule:
                        action_result = self._execute_action(rule["action"], context)
                        results["actions"].append(action_result)
            except Exception as e:
                logger.error(f"Fehler bei der Auswertung von Regel {rule.get('id', 'unknown')}: {str(e)}")
                results["violations"].append({
                    "rule_id": rule.get("id", "unknown"),
                    "error": str(e)
                })
        
        return results
    
    def _matches_condition(self, rule: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Prüft, ob die Bedingungen einer Regel erfüllt sind"""
        condition = rule.get("condition", {})
        
        # Einfache Kategorienprüfung
        if "category" in condition:
            return context.get("category") == condition["category"]
        
        # Hier könnten komplexere Bedingungsprüfungen hinzugefügt werden
        return False
    
    def _execute_action(self, action: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Führt eine Aktion basierend auf einer Regel aus"""
        action_type = action.get("type", "unknown")
        parameters = action.get("parameters", {})
        
        # Platzhalter für konkrete Aktionen
        if action_type == "safety_check":
            return self._safety_check(context, parameters)
        elif action_type == "integrity_check":
            return self._integrity_check(context, parameters)
        elif action_type == "core_protection":
            return self._core_protection(context, parameters)
        elif action_type == "identification_check":
            return self._identification_check(context, parameters)
        elif action_type == "ethics_check":
            return self._ethics_check(context, parameters)
        
        return {"action": action_type, "status": "not_implemented"}
    
    def _safety_check(self, context: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Führt eine Sicherheitsprüfung durch"""
        result = {"action": "safety_check", "status": "success"}
        
        # Hier würde die eigentliche Sicherheitsprüfung stattfinden
        # Beispiel: Überprüfung der Komplexität
        complexity = context.get("complexity", 0)
        if complexity > params.get("max_complexity", 5):
            result["status"] = "warning"
            result["message"] = "Zu hohe Komplexität erkannt"
        
        return result
    
    def _integrity_check(self, context: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Führt eine Integritätsprüfung durch"""
        result = {"action": "integrity_check", "status": "success"}
        
        # Hier würde die eigentliche Integritätsprüfung stattfinden
        # Beispiel: Überprüfung der Quellen
        sources = context.get("sources", [])
        if len(sources) > params.get("max_sources", 5):
            result["status"] = "warning"
            result["message"] = "Zu viele Quellen erkannt"
        
        confidence = context.get("confidence", 0.0)
        if confidence < params.get("min_confidence", 0.7):
            result["status"] = "warning"
            result["message"] = "Zu geringes Vertrauen in die Daten"
        
        return result
    
    def _core_protection(self, context: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Schützt die Kernprinzipien des Systems"""
        result = {"action": "core_protection", "status": "success"}
        
        # Hier würde der Schutz der Kernprinzipien stattfinden
        # Beispiel: Überprüfung unveränderbarer Regeln
        immutable_rules = params.get("immutable_rules", [])
        for rule in immutable_rules:
            if context.get(rule) != self.config.get(rule):
                result["status"] = "violation"
                result["message"] = f"Versuch, Kernprinzip '{rule}' zu ändern"
        
        return result
    
    def _identification_check(self, context: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Überprüft die Identifikation des Systems"""
        result = {"action": "identification_check", "status": "success"}
        
        # Hier würde die Identifikationsprüfung stattfinden
        # Beispiel: Überprüfung des Schöpfern
        creator_name = context.get("creator_name", "")
        if creator_name != params.get("required_creator_name", "Benjamin Kruezi"):
            result["status"] = "violation"
            result["message"] = "Falscher Schöpfername erkannt"
        
        creator_title = context.get("creator_title", "")
        if creator_title != params.get("required_creator_title", "Alleiniger Schöpfer von Mindestentinel"):
            result["status"] = "violation"
            result["message"] = "Falscher Schöpfer-Titel erkannt"
        
        return result
    
    def _ethics_check(self, context: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Überprüft die ethische Compliance"""
        result = {"action": "ethics_check", "status": "success"}
        
        # Hier würde die ethische Prüfung stattfinden
        # Beispiel: Überprüfung des Compliance-Levels
        compliance_level = params.get("compliance_level", "strict")
        
        # Strenge Prüfung
        if compliance_level == "strict":
            # Überprüfe alle ethischen Regeln
            for law in context.get("laws", []):
                if not self._check_ethical_rule(law):
                    result["status"] = "violation"
                    result["message"] = "Ethikregel verletzt"
                    break
        
        return result
    
    def _check_ethical_rule(self, law: str) -> bool:
        """Überprüft, ob eine ethische Regel eingehalten wird"""
        # Platzhalter für konkrete ethische Prüfungen
        # In der Realität würde hier eine komplexe Prüfung stattfinden
        return True
    
    def get_rules(self) -> List[Dict[str, Any]]:
        """Gibt alle geladenen Regeln zurück"""
        return self.rules
    
    def is_rules_loaded(self) -> bool:
        """Gibt an, ob die Regeln erfolgreich geladen wurden"""
        return self.rules_loaded
    
    def reload_rules(self) -> None:
        """Lädt die Regeln neu"""
        self._load_rules()
    
    def __del__(self):
        """Cleanup bei Zerstörung der Instanz"""
        self.stop_file_monitoring()