# src/core/model_manager.py
"""
ModelManager - Verwaltet das Laden, Speichern und Abfragen von KI-Modellen
"""

import logging
import os
import json
from typing import Dict, Any, List, Optional, Callable

logger = logging.getLogger(__name__)

class ModelManager:
    """
    Verwaltet das Laden und Verwalten von KI-Modellen.
    Lädt automatisch alle Modelle aus dem Model-Ordner.
    """
    
    def __init__(self, models_dir: str = "data/models"):
        """
        Initialisiert den ModelManager.
        
        Args:
            models_dir: Verzeichnis, in dem Modelle gespeichert werden
        """
        self.models_dir = models_dir
        self.models = {}  # name -> model_instance
        self.model_configs = {}  # name -> config
        
        # Erstelle Model-Verzeichnis, falls nicht vorhanden
        os.makedirs(models_dir, exist_ok=True)
        
        # Lade Modelle aus dem Ordner
        self._load_models_from_directory()
        
        if not self.models:
            logger.info("Keine Modelle im Ordner gefunden: %s", self.models_dir)
        else:
            logger.info(f"ModelManager initialisiert mit {len(self.models)} Modellen aus {self.models_dir}.")
    
    def _load_models_from_directory(self):
        """Lädt alle Modelle aus dem Model-Ordner"""
        # 1. Versuche, model_registry.json zu laden
        registry_path = os.path.join(self.models_dir, "model_registry.json")
        if os.path.exists(registry_path):
            try:
                with open(registry_path, 'r') as f:
                    registry = json.load(f)
                
                # Registriere alle Modelle aus der Registry
                for model_name, config in registry.items():
                    self._register_model_from_config(model_name, config)
                
                logger.info(f"Geladen: {len(registry)} Modelle aus model_registry.json")
                return
            except Exception as e:
                logger.error(f"Fehler beim Laden der Registry: {str(e)}")
        
        # 2. Fallback: Scanne das Verzeichnis nach Modellen
        model_count = 0
        for item in os.listdir(self.models_dir):
            item_path = os.path.join(self.models_dir, item)
            
            # Prüfe, ob es sich um ein Modell-Verzeichnis handelt
            if os.path.isdir(item_path) and not item.startswith('.'):
                # Erstelle eine Standardkonfiguration für das Modell
                config = {
                    "type": "local",
                    "path": item_path,
                    "status": "loaded",
                    "config": {
                        "temperature": 0.7,
                        "max_tokens": 512
                    },
                    "categories": ["general", "knowledge", "cognitive"],
                    "metadata": {
                        "last_improved": None,
                        "performance_gain": 0.0
                    }
                }
                
                # Registriere das Modell
                self._register_model_from_config(item, config)
                model_count += 1
        
        if model_count > 0:
            logger.info(f"Geladen: {model_count} Modelle aus dem Verzeichnis")
        
        # 3. Wenn immer noch keine Modelle gefunden wurden, erstelle eine leere Registry
        if not self.models:
            self._create_empty_registry()
    
    def _register_model_from_config(self, model_name: str, config: Dict):
        """Registriert ein Modell basierend auf seiner Konfiguration"""
        # Erstelle einen Stub für das Modell
        self.models[model_name] = self._create_model_stub(model_name, config)
        self.model_configs[model_name] = config
        logger.info(f"Modell registriert: {model_name} ({config.get('type', 'unknown')})")
    
    def _create_empty_registry(self):
        """Erstellt eine leere Registry-Datei"""
        registry_path = os.path.join(self.models_dir, "model_registry.json")
        try:
            with open(registry_path, 'w') as f:
                json.dump({}, f, indent=2)
            logger.info(f"Leere Registry erstellt: {registry_path}")
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der leeren Registry: {str(e)}")
    
    def _create_model_stub(self, name: str, config: Dict) -> Callable:
        """Erstellt einen Stub für das Modell"""
        def model_query(prompt: str, **kwargs) -> str:
            # In einer echten Implementierung würde hier das Modell abgefragt
            return f"Simulierte Antwort von {name} auf: '{prompt[:50]}...'"
        return model_query
    
    def list_models(self) -> List[str]:
        """Gibt eine Liste aller verfügbaren Modelle zurück"""
        return list(self.models.keys())
    
    def get_model(self, model_name: str) -> Optional[Callable]:
        """Gibt eine Referenz auf das Modell zurück"""
        return self.models.get(model_name)
    
    def get_model_config(self, model_name: str) -> Dict:
        """Gibt die Konfiguration eines Modells zurück"""
        return self.model_configs.get(model_name, {})
    
    def get_model_metadata(self, model_name: str) -> Dict:
        """Gibt die Metadaten eines Modells zurück"""
        config = self.model_configs.get(model_name, {})
        return config.get("metadata", {})
    
    def update_model_metadata(self, model_name: str, metadata: Dict) -> bool:
        """
        Aktualisiert die Metadaten eines Modells.
        
        Args:
            model_name: Name des Modells
            metadata: Zu aktualisierende Metadaten
            
        Returns:
            bool: True bei Erfolg
        """
        if model_name not in self.model_configs:
            return False
        
        # Stelle sicher, dass der metadata-Schlüssel existiert
        if "metadata" not in self.model_configs[model_name]:
            self.model_configs[model_name]["metadata"] = {}
        
        # Aktualisiere die Metadaten
        self.model_configs[model_name]["metadata"].update(metadata)
        return True
    
    def get_best_model_for_category(self, category: str) -> Optional[str]:
        """
        Gibt das beste Modell für eine bestimmte Kategorie zurück.
        
        Args:
            category: Die Kategorie, für die ein Modell benötigt wird
            
        Returns:
            Der Name des besten Modells oder None, wenn keines passt
        """
        # Definiere, welche Modelle für welche Kategorien geeignet sind
        for model_name, config in self.model_configs.items():
            if "categories" in config and category in config["categories"]:
                return model_name
        
        # Wenn keine passenden Modelle gefunden wurden, wähle einfach das erste verfügbare Modell
        if self.models:
            return next(iter(self.models))
        
        return None
    
    def update_model_config(self, model_name: str, new_config: Dict) -> bool:
        """Aktualisiert die Konfiguration eines Modells"""
        if model_name not in self.model_configs:
            return False
        
        # Aktualisiere nur die angegebenen Felder
        self.model_configs[model_name].update(new_config)
        return True
    
    def query_model(self, model_name: str, prompt: str, **kwargs) -> str:
        """
        Fragt ein Modell mit einem Prompt ab.
        
        Args:
            model_name: Name des Modells
            prompt: Der zu verarbeitende Prompt
            
        Returns:
            Die Antwort des Modells
        """
        model = self.get_model(model_name)
        if not model:
            logger.error(f"Modell nicht gefunden: {model_name}")
            return "Fehler: Modell nicht gefunden"
        
        try:
            # Hole die Konfiguration für das Modell
            config = self.get_model_config(model_name)
            # Aktualisiere mit benutzerspezifischen Parametern
            config.update(kwargs)
            
            # Führe die Abfrage durch
            response = model(prompt, **config)
            logger.debug(f"Antwort von {model_name}: {response[:100]}...")
            return response
        except Exception as e:
            logger.error(f"Fehler bei der Abfrage von {model_name}: {str(e)}", exc_info=True)
            return f"Fehler bei der Abfrage: {str(e)}"
    
    def load_model(self, model_name: str, model_type: str, **kwargs) -> bool:
        """
        Lädt ein neues Modell.
        
        Args:
            model_name: Name des Modells
            model_type: Typ des Modells (local, api, etc.)
            
        Returns:
            bool: True bei Erfolg
        """
        # In einer echten Implementierung würde hier das Modell geladen
        logger.info(f"Lade Modell: {model_name} ({model_type})")
        
        # Erstelle Konfiguration
        config = {
            "type": model_type,
            "status": "loaded",
            "config": kwargs,
            "categories": ["general"],
            "metadata": {
                "last_improved": None,
                "performance_gain": 0.0
            }
        }
        
        # Speichere Konfiguration
        self.model_configs[model_name] = config
        
        # Erstelle Stub
        self.models[model_name] = self._create_model_stub(model_name, config)
        
        # Aktualisiere die Registry
        self._update_registry()
        
        return True
    
    def _update_registry(self):
        """Aktualisiert die model_registry.json mit aktuellen Modellkonfigurationen"""
        registry_path = os.path.join(self.models_dir, "model_registry.json")
        try:
            # Erstelle ein Dictionary nur mit den relevanten Konfigurationsdaten
            registry_data = {}
            for model_name, config in self.model_configs.items():
                # Entferne das Model-Objekt aus der Konfiguration
                safe_config = config.copy()
                if "model" in safe_config:
                    del safe_config["model"]
                registry_data[model_name] = safe_config
            
            with open(registry_path, 'w') as f:
                json.dump(registry_data, f, indent=2)
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der Registry: {str(e)}")
    
    def unload_model(self, model_name: str) -> bool:
        """Entlädt ein Modell"""
        if model_name in self.models:
            del self.models[model_name]
            del self.model_configs[model_name]
            logger.info(f"Modell entladen: {model_name}")
            
            # Aktualisiere die Registry
            self._update_registry()
            
            return True
        return False
    
    def get_model_status(self, model_name: str) -> str:
        """Gibt den Status eines Modells zurück"""
        config = self.model_configs.get(model_name, {})
        return config.get("status", "unknown")