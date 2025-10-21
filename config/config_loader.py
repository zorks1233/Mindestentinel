"""
config_loader.py
Lädt Konfigurationsdateien aus verschiedenen Quellen (YAML, ENV, CLI-Parameter).
Stellt eine zentrale Schnittstelle für alle Konfigurationseinstellungen bereit.
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional

class ConfigLoader:
    """
    Zentrale Klasse zum Laden und Verwalten von Konfigurationen aus verschiedenen Quellen.
    Unterstützt mehrere Konfigurationslayer: Standardwerte < YAML-Dateien < ENV-Variablen < CLI-Parameter
    """
    
    _instance = None
    _logger = None
    
    def __new__(cls, *args, **kwargs):
        """Singleton-Pattern für globale Konfigurationszugriffe"""
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
            cls._logger = logging.getLogger("mindestentinel.config")
            cls._logger.info("ConfigLoader Singleton instanziiert")
        return cls._instance
    
    @classmethod
    def load_config(cls, config_name: str = 'default') -> Dict[str, Any]:
        """
        Lädt eine Konfiguration basierend auf dem Namen.
        
        Args:
            config_name: Name der Konfiguration (z.B. 'default', 'production', 'rules')
            
        Returns:
            dict: Geladene Konfigurationswerte
        """
        logger = logging.getLogger("mindestentinel.config")
        logger.info(f"Lade Konfiguration: {config_name}")
        
        # 1. Standardkonfiguration laden
        base_config = cls._load_yaml('default.yaml')
        
        # 2. Spezifische Konfiguration mergen (falls vorhanden)
        if config_name != 'default':
            specific_config = cls._load_yaml(f'{config_name}.yaml')
            cls._deep_merge(base_config, specific_config)
        
        # 3. ENV-Variablen anwenden
        cls._apply_env_overrides(base_config)
        
        return base_config
    
    @staticmethod
    def _load_yaml(filename: str) -> Dict[str, Any]:
        """Lädt eine YAML-Konfigurationsdatei"""
        config_path = os.path.join(os.path.dirname(__file__), filename)
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return yaml.safe_load(f) or {}
            else:
                logging.getLogger("mindestentinel.config").warning(
                    f"Konfigurationsdatei nicht gefunden: {config_path}. Verwende leere Konfiguration."
                )
                return {}
        except Exception as e:
            logging.getLogger("mindestentinel.config").error(
                f"Fehler beim Laden von {config_path}: {str(e)}"
            )
            return {}
    
    @staticmethod
    def _deep_merge(base: Dict, update: Dict) -> None:
        """Führt zwei Konfigurationsdictionaries rekursiv zusammen"""
        for key, value in update.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                ConfigLoader._deep_merge(base[key], value)
            else:
                base[key] = value
    
    @staticmethod
    def _apply_env_overrides(config: Dict) -> None:
        """Überschreibt Konfigurationswerte mit Umgebungsvariablen"""
        for key, value in os.environ.items():
            if key.startswith('MINDESENTINEL_'):
                config_key = key.replace('MINDESENTINEL_', '').lower()
                ConfigLoader._set_nested_value(config, config_key, value)
    
    @staticmethod
    def _set_nested_value(config: Dict, path: str, value: Any) -> None:
        """Setzt einen Wert in einer verschachtelten Konfigurationsstruktur"""
        keys = path.split('_')
        current = config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value
    
    @staticmethod
    def get_rules() -> Dict[str, Any]:
        """Lädt speziell die Regeln aus rules.yaml"""
        rules_path = os.path.join(os.path.dirname(__file__), 'rules.yaml')
        try:
            if os.path.exists(rules_path):
                with open(rules_path, 'r') as f:
                    rules = yaml.safe_load(f)
                    logging.getLogger("mindestentinel.config").info(
                        f"Geladene Regeln: {len(rules.get('rules', []))} Regeln gefunden"
                    )
                    return rules
            else:
                logging.getLogger("mindestentinel.config").warning(
                    "rules.yaml nicht gefunden. System startet ohne Regeln."
                )
                return {"rules": []}
        except Exception as e:
            logging.getLogger("mindestentinel.config").error(
                f"Fehler beim Laden von rules.yaml: {str(e)}"
            )
            return {"rules": []}