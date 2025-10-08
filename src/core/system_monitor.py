# src/core/system_monitor.py
"""
system_monitor.py - Systemüberwachung für Mindestentinel

Diese Datei implementiert die Systemüberwachung für das autonome Lernen.
"""

import logging
import psutil
import time
from datetime import datetime

logger = logging.getLogger("mindestentinel.system_monitor")

class SystemMonitor:
    """Überwacht Systemressourcen und -leistung"""
    
    def __init__(self):
        """Initialisiert den SystemMonitor"""
        self.monitoring = False
        self.monitoring_thread = None
        self.monitoring_interval = 5  # Sekunden
        self.system_history = []
        self.max_history = 60  # 5 Minuten bei 5-Sekunden-Intervall
        logger.info("SystemMonitor initialisiert.")
    
    def start_monitoring(self):
        """Startet die Systemüberwachung"""
        if self.monitoring:
            logger.info("Systemüberwachung läuft bereits")
            return
        
        self.monitoring = True
        logger.info("Systemüberwachung gestartet")
        
        # In einer echten Implementierung würden wir hier einen Thread starten
        # Für die Kompatibilität mit dem aktuellen Systemprotokoll:
        self._monitor_once()
    
    def stop_monitoring(self):
        """Stoppt die Systemüberwachung"""
        self.monitoring = False
        logger.info("Systemüberwachung gestoppt")
    
    def _monitor_once(self):
        """Führt eine einzelne Überwachung durch"""
        try:
            # CPU-Auslastung
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Speicherauslastung
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Festplattenauslastung
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Netzwerkauslastung
            net_io = psutil.net_io_counters()
            network_stats = {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv
            }
            
            # Systemstatus speichern
            status = {
                'timestamp': datetime.now(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'disk_percent': disk_percent,
                'network_stats': network_stats,
                'system_health': self._determine_system_health(cpu_percent, memory_percent)
            }
            
            self.system_history.append(status)
            
            # Historie begrenzen
            if len(self.system_history) > self.max_history:
                self.system_history.pop(0)
                
            logger.debug(f"Systemstatus erfasst: CPU={cpu_percent}%, RAM={memory_percent}%, DISK={disk_percent}%")
            
            return status
            
        except Exception as e:
            logger.error(f"Fehler bei der Systemüberwachung: {str(e)}")
            return {
                'timestamp': datetime.now(),
                'cpu_percent': 0,
                'memory_percent': 0,
                'disk_percent': 0,
                'network_stats': {'bytes_sent': 0, 'bytes_recv': 0},
                'system_health': 'UNKNOWN'
            }
    
    def _determine_system_health(self, cpu_percent, memory_percent):
        """Bestimmt den Systemgesundheitsstatus basierend auf Ressourcennutzung"""
        if cpu_percent > 90 or memory_percent > 90:
            return 'CRITICAL'
        elif cpu_percent > 75 or memory_percent > 75:
            return 'WARNING'
        else:
            return 'OK'
    
    def get_system_status(self):
        """Gibt den aktuellen Systemstatus zurück"""
        status = self._monitor_once()
        return {
            'cpu_usage': status['cpu_percent'],
            'memory_usage': status['memory_percent'],
            'disk_usage': status['disk_percent'],
            'network_stats': status['network_stats'],
            'system_health': status['system_health'],
            'timestamp': status['timestamp'].isoformat()
        }
    
    def get_system_history(self):
        """Gibt die Historie der Systemstatuswerte zurück"""
        return [{
            'timestamp': status['timestamp'].isoformat(),
            'cpu_usage': status['cpu_percent'],
            'memory_usage': status['memory_percent'],
            'disk_usage': status['disk_percent'],
            'system_health': status['system_health']
        } for status in self.system_history]
    
    def get_resource_recommendations(self):
        """Gibt Empfehlungen basierend auf der Systemauslastung zurück"""
        current_status = self.get_system_status()
        
        recommendations = []
        
        if current_status['system_health'] == 'CRITICAL':
            recommendations.append("HÖCHSTE SYSTEMLAST - Reduzieren Sie die Anzahl aktiver Modelle sofort")
            recommendations.append("Erwägen Sie die Erhöhung der Hardware-Ressourcen")
        elif current_status['system_health'] == 'WARNING':
            recommendations.append("HOHE SYSTEMLAST - Reduzieren Sie bei Bedarf die Anzahl aktiver Modelle")
            recommendations.append("Überwachen Sie die Systemlast regelmäßig")
        
        # Spezifische Empfehlungen basierend auf der Ressource
        if current_status['cpu_usage'] > 85:
            recommendations.append("CPU-Engpass erkannt - Reduzieren Sie rechenintensive Operationen")
        if current_status['memory_usage'] > 85:
            recommendations.append("Speicherengpass erkannt - Reduzieren Sie die Anzahl geladener Modelle")
        if current_status['disk_usage'] > 85:
            recommendations.append("Festplattenspeicher fast voll - Löschen Sie nicht benötigte Daten")
            
        return {
            'current_status': current_status,
            'recommendations': recommendations
        }