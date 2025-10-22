"""
self_learning.py
Implementiert die selbstlernenden Mechanismen für Mindestentinel
"""

import os
import sys
import logging
import json
import time
from typing import Dict, Any, Optional, List, Tuple
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
try:
    from config.config_loader import load_config
    logging.debug("ConfigLoader erfolgreich aus config.config_loader importiert")
except ImportError as e1:
    try:
        # Versuche aus src/config zu importieren
        from src.config.config_loader import load_config
        logging.debug("ConfigLoader erfolgreich aus src.config.config_loader importiert")
    except ImportError as e2:
        try:
            # Dynamischer Importversuch
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
                    load_config = config_loader_module.load_config
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
                        "max_tokens": 500,
                        "temperature": 0.7,
                        "models_dir": os.path.join(PROJECT_ROOT, "models"),
                        "cache_dir": os.path.join(PROJECT_ROOT, "cache")
                    },
                    "self_learning": {
                        "enabled": True,
                        "learning_rate": 0.01,
                        "memory_size": 1000,
                        "save_interval": 300,  # Alle 5 Minuten speichern
                        "learning_cycles": 100
                    }
                }

# Initialisiere Logging
logger = logging.getLogger("mindestentinel.self_learning")
logger.setLevel(logging.INFO)

class SelfLearning:
    """
    Implementiert die selbstlernenden Mechanismen für Mindestentinel
    Sammelt Erfahrungen, analysiert sie und verbessert das System basierend darauf
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialisiert das Selbstlern-System
        
        Args:
            config: Optionale Konfiguration für das Selbstlern-System
        """
        # Lade oder verwende Standardkonfiguration
        if config is None:
            try:
                main_config = load_config()
                self.config = main_config.get("self_learning", {})
                logger.debug("Selbstlern-Konfiguration aus Hauptkonfiguration geladen")
            except Exception as e:
                logger.error(f"Fehler beim Laden der Selbstlern-Konfiguration: {str(e)}")
                self.config = {
                    "enabled": True,
                    "learning_rate": 0.01,
                    "memory_size": 1000,
                    "save_interval": 300,
                    "learning_cycles": 100
                }
        else:
            self.config = config
        
        # Extrahiere Konfigurationsparameter
        self.enabled = self.config.get("enabled", True)
        self.learning_rate = self.config.get("learning_rate", 0.01)
        self.memory_size = self.config.get("memory_size", 1000)
        self.save_interval = self.config.get("save_interval", 300)
        self.learning_cycles = self.config.get("learning_cycles", 100)
        
        # Setze Pfade
        self.experience_path = os.path.join(PROJECT_ROOT, "data", "experiences.json")
        self.model_path = os.path.join(PROJECT_ROOT, "models", "self_learning_model.bin")
        
        # Erstelle Datenverzeichnis, falls nicht vorhanden
        data_dir = os.path.dirname(self.experience_path)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
            logger.info(f"Datenverzeichnis erstellt: {data_dir}")
        
        # Initialisiere interne Datenstrukturen
        self.experience_memory = []
        self.learning_active = False
        self.last_save_time = time.time()
        self.cycle_counter = 0
        
        # Lade gespeicherte Erfahrungen
        self._load_experiences()
        
        logger.info("SelfLearning-Modul erfolgreich initialisiert")
        logger.debug(f"Konfiguration: enabled={self.enabled}, learning_rate={self.learning_rate}, "
                    f"memory_size={self.memory_size}, save_interval={self.save_interval}s")
    
    def start_learning_process(self) -> None:
        """
        Startet den Selbstlernprozess
        
        Raises:
            RuntimeError: Wenn das Selbstlernen deaktiviert ist
        """
        if not self.enabled:
            logger.warning("Versuch, Selbstlernprozess zu starten, aber Selbstlernen ist deaktiviert")
            return
        
        logger.info("Starte Selbstlernprozess...")
        self.learning_active = True
        
        # Hier würde der eigentliche Lernprozess gestartet werden
        # In einer echten Implementierung würden wir einen Hintergrundthread starten
        logger.debug("Selbstlernprozess aktiviert")
    
    def stop_learning_process(self) -> None:
        """
        Stoppt den Selbstlernprozess
        """
        if not self.learning_active:
            logger.debug("Selbstlernprozess ist nicht aktiv, kein Stop erforderlich")
            return
        
        logger.info("Stoppe Selbstlernprozess...")
        self.learning_active = False
        
        # Hier würden wir den Hintergrundthread beenden
        logger.debug("Selbstlernprozess deaktiviert")
    
    def record_experience(self, experience: Dict[str, Any]) -> None:
        """
        Speichert eine neue Erfahrung im Gedächtnis
        
        Args:
            experience: Die zu speichernde Erfahrung
        """
        if not self.enabled:
            return
        
        # Füge Zeitstempel hinzu, falls nicht vorhanden
        if "timestamp" not in experience:
            experience["timestamp"] = datetime.now().isoformat()
        
        # Speichere die Erfahrung
        self.experience_memory.append(experience)
        
        # Begrenze die Gedächtnisgröße
        if len(self.experience_memory) > self.memory_size:
            self.experience_memory = self.experience_memory[-self.memory_size:]
        
        logger.debug(f"Erfahrung gespeichert. Aktuelle Gedächtnisgröße: {len(self.experience_memory)}/{self.memory_size}")
        
        # Speichere regelmäßig die Erfahrungen
        self._auto_save()
    
    def _auto_save(self) -> None:
        """
        Speichert die Erfahrungen automatisch in Intervallen
        """
        current_time = time.time()
        if current_time - self.last_save_time >= self.save_interval:
            self.save_progress()
            self.last_save_time = current_time
    
    def save_progress(self) -> Dict[str, Any]:
        """
        Speichert den aktuellen Lernfortschritt auf die Festplatte
        
        Returns:
            dict: Ergebnis des Speichervorgangs
        """
        if not self.enabled:
            return {"status": "warning", "message": "Selbstlernen ist deaktiviert"}
        
        try:
            # Speichere Erfahrungen
            with open(self.experience_path, 'w') as f:
                json.dump(self.experience_memory, f, indent=2)
            
            # Hier würden wir das Modell speichern
            # Für dieses Beispiel verwenden wir einen Dummy
            
            logger.info(f"Lernfortschritt gespeichert: {len(self.experience_memory)} Erfahrungen")
            return {"status": "success", "experiences_saved": len(self.experience_memory)}
            
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Lernfortschritts: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def load_progress(self) -> Dict[str, Any]:
        """
        Lädt den gespeicherten Lernfortschritt
        
        Returns:
            dict: Ergebnis des Ladevorgangs
        """
        if not self.enabled:
            return {"status": "warning", "message": "Selbstlernen ist deaktiviert"}
        
        return self._load_experiences()
    
    def _load_experiences(self) -> Dict[str, Any]:
        """
        Lädt gespeicherte Erfahrungen
        
        Returns:
            dict: Ergebnis des Ladevorgangs
        """
        if not os.path.exists(self.experience_path):
            logger.info("Keine gespeicherten Erfahrungen gefunden")
            return {"status": "info", "message": "Keine gespeicherten Erfahrungen gefunden"}
        
        try:
            with open(self.experience_path, 'r') as f:
                self.experience_memory = json.load(f)
            
            # Begrenze die Gedächtnisgröße
            if len(self.experience_memory) > self.memory_size:
                self.experience_memory = self.experience_memory[-self.memory_size:]
            
            logger.info(f"Gespeicherte Erfahrungen geladen: {len(self.experience_memory)}/{self.memory_size}")
            return {"status": "success", "experiences_loaded": len(self.experience_memory)}
            
        except Exception as e:
            logger.error(f"Fehler beim Laden der Erfahrungen: {str(e)}")
            self.experience_memory = []
            return {"status": "error", "message": str(e)}
    
    def analyze_experience(self) -> Dict[str, Any]:
        """
        Analysiert die gespeicherten Erfahrungen und leitet Verbesserungen ab
        
        Returns:
            dict: Analyseergebnisse und Verbesserungsvorschläge
        """
        if not self.enabled or not self.experience_memory:
            return {"status": "info", "message": "Keine Erfahrungen zum Analysieren"}
        
        try:
            # Hier würde die eigentliche Analyse stattfinden
            # Für dieses Beispiel geben wir einfache Statistiken zurück
            
            # Sammle Statistiken
            total_experiences = len(self.experience_memory)
            has_feedback = sum(1 for exp in self.experience_memory if "feedback" in exp)
            positive_feedback = sum(1 for exp in self.experience_memory 
                                   if exp.get("feedback") == "positive")
            
            # Berechne Metriken
            feedback_rate = has_feedback / total_experiences if total_experiences > 0 else 0
            positive_rate = positive_feedback / has_feedback if has_feedback > 0 else 0
            
            # Generiere Verbesserungsvorschläge
            suggestions = []
            if feedback_rate < 0.3:
                suggestions.append("Benutzerinteraktionen sind selten bewertet - Ermutige Benutzer zur Feedback-Abgabe")
            if positive_rate < 0.6:
                suggestions.append("Die Antwortqualität muss verbessert werden")
            
            result = {
                "status": "success",
                "total_experiences": total_experiences,
                "feedback_rate": feedback_rate,
                "positive_feedback_rate": positive_rate,
                "suggestions": suggestions,
                "last_analysis": datetime.now().isoformat()
            }
            
            logger.debug(f"Erfahrungsanalyse abgeschlossen: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Fehler bei der Erfahrungsanalyse: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def apply_improvements(self) -> Dict[str, Any]:
        """
        Wendet die abgeleiteten Verbesserungen auf das System an
        
        Returns:
            dict: Ergebnis der Verbesserungsanwendung
        """
        if not self.enabled:
            return {"status": "warning", "message": "Selbstlernen ist deaktiviert"}
        
        try:
            # Analysiere Erfahrungen
            analysis = self.analyze_experience()
            
            if analysis["status"] != "success":
                return analysis
            
            # Hier würden die Verbesserungen angewendet werden
            # Für dieses Beispiel verwenden wir einen Dummy
            
            logger.info("Verbesserungen wurden auf das System angewendet")
            return {
                "status": "success",
                "message": "Verbesserungen erfolgreich angewendet",
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"Fehler bei der Anwendung von Verbesserungen: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def learning_cycle(self) -> Dict[str, Any]:
        """
        Führt einen vollständigen Lernzyklus durch
        
        Returns:
            dict: Ergebnis des Lernzyklus
        """
        if not self.enabled:
            return {"status": "warning", "message": "Selbstlernen ist deaktiviert"}
        
        try:
            logger.debug("Starte Lernzyklus...")
            
            # Analysiere Erfahrungen
            analysis = self.analyze_experience()
            
            # Wende Verbesserungen an
            improvements = self.apply_improvements()
            
            # Speichere den Fortschritt
            save_result = self.save_progress()
            
            # Aktualisiere den Zykluszähler
            self.cycle_counter += 1
            
            result = {
                "status": "success",
                "cycle_number": self.cycle_counter,
                "analysis": analysis,
                "improvements": improvements,
                "save_result": save_result,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Lernzyklus {self.cycle_counter} abgeschlossen")
            return result
            
        except Exception as e:
            logger.error(f"Fehler im Lernzyklus: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Gibt Statistiken über das Selbstlern-System zurück
        
        Returns:
            dict: Statistische Daten
        """
        return {
            "enabled": self.enabled,
            "learning_rate": self.learning_rate,
            "memory_size": self.memory_size,
            "current_memory_usage": len(self.experience_memory),
            "learning_active": self.learning_active,
            "total_cycles": self.cycle_counter,
            "last_save": datetime.fromtimestamp(self.last_save_time).isoformat() if self.last_save_time else None
        }

# Testblock für direkte Ausführung (nur für Tests)
if __name__ == "__main__":
    print("Teste SelfLearning...")
    
    try:
        # Erstelle SelfLearning-Instanz
        print("\n1. Test: Initialisierung")
        sl = SelfLearning()
        print(f"  - SelfLearning initialisiert")
        print(f"  - Selbstlernen aktiviert: {sl.enabled}")
        print(f"  - Gedächtnisgröße: {sl.memory_size}")
        
        # Teste Erfassung von Erfahrungen
        print("\n2. Test: Erfassung von Erfahrungen")
        test_experience = {
            "input": "Hallo, wie geht es dir?",
            "response": "Mir geht es gut, danke!",
            "user_id": "test_user",
            "feedback": "positive"
        }
        sl.record_experience(test_experience)
        print(f"  - Erfahrung gespeichert. Aktuelle Gedächtnisgröße: {len(sl.experience_memory)}/{sl.memory_size}")
        
        # Teste Analyse
        print("\n3. Test: Erfahrungsanalyse")
        analysis = sl.analyze_experience()
        print(f"  - Analysestatus: {analysis['status']}")
        if analysis['status'] == 'success':
            print(f"    - Feedback-Rate: {analysis['feedback_rate']:.2%}")
            print(f"    - Positive Feedback-Rate: {analysis['positive_feedback_rate']:.2%}")
        
        # Teste Lernzyklus
        print("\n4. Test: Lernzyklus")
        cycle_result = sl.learning_cycle()
        print(f"  - Zyklusstatus: {cycle_result['status']}")
        
        # Teste Speichern
        print("\n5. Test: Speichern des Fortschritts")
        save_result = sl.save_progress()
        print(f"  - Speicherstatus: {save_result['status']}")
        if save_result['status'] == 'success':
            print(f"    - Gespeicherte Erfahrungen: {save_result['experiences_saved']}")
        
        # Teste Starten/Stoppen
        print("\n6. Test: Starten und Stoppen des Lernprozesses")
        sl.start_learning_process()
        print(f"  - Lernprozess aktiv: {sl.learning_active}")
        sl.stop_learning_process()
        print(f"  - Lernprozess aktiv: {sl.learning_active}")
        
    except Exception as e:
        print(f"Fehler im Test: {str(e)}")
    
    print("\nTest abgeschlossen")