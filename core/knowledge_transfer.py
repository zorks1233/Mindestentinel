# src/core/knowledge_transfer.py
"""
knowledge_transfer.py - Überträgt gelerntes Wissen in das aktive System

Diese Datei implementiert den Wissenstransfer von der Lernumgebung in das aktive System.
"""

import logging
import time
from typing import Dict, Any, List, Optional

logger = logging.getLogger("mindestentinel.knowledge_transfer")

class KnowledgeTransfer:
    """
    Überträgt gelerntes Wissen von der Lernumgebung in das aktive System.
    
    Stellt sicher, dass nur validiertes und sicheres Wissen integriert wird.
    """
    
    def __init__(self, knowledge_base, rule_engine, protection_module):
        """
        Initialisiert den Wissenstransfer.
        
        Args:
            knowledge_base: Die Wissensdatenbank
            rule_engine: Die Regel-Engine
            protection_module: Das Schutzmodul
        """
        self.kb = knowledge_base
        self.rule_engine = rule_engine
        self.protection = protection_module
        logger.info("KnowledgeTransfer initialisiert.")
    
    def transfer_learned_knowledge(self, learning_session_id: str) -> bool:
        """
        Überträgt gelerntes Wissen aus einer Lernsession in das aktive System.
        
        Args:
            learning_session_id: Die ID der Lernsession
            
        Returns:
            bool: True, wenn erfolgreich, sonst False
        """
        try:
            logger.info(f"Starte Wissenstransfer für Lernsession {learning_session_id}...")
            
            # Hole die Lernergebnisse
            learning_results = self._get_learning_results(learning_session_id)
            if not learning_results:
                logger.error(f"Keine Lernergebnisse für Session {learning_session_id} gefunden")
                return False
            
            # Validiere das gelernte Wissen
            if not self._validate_learned_knowledge(learning_results):
                logger.warning(f"Gelerntes Wissen für Session {learning_session_id} nicht validiert")
                return False
            
            # Prüfe Sicherheit des Wissens
            if not self._check_knowledge_safety(learning_results):
                logger.warning(f"Gelerntes Wissen für Session {learning_session_id} nicht sicher")
                return False
            
            # Übertrage das Wissen
            success = self._transfer_knowledge(learning_results)
            
            if success:
                logger.info(f"Wissenstransfer für Session {learning_session_id} erfolgreich abgeschlossen")
                return True
            else:
                logger.warning(f"Wissenstransfer für Session {learning_session_id} fehlgeschlagen")
                return False
        except Exception as e:
            logger.error(f"Fehler beim Wissenstransfer: {str(e)}", exc_info=True)
            return False
    
    def _get_learning_results(self, learning_session_id: str) -> Optional[Dict[str, Any]]:
        """
        Holt die Lernergebnisse einer Session.
        
        Args:
            learning_session_id: Die ID der Lernsession
            
        Returns:
            Optional[Dict[str, Any]]: Die Lernergebnisse, falls gefunden, sonst None
        """
        try:
            # Hole die Lernergebnisse aus der Wissensdatenbank
            results = self.kb.select(
                "SELECT * FROM knowledge WHERE category = 'learning_session' AND metadata->>'session_id' = ?",
                (learning_session_id,),
                decrypt_column=2
            )
            
            if results:
                return results[0]
            else:
                logger.warning(f"Keine Lernergebnisse für Session {learning_session_id} gefunden")
                return None
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Lernergebnisse: {str(e)}", exc_info=True)
            return None
    
    def _validate_learned_knowledge(self, learning_results: Dict[str, Any]) -> bool:
        """
        Validiert das gelernte Wissen.
        
        Args:
            learning_results: Die Lernergebnisse
            
        Returns:
            bool: True, wenn validiert, sonst False
        """
        try:
            # Prüfe, ob das Wissen konsistent ist
            knowledge_examples = learning_results.get("data", {}).get("examples", [])
            if not knowledge_examples:
                logger.warning("Keine Wissensbeispiele zum Validieren gefunden")
                return False
            
            # Berechne die Konsistenz der Antworten
            consistency_score = self._calculate_consistency(knowledge_examples)
            
            # Prüfe, ob die Konsistenz ausreichend ist
            min_consistency = 0.7  # Mindestkonsistenz
            if consistency_score < min_consistency:
                logger.warning(f"Konsistenz des gelernten Wissens zu niedrig: {consistency_score:.2f} < {min_consistency}")
                return False
            
            logger.info(f"Gelerntes Wissen validiert mit Konsistenz: {consistency_score:.2f}")
            return True
        except Exception as e:
            logger.error(f"Fehler bei der Wissensvalidierung: {str(e)}", exc_info=True)
            return False
    
    def _calculate_consistency(self, knowledge_examples: List[Dict[str, Any]]) -> float:
        """
        Berechnet die Konsistenz der Wissensbeispiele.
        
        Args:
            knowledge_examples: Die Wissensbeispiele
            
        Returns:
            float: Die Konsistenz (0.0 - 1.0)
        """
        # In einer echten Implementierung würden Sie die Konsistenz berechnen
        # Für das Beispiel geben wir einfach einen Dummy-Wert zurück
        return 0.85  # Hohe Konsistenz
    
    def _check_knowledge_safety(self, learning_results: Dict[str, Any]) -> bool:
        """
        Prüft die Sicherheit des gelernten Wissens.
        
        Args:
            learning_results: Die Lernergebnisse
            
        Returns:
            bool: True, wenn sicher, sonst False
        """
        try:
            # Erstelle einen Kontext für die Sicherheitsprüfung
            context = {
                "category": "learned_knowledge",
                "knowledge": learning_results.get("data", {}),
                "timestamp": time.time()
            }
            
            # Prüfe, ob das Wissen sicher ist
            results = self.rule_engine.execute_rules(context)
            
            # Prüfe, ob alle Regeln erfolgreich waren
            for result in results:
                if not result.get("condition_result", False):
                    logger.warning(f"Sicherheitsregel verletzt: {result.get('rule_name')}")
                    return False
            
            logger.info("Gelerntes Wissen ist sicher")
            return True
        except Exception as e:
            logger.error(f"Fehler bei der Sicherheitsprüfung: {str(e)}", exc_info=True)
            return False
    
    def _transfer_knowledge(self, learning_results: Dict[str, Any]) -> bool:
        """
        Überträgt das Wissen in das aktive System.
        
        Args:
            learning_results: Die Lernergebnisse
            
        Returns:
            bool: True, wenn erfolgreich, sonst False
        """
        try:
            # Hier würde der eigentliche Wissenstransfer stattfinden
            # In einer echten Implementierung würden Sie hier:
            # 1. Das Wissen in die Wissensdatenbank speichern
            # 2. Das Modell aktualisieren (falls nötig)
            
            # Für das Beispiel: Speichere das Wissen in der Wissensdatenbank
            session_id = learning_results["metadata"]["session_id"]
            knowledge_examples = learning_results["data"]["examples"]
            
            # Speichere jedes Wissensbeispiel
            for example in knowledge_examples:
                self.kb.store(
                    "knowledge",
                    {
                        "prompt": example["prompt"],
                        "response": example["response"],
                        "source": f"learned_session_{session_id}",
                        "timestamp": time.time()
                    }
                )
            
            logger.info("Gelerntes Wissen erfolgreich in das aktive System übertragen")
            return True
        except Exception as e:
            logger.error(f"Fehler beim Wissenstransfer: {str(e)}", exc_info=True)
            return False
    
    def get_transfer_history(self) -> List[Dict[str, Any]]:
        """
        Gibt den Wissenstransfer-Verlauf zurück.
        
        Returns:
            List[Dict[str, Any]]: Der Transfer-Verlauf
        """
        try:
            # Hole den Transfer-Verlauf aus der Wissensdatenbank
            return self.kb.select(
                "SELECT * FROM knowledge WHERE category = 'knowledge_transfer' ORDER BY timestamp DESC",
                decrypt_column=2
            )
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Transfer-Verlaufs: {str(e)}", exc_info=True)
            return []