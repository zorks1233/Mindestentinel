# src/core/multi_model_orchestrator.py
"""
MultiModelOrchestrator - Koordiniert die Interaktion mit verschiedenen LLMs
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class MultiModelOrchestrator:
    """
    Koordiniert die Interaktion mit verschiedenen LLMs (lokale und externe Modelle)
    """
    
    def __init__(self, model_manager=None):
        self.model_manager = model_manager
        self.teachers = []  # Lehrer-Modelle für Wissensakquisition
        self.students = []  # Studenten-Modelle für lokales Lernen
        logger.info("MultiModelOrchestrator initialisiert.")
    
    def inject_model_manager(self, model_manager):
        """Injiziert den ModelManager"""
        self.model_manager = model_manager
        logger.debug("ModelManager injiziert")
    
    def register_teacher_model(self, model_name: str):
        """Registriert ein Modell als Lehrer-Modell"""
        if model_name not in self.teachers:
            self.teachers.append(model_name)
            logger.info(f"Lehrer-Modell registriert: {model_name}")
    
    def register_student_model(self, model_name: str):
        """Registriert ein Modell als Studenten-Modell"""
        if model_name not in self.students:
            self.students.append(model_name)
            logger.info(f"Studenten-Modell registriert: {model_name}")
    
    def get_teacher_models(self) -> List[str]:
        """Gibt alle registrierten Lehrer-Modelle zurück"""
        return self.teachers
    
    def get_student_models(self) -> List[str]:
        """Gibt alle registrierten Studenten-Modelle zurück"""
        return self.students
    
    def query_models_batch(self, model_names: List[str], prompt: str, timeout: float = 30.0) -> Dict[str, str]:
        """
        Fragt mehrere Modelle synchron mit demselben Prompt ab.
        
        Args:
            model_names: Liste der Modellnamen
            prompt: Der zu verarbeitende Prompt
            timeout: Timeout für jede Abfrage
            
        Returns:
            Dictionary mit Modellname -> Antwort
        """
        results = {}
        if not self.model_manager:
            logger.error("Kein ModelManager injiziert")
            return results
            
        for model_name in model_names:
            try:
                response = self.model_manager.query_model(model_name, prompt)
                results[model_name] = response
                logger.debug(f"Antwort von {model_name}: {response[:100]}...")
            except Exception as e:
                logger.error(f"Fehler bei Abfrage von {model_name}: {str(e)}")
        
        return results
    
    def query_teacher_models(self, prompt: str, num_responses: int = 3, temperature: float = 0.7) -> Dict[str, str]:
        """
        Fragt Lehrer-Modelle für Wissensakquisition ab.
        
        Args:
            prompt: Der zu verarbeitende Prompt
            num_responses: Anzahl der gewünschten Antworten
            temperature: Temperatur für die Generierung
            
        Returns:
            Dictionary mit Modellname -> Antwort
        """
        if not self.model_manager:
            logger.error("Kein ModelManager injiziert. Kann Lehrer-Modelle nicht abfragen.")
            return {}
            
        if not self.teachers:
            # Standard-Lehrer-Modelle verwenden, falls keine registriert
            try:
                all_models = self.model_manager.list_models()
                # Verwende nur die ersten Modelle, die als Lehrer geeignet sind
                self.teachers = all_models[:min(num_responses, len(all_models))]
                logger.info(f"Verwende Standard-Lehrer-Modelle: {self.teachers}")
            except Exception as e:
                logger.error(f"Fehler beim Abrufen der Modelle: {str(e)}")
                return {}
        
        # Beschränke auf die gewünschte Anzahl von Antworten
        models_to_query = self.teachers[:num_responses]
        logger.info(f"Frage {len(models_to_query)} Lehrer-Modelle: {models_to_query}")
        
        # Setze Temperatur für Lehrer-Abfragen
        original_temps = {}
        for model in models_to_query:
            if hasattr(self.model_manager, 'get_model_config'):
                try:
                    original_temps[model] = self.model_manager.get_model_config(model).get('temperature', 0.7)
                    self.model_manager.update_model_config(model, {'temperature': temperature})
                except Exception as e:
                    logger.debug(f"Konnte Temperatur für {model} nicht ändern: {str(e)}")
        
        # Führe Abfragen durch
        results = self.query_models_batch(models_to_query, prompt)
        
        # Setze ursprüngliche Temperaturen zurück
        for model, temp in original_temps.items():
            if hasattr(self.model_manager, 'update_model_config'):
                try:
                    self.model_manager.update_model_config(model, {'temperature': temp})
                except Exception as e:
                    logger.debug(f"Konnte Temperatur für {model} nicht zurücksetzen: {str(e)}")
        
        return results
    
    def query_model(self, model_name: str, prompt: str, **kwargs) -> str:
        """
        Fragt ein einzelnes Modell mit einem Prompt ab.
        
        Args:
            model_name: Name des Modells
            prompt: Der zu verarbeitende Prompt
            
        Returns:
            Die Antwort des Modells
        """
        if not self.model_manager:
            logger.error("Kein ModelManager injiziert. Kann Modell nicht abfragen.")
            return "Fehler: Kein ModelManager injiziert"
        
        try:
            # Hole die Konfiguration für das Modell
            config = {}
            if hasattr(self.model_manager, 'get_model_config'):
                config = self.model_manager.get_model_config(model_name)
            
            # Aktualisiere mit benutzerspezifischen Parametern
            config.update(kwargs)
            
            # Führe die Abfrage durch
            response = self.model_manager.query_model(model_name, prompt, **config)
            logger.debug(f"Antwort von {model_name}: {response[:100]}...")
            return response
        except Exception as e:
            logger.error(f"Fehler bei der Abfrage von {model_name}: {str(e)}", exc_info=True)
            return f"Fehler bei der Abfrage: {str(e)}"