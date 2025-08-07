"""
Service Manager for Carlos Assistant
Handles auto-starting services and intelligent fallbacks
"""

import os
import sys
import time
import subprocess
import platform
import requests
from typing import Dict, Any, Optional
from pathlib import Path


class ServiceManager:
    """Manages external services for Carlos Assistant."""
    
    def __init__(self, logger):
        """Initialize the service manager."""
        self.logger = logger
        self.project_root = Path.cwd()
        self.alltalk_dir = self.project_root / "alltalk_tts"
    
    def check_ollama_running(self) -> bool:
        """Check if Ollama service is running."""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def start_ollama_service(self) -> bool:
        """Attempt to start Ollama service."""
        try:
            self.logger.info("Attempting to start Ollama...")
            
            # Method 1: Try as Windows service
            if platform.system() == "Windows":
                result = subprocess.run(['sc', 'start', 'ollama'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    time.sleep(3)  # Wait for startup
                    if self.check_ollama_running():
                        self.logger.info("Ollama started via Windows service")
                        return True
            
            # Method 2: Try direct executable
            subprocess.Popen(['ollama', 'serve'], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            
            # Wait and test
            time.sleep(5)
            if self.check_ollama_running():
                self.logger.info("Ollama started via direct executable")
                return True
            
            # Method 3: Try with full path (Windows)
            if platform.system() == "Windows":
                ollama_paths = [
                    r"C:\Program Files\Ollama\ollama.exe",
                    r"C:\ProgramData\chocolatey\bin\ollama.exe"
                ]
                
                for path in ollama_paths:
                    if Path(path).exists():
                        subprocess.Popen([path, 'serve'], 
                                       stdout=subprocess.DEVNULL, 
                                       stderr=subprocess.DEVNULL)
                        time.sleep(5)
                        if self.check_ollama_running():
                            self.logger.info(f"Ollama started via {path}")
                            return True
            
            self.logger.warning("Failed to start Ollama service")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to start Ollama: {e}")
            return False
    
    def check_alltalk_running(self) -> bool:
        """Check if AllTalk TTS service is running."""
        try:
            response = requests.get("http://localhost:7851/api/voices", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def start_alltalk_service(self) -> bool:
        """Attempt to start AllTalk TTS service."""
        try:
            self.logger.info("Attempting to start AllTalk TTS...")
            
            if not self.alltalk_dir.exists():
                self.logger.warning("AllTalk directory not found")
                return False
            
            # Find the server script
            server_scripts = [
                self.alltalk_dir / "tts_server.py",
                self.alltalk_dir / "system" / "tts_server.py"
            ]
            
            server_script = None
            for script in server_scripts:
                if script.exists():
                    server_script = script
                    break
            
            if not server_script:
                self.logger.warning("AllTalk server script not found")
                return False
            
            # Start the server
            subprocess.Popen([
                sys.executable, str(server_script)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Wait and test
            time.sleep(10)  # AllTalk takes longer to start
            if self.check_alltalk_running():
                self.logger.info("AllTalk TTS started successfully")
                return True
            
            self.logger.warning("Failed to start AllTalk TTS service")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to start AllTalk TTS: {e}")
            return False
    
    def ensure_all_services(self) -> Dict[str, bool]:
        """Ensure all required services are running."""
        service_status = {
            'ollama': False,
            'alltalk': False
        }
        
        # Check and start Ollama
        if self.check_ollama_running():
            service_status['ollama'] = True
            self.logger.info("Ollama is already running")
        else:
            self.logger.info("Ollama not running, attempting to start...")
            if self.start_ollama_service():
                service_status['ollama'] = True
                self.logger.info("Ollama started successfully")
            else:
                self.logger.error("Failed to start Ollama")
        
        # Check and start AllTalk TTS
        if self.check_alltalk_running():
            service_status['alltalk'] = True
            self.logger.info("AllTalk TTS is already running")
        else:
            self.logger.info("AllTalk TTS not running, attempting to start...")
            if self.start_alltalk_service():
                service_status['alltalk'] = True
                self.logger.info("AllTalk TTS started successfully")
            else:
                self.logger.warning("Failed to start AllTalk TTS - continuing without TTS")
        
        return service_status
    
    def check_setup_completion(self) -> bool:
        """Check if setup has been completed."""
        setup_flag = self.project_root / "setup_completed.flag"
        return setup_flag.exists()
    
    def get_service_status_summary(self) -> str:
        """Get a human-readable summary of service status."""
        ollama_running = self.check_ollama_running()
        alltalk_running = self.check_alltalk_running()
        
        status_lines = []
        status_lines.append("Service Status:")
        status_lines.append(f"  Ollama: {'✅ Running' if ollama_running else '❌ Not Running'}")
        status_lines.append(f"  AllTalk TTS: {'✅ Running' if alltalk_running else '❌ Not Running'}")
        
        return "\n".join(status_lines)
