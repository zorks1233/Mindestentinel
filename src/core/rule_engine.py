# src/core/rule_engine.py
"""
rule_engine.py - Regel-Engine für Mindestentinel

Diese Regel-Engine validiert Aktionen gegen vordefinierte Regeln.
Es verwendet eine einfache, aber effektive Struktur für die Regelverwaltung.

Wichtige Funktionen:
- Regeln aus YAML/JSON laden
- Regeln gegen Kontext auswerten
- Sicherheitsprüfungen für kritische Operationen
- Unterstützung für Regelkategorien
"""

import logging
import os
import yaml
import json
import hmac
import hashlib
from typing import Dict, Any, List, Optional

logger = logging.getLogger("mindestentinel.rule_engine")

class RuleEngine:
    """
    Regel-Engine für Sicherheits- und Validierungsregeln.
    
    Lädt Regeln aus einer Datei und ermöglicht die Auswertung gegen einen Kontext.
    """
    
    def __init__(self, rules_path: str = "config/rules.yaml", enforce_signature: bool = True):
        """
        Initialisiert die Regel-Engine.
        
        Args:
            rules_path: Pfad zur Regelkonfigurationsdatei
            enforce_signature: Gibt an, ob die Regelsignatur erzwungen wird
        """
        self.rules_path = rules_path
        self.enforce_signature = enforce_signature
        self.rules = []
        self.signature_valid = False
        
        # Lade Regeln
        self._load_rules()
        
        # Prüfe Signatur, falls erforderlich
        if enforce_signature:
            self.signature_valid = self._verify_signature()
            if not self.signature_valid:
                logger.critical("Regel-Signatur ungültig und enforce_signature=True. Laden abgebrochen.")
                raise RuntimeError("Rules signature invalid")
        
        logger.info("RuleEngine initialisiert mit %d Regeln.", len(self.rules))
    
    def _load_rules(self):
        """Lädt Regeln aus der Konfigurationsdatei."""
        try:
            # Prüfe, ob die Datei existiert
            if not os.path.exists(self.rules_path):
                logger.error("Regelkonfigurationsdatei nicht gefunden: %s", self.rules_path)
                return
            
            # Lade die Datei basierend auf der Erweiterung
            ext = os.path.splitext(self.rules_path)[1].lower()
            if ext == ".yaml" or ext == ".yml":
                with open(self.rules_path, 'r') as f:
                    self.rules = yaml.safe_load(f)
            elif ext == ".json":
                with open(self.rules_path, 'r') as f:
                    self.rules = json.load(f)
            else:
                logger.error("Unbekanntes Format für Regeldatei: %s", ext)
                return
            
            # Stelle sicher, dass rules eine Liste ist
            if not isinstance(self.rules, list):
                logger.warning("Regeln sind kein Array. Konvertiere zu Liste.")
                self.rules = [self.rules] if self.rules else []
            
            logger.info("Regeln geladen aus %s", self.rules_path)
            
        except Exception as e:
            logger.error("Fehler beim Laden der Regeln: %s", str(e), exc_info=True)
            self.rules = []
    
    def _verify_signature(self) -> bool:
        """
        Überprüft die Signatur der Regeldatei.
        
        Returns:
            bool: True, wenn die Signatur gültig ist, sonst False
        """
        sig_path = os.path.join(os.path.dirname(self.rules_path), "rules.sig")
        key_path = os.path.join(os.path.dirname(self.rules_path), "rules_key.key")
        
        # Prüfe, ob die Dateien existieren
        if not os.path.exists(sig_path) or not os.path.exists(key_path):
            logger.warning("Signaturdatei oder Schlüssel nicht gefunden")
            return False
        
        try:
            # Lade den Schlüssel
            with open(key_path, 'rb') as f:
                key = f.read()
            
            # Lade die Signatur
            with open(sig_path, 'r') as f:
                expected_sig = f.read().strip()
            
            # Berechne die tatsächliche Signatur
            with open(self.rules_path, 'rb') as f:
                data = f.read()
            actual_sig = hmac.new(key, data, hashlib.sha256).hexdigest()
            
            # Vergleiche die Signaturen
            if hmac.compare_digest(actual_sig, expected_sig):
                logger.info("Regel-Signatur erfolgreich verifiziert")
                return True
            else:
                logger.error("Regel-Signatur ungültig")
                return False
                
        except Exception as e:
            logger.error("Fehler bei der Signaturprüfung: %s", str(e), exc_info=True)
            return False
    
    def evaluate_rule(self, rule: Dict, context: Dict) -> bool:
        """
        Evaluiert eine Regel gegen einen Kontext.
        
        Args:
            rule: Die zu evaluierende Regel
            context: Der Kontext, gegen den die Regel evaluiert wird
            
        Returns:
            bool: True, wenn die Regel erfüllt ist, sonst False
        """
        try:
            # Prüfe die Kategorie der Regel
            category = rule.get("category", "general")
            
            # Spezialbehandlung für Lernziele
            if category == "learning_goals" and "goal" in context:
                goal = context["goal"]
                # Prüfe, ob das Ziel sicher ist
                return self._evaluate_learning_goal(goal)
            
            # Standardregel-Evaluation
            conditions = rule.get("conditions", {})
            for key, value in conditions.items():
                if key not in context or context[key] != value:
                    return False
            
            return True
            
        except Exception as e:
            logger.error("Fehler bei der Regel-Evaluation: %s", str(e), exc_info=True)
            return False
    
    def _evaluate_learning_goal(self, goal: Dict) -> bool:
        """
        Evaluiert spezielle Regeln für Lernziele.
        
        Args:
            goal: Das Lernziel
            
        Returns:
            bool: True, wenn das Lernziel sicher ist, sonst False
        """
        # Prüfe die Komplexität
        complexity = goal.get("complexity", 3)
        if complexity > 5:
            logger.warning("Lernziel mit zu hoher Komplexität (%d)", complexity)
            return False
        
        # Prüfe die Kategorie
        category = goal.get("category", "general")
        if category not in ["cognitive", "optimization", "knowledge", "security"]:
            logger.warning("Lernziel mit ungültiger Kategorie: %s", category)
            return False
        
        # Alle Prüfungen bestanden
        return True
    
    def is_consistent(self) -> bool:
        """
        Prüft, ob die Regeln konsistent sind.
        
        Returns:
            bool: True, wenn die Regeln konsistent sind, sonst False
        """
        # In dieser einfachen Implementierung prüfen wir nur, ob Regeln vorhanden sind
        return len(self.rules) > 0
    
    def get_rules(self) -> List[Dict]:
        """
        Gibt alle Regeln zurück.
        
        Returns:
            List[Dict]: Liste aller Regeln
        """
        return self.rules
    
    def get_rules_by_category(self, category: str) -> List[Dict]:
        """
        Gibt Regeln einer bestimmten Kategorie zurück.
        
        Args:
            category: Die gewünschte Kategorie
            
        Returns:
            List[Dict]: Liste der Regeln in der Kategorie
        """
        return [rule for rule in self.rules if rule.get("category") == category]