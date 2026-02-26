#!/usr/bin/env python3
"""
Connection Monitor Service
Periodically updates device connection status based on WireGuard handshakes
"""
import sys
import time
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app import app
from wireguard_manager import WireGuardManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/wireguard-monitor.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('wireguard-monitor')

def monitor_connections():
    """Main monitoring loop"""
    logger.info("WireGuard Connection Monitor started")
    
    update_interval = 30  # Update every 30 seconds
    
    while True:
        try:
            with app.app_context():
                logger.debug("Updating device connection status...")
                WireGuardManager.update_device_connection_status()
                logger.debug("Update completed successfully")
                
        except Exception as e:
            logger.error(f"Error updating connection status: {e}")
        
        time.sleep(update_interval)

if __name__ == '__main__':
    try:
        monitor_connections()
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Monitor crashed: {e}")
        sys.exit(1)
