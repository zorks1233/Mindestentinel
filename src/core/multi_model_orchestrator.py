# src/core/multi_model_orchestrator.py
"""
multi_model_orchestrator.py - Koordiniert die Interaktion zwischen Lehrer- und Schülermodellen

Diese Datei implementiert den Multi-Model-Orchestrator für das System.
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("mindestentinel.multi_model_orchestrator")

class MultiModelOrchestrator:
    """Koordiniert die Interaktion zwischen verschiedenen Modellen"""
    
    def __init__(self, model_manager):
        """Initialisiert den Multi-Model-Orchestrator
        
        Args:
            model_manager: Die ModelManager-Instanz
        """
        self.model_manager = model_manager
        self.teacher_models = []
        self.student_models = []
        logger.info("MultiModelOrchestrator initialisiert.")
    
    def register_teacher_model(self, model_name: str):
        """Registriert ein Modell als Lehrer-Modell
        
        Args:
            model_name: Name des Modells
        """
        if model_name not in self.teacher_models:
            self.teacher_models.append(model_name)
            logger.info(f"Lehrer-Modell registriert: {model_name}")
    
    def register_student_model(self, model_name: str):
        """Registriert ein Modell als Schüler-Modell
        
        Args:
            model_name: Name des Modells
        """
        if model_name not in self.student_models:
            self.student_models.append(model_name)
            logger.info(f"Schüler-Modell registriert: {model_name}")
    
    def get_teacher_models(self) -> List[str]:
        """Holt alle registrierten Lehrer-Modelle"""
        return self.teacher_models
    
    def get_student_models(self) -> List[str]:
        """Holt alle registrierten Schüler-Modelle"""
        return self.student_models
    
    def get_active_models(self) -> List[str]:
        """Holt alle aktiven Modelle (Lehrer + Schüler)"""
        return list(set(self.teacher_models + self.student_models))
    
    def query(self, model_name: str, prompt: str, max_tokens: int = 512) -> str:
        """
        Fragt ein spezifisches Modell mit einer Benutzeranfrage
        
        Args:
            model_name: Name des Modells
            prompt: Die Benutzeranfrage
            max_tokens: Maximale Anzahl der Tokens für die Antwort
            
        Returns:
            str: Die Modellantwort
        """
        try:
            logger.info(f"Frage {model_name} mit Prompt: {prompt[:50]}...")
            
            # Hole das Modell vom ModelManager
            model = self.model_manager.get_model(model_name)
            if not model:
                logger.error(f"Modell {model_name} nicht gefunden")
                return "Entschuldigung, ich konnte diese Anfrage nicht verarbeiten."
            
            # Generiere die Antwort
            response = model.generate(
                prompt,
                max_new_tokens=max_tokens,
                do_sample=True,
                temperature=0.7,
                top_p=0.95
            )
            
            # Extrahiere den generierten Text
            if hasattr(response, 'generated_text'):
                return response.generated_text
            elif isinstance(response, str):
                return response
            else:
                return str(response)
                
        except Exception as e:
            logger.error(f"Fehler bei der Abfrage von {model_name}: {str(e)}", exc_info=True)
            return "Entschuldigung, ich konnte diese Anfrage nicht verarbeiten."
    
    def query_teacher_models(self, prompt: str, num_responses: int = 3, temperature: float = 0.3) -> List[str]:
        """
        Fragt alle Lehrer-Modelle mit einer Benutzeranfrage
        
        Args:
            prompt: Die Benutzeranfrage
            num_responses: Anzahl der gewünschten Antworten
            temperature: Temperatur für die Generierung
            
        Returns:
            List[str]: Antworten von den Lehrer-Modellen
        """
        responses = []
        for model_name in self.teacher_models[:num_responses]:
            response = self.query(model_name, prompt, temperature=temperature)
            responses.append(response)
        return responses
    
    def query_student_models(self, prompt: str, max_tokens: int = 512) -> Dict[str, str]:
        """
        Fragt alle Schüler-Modelle mit einer Benutzeranfrage
        
        Args:
            prompt: Die Benutzeranfrage
            max_tokens: Maximale Anzahl der Tokens für die Antwort
            
        Returns:
            Dict[str, str]: Antworten von den Schüler-Modellen
        """
        responses = {}
        for model_name in self.student_models:
            responses[model_name] = self.query(model_name, prompt, max_tokens=max_tokens)
        return responses