# src/plugins/example_plugin.py
"""
example_plugin.py - Beispiel-Plugin für Mindestentinel

Dieses Plugin ist ein Beispiel für die Plugin-Struktur.
"""

import logging

logger = logging.getLogger("mindestentinel.plugins.example")


class Plugin:
    """Ein Beispiel-Plugin"""

    def __init__(self):
        """Initialisiert das Plugin"""
        logger.info("ExamplePlugin initialisiert")

    def initialize(self, **components):
        """Initialisiert das Plugin mit Systemkomponenten

        Args:
            **components: Alle benötigten Systemkomponenten
        """
        logger.info("ExamplePlugin initialisiert mit Systemkomponenten")

        # Speichere benötigte Komponenten
        self.brain = components.get('brain')
        self.model_manager = components.get('model_manager')
        self.rule_engine = components.get('rule_engine')

    def process(self, data, context=None):
        """Verarbeitet Daten

        Args:
            data: Die zu verarbeitenden Daten
            context: Optionaler Kontext

        Returns:
            Die verarbeiteten Daten
        """
        if context is None:
            context = {}

        logger.debug("ExamplePlugin verarbeitet Daten")

        # Beispielverarbeitung
        if isinstance(data, str):
            return data + " [verarbeitet durch ExamplePlugin]"

        return data

    def get_metadata(self):
        """Holt Metadaten über das Plugin"""
        return {
            'name': 'ExamplePlugin',
            'version': '1.0',
            'description': 'Ein Beispiel-Plugin für Mindestentinel'
        }
