# core package 
# src/core/__init__.py

# src/core/__init__.py
"""
Dies ist eine leere Datei, die benötigt wird, damit Python das Verzeichnis 'core' als Package erkennt.
Ohne diese Datei funktionieren die Importe nicht.
"""
"""
src.core package initializer for Mindestentinel.
Exports important classes for convenience imports such as:
  from src.core import AIBrain, RuleEngine, KnowledgeBase, SelfLearning, ...
"""

from .ai_engine import AIBrain  # main orchestrator
from .rule_engine import RuleEngine
from .protection_module import ProtectionModule
from .knowledge_base import KnowledgeBase
from .self_learning import SelfLearning
from .multi_model_orchestrator import MultiModelOrchestrator
from .system_monitor import SystemMonitor
from .task_management import TaskManagement
from .quantum_core import QuantumCore

__all__ = [
    "AIBrain",
    "RuleEngine",
    "ProtectionModule",
    "KnowledgeBase",
    "SelfLearning",
    "MultiModelOrchestrator",
    "SystemMonitor",
    "TaskManagement",
    "QuantumCore",
]
