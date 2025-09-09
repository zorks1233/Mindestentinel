# src/core/self_learning.py
"""
self_learning.py - Modul für autonome Lernmechanismen und Wissensakquisition

Dieses Modul implementiert den autonomen Lernprozess für Mindestentinel.
Es ermöglicht das Sammeln von Wissen aus Benutzerinteraktionen, die Verarbeitung
dieser Daten und die Integration neuer Erkenntnisse in das System.

Hauptfunktionen:
- Batch-Learning aus Benutzerinteraktionen
- Wissensextraktion und -verdichtung
- Integration neuer Erkenntnisse in das Wissenbasis
- Metriken für Lernerfolg
"""

import re
import time
import logging
import datetime
from typing import Dict, List, Optional, Any
from collections import Counter
import threading

# Initialisiere Logger
logger = logging.getLogger("mindestentinel.self_learning")
logger.addHandler(logging.NullHandler())

class SelfLearning:
    """
    Hauptklasse für den autonomen Lernprozess.
    
    Verwaltet die Extraktion, Verarbeitung und Integration von Wissen
    aus Benutzerinteraktionen und anderen Quellen.
    """
    
    def __init__(self, knowledge_base, model_manager=None, max_history: int = 10000):
        """
        Initialisiert das SelfLearning-Modul.
        
        Args:
            knowledge_base: Instanz der Wissensdatenbank
            model_manager: Optionaler ModelManager für Wissensverdichtung
            max_history: Maximale Anzahl an gespeicherten Lernitems
        """
        self.knowledge_base = knowledge_base
        self.model_manager = model_manager
        self.max_history = max_history
        self._lock = threading.RLock()
        self._incoming: List[str] = []
        self.plugins = []
        self._requests = {}  # Cache für GPU-Anfragen bis zur Persistenz
        self.last_batch_time = 0
        self.batch_interval = 30  # Sekunden zwischen Batch-Learning-Zyklen
        logger.info("SelfLearning-Modul initialisiert.")
    
    def register_plugin(self, plugin_obj) -> None:
        """
        Registriert ein Plugin, das Lernitems vorverarbeiten kann.
        
        Args:
            plugin_obj: Das Plugin-Objekt
            
        Raises:
            ValueError: Wenn das Plugin kein 'name'-Attribut hat
        """
        if not hasattr(plugin_obj, "name"):
            raise ValueError("Plugin muss 'name' Attribut besitzen")
        
        self.plugins.append(plugin_obj)
        logger.info("Plugin für SelfLearning registriert: %s", plugin_obj.name)
    
    def learn_from_input(self, input_text: str) -> str:
        """
        Fügt Text zur Lern-Queue hinzu und persistiert minimal (schnell).
        
        Args:
            input_text: Der zu verarbeitende Text
            
        Returns:
            str: Statusmeldung
            
        Raises:
            ValueError: Wenn input_text leer ist
        """
        if not input_text:
            raise ValueError("input_text darf nicht leer sein")
        
        with self._lock:
            # Einfache Deduplizierung und Begrenzung der Historie
            if len(self._incoming) >= self.max_history:
                self._incoming.pop(0)
            self._incoming.append(input_text)
            
            # Speichere in der Wissensdatenbank
            self.knowledge_base.store("learning_queue", {
                "text": input_text,
                "timestamp": datetime.datetime.now().isoformat(),
                "processed": False
            })
            
            logger.debug("Neues Lernitem hinzugefügt (Queue-Länge: %d)", len(self._incoming))
            return "Lernitem hinzugefügt"
    
    def batch_learn(self, max_items: int = 32) -> int:
        """
        Führt Batch-Learning durch, indem unverarbeitete Interaktionen verarbeitet werden.
        
        Args:
            max_items: Maximale Anzahl an Items, die verarbeitet werden sollen
            
        Returns:
            int: Anzahl der erfolgreich verarbeiteten Items
        """
        # Prüfe, ob genügend Zeit seit dem letzten Batch vergangen ist
        current_time = time.time()
        if current_time - self.last_batch_time < self.batch_interval:
            logger.debug("Batch-Learning übersprungen (noch nicht genügend Zeit vergangen)")
            return 0
            
        # Hole die neuesten Benutzerinteraktionen
        interactions = self.knowledge_base.get_recent_interactions(limit=max_items)
        
        if not interactions:
            logger.info("Keine unverarbeiteten Interaktionen gefunden.")
            self.last_batch_time = current_time
            return 0
        
        processed = 0
        for interaction in interactions:
            try:
                # Prüfe, ob die Interaktion bereits verarbeitet wurde
                if interaction.get("processed", False):
                    continue
                    
                # Extrahiere Wissen aus der Interaktion
                knowledge = self._extract_knowledge(interaction)
                
                # Speichere neues Wissen
                if knowledge:
                    self.knowledge_base.store("learning_items", knowledge)
                    # Markiere Interaktion als verarbeitet
                    interaction["processed"] = True
                    processed += 1
            except Exception as e:
                logger.error(f"Fehler bei der Verarbeitung der Interaktion {interaction.get('id', 'unknown')}: {str(e)}")
        
        # Aktualisiere die Metadaten für das Modell
        if processed > 0:
            model_name = self.knowledge_base.get_statistics().get("models_loaded", [])[0] if self.knowledge_base.get_statistics().get("models_loaded") else None
            if model_name:
                improvement = {
                    "model": model_name,
                    "items_processed": processed,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                self.knowledge_base.store("model_improvements", improvement)
        
        self.last_batch_time = current_time
        logger.info(f"Batch-Learn abgeschlossen: {processed} Items verarbeitet")
        return processed

    def _extract_knowledge(self, interaction: Dict) -> Optional[Dict]:
        """
        Extrahiert Wissen aus einer Benutzerinteraktion.
        
        Args:
            interaction: Die Benutzerinteraktion
            
        Returns:
            Dict: Extrahiertes Wissen oder None, wenn nichts extrahiert werden konnte
        """
        # Extrahiere Schlüsselwörter aus der Frage
        keywords = self._extract_keywords(interaction["query"])
        
        # Bestimme die Relevanz
        relevance = self._determine_relevance(interaction["query"], interaction["response"])
        
        # Nur relevante Interaktionen verarbeiten
        if relevance < 0.6:
            return None
        
        return {
            "query": interaction["query"],
            "response": interaction["response"],
            "keywords": keywords,
            "relevance": relevance,
            "timestamp": interaction["timestamp"]
        }

    def _extract_keywords(self, text: str) -> List[str]:
        """Extrahiert Schlüsselwörter aus einem Text"""
        # Entferne Satzzeichen und konvertiere zu Kleinbuchstaben
        text = re.sub(r'[^\w\s]', '', text.lower())
        
        # Splitte in Wörter
        words = text.split()
        
        # Filtere Stopwörter (vereinfachte Liste)
        stop_words = ["der", "die", "das", "und", "oder", "aber", "ist", "war", "sind", "ein", "eine"]
        keywords = [w for w in words if len(w) > 3 and w not in stop_words]
        
        # Gib die 5 häufigsten Wörter zurück
        word_count = Counter(keywords)
        return [word for word, _ in word_count.most_common(5)]
        
    def _determine_relevance(self, query: str, response: str) -> float:
        """Bestimmt die Relevanz einer Interaktion"""
        # Konvertiere zu Kleinbuchstaben und entferne Satzzeichen
        query = re.sub(r'[^\w\s]', '', query.lower())
        response = re.sub(r'[^\w\s]', '', response.lower())
        
        # Splitte in Wörter
        query_words = set(query.split())
        response_words = set(response.split())
        
        if not query_words:
            return 0.0
        
        # Anteil der Query-Wörter, die in der Antwort vorkommen
        overlap = len(query_words & response_words) / len(query_words)
        
        # Berücksichtige auch die Länge der Antwort
        response_length = len(response.split())
        length_factor = min(1.0, response_length / 50)
        
        # Berücksichtige auch die Antwortqualität (einfache Heuristik)
        quality_factor = 0.7 if "error" not in response else 0.2
        
        return 0.5 * overlap + 0.3 * length_factor + 0.2 * quality_factor

    def request_gpu_session(self, hours: float, reason: str, requester: str = "admin") -> str:
        """
        Erstelle einen Antrag für GPU-Sessions.
        
        Args:
            hours: Gewünschte Dauer in Stunden
            reason: Begründung für die Anfrage
            requester: Anfragender Benutzer (Standard: admin)
            
        Returns:
            str: Anfrage-ID
        """
        req_id = f"gpu_req_{int(time.time())}_{requester[:3]}"
        
        # Speichere die Anfrage
        self._requests[req_id] = {
            "hours": hours,
            "reason": reason,
            "requester": requester,
            "status": "pending",
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        # Speichere in der Wissensdatenbank
        self.knowledge_base.store("gpu_requests", self._requests[req_id])
        
        logger.info("GPU-Session beantragt: %s (hours=%s) by %s", req_id, hours, requester)
        return req_id

    def get_gpu_request_status(self, req_id: str) -> Dict[str, Any]:
        """
        Gibt den Status einer GPU-Anfrage zurück.
        
        Args:
            req_id: Anfrage-ID
            
        Returns:
            Dict: Statusinformationen
        """
        # Hole den Status aus der Wissensdatenbank
        requests = self.knowledge_base.query(
            "SELECT * FROM gpu_requests WHERE id = ?", 
            (req_id,)
        )
        
        if requests:
            return dict(requests[0])
        
        # Falls nicht in DB, prüfe den Cache
        if req_id in self._requests:
            return self._requests[req_id]
            
        return {"error": "Anfrage nicht gefunden"}

    def perform_optimization(self) -> Dict[str, Any]:
        """
        Führt eine Optimierung des Systems durch.
        
        Returns:
            Dict: Optimierungsergebnisse
        """
        # Hole Systemstatistiken
        stats = self.knowledge_base.get_statistics()
        
        # Analysiere Wissenslücken
        knowledge_gaps = self._identify_knowledge_gaps()
        
        # Erstelle Optimierungsplan
        optimization_plan = {
            "timestamp": datetime.datetime.now().isoformat(),
            "current_model_count": len(stats.get("models_loaded", [])),
            "knowledge_entries": stats["total_entries"],
            "identified_gaps": len(knowledge_gaps),
            "suggested_actions": []
        }
        
        # Generiere Vorschläge basierend auf den Lücken
        for gap in knowledge_gaps[:3]:  # Maximal 3 Vorschläge
            optimization_plan["suggested_actions"].append({
                "action": "expand_knowledge",
                "target": gap["concept"],
                "priority": gap["priority"],
                "estimated_effort": gap["complexity"]
            })
        
        # Speichere den Optimierungsplan
        self.knowledge_base.store("optimization_plans", optimization_plan)
        
        logger.info("Optimierungsplan erstellt mit %d Vorschlägen", len(optimization_plan["suggested_actions"]))
        return optimization_plan

    def _identify_knowledge_gaps(self) -> List[Dict]:
        """
        Identifiziert Wissenslücken durch Analyse der bestehenden Wissensdatenbank.
        
        Returns:
            List[Dict]: Eine Liste von identifizierten Wissenslücken
        """
        # In einer realen Implementierung würde dies komplexe Analysen durchführen
        # Für diesen Stub generieren wir einige Beispieldaten
        return [
            {"id": "gap_001", "concept": "Quantenverschränkung", "priority": 4, "complexity": 4},
            {"id": "gap_002", "concept": "Neuronale Netzoptimierung", "priority": 3, "complexity": 3},
            {"id": "gap_003", "concept": "Ethik in autonomen Systemen", "priority": 5, "complexity": 2}
        ]

    def _bg_loop(self) -> None:
        """
        Hintergrund-Loop für automatisches Batch-Learning.
        """
        logger.info("SelfLearning Hintergrund-Loop gestartet.")
        
        while True:
            try:
                # Prüfe auf neue Lernitems
                self.batch_learn()
                
                # Warte vor dem nächsten Zyklus
                time.sleep(self.batch_interval)
            except Exception as e:
                logger.error(f"Fehler im SelfLearning Hintergrund-Loop: {str(e)}", exc_info=True)
                time.sleep(10)  # Warte länger nach einem Fehler

    def start_background_loop(self) -> None:
        """
        Startet den Hintergrund-Loop für automatisches Batch-Learning.
        """
        bg_thread = threading.Thread(target=self._bg_loop, daemon=True)
        bg_thread.start()
        logger.info("SelfLearning Hintergrund-Loop gestartet.")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Gibt Statistiken über den Lernprozess zurück.
        
        Returns:
            Dict: Statistikinformationen
        """
        # Hole Lernstatistiken aus der Wissensdatenbank
        learning_stats = self.knowledge_base.query(
            "SELECT COUNT(*) as total, AVG(relevance) as avg_relevance FROM learning_items"
        )
        
        # Hole Optimierungsstatistiken
        optimization_stats = self.knowledge_base.query(
            "SELECT COUNT(*) as total_plans FROM optimization_plans"
        )
        
        return {
            "total_learned_items": learning_stats[0]["total"] if learning_stats else 0,
            "average_relevance": learning_stats[0]["avg_relevance"] if learning_stats else 0.0,
            "total_optimization_plans": optimization_stats[0]["total_plans"] if optimization_stats else 0,
            "last_batch_time": self.last_batch_time,
            "queue_length": len(self._incoming)
        }