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
from utils.logger import CarlosLogger


class ServiceManager:
    """Manages external services for Carlos Assistant."""
    
    def __init__(self, logger: CarlosLogger):
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
        """Enhanced AllTalk running check"""
        try:
            # Test multiple endpoints to be sure
            test_urls = [
                "http://localhost:7851/api/voices",
                "http://localhost:7851/docs",
                "http://localhost:7851/"
            ]
            
            for url in test_urls:
                try:
                    response = requests.get(url, timeout=3)
                    if response.status_code in [200, 307, 404]:  # Various success codes
                        self.logger.info(f"AllTalk detected via {url}")
                        return True
                except Exception:
                    continue
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking AllTalk: {e}")
            return False
    
    def start_alltalk_service(self) -> bool:
        """Attempt to start AllTalk TTS service."""
        try:
            self.logger.info("Attempting to start AllTalk TTS...")
            
            # Check if AllTalk is installed
            if not self.alltalk_dir.exists():
                self.logger.warning("AllTalk TTS not found - will be auto-installed")
                return False
            
            # Try to start AllTalk server
            start_script = self.alltalk_dir / "start_alltalk.py"
            if start_script.exists():
                subprocess.Popen([sys.executable, str(start_script)], 
                               cwd=str(self.alltalk_dir),
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
                
                # Wait for startup
                time.sleep(10)
                
                if self.check_alltalk_running():
                    self.logger.info("AllTalk TTS started successfully")
                    return True
            
            self.logger.warning("Failed to start AllTalk TTS service")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to start AllTalk TTS: {e}")
            return False
    
    def ensure_all_services(self) -> Dict[str, bool]:
        """
        Ensure all required services are running.
        
        Returns:
            Dictionary with service status
        """
        services = {
            'ollama': False,
            'alltalk': False
        }
        
        # Check Ollama
        if self.check_ollama_running():
            services['ollama'] = True
            self.logger.info("Ollama is running")
        else:
            self.logger.info("Ollama not running, attempting to start...")
            if self.start_ollama_service():
                services['ollama'] = True
                self.logger.info("Ollama started successfully")
            else:
                self.logger.error("Failed to start Ollama")
        
        # Check AllTalk TTS
        if self.check_alltalk_running():
            services['alltalk'] = True
            self.logger.info("AllTalk TTS is running")
        else:
            self.logger.info("AllTalk TTS not running, attempting to start...")
            if self.start_alltalk_service():
                services['alltalk'] = True
                self.logger.info("AllTalk TTS started successfully")
            else:
                self.logger.warning("AllTalk TTS not available - continuing without TTS")
        
        return services
    
    def check_setup_completion(self) -> bool:
        """Check if setup has been completed."""
        setup_flag = self.project_root / "setup_completed.flag"
        return setup_flag.exists()
    
    def get_service_status_summary(self) -> str:
        """Get a summary of all service statuses."""
        ollama_status = "✅ Running" if self.check_ollama_running() else "❌ Not Running"
        alltalk_status = "✅ Running" if self.check_alltalk_running() else "❌ Not Running"
        
        return f"Ollama: {ollama_status} | AllTalk TTS: {alltalk_status}"
