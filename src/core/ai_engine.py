# src/core/ai_engine.py
"""
AIBrain / AI Engine - Orchestrator für Mindestentinel
- Kapselt RuleEngine, ProtectionModule, KnowledgeBase, SelfLearning, MultiModelOrchestrator und SystemMonitor
- Bietet lifecycle: start(), stop(), status(), query()
- Thread-safe, mit Hintergrundloop für Wartungsjobs (snapshot, persistence)
"""

from __future__ import annotations
import logging
import threading
import asyncio
import time
from typing import Optional, Dict, Any

# Lokale Komponenten (werden als Dateien im selben Paket implementiert)
from src.core.rule_engine import RuleEngine
from src.core.protection_module import ProtectionModule
from src.core.knowledge_base import KnowledgeBase
from src.core.self_learning import SelfLearning
from src.core.multi_model_orchestrator import MultiModelOrchestrator
from src.core.system_monitor import SystemMonitor
from src.core.model_manager import ModelManager

_LOGGER = logging.getLogger("mindestentinel.ai_engine")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class AIBrain:
    """
    Hauptklasse für das Mindestentinel-System.
    Initialisiert Kernkomponenten, startet Hintergrundarbeiten und stellt die Query-API bereit.
    """

    def __init__(self, rules_path: str, max_workers: int = 4):
        # Kernkomponenten
        self.rule_engine = RuleEngine(rules_path)
        self.protection = ProtectionModule(self.rule_engine)
        self.knowledge_base = KnowledgeBase()
        self.self_learning = SelfLearning(self.knowledge_base)
        self.multi_orchestrator = MultiModelOrchestrator()  # model_manager wird später injiziert
        self.system_monitor = SystemMonitor()

        # Laufzeit / Lifecycle
        self._running = False
        self._lock = threading.RLock()
        self._bg_thread: Optional[threading.Thread] = None
        self._bg_loop_interval = 30  # Sekunden zwischen Wartungszyklen
        self._async_loop: Optional[asyncio.AbstractEventLoop] = None
        self._max_workers = max_workers

        # Health / meta
        self.start_time: Optional[float] = None
        self.metrics: Dict[str, Any] = {}

        _LOGGER.info("AIBrain initialisiert.")

    def inject_model_manager(self, model_manager: ModelManager) -> None:
        """
        Injiziere model_manager (z.B. zur Laufzeit, sobald dieser verfügbar ist).
        """
        with self._lock:
            self.multi_orchestrator.inject_model_manager(model_manager)
            _LOGGER.info("Model manager injiziert in MultiModelOrchestrator.")

    def start(self) -> None:
        """Starte die AIBrain: background thread für Wartungsjobs und set running flag."""
        with self._lock:
            if self._running:
                _LOGGER.warning("AIBrain bereits gestartet.")
                return
            self._running = True
            self.start_time = time.time()

            # Starten des Hintergrundthreads (führt async tasks in eigenem event loop aus)
            self._bg_thread = threading.Thread(target=self._bg_thread_fn, name="AIBrainBG", daemon=True)
            self._bg_thread.start()
            _LOGGER.info("AIBrain gestartet.")

    def stop(self) -> None:
        """Stoppe das AIBrain sauber."""
        with self._lock:
            if not self._running:
                _LOGGER.warning("AIBrain ist nicht aktiv.")
                return
            self._running = False

        # Stoppe async loop (falls vorhanden)
        if self._async_loop and self._async_loop.is_running():
            try:
                self._async_loop.call_soon_threadsafe(self._async_loop.stop)
            except Exception:
                _LOGGER.exception("Fehler beim Stoppen des async-loops.")

        if self._bg_thread:
            self._bg_thread.join(timeout=5.0)

        _LOGGER.info("AIBrain gestoppt.")

    def _bg_thread_fn(self) -> None:
        """
        Hintergrund-Thread: erzeugt einen eigenen asyncio-Eventloop,
        führt periodische Jobs (Snapshot, persist, self-learning trigger) aus.
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._async_loop = loop
            loop.run_until_complete(self._bg_loop())
        except Exception:
            _LOGGER.exception("Fehler im Hintergrundthread.")
        finally:
            try:
                if self._async_loop and not self._async_loop.is_closed():
                    self._async_loop.close()
            except Exception:
                pass

    async def _bg_loop(self) -> None:
        _LOGGER.info("Hintergrund-Loop gestartet.")
        while self._running:
            try:
                # 1) System-Snapshot für Monitoring
                snap = self.system_monitor.snapshot()
                self.metrics['last_snapshot'] = snap
                _LOGGER.debug("Snapshot: %s", snap)

                # 2) Trigger für Selbstlernen (falls genügend neue Daten)
                try:
                    await self._maybe_trigger_self_learning()
                except Exception:
                    _LOGGER.exception("Self-Learning Trigger Fehler")

                # 3) Periodische Persistenz (z.B. KnowledgeBase flush) - call sync if available
                try:
                    if hasattr(self.knowledge_base, "persist"):
                        self.knowledge_base.persist()
                except Exception:
                    _LOGGER.exception("Persistenz-Fehler KnowledgeBase")

            except Exception:
                _LOGGER.exception("Fehler im Wartungszyklus")

            # Sleep non-blocking in the async loop
            await asyncio.sleep(self._bg_loop_interval)
        _LOGGER.info("Hintergrund-Loop beendet.")

    async def _maybe_trigger_self_learning(self) -> None:
        """
        Entscheidet, ob Self-Learning-Job gestartet wird.
        Hier: sehr konservative Heuristik — nur starten, wenn CPU/RAM unter Schwelle liegen.
        """
        try:
            status = self.system_monitor.snapshot()
            cpu = status.get("cpu", 100)
            mem = status.get("memory", 100)
            # einfache Schwellenwerte; konfigurierbar in späterer Version
            if cpu < 60 and mem < 75:
                # sichere Lernaktion: sammle Batch von unverarbeiteten Items und lerne
                new_count = self.self_learning.batch_learn(max_items=32)
                if new_count:
                    _LOGGER.info("SelfLearning: %d neue Items verarbeitet.", new_count)
            else:
                _LOGGER.debug("SelfLearning ausgelassen (System ausgelastet). CPU=%s MEM=%s", cpu, mem)
        except Exception:
            _LOGGER.exception("Fehler beim Entscheiden über Self-Learning")

    def status(self) -> Dict[str, Any]:
        """Gebe Status-Informationen zurück (health, metrics, uptime)."""
        with self._lock:
            uptime = None
            if self.start_time:
                uptime = time.time() - self.start_time
            return {
                "running": self._running,
                "uptime": uptime,
                "metrics": self.metrics,
                "models_loaded": getattr(self.multi_orchestrator.model_manager, "list_models", lambda: [])()
            }

    async def query_async(self, prompt: str, models: Optional[list[str]] = None, timeout: float = 30.0) -> Dict[str, str]:
        """
        Asynchrone Abfrage mehrerer Modelle über MultiModelOrchestrator.
        Wenn `models` None ist, werden alle verfügbaren Modelle befragt.
        """
        if not self._running:
            raise RuntimeError("AIBrain ist nicht gestartet.")

        # Protection: validiere Prompt gegen Rules bevor external calls
        self.protection.validate_user_input(prompt)

        # Modelle abfragen (delegiert an MultiModelOrchestrator)
        if models:
            # filtern ggf. von ModelManager
            names = models
        else:
            names = self.multi_orchestrator.model_manager.list_models()

        # delegiere an orchestrator
        try:
            # Erstelle Task-Group
            coro = self.multi_orchestrator.query_models_batch(names, prompt, timeout=timeout)
            # run in the engine loop if available, else new loop
            if self._async_loop and self._async_loop.is_running():
                future = asyncio.run_coroutine_threadsafe(coro, self._async_loop)
                results = future.result(timeout=timeout + 5)
            else:
                results = await coro
            # speichere Antworten in KnowledgeBase (optional)
            for mname, resp in results.items():
                self.knowledge_base.store(mname, resp)
            return results
        except Exception as e:
            _LOGGER.exception("Fehler bei query_async: %s", e)
            raise

    def query(self, prompt: str, models: Optional[list[str]] = None, timeout: float = 30.0) -> Dict[str, str]:
        """
        Synchrone Wrapper für query_async - nützlich für CLI oder einfache APIs.
        """
        # Run in new short-lived loop to keep API sync-friendly
        return asyncio.run(self.query_async(prompt, models=models, timeout=timeout))

    def request_gpu_session(self, hours: float, reason: str, requester: str = "admin") -> str:
        """
        Erzeuge einen Antrag für GPU-Sessions; delegiere an SelfLearning / Protection Module wenn nötig.
        Gibt eine request_id zurück - Admin muss freigeben (manuell über Admin-Console).
        """
        # Protection: prüfe ob Regelkonform
        self.protection.validate_system_action(reason)
        req_id = self.self_learning.request_gpu_session(hours, reason, requester)
        _LOGGER.info("GPU-Session beantragt: %s (hours=%s) by %s", req_id, hours, requester)
        return req_id

    def register_plugin(self, plugin_obj) -> None:
        """Registriert ein Plugin-Objekt (Plugin muss process/query Schnittstelle implementieren)."""
        if not hasattr(plugin_obj, "name"):
            raise ValueError("Plugin muss ein 'name' Attribut besitzen.")
        # plugin registration: self-learning / orchestrator / KB können Plugin nutzen
        if hasattr(self.self_learning, "register_plugin"):
            self.self_learning.register_plugin(plugin_obj)
        _LOGGER.info("Plugin '%s' registriert.", getattr(plugin_obj, "name", "<unknown>"))