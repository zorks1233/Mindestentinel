# core/protection_module.py
"""
ProtectionModule

Verantwortlich für die Prüfung von Benutzer-Eingaben und System-Aktionen gegen die RuleEngine.
Diese Implementation versucht, kompatibel mit verschiedenen RuleEngine-APIs zu sein,
indem sie die verfügbaren Methoden zur Laufzeit prüft.

Wesentliche Funktionen:
- Flexible Initialisierung (Instanz, Pfad-String, Klasse oder None)
- validate_user_input(user_input, context) -> bool (True erlaubt, sonst raised PermissionError)
- validate_system_action(action_desc, context) -> bool
- enforce_action(action_desc, context) -> returns rule evaluation / raises

Fehlerausgabe ist bewusst deutlich (TypeError / PermissionError).
"""

from __future__ import annotations
from typing import Any, Optional, Dict
import logging

log = logging.getLogger("mindestentinel.protection_module")

# Versuche, die RuleEngine aus dem erwarteten Modulpfad zu importieren.
try:
    # In deiner Codebasis könnte RuleEngine in src.core.rule_engine oder core.rule_engine liegen.
    try:
        from src.core.rule_engine import RuleEngine  # bevorzugte (package) Variante
    except Exception:
        from core.rule_engine import RuleEngine  # fallback
except Exception:
    RuleEngine = None  # wird später geprüft

class ProtectionModule:
    def __init__(self, rule_engine: Optional[Any] = None, verify_signature: bool = True):
        """
        rule_engine:
            - None: es wird versucht, RuleEngine() zu instanziieren (sofern importierbar)
            - str: Pfad/Verzeichnis zu Regeln -> RuleEngine(rules_path=...)
            - RuleEngine-Instanz: wird direkt verwendet
            - Klasse: wird instanziiert (Klassenobjekt wird aufgerufen)
        verify_signature:
            - Wenn True und rule_engine ein passenden Methode besitzt, wird
              rule/signature verification ausgeführt (falls vorhanden).
        """
        # Resolve RuleEngine import availability
        if RuleEngine is None:
            raise ImportError("RuleEngine konnte nicht importiert werden. Prüfe core/rule_engine.py")

        resolved = None

        # 1) None -> default
        if rule_engine is None:
            try:
                resolved = RuleEngine()
                log.debug("ProtectionModule: RuleEngine mit Default initialisiert.")
            except Exception as e:
                log.error("ProtectionModule: Konnte RuleEngine nicht mit Default erzeugen: %s", e, exc_info=True)
                resolved = None

        # 2) string -> treat as path
        elif isinstance(rule_engine, str):
            try:
                resolved = RuleEngine(rules_path=rule_engine)
                log.debug("ProtectionModule: RuleEngine mit rules_path=%s initialisiert.", rule_engine)
            except Exception as e:
                log.error("ProtectionModule: Fehler beim Erzeugen von RuleEngine aus Pfad '%s': %s", rule_engine, e, exc_info=True)
                resolved = None

        # 3) already instance
        elif isinstance(rule_engine, RuleEngine):
            resolved = rule_engine
            log.debug("ProtectionModule: vorhandene RuleEngine-Instanz verwendet.")

        # 4) class/type -> instantiate
        elif isinstance(rule_engine, type):
            try:
                resolved = rule_engine()
                log.debug("ProtectionModule: RuleEngine-Klasse instanziiert.")
            except Exception as e:
                log.error("ProtectionModule: Konnte RuleEngine-Klasse nicht instanziieren: %s", e, exc_info=True)
                resolved = None

        else:
            log.error("ProtectionModule: Ungültiger rule_engine-Parameter: %r", type(rule_engine))
            resolved = None

        # Letzte Absicherung: resolved muss RuleEngine-Instanz sein
        if not isinstance(resolved, RuleEngine):
            raise TypeError("rule_engine muss eine RuleEngine-Instanz sein oder ein gültiger Konstruktor/Pfad")

        # Optional: verify signature / consistency (falls Methode vorhanden)
        try:
            if verify_signature:
                # mögliche Methoden prüfen: verify_signature, validate_signatures, check_integrity
                if hasattr(resolved, "verify_signature"):
                    resolved.verify_signature()
                    log.debug("ProtectionModule: verify_signature() aufgerufen.")
                elif hasattr(resolved, "validate_signatures"):
                    resolved.validate_signatures()
                    log.debug("ProtectionModule: validate_signatures() aufgerufen.")
                # falls keine vorhanden, still accept
        except Exception as e:
            # Signaturprüfung soll nicht stillschweigend brechen, aber wir loggen das
            log.warning("ProtectionModule: Regel-Signaturprüfung fehlerhaft: %s", e, exc_info=True)

        self.rule_engine: RuleEngine = resolved

    # interne helper: versucht Regel-API kompatibel abzufragen
    def _is_allowed(self, subject: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Versucht eine existierende API aufzurufen, um zu prüfen, ob 'subject' erlaubt ist.
        Unterstützt mehrere Signaturen:
        - rule_engine.is_action_allowed(subject)
        - rule_engine.evaluate(subject, context) -> dict/obj mit 'allowed' bool
        - rule_engine.match_rules(subject) -> returns list (empty -> allowed)
        """
        context = context or {}

        # 1) is_action_allowed(subject)
        if hasattr(self.rule_engine, "is_action_allowed"):
            try:
                result = self.rule_engine.is_action_allowed(subject)
                # Falls bool -> return
                if isinstance(result, bool):
                    return result
                # Falls dict mit 'allowed'
                if isinstance(result, dict) and "allowed" in result:
                    return bool(result["allowed"])
            except Exception as e:
                log.exception("ProtectionModule: Fehler beim Aufruf is_action_allowed: %s", e)

        # 2) evaluate(subject, context)
        if hasattr(self.rule_engine, "evaluate"):
            try:
                res = self.rule_engine.evaluate(subject, context)
                # akzeptiere dict/obj mit 'allowed' oder True/False
                if isinstance(res, bool):
                    return res
                if isinstance(res, dict) and "allowed" in res:
                    return bool(res["allowed"])
            except Exception as e:
                log.exception("ProtectionModule: Fehler beim Aufruf evaluate: %s", e)

        # 3) match_rules(subject) -> list of matches -> deny if any matches
        if hasattr(self.rule_engine, "match_rules"):
            try:
                matches = self.rule_engine.match_rules(subject)
                # falls None oder [] -> erlaubt
                if matches:
                    return False
                return True
            except Exception as e:
                log.exception("ProtectionModule: Fehler beim Aufruf match_rules: %s", e)

        # 4) fallback: rule_engine.has_rule_for / allows / check
        for candidate in ("allows", "allow", "check", "is_allowed"):
            if hasattr(self.rule_engine, candidate):
                try:
                    fn = getattr(self.rule_engine, candidate)
                    result = fn(subject, context) if callable(fn) else bool(fn)
                    if isinstance(result, bool):
                        return result
                except Exception:
                    pass

        # Wenn wir nichts sicher prüfen können, lehnen wir nicht stillschweigend ab.
        # Stattdessen erlauben wir nicht blind, sondern werfen eine Ausnahme damit der Aufrufer entscheidet.
        log.error("ProtectionModule: Keine bekannte Prüf-Methode in RuleEngine gefunden; weise auf Sicherheitsrisiko hin.")
        raise RuntimeError("RuleEngine-API nicht kompatibel mit ProtectionModule (keine Prüf-Methode gefunden)")

    def validate_user_input(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Prüft eine Benutzereingabe. Erlaubt -> True zurück, sonst PermissionError.
        """
        if not isinstance(user_input, str):
            raise TypeError("user_input muss eine string sein")
        ok = self._is_allowed(user_input, context)
        if not ok:
            raise PermissionError("Eingabe verletzt Regeln und wurde verworfen.")
        return True

    def validate_system_action(self, action_desc: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Prüft eine System-Aktion (z. B. 'update_config', 'execute_command ...').
        """
        if not isinstance(action_desc, str):
            raise TypeError("action_desc muss string sein")
        ok = self._is_allowed(action_desc, context)
        if not ok:
            raise PermissionError("Systemaktion verletzt Regeln.")
        return True

    def enforce_action(self, action_desc: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Führt eine abschließende Prüfung durch und gibt das Evaluations-Resultat zurück.
        Nützlich, wenn RuleEngine komplexe Auswertungen (z.B. reasons, matched_rules) zurückliefert.
        """
        # Versuche die evaluate-Methode oder is_action_allowed je nach Verfügbarkeit
        context = context or {}
        if hasattr(self.rule_engine, "evaluate"):
            try:
                return self.rule_engine.evaluate(action_desc, context)
            except Exception as e:
                log.exception("ProtectionModule: Fehler beim Aufruf evaluate: %s", e)
                raise
        # fallback: is_action_allowed
        if hasattr(self.rule_engine, "is_action_allowed"):
            try:
                allowed = self.rule_engine.is_action_allowed(action_desc)
                return {"allowed": bool(allowed)}
            except Exception as e:
                log.exception("ProtectionModule: Fehler beim Aufruf is_action_allowed: %s", e)
                raise
        # fallback: _is_allowed (gibt bool zurück oder wirft)
        allowed = self._is_allowed(action_desc, context)
        return {"allowed": bool(allowed)}
