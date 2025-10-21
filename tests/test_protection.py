# test_protection.py
from core.protection_module import ProtectionModule

pm = ProtectionModule()  # erwartet, dass RuleEngine importierbar ist
try:
    pm.validate_user_input("ping external_api", {"user": "test"})
    print("Eingabe erlaubt")
except PermissionError as e:
    print("Eingabe verboten:", e)
except Exception as e:
    print("Fehler bei Prüfung:", e)
