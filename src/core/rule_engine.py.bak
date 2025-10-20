# src/core/rule_engine.py
"""
rule_engine.py - Regel-Engine für Mindestentinel

Diese Datei implementiert die Regel-Engine des Systems.
"""

import os
import logging
import yaml
import hmac
import hashlib
from typing import List, Dict, Any, Optional

logger = logging.getLogger("mindestentinel.rule_engine")


class RuleEngine:
    """Verwaltet Regeln und deren Ausführung"""

    def __init__(self, rules_path: str):
        """Initialisiert die Regel-Engine

        Args:
            rules_path: Pfad zur Regelkonfigurationsdatei
        """
        self.rules_path = rules_path
        self.rules = []
        self.signature = None
        self.key_path = os.path.join(os.path.dirname(rules_path), "rules_key.key")
        self.sig_path = os.path.join(os.path.dirname(rules_path), "rules.sig")

        # Lade Regeln
        self.rules = self.load_rules(rules_path)

        # Überprüfe die Signatur
        if not self.verify_signature():
            logger.warning("Regel-Signatur ungültig oder nicht vorhanden")

        # Starte Überwachung der Regeldatei
        self.start_rule_file_monitoring()

        logger.info(f"RuleEngine initialisiert mit {len(self.rules)} Regeln.")

    def load_rules(self, rules_path: str) -> List[Dict[str, Any]]:
        """Lädt die Regeln aus der Konfigurationsdatei.

        Args:
            rules_path: Pfad zur Regelkonfiguration

        Returns:
            List[Dict[str, Any]]: Die geladenen Regeln
        """
        if not os.path.exists(rules_path):
            logger.error(f"Regelkonfigurationsdatei nicht gefunden: {rules_path}")
            return []

        try:
            with open(rules_path, 'r', encoding='utf-8') as f:
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

            # KLARE ANZEIGE DER GELADENEN REGELN AM ANFANG
            logger.info(f"Regeln geladen: ({len(self.rules)})")

            return self.rules
        except Exception as e:
            logger.error(f"Fehler beim Laden der Regeln: {str(e)}", exc_info=True)
            return []

    def verify_signature(self) -> bool:
        """Überprüft die Signatur der Regeldatei

        Returns:
            bool: True, wenn die Signatur gültig ist, sonst False
        """
        # Prüfe, ob die Signaturdatei existiert
        if not os.path.exists(self.sig_path):
            logger.warning(f"Signaturdatei nicht gefunden: {self.sig_path}")
            return False

        # Prüfe, ob der Schlüssel existiert
        if not os.path.exists(self.key_path):
            logger.warning(f"Schlüsseldatei nicht gefunden: {self.key_path}")
            return False

        try:
            # Lade den Schlüssel
            with open(self.key_path, 'rb') as f:
                key = f.read()

            # Lade die Signatur
            with open(self.sig_path, 'r') as f:
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
            logger.error(f"Fehler bei der Signaturüberprüfung: {str(e)}", exc_info=True)
            return False

    def start_rule_file_monitoring(self, interval: int = 30):
        """Startet die Überwachung der Regeldatei

        Args:
            interval: Überwachungsintervall in Sekunden
        """
        logger.info(f"Starte Regeldatei-Überwachung (Intervall: {interval} Sekunden)...")
        # In einer echten Implementierung würde hier ein Monitoring-Thread gestartet werden
        # Für das Beispielprotokoll:
        logger.debug("Regeldatei-Überwachung gestartet (Simulationsmodus)")

    def apply_rules(self, data: Any, rule_category: str) -> Dict[str, Any]:
        """Wendet Regeln auf Daten an

        Args:
            data: Die zu verarbeitenden Daten
            rule_category: Die Kategorie der Regeln

        Returns:
            Dict[str, Any]: Ergebnisse der Regelanwendung
        """
        results = {
            "input": data,
            "processed": data,
            "violations": [],
            "category": rule_category
        }

        # In einer echten Implementierung würden hier die Regeln angewendet
        logger.debug(f"Wende Regeln der Kategorie '{rule_category}' auf Daten an")

        return results

    def get_rules(self) -> List[Dict[str, Any]]:
        """Gibt alle Regeln zurück

        Returns:
            List[Dict[str, Any]]: Liste der Regeln
        """
        return self.rules

    def get_rule_by_id(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """Holt eine Regel anhand ihrer ID

        Args:
            rule_id: ID der Regel

        Returns:
            Dict[str, Any] oder None: Die gefundene Regel oder None
        """
        for rule in self.rules:
            if rule.get("id") == rule_id:
                return rule
        return None
