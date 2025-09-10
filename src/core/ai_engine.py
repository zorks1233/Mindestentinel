# src/core/ai_engine.py
"""
AIBrain / AI Engine - Orchestrator für Mindestentinel

Dieses Modul ist der zentrale Orchestrator des Mindestentinel-Systems.
Es verwaltet alle Komponenten und koordiniert die Interaktion zwischen ihnen.

Hauptfunktionen:
- Initialisierung aller Systemkomponenten
- Verwaltung des Hintergrundloops
- Koordination von Anfragen und Lernprozessen
- Sicherheitsüberwachung durch RuleEngine
"""

import logging
import threading
import time
import asyncio
from typing import Dict, Any, Optional, List

# Initialisiere Logger
logger = logging.getLogger("mindestentinel.ai_engine")
logger.addHandler(logging.NullHandler())

class AIBrain:
    """
    Hauptklasse für das Mindestentinel-System.
    
    Initialisiert Kernkomponenten, startet Hintergrundarbeiten und stellt die Query-API bereit.
    """
    
    def __init__(self, rules_path: Optional[str] = None, max_workers: int = 4):
        """
        Initialisiert das AIBrain.
        
        Args:
            rules_path: Pfad zur Regelkonfiguration
            max_workers: Maximale Anzahl an Worker-Threads
        """
        # Referenzen auf Systemkomponenten
        self.rule_engine = None
        self.protection_module = None
        self.knowledge_base = None
        self.model_orchestrator = None
        self.self_learning = None
        self.system_monitor = None
        self.autonomous_loop = None
        
        # Laufzeitvariablen
        self.max_workers = max_workers
        self._running = False
        self._lock = threading.RLock()
        self._async_loop = None
        self._bg_thread = None
        self.start_time = time.time()
        
        logger.info("AIBrain initialisiert.")
    
    def inject_model_manager(self, model_manager) -> None:
        """
        Injiziert den ModelManager in das System.
        
        Args:
            model_manager: Der zu injizierende ModelManager
        """
        if self.model_orchestrator:
            self.model_orchestrator.inject_model_manager(model_manager)
        logger.debug("ModelManager injiziert")
    
    def start(self) -> None:
        """
        Startet das AIBrain und alle verbundenen Komponenten.
        
        Erstellt und startet den Hintergrundthread für kontinuierliche Prozesse.
        """
        with self._lock:
            if self._running:
                logger.warning("AIBrain ist bereits gestartet.")
                return
                
            self._running = True
            
            # Starte den Hintergrundthread
            self._bg_thread = threading.Thread(
                target=self._bg_thread_fn, 
                name="AIBrainBG", 
                daemon=True
            )
            self._bg_thread.start()
            
            logger.info("AIBrain gestartet.")
    
    def stop(self) -> None:
        """
        Stoppt das AIBrain und alle verbundenen Komponenten.
        
        Stoppt den Hintergrundthread und sorgt für eine saubere Beendigung.
        """
        with self._lock:
            if not self._running:
                logger.warning("AIBrain ist nicht gestartet.")
                return
                
            self._running = False
            
            # Warte auf das Beenden des Hintergrundthreads
            if self._bg_thread and self._bg_thread.is_alive():
                self._bg_thread.join(timeout=5.0)
                if self._bg_thread.is_alive():
                    logger.warning("Hintergrundthread wurde nicht innerhalb des Timeouts beendet.")
            
            logger.info("AIBrain gestoppt.")
    
    def _bg_thread_fn(self) -> None:
        """
        Hintergrund-Thread: erzeugt einen eigenen asyncio-Eventloop,
        führt periodische Jobs (Snapshot, persist, self-learning trigger) aus.
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._async_loop = loop
            
            # Starte den Hintergrundloop
            loop.run_until_complete(self._bg_loop())
            
        except Exception:
            # Nur loggen, wenn das System noch läuft
            with self._lock:
                if self._running:
                    logger.exception("Fehler im Hintergrundthread.")
        finally:
            try:
                # Stelle sicher, dass alle Tasks abgebrochen werden
                if loop.is_running():
                    # Hole alle laufenden Tasks
                    tasks = asyncio.all_tasks(loop=loop)
                    for task in tasks:
                        task.cancel()
                    
                    # Warte auf Abschluss der Tasks
                    loop.run_until_complete(
                        asyncio.gather(*tasks, return_exceptions=True)
                    )
                
                # Schließe den Loop sauber
                if not loop.is_closed():
                    loop.close()
            except Exception:
                logger.exception("Fehler beim Schließen des Event-Loops")
    
    async def _bg_loop(self) -> None:
        """
        Hintergrundloop für das AIBrain.
        
        Führt periodische Aufgaben aus wie:
        - Persistierung von Snapshots
        - Triggerung von Self-Learning-Prozessen
        - Systemüberwachung
        """
        logger.info("Hintergrund-Loop gestartet.")
        
        while self._running:
            try:
                # Prüfe auf Systemressourcen
                if self.system_monitor:
                    system_stats = self.system_monitor.snapshot()
                    logger.debug("Systemstatistiken: CPU=%.1f%%, Memory=%.1f%%", 
                                system_stats["cpu"], system_stats["memory"])
                
                # Trigger Self-Learning, falls aktiviert
                if self.autonomous_loop and self.autonomous_loop.active:
                    # Prüfe, ob genügend Zeit seit dem letzten Zyklus vergangen ist
                    if time.time() - self.autonomous_loop.last_cycle_time >= self.autonomous_loop.config["learning_interval_seconds"]:
                        self.autonomous_loop._run_learning_cycle()
                
                # Warte vor dem nächsten Zyklus
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error("Fehler im Hintergrundloop: %s", str(e), exc_info=True)
                await asyncio.sleep(10)  # Warte länger nach einem Fehler
    
    def query(self, prompt: str, models: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Verarbeitet eine Anfrage an das KI-System.
        
        Args:
            prompt: Die Anfrage
            models: Optionale Liste von Modellen, die verwendet werden sollen
            
        Returns:
            Dict: Antworten der Modelle
            
        Raises:
            RuntimeError: Wenn das System nicht läuft oder keine Modelle verfügbar sind
        """
        if not self._running:
            raise RuntimeError("AIBrain ist nicht gestartet")
        
        if not self.model_orchestrator:
            raise RuntimeError("Kein ModelOrchestrator verfügbar")
        
        try:
            # Hole die Modelle, falls nicht spezifiziert
            if not models:
                models = self.model_orchestrator.get_teacher_models()
                if not models:
                    models = self.model_orchestrator.get_student_models()
            
            # Frage die Modelle ab
            responses = self.model_orchestrator.query_teacher_models(
                prompt, 
                num_responses=len(models),
                temperature=0.7
            )
            
            # Speichere die Interaktion für späteres Lernen
            if self.knowledge_base:
                self.knowledge_base.store("interactions", {
                    "query": prompt,
                    "responses": responses,
                    "models": models,
                    "timestamp": time.time()
                })
            
            return responses
            
        except Exception as e:
            logger.error("Fehler bei der Abfrage: %s", str(e), exc_info=True)
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """
        Gibt den aktuellen Systemstatus zurück.
        
        Returns:
            Dict: Statusinformationen
        """
        return {
            "running": self._running,
            "uptime": time.time() - self.start_time,
            "components": {
                "rule_engine": self.rule_engine is not None,
                "protection_module": self.protection_module is not None,
                "knowledge_base": self.knowledge_base is not None,
                "model_orchestrator": self.model_orchestrator is not None,
                "self_learning": self.self_learning is not None,
                "system_monitor": self.system_monitor is not None,
                "autonomous_loop": self.autonomous_loop is not None
            }
        }