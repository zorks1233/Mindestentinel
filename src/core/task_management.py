"""
task_management.py
Verwaltet Aufgaben, Jobs und Workflows innerhalb des Mindestentinel-Systems.
Stellt sicher, dass Aufgaben effizient geplant, ausgeführt und überwacht werden.
"""

import logging
import time
import threading
import queue
import uuid
from typing import Dict, Any, List, Optional, Callable, Tuple, TypeVar, Generic

T = TypeVar('T')

logger = logging.getLogger("mindestentinel.task_management")

class TaskStatus:
    """Enum für den Status einer Aufgabe"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Task(Generic[T]):
    """
    Repräsentiert eine einzelne Aufgabe im Task-Management-System.
    """
    
    def __init__(
        self,
        task_id: Optional[str] = None,
        name: str = "Unnamed Task",
        description: str = "",
        priority: int = 1,
        dependencies: Optional[List[str]] = None,
        timeout: Optional[float] = None,
        retry_count: int = 0,
        max_retries: int = 3,
        callback: Optional[Callable[[T], None]] = None
    ):
        """
        Initialisiert eine neue Aufgabe.
        
        Args:
            task_id: Optionale ID der Aufgabe (wird generiert, wenn nicht angegeben)
            name: Name der Aufgabe
            description: Beschreibung der Aufgabe
            priority: Priorität der Aufgabe (niedriger Wert = höhere Priorität)
            dependencies: Liste von Task-IDs, von denen diese Aufgabe abhängt
            timeout: Optionale Timeout-Zeit in Sekunden
            retry_count: Aktuelle Anzahl der Wiederholungsversuche
            max_retries: Maximale Anzahl der Wiederholungsversuche
            callback: Optionale Callback-Funktion, die nach Abschluss aufgerufen wird
        """
        self.task_id = task_id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.priority = priority
        self.dependencies = dependencies or []
        self.timeout = timeout
        self.retry_count = retry_count
        self.max_retries = max_retries
        self.callback = callback
        
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.start_time = None
        self.end_time = None
        self.created_at = time.time()
    
    def start(self) -> None:
        """Markiert die Aufgabe als gestartet"""
        self.status = TaskStatus.RUNNING
        self.start_time = time.time()
        logger.debug(f"Aufgabe gestartet: {self.task_id} ({self.name})")
    
    def complete(self, result: T) -> None:
        """
        Markiert die Aufgabe als abgeschlossen.
        
        Args:
            result: Das Ergebnis der Aufgabe
        """
        self.result = result
        self.status = TaskStatus.COMPLETED
        self.end_time = time.time()
        logger.debug(f"Aufgabe abgeschlossen: {self.task_id} ({self.name})")
        
        # Rufe Callback auf, falls vorhanden
        if self.callback:
            try:
                self.callback(result)
            except Exception as e:
                logger.error(f"Fehler beim Ausführen des Callbacks für Aufgabe {self.task_id}: {str(e)}")
    
    def fail(self, error: Exception) -> None:
        """
        Markiert die Aufgabe als fehlgeschlagen.
        
        Args:
            error: Die aufgetretene Exception
        """
        self.error = error
        self.status = TaskStatus.FAILED
        self.end_time = time.time()
        logger.error(f"Aufgabe fehlgeschlagen: {self.task_id} ({self.name}) - {str(error)}")
    
    def cancel(self) -> None:
        """Markiert die Aufgabe als abgebrochen"""
        self.status = TaskStatus.CANCELLED
        self.end_time = time.time()
        logger.info(f"Aufgabe abgebrochen: {self.task_id} ({self.name})")
    
    def retry(self) -> bool:
        """
        Versucht, die Aufgabe erneut auszuführen.
        
        Returns:
            bool: True, wenn ein Wiederholungsversuch möglich ist, sonst False
        """
        if self.retry_count < self.max_retries:
            self.retry_count += 1
            self.status = TaskStatus.PENDING
            self.error = None
            logger.info(f"Aufgabe wird erneut versucht ({self.retry_count}/{self.max_retries}): {self.task_id} ({self.name})")
            return True
        else:
            logger.warning(f"Maximale Wiederholungsversuche erreicht für Aufgabe: {self.task_id} ({self.name})")
            return False
    
    def get_duration(self) -> Optional[float]:
        """
        Gibt die Ausführungsdauer der Aufgabe zurück.
        
        Returns:
            Optional[float]: Dauer in Sekunden oder None, wenn die Aufgabe nicht gestartet/beendet wurde
        """
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Konvertiert die Aufgabe in ein Dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary-Repräsentation der Aufgabe
        """
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "status": self.status,
            "result": str(self.result) if self.result is not None else None,
            "error": str(self.error) if self.error is not None else None,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "created_at": self.created_at,
            "duration": self.get_duration()
        }

class TaskManager:
    """
    Verwaltet Aufgaben, Jobs und Workflows innerhalb des Mindestentinel-Systems.
    Stellt sicher, dass Aufgaben effizient geplant, ausgeführt und überwacht werden.
    """
    
    def __init__(
        self,
        max_workers: int = 4,
        task_queue_size: int = 100,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialisiert den TaskManager.
        
        Args:
            max_workers: Maximale Anzahl gleichzeitiger Worker-Threads
            task_queue_size: Maximale Größe der Aufgaben-Warteschlange
            config: Optionale Konfigurationsparameter
        """
        logger.info("Initialisiere TaskManager...")
        self.config = config or {}
        self.max_workers = max_workers
        self.task_queue = queue.PriorityQueue(maxsize=task_queue_size)
        self.tasks: Dict[str, Task] = {}
        self.workers: List[threading.Thread] = []
        self.worker_stop = threading.Event()
        
        # Starte Worker-Threads
        self._start_workers()
        
        logger.info(f"TaskManager erfolgreich initialisiert mit {max_workers} Workern")
    
    def _start_workers(self) -> None:
        """Startet die Worker-Threads"""
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"TaskWorker-{i+1}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
            logger.debug(f"Worker-Thread gestartet: {worker.name}")
    
    def _worker_loop(self) -> None:
        """Hauptschleife für Worker-Threads"""
        while not self.worker_stop.is_set():
            try:
                # Warte auf die nächste Aufgabe (mit Timeout, um bei Stop prüfen zu können)
                try:
                    priority, task = self.task_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Führe Aufgabe aus
                self._execute_task(task)
                
                # Markiere Aufgabe als abgeschlossen
                self.task_queue.task_done()
            except Exception as e:
                logger.error(f"Fehler im Worker-Thread: {str(e)}")
    
    def _execute_task(self, task: Task) -> None:
        """Führt eine Aufgabe aus"""
        try:
            task.start()
            
            # Hier würde die eigentliche Aufgabenlogik ausgeführt werden
            # In einer realen Implementierung würde hier die Task-Funktion aufgerufen
            
            # Simuliere eine Ausführung (in der echten Implementierung würde hier die Task-Funktion aufgerufen)
            time.sleep(0.1)  # Simuliere eine kurze Ausführung
            
            # Markiere Aufgabe als abgeschlossen
            task.complete("Task completed successfully")
        except Exception as e:
            task.fail(e)
            
            # Versuche, die Aufgabe erneut auszuführen
            if task.retry():
                # Lege die Aufgabe mit niedrigerer Priorität zurück in die Warteschlange
                self.task_queue.put((task.priority + 1, task))
            else:
                logger.error(f"Aufgabe {task.task_id} ({task.name}) endgültig fehlgeschlagen")
    
    def submit(
        self,
        task_func: Callable[..., T],
        *args,
        **kwargs
    ) -> str:
        """
        Sendet eine neue Aufgabe zur Ausführung.
        
        Args:
            task_func: Die auszuführende Funktion
            *args: Positionale Argumente für die Funktion
            **kwargs: Schlüsselwort-Argumente für die Funktion
            
        Returns:
            str: Die ID der erstellten Aufgabe
        """
        # Erstelle eine Wrapper-Funktion, die die eigentliche Aufgabe ausführt
        def task_wrapper():
            return task_func(*args, **kwargs)
        
        # Erstelle eine neue Aufgabe
        task = Task(
            name=kwargs.pop("name", "Unnamed Task"),
            description=kwargs.pop("description", ""),
            priority=kwargs.pop("priority", 1),
            dependencies=kwargs.pop("dependencies", None),
            timeout=kwargs.pop("timeout", None),
            max_retries=kwargs.pop("max_retries", 3),
            callback=kwargs.pop("callback", None)
        )
        
        # Füge die Aufgabe zur Warteschlange hinzu
        self.task_queue.put((task.priority, task))
        self.tasks[task.task_id] = task
        
        logger.debug(f"Aufgabe eingereicht: {task.task_id} ({task.name})")
        return task.task_id
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Gibt eine Aufgabe basierend auf ihrer ID zurück.
        
        Args:
            task_id: Die ID der Aufgabe
            
        Returns:
            Optional[Task]: Die Aufgabe oder None, wenn nicht gefunden
        """
        return self.tasks.get(task_id)
    
    def get_task_status(self, task_id: str) -> Optional[str]:
        """
        Gibt den Status einer Aufgabe zurück.
        
        Args:
            task_id: Die ID der Aufgabe
            
        Returns:
            Optional[str]: Der Status der Aufgabe oder None, wenn nicht gefunden
        """
        task = self.get_task(task_id)
        return task.status if task else None
    
    def get_task_result(self, task_id: str) -> Optional[Any]:
        """
        Gibt das Ergebnis einer Aufgabe zurück.
        
        Args:
            task_id: Die ID der Aufgabe
            
        Returns:
            Optional[Any]: Das Ergebnis der Aufgabe oder None, wenn nicht verfügbar
        """
        task = self.get_task(task_id)
        return task.result if task and task.status == TaskStatus.COMPLETED else None
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Bricht eine Aufgabe ab.
        
        Args:
            task_id: Die ID der Aufgabe
            
        Returns:
            bool: True, wenn die Aufgabe erfolgreich abgebrochen wurde, sonst False
        """
        task = self.get_task(task_id)
        if task and task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            task.cancel()
            return True
        return False
    
    def get_pending_tasks(self) -> List[Task]:
        """Gibt alle ausstehenden Aufgaben zurück"""
        return [task for task in self.tasks.values() if task.status == TaskStatus.PENDING]
    
    def get_running_tasks(self) -> List[Task]:
        """Gibt alle laufenden Aufgaben zurück"""
        return [task for task in self.tasks.values() if task.status == TaskStatus.RUNNING]
    
    def get_completed_tasks(self) -> List[Task]:
        """Gibt alle abgeschlossenen Aufgaben zurück"""
        return [task for task in self.tasks.values() if task.status == TaskStatus.COMPLETED]
    
    def get_failed_tasks(self) -> List[Task]:
        """Gibt alle fehlgeschlagenen Aufgaben zurück"""
        return [task for task in self.tasks.values() if task.status == TaskStatus.FAILED]
    
    def get_task_statistics(self) -> Dict[str, int]:
        """Gibt Statistiken über die Aufgaben zurück"""
        return {
            "total": len(self.tasks),
            "pending": len(self.get_pending_tasks()),
            "running": len(self.get_running_tasks()),
            "completed": len(self.get_completed_tasks()),
            "failed": len(self.get_failed_tasks()),
            "cancelled": len([task for task in self.tasks.values() if task.status == TaskStatus.CANCELLED])
        }
    
    def start(self) -> None:
        """Startet den TaskManager (bereits beim Initialisieren gestartet)"""
        logger.info("TaskManager ist bereits gestartet")
    
    def stop(self) -> None:
        """Stoppt den TaskManager und wartet auf den Abschluss aller Aufgaben"""
        logger.info("Stoppe TaskManager...")
        
        # Signalisiere den Workern, dass sie stoppen sollen
        self.worker_stop.set()
        
        # Warte auf den Abschluss der Worker
        for worker in self.workers:
            worker.join(timeout=2.0)
            if worker.is_alive():
                logger.warning(f"Worker-Thread {worker.name} wurde nicht ordnungsgemäß beendet")
        
        # Leere die Warteschlange
        while not self.task_queue.empty():
            try:
                self.task_queue.get_nowait()
                self.task_queue.task_done()
            except queue.Empty:
                break
        
        logger.info("TaskManager erfolgreich gestoppt")
    
    def get_status(self) -> Dict[str, Any]:
        """Gibt den aktuellen Status des TaskManagers zurück"""
        return {
            "status": "running",
            "worker_count": len(self.workers),
            "pending_tasks": len(self.get_pending_tasks()),
            "running_tasks": len(self.get_running_tasks()),
            "completed_tasks": len(self.get_completed_tasks()),
            "failed_tasks": len(self.get_failed_tasks()),
            "queue_size": self.task_queue.qsize(),
            "max_queue_size": self.task_queue.maxsize,
            "timestamp": time.time()
        }