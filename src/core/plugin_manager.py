"""
plugin_manager.py
Verwaltet das Laden, Registrieren und Verwalten von Plugins in Mindestentinel
"""

import os
import sys
import logging
import importlib
import inspect
from typing import Dict, Any, List, Optional, Callable, Type

# Robuste Projekt-Root-Erkennung
def get_project_root() -> str:
    """
    Findet das Projekt-Root-Verzeichnis unabhängig vom aktuellen Arbeitsverzeichnis
    
    Returns:
        str: Absolute Pfad zum Projekt-Root
    """
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)
    
    # Versuche 1: Von src/core aus
    project_root = os.path.dirname(os.path.dirname(current_dir))
    if os.path.exists(os.path.join(project_root, "core")):
        return project_root
    
    # Versuche 2: Von core aus
    project_root = os.path.dirname(current_dir)
    if os.path.exists(os.path.join(project_root, "src", "core")):
        return project_root
    
    # Versuche 3: Aktuelles Verzeichnis ist Projekt-Root
    project_root = current_dir
    if os.path.exists(os.path.join(project_root, "src", "core")) or os.path.exists(os.path.join(project_root, "core")):
        return project_root
    
    # Versuche 4: Projekt-Root ist zwei Ebenen höher
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    if os.path.exists(os.path.join(project_root, "core")):
        return project_root
    
    # Fallback: Aktuelles Verzeichnis
    return os.getcwd()

# Setze PYTHONPATH korrekt
PROJECT_ROOT = get_project_root()
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Initialisiere Logging
logger = logging.getLogger("mindestentinel.plugin_manager")
logger.setLevel(logging.INFO)

class Plugin:
    """
    Basisklasse für alle Plugins
    """
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.enabled = True
        self.version = "1.0"
        self.author = "Unknown"
        self.dependencies = []
        
    def initialize(self, *args, **kwargs) -> None:
        """Wird beim Initialisieren des Plugins aufgerufen"""
        logger.info(f"Plugin initialisiert: {self.name}")
    
    def shutdown(self) -> None:
        """Wird beim Herunterfahren des Plugins aufgerufen"""
        logger.info(f"Plugin heruntergefahren: {self.name}")

class PluginManager:
    """
    Verwaltet das Laden, Registrieren und Verwalten von Plugins
    """
    
    def __init__(self, plugin_dir: Optional[str] = None):
        """
        Initialisiert den PluginManager
        
        Args:
            plugin_dir: Optionales Verzeichnis für Plugins (überschreibt Standardverzeichnis)
        """
        self.plugins = {}
        self.plugin_classes = {}
        self.plugin_instances = {}
        self.plugin_dir = plugin_dir
        
        # Setze Standard-Plugin-Verzeichnis, falls nicht angegeben
        if not self.plugin_dir:
            # Versuche 1: plugins-Verzeichnis im Projekt-Root
            root_plugin_dir = os.path.join(PROJECT_ROOT, "plugins")
            if os.path.exists(root_plugin_dir):
                self.plugin_dir = root_plugin_dir
                logger.debug(f"Verwende Root-Plugin-Verzeichnis: {self.plugin_dir}")
            else:
                # Versuche 2: plugins-Verzeichnis im src-Verzeichnis
                src_plugin_dir = os.path.join(PROJECT_ROOT, "src", "plugins")
                if os.path.exists(src_plugin_dir):
                    self.plugin_dir = src_plugin_dir
                    logger.debug(f"Verwende src-Plugin-Verzeichnis: {self.plugin_dir}")
                else:
                    # Erstelle ein neues Plugin-Verzeichnis
                    self.plugin_dir = os.path.join(PROJECT_ROOT, "plugins")
                    os.makedirs(self.plugin_dir, exist_ok=True)
                    logger.info(f"Erstelle neues Plugin-Verzeichnis: {self.plugin_dir}")
        
        logger.info(f"PluginManager initialisiert mit Plugin-Verzeichnis: {self.plugin_dir}")
    
    def load_plugins(self) -> Dict[str, Any]:
        """
        Lädt alle verfügbaren Plugins aus dem Plugin-Verzeichnis
        
        Returns:
            dict: Status der Plugin-Ladevorgänge
        """
        logger.info(f"Lade Plugins aus: {self.plugin_dir}")
        results = {}
        
        # Prüfe, ob das Plugin-Verzeichnis existiert
        if not os.path.exists(self.plugin_dir):
            logger.error(f"Plugin-Verzeichnis nicht gefunden: {self.plugin_dir}")
            return {"status": "error", "message": f"Plugin-Verzeichnis nicht gefunden: {self.plugin_dir}"}
        
        # Finde alle Python-Dateien im Plugin-Verzeichnis
        plugin_files = [
            f for f in os.listdir(self.plugin_dir)
            if f.endswith('.py') and f != '__init__.py'
        ]
        
        logger.debug(f"Gefundene Plugin-Dateien: {plugin_files}")
        
        # Lade jedes Plugin
        for plugin_file in plugin_files:
            plugin_name = os.path.splitext(plugin_file)[0]
            try:
                # Lade das Plugin-Modul
                plugin_module = self._load_plugin_module(plugin_name)
                
                # Registriere das Plugin
                self._register_plugin(plugin_name, plugin_module)
                
                # Erstelle eine Instanz des Plugins
                self._instantiate_plugin(plugin_name)
                
                results[plugin_name] = {"status": "success", "message": "Plugin geladen"}
                logger.info(f"Plugin erfolgreich geladen: {plugin_name}")
                
            except Exception as e:
                results[plugin_name] = {"status": "error", "message": str(e)}
                logger.error(f"Fehler beim Laden des Plugins '{plugin_name}': {str(e)}")
        
        # Initialisiere alle geladenen Plugins
        self._initialize_plugins()
        
        logger.info(f"{len(self.plugins)} Plugins geladen: ({len(self.plugin_instances)})")
        return {"status": "success", "plugins_loaded": len(self.plugins)}
    
    def _load_plugin_module(self, plugin_name: str) -> Any:
        """
        Lädt ein Plugin-Modul
        
        Args:
            plugin_name: Name des Plugins
            
        Returns:
            Das geladene Modul
            
        Raises:
            ImportError: Wenn das Modul nicht geladen werden kann
        """
        # Versuche 1: Direkter Import aus dem Plugin-Verzeichnis
        try:
            # Erstelle einen relativen Pfad zum Plugin-Verzeichnis
            relative_path = os.path.relpath(self.plugin_dir, PROJECT_ROOT).replace(os.sep, '.')
            if relative_path.startswith('.'):
                relative_path = relative_path[1:]
            
            module_name = f"{relative_path}.{plugin_name}"
            plugin_module = importlib.import_module(module_name)
            logger.debug(f"Plugin-Modul geladen (relativer Pfad): {module_name}")
            return plugin_module
        except ImportError as e1:
            pass
        
        # Versuche 2: Direkter Import aus dem Root
        try:
            module_name = f"plugins.{plugin_name}"
            plugin_module = importlib.import_module(module_name)
            logger.debug(f"Plugin-Modul geladen (Root): {module_name}")
            return plugin_module
        except ImportError as e2:
            pass
        
        # Versuche 3: Direkter Import aus src/plugins
        try:
            module_name = f"src.plugins.{plugin_name}"
            plugin_module = importlib.import_module(module_name)
            logger.debug(f"Plugin-Modul geladen (src): {module_name}")
            return plugin_module
        except ImportError as e3:
            pass
        
        # Versuche 4: Dynamischer Import
        try:
            plugin_path = os.path.join(self.plugin_dir, f"{plugin_name}.py")
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
            plugin_module = importlib.util.module_from_spec(spec)
            sys.modules[plugin_name] = plugin_module
            spec.loader.exec_module(plugin_module)
            logger.debug(f"Plugin-Modul dynamisch geladen: {plugin_path}")
            return plugin_module
        except Exception as e4:
            logger.error(f"Alle Importversuche für Plugin '{plugin_name}' fehlgeschlagen: {str(e1)}, {str(e2)}, {str(e3)}, {str(e4)}")
            raise
    
    def _register_plugin(self, plugin_name: str, plugin_module: Any) -> None:
        """
        Registriert ein Plugin
        
        Args:
            plugin_name: Name des Plugins
            plugin_module: Das geladene Modul
        """
        # Finde alle Plugin-Klassen im Modul
        for name, obj in inspect.getmembers(plugin_module):
            if inspect.isclass(obj) and issubclass(obj, Plugin) and obj != Plugin:
                logger.debug(f"Plugin-Klasse gefunden: {name}")
                self.plugin_classes[plugin_name] = obj
                self.plugins[plugin_name] = {
                    "class": obj,
                    "module": plugin_module,
                    "name": plugin_name,
                    "description": getattr(obj, "description", "Keine Beschreibung"),
                    "version": getattr(obj, "version", "1.0"),
                    "author": getattr(obj, "author", "Unbekannt")
                }
                return
        
        # Wenn keine Plugin-Klasse gefunden wurde, versuche es mit einer Standardklasse
        if hasattr(plugin_module, "PluginClass"):
            self.plugin_classes[plugin_name] = plugin_module.PluginClass
            self.plugins[plugin_name] = {
                "class": plugin_module.PluginClass,
                "module": plugin_module,
                "name": plugin_name,
                "description": getattr(plugin_module.PluginClass, "description", "Keine Beschreibung"),
                "version": getattr(plugin_module.PluginClass, "version", "1.0"),
                "author": getattr(plugin_module.PluginClass, "author", "Unbekannt")
            }
            logger.warning(f"Verwende benannte Plugin-Klasse für: {plugin_name}")
            return
        
        # Wenn immer noch keine Klasse gefunden wurde, erstelle eine Dummy-Implementierung
        class DynamicPlugin(Plugin):
            def __init__(self):
                super().__init__(plugin_name, "Dynamisch erstelltes Plugin")
        
        self.plugin_classes[plugin_name] = DynamicPlugin
        self.plugins[plugin_name] = {
            "class": DynamicPlugin,
            "module": plugin_module,
            "name": plugin_name,
            "description": "Dynamisch erstelltes Plugin",
            "version": "1.0",
            "author": "System"
        }
        logger.warning(f"Keine Plugin-Klasse gefunden für: {plugin_name}. Erstelle dynamische Klasse.")
    
    def _instantiate_plugin(self, plugin_name: str) -> None:
        """
        Erstellt eine Instanz eines Plugins
        
        Args:
            plugin_name: Name des Plugins
        """
        plugin_class = self.plugin_classes.get(plugin_name)
        if not plugin_class:
            logger.error(f"Keine Plugin-Klasse für '{plugin_name}' registriert")
            return
        
        try:
            # Erstelle eine Instanz des Plugins
            plugin_instance = plugin_class()
            self.plugin_instances[plugin_name] = plugin_instance
            logger.debug(f"Plugin-Instanz erstellt: {plugin_name}")
        except Exception as e:
            logger.error(f"Fehler beim Instanziieren des Plugins '{plugin_name}': {str(e)}")
    
    def _initialize_plugins(self) -> None:
        """
        Initialisiert alle geladenen Plugins
        """
        for plugin_name, plugin_instance in self.plugin_instances.items():
            try:
                plugin_instance.initialize()
                logger.info(f"Plugin initialisiert: {plugin_name}")
            except Exception as e:
                logger.error(f"Fehler bei der Initialisierung des Plugins '{plugin_name}': {str(e)}")
    
    def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """
        Gibt eine Plugin-Instanz zurück
        
        Args:
            plugin_name: Name des Plugins
            
        Returns:
            Optional[Plugin]: Die Plugin-Instanz oder None, wenn nicht gefunden
        """
        return self.plugin_instances.get(plugin_name)
    
    def get_plugin_info(self, plugin_name: str) -> Dict[str, Any]:
        """
        Gibt Informationen über ein Plugin zurück
        
        Args:
            plugin_name: Name des Plugins
            
        Returns:
            dict: Informationen über das Plugin
        """
        if plugin_name not in self.plugins:
            return {
                "status": "error",
                "message": f"Plugin '{plugin_name}' nicht gefunden"
            }
        
        plugin_info = self.plugins[plugin_name].copy()
        plugin_info["status"] = "loaded" if plugin_name in self.plugin_instances else "available"
        plugin_info["is_loaded"] = plugin_name in self.plugin_instances
        
        return plugin_info
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """
        Listet alle verfügbaren Plugins auf
        
        Returns:
            list: Liste der verfügbaren Plugins mit Informationen
        """
        plugin_list = []
        
        for plugin_name, plugin_info in self.plugins.items():
            plugin_list.append({
                "name": plugin_name,
                "description": plugin_info["description"],
                "version": plugin_info["version"],
                "author": plugin_info["author"],
                "status": "loaded" if plugin_name in self.plugin_instances else "available"
            })
        
        logger.info(f"{len(plugin_list)} Plugins verfügbar")
        return plugin_list
    
    def unload_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """
        Entlädt ein Plugin
        
        Args:
            plugin_name: Name des zu entladenden Plugins
            
        Returns:
            dict: Ergebnis des Entladevorgangs
        """
        logger.info(f"Entlade Plugin: {plugin_name}")
        
        if plugin_name not in self.plugin_instances:
            logger.warning(f"Plugin nicht geladen: {plugin_name}")
            return {
                "status": "warning",
                "message": f"Plugin '{plugin_name}' ist nicht geladen"
            }
        
        try:
            # Rufe die shutdown-Methode auf
            self.plugin_instances[plugin_name].shutdown()
            
            # Entferne die Instanz
            del self.plugin_instances[plugin_name]
            
            logger.info(f"Plugin erfolgreich entladen: {plugin_name}")
            return {"status": "success", "message": f"Plugin '{plugin_name}' entladen"}
        except Exception as e:
            logger.error(f"Fehler beim Entladen des Plugins '{plugin_name}': {str(e)}")
            return {
                "status": "error",
                "message": f"Fehler beim Entladen: {str(e)}"
            }
    
    def unload_all_plugins(self) -> Dict[str, Any]:
        """
        Entlädt alle geladenen Plugins
        
        Returns:
            dict: Ergebnis des Entladevorgangs
        """
        logger.info("Entlade alle Plugins...")
        
        results = {}
        for plugin_name in list(self.plugin_instances.keys()):
            results[plugin_name] = self.unload_plugin(plugin_name)
        
        logger.info("Alle Plugins entladen")
        return results
    
    def reload_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """
        Lädt ein Plugin neu
        
        Args:
            plugin_name: Name des zu neuladenden Plugins
            
        Returns:
            dict: Ergebnis des Neuladevorgangs
        """
        logger.info(f"Lade Plugin neu: {plugin_name}")
        
        # Entlade das Plugin
        unload_result = self.unload_plugin(plugin_name)
        if unload_result["status"] != "success":
            return unload_result
        
        # Lade das Plugin neu
        try:
            # Lade das Modul neu
            plugin_module = self._load_plugin_module(plugin_name)
            
            # Registriere das Plugin neu
            self._register_plugin(plugin_name, plugin_module)
            
            # Erstelle eine neue Instanz
            self._instantiate_plugin(plugin_name)
            
            # Initialisiere das Plugin
            if plugin_name in self.plugin_instances:
                self.plugin_instances[plugin_name].initialize()
            
            logger.info(f"Plugin erfolgreich neu geladen: {plugin_name}")
            return {"status": "success", "message": f"Plugin '{plugin_name}' neu geladen"}
        except Exception as e:
            logger.error(f"Fehler beim Neuladen des Plugins '{plugin_name}': {str(e)}")
            return {
                "status": "error",
                "message": f"Fehler beim Neuladen: {str(e)}"
            }
    
    def reload_all_plugins(self) -> Dict[str, Any]:
        """
        Lädt alle Plugins neu
        
        Returns:
            dict: Ergebnis des Neuladevorgangs
        """
        logger.info("Lade alle Plugins neu...")
        
        results = {}
        for plugin_name in self.plugins.keys():
            results[plugin_name] = self.reload_plugin(plugin_name)
        
        logger.info("Alle Plugins neu geladen")
        return results
    
    def execute_plugin(self, plugin_name: str, method_name: str, *args, **kwargs) -> Any:
        """
        Führt eine Methode eines Plugins aus
        
        Args:
            plugin_name: Name des Plugins
            method_name: Name der auszuführenden Methode
            *args: Positionale Argumente für die Methode
            **kwargs: Schlüsselwort-Argumente für die Methode
            
        Returns:
            Das Ergebnis der Methodenausführung
            
        Raises:
            AttributeError: Wenn die Methode nicht existiert
        """
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            raise ValueError(f"Plugin '{plugin_name}' nicht gefunden oder nicht geladen")
        
        if not hasattr(plugin, method_name):
            raise AttributeError(f"Plugin '{plugin_name}' hat keine Methode '{method_name}'")
        
        method = getattr(plugin, method_name)
        return method(*args, **kwargs)
    
    def register_plugin_class(self, plugin_name: str, plugin_class: Type[Plugin]) -> None:
        """
        Registriert eine Plugin-Klasse manuell
        
        Args:
            plugin_name: Name des Plugins
            plugin_class: Die zu registrierende Plugin-Klasse
        """
        self.plugin_classes[plugin_name] = plugin_class
        self.plugins[plugin_name] = {
            "class": plugin_class,
            "module": None,
            "name": plugin_name,
            "description": getattr(plugin_class, "description", "Keine Beschreibung"),
            "version": getattr(plugin_class, "version", "1.0"),
            "author": getattr(plugin_class, "author", "Unbekannt")
        }
        logger.debug(f"Plugin-Klasse manuell registriert: {plugin_name}")
    
    def create_plugin_instance(self, plugin_name: str) -> Optional[Plugin]:
        """
        Erstellt eine neue Instanz eines Plugins
        
        Args:
            plugin_name: Name des Plugins
            
        Returns:
            Optional[Plugin]: Die neue Plugin-Instanz oder None bei Fehler
        """
        if plugin_name not in self.plugin_classes:
            logger.error(f"Plugin-Klasse für '{plugin_name}' nicht registriert")
            return None
        
        try:
            plugin_instance = self.plugin_classes[plugin_name]()
            logger.debug(f"Neue Plugin-Instanz erstellt: {plugin_name}")
            return plugin_instance
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Plugin-Instanz '{plugin_name}': {str(e)}")
            return None
    
    def get_plugin_count(self) -> int:
        """
        Gibt die Anzahl der geladenen Plugins zurück
        
        Returns:
            int: Anzahl der geladenen Plugins
        """
        return len(self.plugin_instances)
    
    def is_plugin_loaded(self, plugin_name: str) -> bool:
        """
        Prüft, ob ein Plugin geladen ist
        
        Args:
            plugin_name: Name des Plugins
            
        Returns:
            bool: True, wenn das Plugin geladen ist, sonst False
        """
        return plugin_name in self.plugin_instances

# Testblock für direkte Ausführung (nur für Tests)
if __name__ == "__main__":
    print("Teste PluginManager...")
    
    try:
        # Erstelle PluginManager
        print("\n1. Test: Initialisierung")
        manager = PluginManager()
        print(f"  - PluginManager initialisiert")
        print(f"  - Plugin-Verzeichnis: {manager.plugin_dir}")
        
        # Teste Plugin-Liste vor dem Laden
        print("\n2. Test: Plugins vor dem Laden")
        plugins_before = manager.list_plugins()
        print(f"  - {len(plugins_before)} Plugins vor dem Laden: {[p['name'] for p in plugins_before]}")
        
        # Teste Plugin-Ladung
        print("\n3. Test: Lade Plugins")
        load_result = manager.load_plugins()
        print(f"  - Ladungsergebnis: {load_result['status']}")
        print(f"  - Geladene Plugins: {manager.get_plugin_count()}")
        
        # Teste Plugin-Liste nach dem Laden
        print("\n4. Test: Plugins nach dem Laden")
        plugins_after = manager.list_plugins()
        for plugin in plugins_after:
            print(f"  - {plugin['name']}: {plugin['description']} (v{plugin['version']}) von {plugin['author']}")
        
        # Teste Plugin-Ausführung (wenn Plugins vorhanden sind)
        if manager.get_plugin_count() > 0:
            test_plugin = list(manager.plugin_instances.keys())[0]
            print(f"\n5. Test: Teste Plugin '{test_plugin}'")
            
            # Versuche eine Methode auszuführen
            try:
                # Dies ist nur ein Test - die meisten Plugins haben keine 'test'-Methode
                result = manager.execute_plugin(test_plugin, "test_method", "Testargument")
                print(f"  - Testmethode ausgeführt: {result}")
            except Exception as e:
                print(f"  - Testmethode nicht verfügbar: {str(e)}")
            
            # Entlade das Plugin
            print(f"\n6. Test: Entlade Plugin '{test_plugin}'")
            unload_result = manager.unload_plugin(test_plugin)
            print(f"  - Entladeergebnis: {unload_result['status']}")
            print(f"  - Geladene Plugins nach Entladung: {manager.get_plugin_count()}")
        
        # Teste Neuladen aller Plugins
        print("\n7. Test: Neuladen aller Plugins")
        reload_result = manager.reload_all_plugins()
        print(f"  - Neuladeergebnis: {len(reload_result)} Plugins")
        
    except Exception as e:
        print(f"Fehler im Test: {str(e)}")
    
    print("\nTest abgeschlossen")