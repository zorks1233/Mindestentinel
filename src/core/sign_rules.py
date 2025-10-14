import os
import sys
import logging
from core.rule_engine import RuleEngine

# Setze den Projekt-Root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Konfiguriere Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("mindestentinel.sign_rules")


def sign_rules():
    """Signiert die Regeln und erstellt die notwendigen Signaturdateien"""
    try:
        # Pfad zur Regelkonfiguration
        rules_path = os.path.join("config", "rules.yaml")

        # Initialisiere RuleEngine zum Signieren
        rule_engine = RuleEngine(rules_path)

        # Signiere die Regeln
        rule_engine.sign_rules()

        logger.info("Regeln erfolgreich signiert!")
        logger.info("Signaturdateien wurden erstellt:")
        logger.info(f"- {os.path.join('config', 'rules.sig')}")
        logger.info(f"- {os.path.join('config', 'rules_key.key')}")

        return 0
    except Exception as e:
        logger.error(f"Fehler beim Signieren der Regeln: {str(e)}")
        return 1


if __name__ == "__main__":
    sign_rules()
