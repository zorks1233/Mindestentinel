"""
shutdown.py - API-Endpunkt für sauberes Herunterfahren des Systems

Dieses Modul stellt einen Endpunkt bereit, um das System ordnungsgemäß herunterzufahren.
"""

import os
import time
import threading
import logging
from fastapi import APIRouter, HTTPException

router = APIRouter()
logger = logging.getLogger("mindestentinel.shutdown")

@router.post("/shutdown")
async def shutdown():
    """Initiiert einen sauberen Shutdown des Systems"""
    logger.info("Shutdown-Anfrage erhalten. Beende System...")
    
    # Starte Shutdown in einem Hintergrundthread, damit die Antwort gesendet werden kann
    def shutdown_server():
        time.sleep(1)  # Kleine Pause, damit die Antwort gesendet werden kann
        
        # Hier können zusätzliche