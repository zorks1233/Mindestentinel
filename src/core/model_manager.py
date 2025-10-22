"""
model_manager.py
Verwaltet das Laden, Speichern und Verwalten von KI-Modellen in Mindestentinel
"""

import os
import sys
import logging
import json
import time
from typing import Dict, Any, Optional, List, Union, Tuple
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
                        "memory_size": 1000
                    }
                }

# Initialisiere Logging
logger = logging.getLogger("mindestentinel.model_manager")
logger.setLevel(logging.INFO)

class ModelManager:
    """
    Verwaltet das Laden, Speichern und Verwalten von KI-Modellen
    """
    
    def __init__(self, config: Union[Dict[str, Any], str, None] = None, 
                 models_dir: Optional[str] = None,
                 cache_dir: Optional[str] = None):
        """
        Initialisiert den ModelManager
        
        Args:
            config: Konfigurationsdaten oder Pfad zur Konfigurationsdatei
            models_dir: Optionales Verzeichnis für Modelle (überschreibt Konfiguration)
            cache_dir: Optionales Verzeichnis für Cache (überschreibt Konfiguration)
        """
        # Verarbeite die Konfiguration
        if config is None:
            try:
                self.config = load_config()
                logger.debug("Konfiguration über load_config() geladen")
            except Exception as e:
                logger.error(f"Fehler beim Laden der Konfiguration: {str(e)}")
                self.config = {
                    "model": {
                        "default": "gpt-3.5-turbo",
                        "max_tokens": 500,
                        "temperature": 0.7,
                        "models_dir": os.path.join(PROJECT_ROOT, "models"),
                        "cache_dir": os.path.join(PROJECT_ROOT, "cache")
                    }
                }
        elif isinstance(config, str):
            try:
                # Annahme: config ist ein Pfad zur Konfigurationsdatei
                if config.endswith('.yaml') or config.endswith('.yml'):
                    import yaml
                    with open(config, 'r') as f:
                        self.config = yaml.safe_load(f)
                elif config.endswith('.json'):
                    with open(config, 'r') as f:
                        self.config = json.load(f)
                else:
                    raise ValueError(f"Unbekanntes Konfigurationsformat: {config}")
                logger.debug(f"Konfiguration aus Datei geladen: {config}")
            except Exception as e:
                logger.error(f"Fehler beim Laden der Konfigurationsdatei {config}: {str(e)}")
                self.config = {
                    "model": {
                        "default": "gpt-3.5-turbo",
                        "max_tokens": 500,
                        "temperature": 0.7,
                        "models_dir": os.path.join(PROJECT_ROOT, "models"),
                        "cache_dir": os.path.join(PROJECT_ROOT, "cache")
                    }
                }
        else:
            # config ist bereits ein Dictionary
            self.config = config
            logger.debug("Konfiguration direkt übergeben")
        
        # Extrahiere Model-Konfiguration
        self.model_config = self.config.get("model", {})
        
        # Setze Modelle-Verzeichnis
        if models_dir:
            self.models_dir = models_dir
        else:
            self.models_dir = self.model_config.get("models_dir", 
                                                   os.path.join(PROJECT_ROOT, "models"))
        
        # Stelle sicher, dass models_dir ein String ist
        if isinstance(self.models_dir, dict):
            # Extrahiere den tatsächlichen Pfad aus dem Dictionary
            self.models_dir = self.models_dir.get("path", 
                                                os.path.join(PROJECT_ROOT, "models"))
        
        # Konvertiere zu String, falls nötig
        if not isinstance(self.models_dir, str):
            self.models_dir = str(self.models_dir)
        
        # Setze Cache-Verzeichnis
        if cache_dir:
            self.cache_dir = cache_dir
        else:
            self.cache_dir = self.model_config.get("cache_dir", 
                                                  os.path.join(self.models_dir, "cache"))
        
        # Konvertiere zu String, falls nötig
        if not isinstance(self.cache_dir, str):
            self.cache_dir = str(self.cache_dir)
        
        # Erstelle Verzeichnisse, falls nicht vorhanden
        try:
            os.makedirs(self.models_dir, exist_ok=True)
            logger.info(f"Modelle-Verzeichnis erstellt/verifiziert: {self.models_dir}")
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Modelle-Verzeichnisses: {str(e)}")
            # Versuche einen Fallback-Pfad
            self.models_dir = os.path.join(PROJECT_ROOT, "models")
            os.makedirs(self.models_dir, exist_ok=True)
            logger.info(f"Verwende Fallback-Modelle-Verzeichnis: {self.models_dir}")
        
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            logger.info(f"Cache-Verzeichnis erstellt/verifiziert: {self.cache_dir}")
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Cache-Verzeichnisses: {str(e)}")
            # Versuche einen Fallback-Pfad
            self.cache_dir = os.path.join(self.models_dir, "cache")
            os.makedirs(self.cache_dir, exist_ok=True)
            logger.info(f"Verwende Fallback-Cache-Verzeichnis: {self.cache_dir}")
        
        # Initialisiere interne Datenstrukturen
        self.loaded_models = {}
        self.model_metadata = {}
        self.default_model = self.model_config.get("default", "gpt-3.5-turbo")
        self.max_tokens = self.model_config.get("max_tokens", 500)
        self.temperature = self.model_config.get("temperature", 0.7)
        
        logger.info("ModelManager erfolgreich initialisiert")
    
    def load_models(self) -> Dict[str, Any]:
        """
        Lädt alle verfügbaren Modelle
        
        Returns:
            dict: Status der Modell-Ladevorgänge
        """
        logger.info("Lade Modelle...")
        results = {}
        
        # Lade das Standardmodell
        try:
            self.load_model(self.default_model)
            results[self.default_model] = {"status": "success", "message": "Standardmodell geladen"}
            logger.info(f"Standardmodell geladen: {self.default_model}")
        except Exception as e:
            results[self.default_model] = {"status": "error", "message": str(e)}
            logger.error(f"Fehler beim Laden des Standardmodells: {str(e)}")
        
        # Hier könnten weitere Modelle geladen werden
        # z.B. durch Durchsuchen des models_dir
        
        return results
    
    def load_model(self, model_name: str) -> Any:
        """
        Lädt ein spezifisches Modell
        
        Args:
            model_name: Name des zu ladenden Modells
            
        Returns:
            Das geladene Modell
            
        Raises:
            ValueError: Wenn das Modell nicht gefunden wird
        """
        logger.debug(f"Versuche Modell zu laden: {model_name}")
        
        # Prüfe, ob das Modell bereits geladen ist
        if model_name in self.loaded_models:
            logger.debug(f"Modell bereits geladen: {model_name}")
            return self.loaded_models[model_name]
        
        # Versuche das Modell zu laden
        try:
            # Hier würde die eigentliche Modell-Ladung stattfinden
            # Für dieses Beispiel verwenden wir einen Dummy
            logger.info(f"Modell '{model_name}' wird geladen...")
            
            # Simuliere Ladezeit
            time.sleep(0.5)
            
            # Erstelle ein Dummy-Modell
            model = {
                "name": model_name,
                "loaded_at": datetime.now().isoformat(),
                "status": "loaded"
            }
            
            # Speichere das geladene Modell
            self.loaded_models[model_name] = model
            self.model_metadata[model_name] = {
                "path": os.path.join(self.models_dir, f"{model_name}.bin"),
                "size": "1.2GB",
                "loaded_at": datetime.now().isoformat()
            }
            
            logger.info(f"Modell erfolgreich geladen: {model_name}")
            return model
            
        except Exception as e:
            logger.error(f"Fehler beim Laden des Modells '{model_name}': {str(e)}")
            raise
    
    def save_models(self) -> Dict[str, Any]:
        """
        Speichert alle geladenen Modelle
        
        Returns:
            dict: Status der Modell-Speichervorgänge
        """
        logger.info("Speichere Modelle...")
        results = {}
        
        for model_name, model in self.loaded_models.items():
            try:
                self.save_model(model_name)
                results[model_name] = {"status": "success", "message": "Modell gespeichert"}
            except Exception as e:
                results[model_name] = {"status": "error", "message": str(e)}
        
        return results
    
    def save_model(self, model_name: str) -> None:
        """
        Speichert ein spezifisches Modell
        
        Args:
            model_name: Name des zu speichernden Modells
            
        Raises:
            ValueError: Wenn das Modell nicht geladen ist
        """
        logger.debug(f"Versuche Modell zu speichern: {model_name}")
        
        # Prüfe, ob das Modell geladen ist
        if model_name not in self.loaded_models:
            logger.error(f"Modell nicht geladen: {model_name}")
            raise ValueError(f"Modell '{model_name}' ist nicht geladen")
        
        # Speichere das Modell
        try:
            logger.info(f"Speichere Modell: {model_name}")
            
            # Hier würde die eigentliche Modell-Speicherung stattfinden
            # Für dieses Beispiel verwenden wir einen Dummy
            
            # Simuliere Speicherzeit
            time.sleep(0.3)
            
            # Aktualisiere die Metadaten
            self.model_metadata[model_name]["saved_at"] = datetime.now().isoformat()
            
            logger.info(f"Modell erfolgreich gespeichert: {model_name}")
            
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Modells '{model_name}': {str(e)}")
            raise
    
    def generate_response(self, input_: str, user_id: Optional[str] = None, 
                          enable_autonomy: bool = False, **kwargs) -> str:
        """
        Generiert eine Antwort basierend auf dem Eingabetext
        
        Args:
            input_: Der Eingabetext
            user_id: Optional die ID des Benutzers
            enable_autonomy: Gibt an, ob autonome Funktionen aktiviert sind
            **kwargs: Zusätzliche Parameter für die Antwortgenerierung
            
        Returns:
            Die generierte Antwort
        """
        logger.debug(f"Generiere Antwort für Eingabe: {input_[:50]}{'...' if len(input_) > 50 else ''}")
        
        # Wähle das Modell (Standardmodell oder benutzerspezifisches Modell)
        model_name = self.default_model
        if user_id and f"{user_id}_model" in self.loaded_models:
            model_name = f"{user_id}_model"
        
        # Prüfe, ob das Modell geladen ist
        if model_name not in self.loaded_models:
            try:
                self.load_model(model_name)
            except Exception as e:
                logger.error(f"Fehler beim Laden des Modells '{model_name}': {str(e)}")
                # Fallback auf ein einfaches Modell
                model_name = "gpt-3.5-turbo"
                if model_name not in self.loaded_models:
                    self.load_model(model_name)
        
        # Generiere die Antwort
        try:
            logger.info(f"Generiere Antwort mit Modell: {model_name}")
            
            # Hier würde die eigentliche Antwortgenerierung stattfinden
            # Für dieses Beispiel verwenden wir einen Dummy
            
            # Simuliere Verarbeitungszeit
            time.sleep(0.2)
            
            # Erstelle eine Dummy-Antwort
            if "hallo" in input_.lower():
                response = "Hallo! Wie kann ich Ihnen heute helfen?"
            elif "name" in input_.lower():
                response = "Ich bin Mindestentinel, eine fortschrittliche KI-Plattform im Alpha-Stadium."
            elif "aufgabe" in input_.lower() or "was kannst du" in input_.lower():
                response = ("Ich bin eine experimentelle KI-Plattform namens Mindestentinel, "
                           "die darauf abzielt, AGI (Artificial General Intelligence) zu entwickeln. "
                           "Ich kann komplexe Aufgaben lösen, lernen und mich an Benutzer anpassen.")
            else:
                # Einfache Echo-Antwort mit etwas Variation
                response = f"Ich habe verstanden: '{input_}'. "
                if enable_autonomy:
                    response += "Basierend auf meiner autonomen Analyse würde ich vorschlagen, dass wir dies weiter besprechen."
                else:
                    response += "Könnten Sie Ihre Frage präzisieren?"
            
            logger.info(f"Antwort generiert: {response[:50]}{'...' if len(response) > 50 else ''}")
            return response
            
        except Exception as e:
            logger.error(f"Fehler bei der Antwortgenerierung: {str(e)}")
            return "Entschuldigung, ich konnte Ihre Anfrage nicht verarbeiten."
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Gibt Informationen über ein geladenes Modell zurück
        
        Args:
            model_name: Name des Modells
            
        Returns:
            dict: Informationen über das Modell
        """
        if model_name not in self.model_metadata:
            logger.warning(f"Keine Metadaten für Modell: {model_name}")
            return {
                "name": model_name,
                "status": "not_loaded",
                "message": "Modell ist nicht geladen oder existiert nicht"
            }
        
        return {
            "name": model_name,
            "status": "loaded" if model_name in self.loaded_models else "available",
            "metadata": self.model_metadata.get(model_name, {}),
            "is_loaded": model_name in self.loaded_models
        }
    
    def list_available_models(self) -> List[str]:
        """
        Listet alle verfügbaren Modelle auf
        
        Returns:
            list: Liste der verfügbaren Modellnamen
        """
        logger.debug("Liste verfügbare Modelle...")
        
        # In einer echten Implementierung würden wir das models_dir durchsuchen
        # Für dieses Beispiel geben wir einige Dummy-Modelle zurück
        available_models = [
            "gpt-3.5-turbo",
            "gpt-4",
            "llama-2-7b",
            "mindestentinel-base",
            "mindestentinel-quantum"
        ]
        
        logger.info(f"{len(available_models)} Modelle verfügbar")
        return available_models
    
    def unload_model(self, model_name: str) -> None:
        """
        Entlädt ein geladenes Modell
        
        Args:
            model_name: Name des zu entladenden Modells
        """
        logger.debug(f"Entlade Modell: {model_name}")
        
        if model_name in self.loaded_models:
            # Hier würde die eigentliche Modell-Entladung stattfinden
            # Für dieses Beispiel entfernen wir es einfach aus dem Dictionary
            
            # Speichere das Modell vor dem Entladen (optional)
            try:
                self.save_model(model_name)
                logger.info(f"Modell vor dem Entladen gespeichert: {model_name}")
            except Exception as e:
                logger.warning(f"Fehler beim Speichern vor dem Entladen: {str(e)}")
            
            # Entlade das Modell
            del self.loaded_models[model_name]
            logger.info(f"Modell entladen: {model_name}")
        else:
            logger.warning(f"Versuch, nicht geladenes Modell zu entladen: {model_name}")
    
    def unload_all_models(self) -> None:
        """
        Entlädt alle geladenen Modelle
        """
        logger.info("Entlade alle Modelle...")
        
        # Erstelle eine Kopie der Schlüssel, da wir das Dictionary ändern
        model_names = list(self.loaded_models.keys())
        
        for model_name in model_names:
            self.unload_model(model_name)
        
        logger.info("Alle Modelle entladen")
    
    def get_default_model(self) -> str:
        """
        Gibt das Standardmodell zurück
        
        Returns:
            str: Name des Standardmodells
        """
        return self.default_model
    
    def set_default_model(self, model_name: str) -> None:
        """
        Setzt das Standardmodell
        
        Args:
            model_name: Name des neuen Standardmodells
        """
        logger.info(f"Setze Standardmodell auf: {model_name}")
        self.default_model = model_name
    
    def get_model_path(self, model_name: str) -> str:
        """
        Gibt den Pfad zu einem Modell zurück
        
        Args:
            model_name: Name des Modells
            
        Returns:
            str: Pfad zum Modell
        """
        return os.path.join(self.models_dir, f"{model_name}.bin")
    
    def optimize_model(self, model_name: str, optimization_level: int = 2) -> Dict[str, Any]:
        """
        Optimiert ein Modell für bessere Leistung
        
        Args:
            model_name: Name des zu optimierenden Modells
            optimization_level: Stufe der Optimierung (1-3)
            
        Returns:
            dict: Ergebnis der Optimierung
        """
        logger.info(f"Optimiere Modell {model_name} (Stufe {optimization_level})...")
        
        try:
            # Prüfe, ob das Modell geladen ist
            if model_name not in self.loaded_models:
                self.load_model(model_name)
            
            # Hier würde die eigentliche Modell-Optimierung stattfinden
            # Für dieses Beispiel verwenden wir einen Dummy
            
            # Simuliere Optimierungszeit
            time.sleep(1.0)
            
            # Erstelle Optimierungsmetadaten
            optimization_data = {
                "model": model_name,
                "optimization_level": optimization_level,
                "optimized_at": datetime.now().isoformat(),
                "size_before": self.model_metadata[model_name].get("size", "1.2GB"),
                "size_after": "900MB",
                "speedup_factor": 1.5
            }
            
            # Speichere die Optimierungsmetadaten
            if model_name not in self.model_metadata:
                self.model_metadata[model_name] = {}
            self.model_metadata[model_name]["optimization"] = optimization_data
            
            logger.info(f"Modell erfolgreich optimiert: {model_name}")
            return {
                "status": "success",
                "message": f"Modell {model_name} erfolgreich optimiert",
                "data": optimization_data
            }
            
        except Exception as e:
            logger.error(f"Fehler bei der Modell-Optimierung: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def clone_model(self, source_model: str, target_model: str) -> Dict[str, Any]:
        """
        Klont ein Modell
        
        Args:
            source_model: Name des Quellmodells
            target_model: Name des Zielmodells
            
        Returns:
            dict: Ergebnis des Klonvorgangs
        """
        logger.info(f"Klone Modell {source_model} zu {target_model}...")
        
        try:
            # Prüfe, ob das Quellmodell existiert
            if source_model not in self.loaded_models and not os.path.exists(self.get_model_path(source_model)):
                raise ValueError(f"Quellmodell {source_model} existiert nicht")
            
            # Lade das Quellmodell, falls nicht geladen
            if source_model not in self.loaded_models:
                self.load_model(source_model)
            
            # Hier würde die eigentliche Modell-Klonung stattfinden
            # Für dieses Beispiel verwenden wir einen Dummy
            
            # Simuliere Klonzeit
            time.sleep(0.7)
            
            # Erstelle das geklonte Modell
            self.loaded_models[target_model] = {
                "name": target_model,
                "cloned_from": source_model,
                "cloned_at": datetime.now().isoformat(),
                "status": "cloned"
            }
            
            # Kopiere die Metadaten
            self.model_metadata[target_model] = {
                **self.model_metadata.get(source_model, {}),
                "cloned_from": source_model,
                "cloned_at": datetime.now().isoformat()
            }
            
            logger.info(f"Modell erfolgreich geklont: {source_model} -> {target_model}")
            return {
                "status": "success",
                "message": f"Modell {source_model} erfolgreich zu {target_model} geklont"
            }
            
        except Exception as e:
            logger.error(f"Fehler beim Klonen des Modells: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

# Testblock für direkte Ausführung (nur für Tests)
if __name__ == "__main__":
    print("Teste ModelManager...")
    
    try:
        # Erstelle ModelManager
        print("\n1. Test: Initialisierung")
        manager = ModelManager()
        print(f"  - ModelManager initialisiert")
        print(f"  - Modelle-Verzeichnis: {manager.models_dir}")
        print(f"  - Cache-Verzeichnis: {manager.cache_dir}")
        
        # Teste Modell-Liste
        print("\n2. Test: Verfügbare Modelle")
        models = manager.list_available_models()
        print(f"  - {len(models)} Modelle verfügbar: {models}")
        
        # Teste Standardmodell-Ladung
        print(f"\n3. Test: Lade Standardmodell ({manager.default_model})")
        manager.load_models()
        print(f"  - Geladene Modelle: {list(manager.loaded_models.keys())}")
        
        # Teste Antwortgenerierung
        print("\n4. Test: Antwortgenerierung")
        response = manager.generate_response("Hallo, wie geht es dir?")
        print(f"  - Antwort: {response}")
        
        # Teste Modell-Optimierung
        print(f"\n5. Test: Optimiere Modell {manager.default_model}")
        optimization_result = manager.optimize_model(manager.default_model)
        print(f"  - Optimierungsergebnis: {optimization_result['status']}")
        if optimization_result['status'] == 'success':
            print(f"    - Größenreduktion: {optimization_result['data']['size_before']} -> {optimization_result['data']['size_after']}")
        
        # Teste Modell-Klonung
        print(f"\n6. Test: Klone Modell {manager.default_model} zu test_clone")
        clone_result = manager.clone_model(manager.default_model, "test_clone")
        print(f"  - Klonungsergebnis: {clone_result['status']}")
        if clone_result['status'] == 'success':
            print(f"    - Geladene Modelle nach Klonung: {list(manager.loaded_models.keys())}")
        
        # Teste Modell-Entladung
        print("\n7. Test: Entlade alle Modelle")
        manager.unload_all_models()
        print(f"  - Geladene Modelle nach Entladung: {list(manager.loaded_models.keys())}")
        
    except Exception as e:
        print(f"Fehler im Test: {str(e)}")
    
    print("\nTest abgeschlossen")