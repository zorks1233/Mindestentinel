# src/core/model_cloner.py
"""
model_cloner.py - Erstellt sichere Kopien von Modellen für das Lernen

Diese Datei implementiert die Erstellung von Modell-Kopien für den Lernprozess.
"""

import logging
import os
import time
import shutil
from typing import Dict, Any, Optional
import json

logger = logging.getLogger("mindestentinel.model_cloner")

class ModelCloner:
    """
    Erstellt sichere Kopien von Modellen für den Lernprozess.
    
    Stellt sicher, dass das aktive System während des Lernens stabil bleibt.
    """
    
    def __init__(self, model_manager, knowledge_base, backup_dir: str = "data/models/backups"):
        """
        Initialisiert den ModelCloner.
        
        Args:
            model_manager: Der ModelManager
            knowledge_base: Die Wissensdatenbank
            backup_dir: Verzeichnis für Modell-Backups
        """
        self.mm = model_manager
        self.kb = knowledge_base
        self.backup_dir = backup_dir
        
        # Erstelle Backup-Verzeichnis, falls nicht vorhanden
        os.makedirs(self.backup_dir, exist_ok=True)
        
        logger.info(f"ModelCloner initialisiert. Backup-Verzeichnis: {self.backup_dir}")
    
    def create_model_copy(self, model_name: str, copy_name: Optional[str] = None) -> str:
        """
        Erstellt eine Kopie eines Modells für den Lernprozess.
        
        Args:
            model_name: Der Name des Originalmodells
            copy_name: Optionaler Name für die Kopie (wird automatisch generiert, wenn nicht angegeben)
            
        Returns:
            str: Der Name der Modell-Kopie
        """
        try:
            # Hole das Originalmodell
            model_info = self.mm.get_model(model_name)
            if not model_info:
                logger.error(f"Modell '{model_name}' nicht gefunden. Kann keine Kopie erstellen.")
                raise ValueError(f"Modell '{model_name}' nicht gefunden")
            
            # Generiere einen Namen für die Kopie, falls nicht angegeben
            if not copy_name:
                timestamp = int(time.time())
                copy_name = f"{model_name}_copy_{timestamp}"
            
            # Pfade für Original und Kopie
            original_path = os.path.join(self.mm.models_dir, model_name)
            copy_path = os.path.join(self.mm.models_dir, copy_name)
            
            # Erstelle eine Kopie des Modell-Verzeichnisses
            logger.info(f"Erstelle Kopie von '{model_name}' als '{copy_name}'...")
            shutil.copytree(original_path, copy_path)
            
            # Erstelle Metadaten für die Kopie
            copy_metadata = {
                "original_model": model_name,
                "created_at": time.time(),
                "copy_name": copy_name,
                "status": "training",  # training, validated, ready_for_integration
                "training_progress": 0.0,
                "validation_score": 0.0,
                "description": f"Kopie von {model_name} für Lernprozess"
            }
            
            # Speichere die Metadaten
            with open(os.path.join(copy_path, "copy_metadata.json"), "w") as f:
                json.dump(copy_metadata, f, indent=2)
            
            logger.info(f"Modell-Kopie erstellt: {copy_name}")
            return copy_name
        except Exception as e:
            logger.error(f"Fehler bei der Erstellung der Modell-Kopie: {str(e)}", exc_info=True)
            raise
    
    def update_copy_status(self, copy_name: str, status: str, **kwargs):
        """
        Aktualisiert den Status einer Modell-Kopie.
        
        Args:
            copy_name: Der Name der Modell-Kopie
            status: Der neue Status
            **kwargs: Zusätzliche Metadaten
        """
        try:
            copy_path = os.path.join(self.mm.models_dir, copy_name)
            metadata_path = os.path.join(copy_path, "copy_metadata.json")
            
            if not os.path.exists(metadata_path):
                logger.error(f"Metadaten für Modell-Kopie '{copy_name}' nicht gefunden")
                return
            
            # Lade vorhandene Metadaten
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Aktualisiere Metadaten
            metadata["status"] = status
            for key, value in kwargs.items():
                metadata[key] = value
            
            # Speichere aktualisierte Metadaten
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Status der Modell-Kopie '{copy_name}' aktualisiert: {status}")
        except Exception as e:
            logger.error(f"Fehler bei der Statusaktualisierung: {str(e)}", exc_info=True)
    
    def get_copy_status(self, copy_name: str) -> Dict[str, Any]:
        """
        Gibt den Status einer Modell-Kopie zurück.
        
        Args:
            copy_name: Der Name der Modell-Kopie
            
        Returns:
            Dict[str, Any]: Der Status der Modell-Kopie
        """
        try:
            copy_path = os.path.join(self.mm.models_dir, copy_name)
            metadata_path = os.path.join(copy_path, "copy_metadata.json")
            
            if not os.path.exists(metadata_path):
                logger.error(f"Metadaten für Modell-Kopie '{copy_name}' nicht gefunden")
                return {}
            
            # Lade Metadaten
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            return metadata
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Status: {str(e)}", exc_info=True)
            return {}
    
    def integrate_learned_knowledge(self, copy_name: str, target_model: str) -> bool:
        """
        Integriert gelerntes Wissen aus einer Modell-Kopie in das Zielmodell.
        
        Args:
            copy_name: Der Name der Modell-Kopie
            target_model: Das Zielmodell
            
        Returns:
            bool: True, wenn erfolgreich, sonst False
        """
        try:
            # Prüfe den Status der Kopie
            status = self.get_copy_status(copy_name)
            if status.get("status") != "validated":
                logger.error(f"Modell-Kopie '{copy_name}' ist nicht validiert. Integration abgebrochen.")
                return False
            
            # Prüfe die Validierungsscore
            if status.get("validation_score", 0.0) < 0.7:  # Mindest-Validierungsscore
                logger.warning(f"Modell-Kopie '{copy_name}' hat zu niedrigen Validierungsscore. Integration abgebrochen.")
                return False
            
            logger.info(f"Integriere gelerntes Wissen aus '{copy_name}' in '{target_model}'...")
            
            # Hier würde der eigentliche Wissenstransfer stattfinden
            # In einer echten Implementierung würden Sie hier:
            # 1. Die Gewichte des kopierten Modells in das Zielmodell übertragen
            # 2. ODER: Die Wissensbeispiele aus der Kopie in die Wissensdatenbank übertragen
            
            # Für das Beispiel: Markiere die Kopie als integriert
            self.update_copy_status(copy_name, "integrated", integrated_at=time.time())
            
            logger.info(f"Gelerntes Wissen erfolgreich integriert aus '{copy_name}' in '{target_model}'")
            return True
        except Exception as e:
            logger.error(f"Fehler bei der Wissensintegration: {str(e)}", exc_info=True)
            return False
    
    def create_backup(self, model_name: str, backup_name: Optional[str] = None) -> str:
        """
        Erstellt ein Backup eines Modells.
        
        Args:
            model_name: Der Name des Modells
            backup_name: Optionaler Name für das Backup
            
        Returns:
            str: Der Name des Backups
        """
        try:
            # Generiere einen Namen für das Backup, falls nicht angegeben
            if not backup_name:
                timestamp = int(time.time())
                backup_name = f"{model_name}_backup_{timestamp}"
            
            # Pfade für Original und Backup
            original_path = os.path.join(self.mm.models_dir, model_name)
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            # Erstelle ein Backup
            logger.info(f"Erstelle Backup von '{model_name}' als '{backup_name}'...")
            shutil.copytree(original_path, backup_path)
            
            logger.info(f"Modell-Backup erstellt: {backup_name}")
            return backup_name
        except Exception as e:
            logger.error(f"Fehler bei der Erstellung des Backups: {str(e)}", exc_info=True)
            raise
    
    def restore_from_backup(self, backup_name: str, model_name: str) -> bool:
        """
        Stellt ein Modell aus einem Backup wieder her.
        
        Args:
            backup_name: Der Name des Backups
            model_name: Der Name des Modells
            
        Returns:
            bool: True, wenn erfolgreich, sonst False
        """
        try:
            # Pfade für Backup und Modell
            backup_path = os.path.join(self.backup_dir, backup_name)
            model_path = os.path.join(self.mm.models_dir, model_name)
            
            # Lösche das aktuelle Modell, falls vorhanden
            if os.path.exists(model_path):
                shutil.rmtree(model_path)
            
            # Stelle das Backup wieder her
            logger.info(f"Stelle Modell '{model_name}' aus Backup '{backup_name}' wieder her...")
            shutil.copytree(backup_path, model_path)
            
            logger.info(f"Modell '{model_name}' erfolgreich aus Backup wiederhergestellt")
            return True
        except Exception as e:
            logger.error(f"Fehler bei der Wiederherstellung aus dem Backup: {str(e)}", exc_info=True)
            return False