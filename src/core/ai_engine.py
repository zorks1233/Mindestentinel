"""
ai_engine.py
Hauptmodul für das KI-Gehirn des Mindestentinel-Systems.
Enthält die AIBrain-Klasse, die als zentrale Steuerung für alle KI-Funktionen dient.
"""

import logging
import os
import time
from typing import Optional, Dict, Any, List, Callable
from .rule_engine import RuleEngine
from .model_manager import ModelManager
from .plugin_manager import PluginManager
from .user_manager import UserManager
from .auth_manager import AuthManager
from .protection_module import ProtectionModule
from .self_learning import SelfLearningEngine
from .quantum_core import QuantumCore
from .simulation_engine import SimulationEngine
from .system_monitor import SystemMonitor
from .task_management import TaskManager
from .vision_audio import VisionAudioProcessor
from .cognitive_core import CognitiveCore

logger = logging.getLogger("mindestentinel.ai_engine")

class AIBrain:
    """
    Zentrale Klasse für das KI-Gehirn des Mindestentinel-Systems.
    Koordiniert alle Komponenten und stellt die Hauptlogik bereit.
    """
    
    def __init__(
        self,
        rule_engine: Optional[RuleEngine] = None,
        model_manager: Optional[ModelManager] = None,
        plugin_manager: Optional[PluginManager] = None,
        user_manager: Optional[UserManager] = None,
        auth_manager: Optional[AuthManager] = None,
        protection_module: Optional[ProtectionModule] = None,
        self_learning_engine: Optional[SelfLearningEngine] = None,
        quantum_core: Optional[QuantumCore] = None,
        simulation_engine: Optional[SimulationEngine] = None,
        system_monitor: Optional[SystemMonitor] = None,
        task_manager: Optional[TaskManager] = None,
        vision_audio: Optional[VisionAudioProcessor] = None,
        cognitive_core: Optional[CognitiveCore] = None,
        enable_autonomy: bool = False,
        rules_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialisiert das AIBrain.
        
        Args:
            rule_engine: Optional bereitgestellte RuleEngine-Instanz
            model_manager: Optional bereitgestellter ModelManager
            plugin_manager: Optional bereitgestellter PluginManager
            user_manager: Optional bereitgestellter UserManager
            auth_manager: Optional bereitgestellter AuthManager
            protection_module: Optional bereitgestelltes ProtectionModule
            self_learning_engine: Optional bereitgestellter SelfLearningEngine
            quantum_core: Optional bereitgestellter QuantumCore
            simulation_engine: Optional bereitgestellter SimulationEngine
            system_monitor: Optional bereitgestellter SystemMonitor
            task_manager: Optional bereitgestellter TaskManager
            vision_audio: Optional bereitgestellter VisionAudioProcessor
            cognitive_core: Optional bereitgestellter CognitiveCore
            enable_autonomy: Gibt an, ob autonome Funktionen aktiviert sind
            rules_path: Optionaler Pfad zu den Regeldateien
            config: Optionale Konfigurationsparameter
        """
        logger.info("Initialisiere AIBrain...")
        self.config = config or {}
        self.enable_autonomy = enable_autonomy
        
        # Initialisiere alle Komponenten
        self._initialize_components(
            rule_engine, 
            model_manager, 
            plugin_manager,
            user_manager,
            auth_manager,
            protection_module,
            self_learning_engine,
            quantum_core,
            simulation_engine,
            system_monitor,
            task_manager,
            vision_audio,
            cognitive_core,
            rules_path
        )
        
        # Initialisiere autonomen Modus, falls aktiviert
        if self.enable_autonomy:
            self.autonomous_loop = AutonomousLoop(
                brain=self,
                rule_engine=self.rule_engine,
                model_manager=self.model_manager,
                plugin_manager=self.plugin_manager,
                user_manager=self.user_manager,
                auth_manager=self.auth_manager,
                protection_module=self.protection_module,
                self_learning_engine=self.self_learning_engine,
                quantum_core=self.quantum_core,
                simulation_engine=self.simulation_engine,
                system_monitor=self.system_monitor,
                task_manager=self.task_manager,
                vision_audio=self.vision_audio,
                cognitive_core=self.cognitive_core
            )
            logger.info("Autonomer Modus aktiviert")
        else:
            self.autonomous_loop = None
            logger.info("Autonomer Modus deaktiviert")
        
        logger.info("AIBrain erfolgreich initialisiert")
    
    def _initialize_components(
        self,
        rule_engine: Optional[RuleEngine],
        model_manager: Optional[ModelManager],
        plugin_manager: Optional[PluginManager],
        user_manager: Optional[UserManager],
        auth_manager: Optional[AuthManager],
        protection_module: Optional[ProtectionModule],
        self_learning_engine: Optional[SelfLearningEngine],
        quantum_core: Optional[QuantumCore],
        simulation_engine: Optional[SimulationEngine],
        system_monitor: Optional[SystemMonitor],
        task_manager: Optional[TaskManager],
        vision_audio: Optional[VisionAudioProcessor],
        cognitive_core: Optional[CognitiveCore],
        rules_path: Optional[str]
    ) -> None:
        """Initialisiert alle Komponenten des AIBrain"""
        # RuleEngine initialisieren
        if rule_engine is None:
            try:
                self.rule_engine = RuleEngine(rules_path=rules_path)
                logger.debug("RuleEngine neu initialisiert")
            except Exception as e:
                logger.error(f"Fehler bei RuleEngine-Initialisierung: {str(e)}")
                raise
        else:
            self.rule_engine = rule_engine
        
        # ModelManager initialisieren
        if model_manager is None:
            try:
                self.model_manager = ModelManager()
                logger.debug("ModelManager neu initialisiert")
            except Exception as e:
                logger.error(f"Fehler bei ModelManager-Initialisierung: {str(e)}")
                raise
        else:
            self.model_manager = model_manager
        
        # PluginManager initialisieren
        if plugin_manager is None:
            try:
                self.plugin_manager = PluginManager()
                logger.debug("PluginManager neu initialisiert")
            except Exception as e:
                logger.error(f"Fehler bei PluginManager-Initialisierung: {str(e)}")
                raise
        else:
            self.plugin_manager = plugin_manager
        
        # UserManager initialisieren
        if user_manager is None:
            try:
                self.user_manager = UserManager()
                logger.debug("UserManager neu initialisiert")
            except Exception as e:
                logger.error(f"Fehler bei UserManager-Initialisierung: {str(e)}")
                raise
        else:
            self.user_manager = user_manager
        
        # AuthManager initialisieren
        if auth_manager is None:
            try:
                self.auth_manager = AuthManager()
                logger.debug("AuthManager neu initialisiert")
            except Exception as e:
                logger.error(f"Fehler bei AuthManager-Initialisierung: {str(e)}")
                raise
        else:
            self.auth_manager = auth_manager
        
        # ProtectionModule initialisieren
        if protection_module is None:
            try:
                self.protection_module = ProtectionModule(rule_engine=self.rule_engine)
                logger.debug("ProtectionModule neu initialisiert")
            except Exception as e:
                logger.error(f"Fehler bei ProtectionModule-Initialisierung: {str(e)}")
                raise
        else:
            self.protection_module = protection_module
        
        # SelfLearningEngine initialisieren
        if self_learning_engine is None:
            try:
                self.self_learning_engine = SelfLearningEngine(
                    rule_engine=self.rule_engine,
                    model_manager=self.model_manager
                )
                logger.debug("SelfLearningEngine neu initialisiert")
            except Exception as e:
                logger.error(f"Fehler bei SelfLearningEngine-Initialisierung: {str(e)}")
                raise
        else:
            self.self_learning_engine = self_learning_engine
        
        # QuantumCore initialisieren
        if quantum_core is None:
            try:
                self.quantum_core = QuantumCore()
                logger.debug("QuantumCore neu initialisiert")
            except Exception as e:
                logger.warning(f"QuantumCore konnte nicht initialisiert werden: {str(e)}")
                self.quantum_core = None
        else:
            self.quantum_core = quantum_core
        
        # SimulationEngine initialisieren
        if simulation_engine is None:
            try:
                self.simulation_engine = SimulationEngine()
                logger.debug("SimulationEngine neu initialisiert")
            except Exception as e:
                logger.warning(f"SimulationEngine konnte nicht initialisiert werden: {str(e)}")
                self.simulation_engine = None
        else:
            self.simulation_engine = simulation_engine
        
        # SystemMonitor initialisieren
        if system_monitor is None:
            try:
                self.system_monitor = SystemMonitor()
                logger.debug("SystemMonitor neu initialisiert")
            except Exception as e:
                logger.warning(f"SystemMonitor konnte nicht initialisiert werden: {str(e)}")
                self.system_monitor = None
        else:
            self.system_monitor = system_monitor
        
        # TaskManager initialisieren
        if task_manager is None:
            try:
                self.task_manager = TaskManager()
                logger.debug("TaskManager neu initialisiert")
            except Exception as e:
                logger.warning(f"TaskManager konnte nicht initialisiert werden: {str(e)}")
                self.task_manager = None
        else:
            self.task_manager = task_manager
        
        # VisionAudioProcessor initialisieren
        if vision_audio is None:
            try:
                self.vision_audio = VisionAudioProcessor()
                logger.debug("VisionAudioProcessor neu initialisiert")
            except Exception as e:
                logger.warning(f"VisionAudioProcessor konnte nicht initialisiert werden: {str(e)}")
                self.vision_audio = None
        else:
            self.vision_audio = vision_audio
        
        # CognitiveCore initialisieren
        if cognitive_core is None:
            try:
                self.cognitive_core = CognitiveCore(
                    rule_engine=self.rule_engine,
                    model_manager=self.model_manager
                )
                logger.debug("CognitiveCore neu initialisiert")
            except Exception as e:
                logger.warning(f"CognitiveCore konnte nicht initialisiert werden: {str(e)}")
                self.cognitive_core = None
        else:
            self.cognitive_core = cognitive_core
    
    def start(self) -> None:
        """Startet das AIBrain und alle zugehörigen Komponenten"""
        logger.info("Starte AIBrain...")
        
        # Starte alle Komponenten
        self._start_components()
        
        # Starte autonomen Modus, falls aktiviert
        if self.enable_autonomy and self.autonomous_loop:
            self.autonomous_loop.start()
            logger.info("Autonomer Modus gestartet")
    
    def _start_components(self) -> None:
        """Startet alle Komponenten des AIBrain"""
        # Starte SystemMonitor
        if self.system_monitor:
            self.system_monitor.start()
            logger.debug("SystemMonitor gestartet")
        
        # Starte TaskManager
        if self.task_manager:
            self.task_manager.start()
            logger.debug("TaskManager gestartet")
        
        # Starte QuantumCore
        if self.quantum_core:
            self.quantum_core.start()
            logger.debug("QuantumCore gestartet")
        
        # Starte SimulationEngine
        if self.simulation_engine:
            self.simulation_engine.start()
            logger.debug("SimulationEngine gestartet")
        
        # Starte VisionAudioProcessor
        if self.vision_audio:
            self.vision_audio.start()
            logger.debug("VisionAudioProcessor gestartet")
        
        # Starte ModelManager
        if self.model_manager:
            self.model_manager.start()
            logger.debug("ModelManager gestartet")
        
        # Starte SelfLearningEngine
        if self.self_learning_engine:
            self.self_learning_engine.start()
            logger.debug("SelfLearningEngine gestartet")
        
        # Starte CognitiveCore
        if self.cognitive_core:
            self.cognitive_core.start()
            logger.debug("CognitiveCore gestartet")
    
    def stop(self) -> None:
        """Stoppt das AIBrain und alle zugehörigen Komponenten"""
        logger.info("Stoppe AIBrain...")
        
        # Stoppe autonomen Modus
        if self.autonomous_loop:
            self.autonomous_loop.stop()
            logger.debug("Autonomer Modus gestoppt")
        
        # Stoppe alle Komponenten
        self._stop_components()
        
        logger.info("AIBrain erfolgreich gestoppt")
    
    def _stop_components(self) -> None:
        """Stoppt alle Komponenten des AIBrain"""
        # Stoppe CognitiveCore
        if self.cognitive_core:
            self.cognitive_core.stop()
            logger.debug("CognitiveCore gestoppt")
        
        # Stoppe SelfLearningEngine
        if self.self_learning_engine:
            self.self_learning_engine.stop()
            logger.debug("SelfLearningEngine gestoppt")
        
        # Stoppe ModelManager
        if self.model_manager:
            self.model_manager.stop()
            logger.debug("ModelManager gestoppt")
        
        # Stoppe VisionAudioProcessor
        if self.vision_audio:
            self.vision_audio.stop()
            logger.debug("VisionAudioProcessor gestoppt")
        
        # Stoppe SimulationEngine
        if self.simulation_engine:
            self.simulation_engine.stop()
            logger.debug("SimulationEngine gestoppt")
        
        # Stoppe QuantumCore
        if self.quantum_core:
            self.quantum_core.stop()
            logger.debug("QuantumCore gestoppt")
        
        # Stoppe TaskManager
        if self.task_manager:
            self.task_manager.stop()
            logger.debug("TaskManager gestoppt")
        
        # Stoppe SystemMonitor
        if self.system_monitor:
            self.system_monitor.stop()
            logger.debug("SystemMonitor gestoppt")
    
    def process_request(
        self, 
        request: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Verarbeitet eine Anfrage durch das AIBrain.
        
        Args:
            request: Die zu verarbeitende Anfrage
            context: Optionaler Kontext für die Verarbeitung
            
        Returns:
            Dict[str, Any]: Die Antwort auf die Anfrage
        """
        logger.debug(f"Verarbeite Anfrage: {request}")
        
        # Überprüfe Zugriffsberechtigung
        if not self._check_access(request, context):
            logger.warning("Zugriff verweigert")
            return {
                "status": "error",
                "code": 403,
                "message": "Zugriff verweigert"
            }
        
        # Verarbeite die Anfrage
        try:
            # Wende Schutzregeln an
            protected_request = self.protection_module.apply_protection_rules(request)
            
            # Verarbeite mit CognitiveCore
            response = self.cognitive_core.process(protected_request, context)
            
            # Wende Schutzregeln auf die Antwort an
            protected_response = self.protection_module.apply_protection_rules(response)
            
            logger.debug("Anfrage erfolgreich verarbeitet")
            return {
                "status": "success",
                "data": protected_response
            }
        except Exception as e:
            logger.error(f"Fehler bei der Anfrageverarbeitung: {str(e)}")
            return {
                "status": "error",
                "code": 500,
                "message": f"Interner Fehler: {str(e)}"
            }
    
    def _check_access(
        self, 
        request: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Überprüft, ob der Zugriff auf eine Ressource erlaubt ist.
        
        Args:
            request: Die Anfrage, für die der Zugriff geprüft werden soll
            context: Optionaler Kontext für die Zugriffsprüfung
            
        Returns:
            bool: True, wenn der Zugriff erlaubt ist, sonst False
        """
        # Extrahiere Benutzer aus dem Kontext
        user = context.get('user') if context else None
        
        # Extrahiere Ressource und Aktion aus der Anfrage
        resource = request.get('resource', 'unknown')
        action = request.get('action', 'unknown')
        
        # Überprüfe Zugriff über ProtectionModule
        return self.protection_module.check_access(user, resource, action)
    
    def get_status(self) -> Dict[str, Any]:
        """Gibt den aktuellen Status des AIBrain zurück"""
        return {
            "status": "running" if self.enable_autonomy and self.autonomous_loop and self.autonomous_loop.is_running() else "idle",
            "components": {
                "rule_engine": "active" if self.rule_engine else "inactive",
                "model_manager": "active" if self.model_manager else "inactive",
                "plugin_manager": "active" if self.plugin_manager else "inactive",
                "user_manager": "active" if self.user_manager else "inactive",
                "auth_manager": "active" if self.auth_manager else "inactive",
                "protection_module": "active" if self.protection_module else "inactive",
                "self_learning_engine": "active" if self.self_learning_engine else "inactive",
                "quantum_core": "active" if self.quantum_core else "inactive",
                "simulation_engine": "active" if self.simulation_engine else "inactive",
                "system_monitor": "active" if self.system_monitor else "inactive",
                "task_manager": "active" if self.task_manager else "inactive",
                "vision_audio": "active" if self.vision_audio else "inactive",
                "cognitive_core": "active" if self.cognitive_core else "inactive"
            },
            "autonomy_enabled": self.enable_autonomy,
            "timestamp": time.time()
        }