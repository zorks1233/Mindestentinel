# tests/test_smoke_core.py
import unittest
from src.core.ai_engine import AIBrain
from src.core.model_manager import ModelManager
from src.modules.plugin_manager import PluginManager

class SmokeTestCore(unittest.TestCase):
    def test_components_init(self):
        brain = AIBrain("config/rules.yaml")
        mm = ModelManager()
        pm = PluginManager()
        brain.inject_model_manager(mm)
        self.assertIsNotNone(brain.rule_engine)
        self.assertIsNotNone(brain.knowledge_base)
        self.assertIsNotNone(mm)
        self.assertIsNotNone(pm)

if __name__ == "__main__":
    unittest.main()
