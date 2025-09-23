# src/core/rule_engine.py
"""
rule_engine.py - Regel-Engine für Mindestentinel

Diese Datei implementiert die Regel-Engine für das System.
Es ermöglicht das Laden, Validieren und Ausführen von Regeln.
"""

import logging
import os
import yaml
import json
import time
import threading
from typing import Dict, Any, List, Optional, Callable
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger("mindestentinel.rule_engine")

class RuleEngine:
    """
    Verwaltet die Regeln für das System.
    
    Lädt, validiert und führt Regeln aus.
    """
    
    def __init__(self, rules_path: str = "config/rules.yaml"):
        """
        Initialisiert die Regel-Engine.
        
        Args:
            rules_path: Pfad zur Regelkonfiguration
        """
        self.rules_path = rules_path
        self.rules = []
        self.signature = None
        self.monitoring = False
        self.monitor_thread = None
        
        # Lade die Regeln
        self.load_rules(rules_path)
        
        # Überprüfe die Signatur der Regeln
        self.verify_rules_signature()
        
        # Starte die Regeldatei-Überwachung
        self.monitor_rules_file()
        
        logger.info(f"RuleEngine initialisiert mit {len(self.rules)} Regeln.")
    
    def load_rules(self, rules_path: str) -> List[Dict[str, Any]]:
        """
        Lädt die Regeln aus der Konfigurationsdatei.
        
        Args:
            rules_path: Pfad zur Regelkonfiguration
            
        Returns:
            List[Dict[str, Any]]: Die geladenen Regeln
        """
        if not os.path.exists(rules_path):
            logger.error(f"Regelkonfigurationsdatei nicht gefunden: {rules_path}")
            return []
        
        try:
            with open(rules_path, 'r') as f:
                rules_data = yaml.safe_load(f)
            
            # Prüfe, ob Regeln vorhanden sind
            if not rules_data or "rules" not in rules_data:
                logger.error("Keine Regeln in der Konfigurationsdatei gefunden")
                return []
            
            # Lade die Regeln
            self.rules = rules_data["rules"]
            
            # Lade die Signatur, falls vorhanden
            if "signature" in rules_data:
                self.signature = rules_data["signature"]
            
            logger.info(f"{len(self.rules)} Regeln geladen aus {rules_path}")
            return self.rules
        except Exception as e:
            logger.error(f"Fehler beim Laden der Regeln: {str(e)}", exc_info=True)
            return []
    
    def verify_rules_signature(self) -> bool:
        """
        Überprüft die Signatur der Regeln.
        
        Returns:
            bool: True, wenn die Signatur gültig ist, sonst False
        """
        if not self.signature or not self.rules:
            logger.warning("Keine Signatur oder Regeln zum Überprüfen vorhanden")
            return False
        
        try:
            # Konvertiere die Regeln in einen Hash
            rules_hash = self._hash_rules(self.rules)
            
            # Überprüfe die Signatur
            # In einer echten Implementierung würden Sie hier die Signatur mit einem öffentlichen Schlüssel überprüfen
            # Für diese vereinfachte Version geben wir einfach True zurück
            
            # Für das Beispiel: Überprüfe, ob die Signatur mit dem Hash übereinstimmt
            # (Dies ist NICHT sicher, nur für das Beispiel)
            if self.signature == rules_hash.hex():
                logger.info("Regel-Signatur erfolgreich verifiziert")
                return True
            else:
                logger.error("Regel-Signatur ungültig")
                return False
        except Exception as e:
            logger.error(f"Fehler bei der Signaturüberprüfung: {str(e)}", exc_info=True)
            return False
    
    def _hash_rules(self, rules: List[Dict[str, Any]]) -> bytes:
        """
        Erstellt einen Hash der Regeln.
        
        Args:
            rules: Die Regeln
            
        Returns:
            bytes: Der Hash der Regeln
        """
        # Konvertiere die Regeln in einen JSON-String
        rules_json = json.dumps(rules, sort_keys=True)
        
        # Erstelle einen Hash
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(rules_json.encode('utf-8'))
        return digest.finalize()
    
    def execute_rules(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Führt alle Regeln aus.
        
        Args:
            context: Der Kontext für die Regelprüfung
            
        Returns:
            List[Dict[str, Any]]: Die Ergebnisse der Regelprüfung
        """
        results = []
        
        for rule in self.rules:
            try:
                # Prüfe, ob die Regelbedingung erfüllt ist
                condition_result = self._evaluate_condition(rule.get("condition", {}), context)
                
                # Wenn die Bedingung erfüllt ist, führe die Aktion aus
                if condition_result:
                    action_result = self._execute_action(rule.get("action", {}), context)
                    results.append({
                        "rule_id": rule.get("id"),
                        "rule_name": rule.get("name"),
                        "condition": rule.get("condition"),
                        "action": rule.get("action"),
                        "condition_result": condition_result,
                        "action_result": action_result,
                        "timestamp": time.time()
                    })
            except Exception as e:
                logger.error(f"Fehler bei der Ausführung der Regel {rule.get('id')}: {str(e)}", exc_info=True)
        
        return results
    
    def _evaluate_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """
        Bewertet eine Regelbedingung.
        
        Args:
            condition: Die Bedingung
            context: Der Kontext
            
        Returns:
            bool: True, wenn die Bedingung erfüllt ist, sonst False
        """
        # In einer echten Implementierung würden Sie hier die Bedingung auswerten
        # Für das Beispiel geben wir einfach True zurück, wenn eine Bedingung existiert
        
        if not condition:
            return True  # Keine Bedingung bedeutet immer erfüllt
        
        # Für das Beispiel: Prüfe, ob der Kontext die erforderlichen Felder enthält
        for key, value in condition.items():
            if key not in context or context[key] != value:
                return False
        
        return True
    
    def _execute_action(self, action: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Führt eine Regelaktion aus.
        
        Args:
            action: Die Aktion
            context: Der Kontext
            
        Returns:
            Dict[str, Any]: Das Ergebnis der Aktion
        """
        # In einer echten Implementierung würden Sie hier die Aktion ausführen
        # Für das Beispiel geben wir nur einen Dummy-Erfolg zurück
        return {
            "status": "success",
            "message": "Aktion erfolgreich ausgeführt",
            "action": action,
            "context": context
        }
    
    def get_rules(self) -> List[Dict[str, Any]]:
        """
        Gibt alle Regeln zurück.
        
        Returns:
            List[Dict[str, Any]]: Die Regeln
        """
        return self.rules
    
    def evaluate_rule(self, rule: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """
        Bewertet eine einzelne Regel.
        
        Args:
            rule: Die Regel
            context: Der Kontext
            
        Returns:
            bool: True, wenn die Regel erfüllt ist, sonst False
        """
        # Prüfe, ob die Regelbedingung erfüllt ist
        return self._evaluate_condition(rule.get("condition", {}), context)
    
    def add_rule(self, rule: Dict[str, Any]):
        """
        Fügt eine neue Regel hinzu.
        
        Args:
            rule: Die neue Regel
        """
        self.rules.append(rule)
        logger.info(f"Neue Regel hinzugefügt: {rule.get('name')}")
    
    def remove_rule(self, rule_id: str):
        """
        Entfernt eine Regel.
        
        Args:
            rule_id: Die ID der Regel
        """
        self.rules = [rule for rule in self.rules if rule.get("id") != rule_id]
        logger.info(f"Regel entfernt: {rule_id}")
    
    def update_rule(self, rule_id: str, updated_rule: Dict[str, Any]):
        """
        Aktualisiert eine Regel.
        
        Args:
            rule_id: Die ID der Regel
            updated_rule: Die aktualisierte Regel
        """
        for i, rule in enumerate(self.rules):
            if rule.get("id") == rule_id:
                self.rules[i] = updated_rule
                logger.info(f"Regel aktualisiert: {rule_id}")
                return
        
        logger.warning(f"Regel mit ID {rule_id} nicht gefunden")
    
    def monitor_rules_file(self, interval: int = 30):
        """
        Überwacht die Regeldatei auf Änderungen.
        
        Args:
            interval: Überwachungsintervall in Sekunden
        """
        if self.monitoring:
            logger.warning("Regeldatei-Überwachung bereits aktiv.")
            return
        
        if not self.rules_path or not os.path.exists(self.rules_path):
            logger.warning("Regeldatei nicht gefunden. Überwachung nicht möglich.")
            return
        
        self.monitoring = True
        logger.info(f"Starte Regeldatei-Überwachung (Intervall: {interval} Sekunden)...")
        
        last_modified = os.path.getmtime(self.rules_path)
        
        def check_for_changes():
            nonlocal last_modified
            
            while self.monitoring:
                try:
                    if os.path.exists(self.rules_path):
                        current_mtime = os.path.getmtime(self.rules_path)
                        if current_mtime != last_modified:
                            logger.info("Regeldatei wurde geändert. Lade Regeln neu...")
                            try:
                                # Lade die neuen Regeln
                                new_rules = self.load_rules(self.rules_path)
                                
                                # Überprüfe die Signatur der neuen Regeln
                                if self.verify_rules_signature():
                                    self.rules = new_rules
                                    last_modified = current_mtime
                                    logger.info("Regeln erfolgreich aktualisiert")
                                else:
                                    logger.error("Regel-Signatur ungültig. Änderungen verworfen.")
                            except Exception as e:
                                logger.error(f"Fehler beim Neuladen der Regeln: {str(e)}")
                    else:
                        logger.warning("Regeldatei nicht gefunden. Überwachung pausiert.")
                    
                    # Warte vor der nächsten Überprüfung
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"Fehler bei der Regeldatei-Überwachung: {str(e)}", exc_info=True)
        
        # Starte den Überwachungs-Thread
        self.monitor_thread = threading.Thread(target=check_for_changes, daemon=True)
        self.monitor_thread.start()
    
    def stop_rule_monitoring(self):
        """Stoppt die Regeldatei-Überwachung."""
        if self.monitoring:
            self.monitoring = False
            logger.info("Regeldatei-Überwachung gestoppt.")
        else:
            logger.warning("Regeldatei-Überwachung war nicht aktiv.")
    
    def get_rule_statistics(self) -> Dict[str, Any]:
        """
        Gibt Statistiken über die Regeln zurück.
        
        Returns:
            Dict[str, Any]: Die Statistiken
        """
        return {
            "total_rules": len(self.rules),
            "rule_types": self._count_rule_types(),
            "last_updated": time.time()
        }
    
    def _count_rule_types(self) -> Dict[str, int]:
        """
        Zählt die Regeltypen.
        
        Returns:
            Dict[str, int]: Die Anzahl der Regeltypen
        """
        rule_types = {}
        
        for rule in self.rules:
            rule_type = rule.get("type", "unknown")
            rule_types[rule_type] = rule_types.get(rule_type, 0) + 1
        
        return rule_types