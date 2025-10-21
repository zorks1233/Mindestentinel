# protection_module 
# src/core/protection_module.py
"""
ProtectionModule - Validiert Eingaben und Systemaktionen gegen RuleEngine.
- Hebt PermissionError bei Verstößen.
"""

from __future__ import annotations
from typing import Any

from src.core.rule_engine import RuleEngine

class ProtectionModule:
    def __init__(self, rule_engine: RuleEngine = None):
    # Flexible initialization: accept a RuleEngine instance, a path, a class, or None.
    # If None, attempt to create a default RuleEngine.
    if rule_engine is None:
        try:
            rule_engine = RuleEngine()
        except Exception:
            rule_engine = None
    else:
        # If a string path is provided, try to instantiate RuleEngine with it
        if isinstance(rule_engine, str):
            try:
                rule_engine = RuleEngine(rules_path=rule_engine)
            except Exception:
                pass
        # If a class is provided, try to instantiate it
        elif isinstance(rule_engine, type):
            try:
                rule_engine = rule_engine()
            except Exception:
                pass
    if not isinstance(rule_engine, RuleEngine):
        raise TypeError("rule_engine muss RuleEngine-Instanz sein")
    self.rule_engine = rule_engine

        if not isinstance(rule_engine, RuleEngine):
            raise TypeError("rule_engine muss RuleEngine-Instanz sein")
        self.rule_engine = rule_engine

    def validate_user_input(self, user_input: str) -> bool:
        if not isinstance(user_input, str):
            raise TypeError("user_input muss string sein")
        if not self.rule_engine.is_action_allowed(user_input):
            raise PermissionError("Eingabe verletzt die Regeln und wurde verworfen.")
        return True

    def validate_system_action(self, action_desc: str) -> bool:
        if not self.rule_engine.is_action_allowed(action_desc):
            raise PermissionError("Systemaktion verletzt Regeln.")
        return True
