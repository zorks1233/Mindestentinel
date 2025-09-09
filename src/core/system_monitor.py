"""
SystemMonitor - Überwacht Systemressourcen und Leistung
"""

import logging
import psutil
import time
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SystemMonitor:
    """
    Überwacht Systemressourcen wie CPU, Speicher, Festplatte und Netzwerk.
    Stellt Metriken für das System-Management bereit.
    """
    
    def __init__(self):
        """Initialisiert den SystemMonitor."""
        self.last_snapshot = None
        self.start_time = time.time()
        logger.info("SystemMonitor initialisiert.")
    
    def snapshot(self) -> Dict[str, Any]:
        """
        Erstellt eine Momentaufnahme der aktuellen Systemressourcen.
        
        Returns:
            Dict mit den aktuellen Systemmetriken
        """
        try:
            # CPU-Auslastung (prozentual)
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Speicherauslastung (prozentual)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Festplattennutzung (prozentual)
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Netzwerkstatistiken
            net_io = psutil.net_io_counters()
            
            # Erstelle Snapshot
            self.last_snapshot = {
                "cpu": cpu_percent,
                "memory": memory_percent,
                "disk": disk_percent,
                "network": {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv
                },
                "uptime": time.time() - self.start_time,
                "timestamp": time.time()
            }
            
            return self.last_snapshot
        except Exception as e:
            logger.error(f"Fehler bei der Erstellung des System-Snapshots: {str(e)}", exc_info=True)
            # Fallback-Werte, falls psutil nicht verfügbar ist
            return {
                "cpu": 50.0,
                "memory": 50.0,
                "disk": 50.0,
                "network": {
                    "bytes_sent": 0,
                    "bytes_recv": 0
                },
                "uptime": time.time() - self.start_time,
                "timestamp": time.time()
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Gibt die aktuellen Systemstatistiken zurück.
        
        Returns:
            Dict mit Systemstatistiken
        """
        snapshot = self.snapshot()
        return {
            "resource_usage": {
                "cpu": snapshot["cpu"],
                "memory": snapshot["memory"],
                "disk": snapshot["disk"]
            },
            "network_usage": snapshot["network"],
            "uptime": snapshot["uptime"],
            "timestamp": snapshot["timestamp"]
        }
    
    def get_resource_usage(self) -> Dict[str, float]:
        """
        Gibt nur die Ressourcennutzung zurück (CPU, Speicher, Festplatte).
        
        Returns:
            Dict mit Ressourcennutzung
        """
        stats = self.get_statistics()
        return stats["resource_usage"]
    
    def check_resource_thresholds(self, cpu_threshold: float = 80.0, 
                                 memory_threshold: float = 85.0, 
                                 disk_threshold: float = 90.0) -> bool:
        """
        Prüft, ob die Ressourcennutzung kritische Schwellenwerte überschreitet.
        
        Args:
            cpu_threshold: CPU-Schwellenwert in Prozent
            memory_threshold: Speicher-Schwellenwert in Prozent
            disk_threshold: Festplatten-Schwellenwert in Prozent
            
        Returns:
            bool: True, wenn alle Ressourcen unter den Schwellenwerten liegen
        """
        usage = self.get_resource_usage()
        return (
            usage["cpu"] < cpu_threshold and
            usage["memory"] < memory_threshold and
            usage["disk"] < disk_threshold
        )
    
    def get_uptime(self) -> float:
        """
        Gibt die Systemlaufzeit in Sekunden zurück.
        
        Returns:
            float: Uptime in Sekunden
        """
        return time.time() - self.start_time