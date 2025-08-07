"""
TTS Handler for Carlos Assistant with AllTalk TTS integration.
"""

import os
import json
import time
import requests
import threading
import subprocess
import pygame
from typing import Dict, List, Optional, Any
from utils.logger import CarlosLogger


class TTSHandler:
    """Handler for Text-to-Speech using AllTalk TTS API."""
    
    def __init__(self, config: dict, logger: CarlosLogger):
        """
        Initialize the TTS handler.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.base_url = config['alltalk_tts']['base_url']
        self.enabled = config['alltalk_tts'].get('enabled', True)
        self.voice = config['alltalk_tts'].get('voice', 'default')
        self.speed = config['alltalk_tts'].get('speed', 1.0)
        self.pitch = config['alltalk_tts'].get('pitch', 1.0)
        self.volume = config['alltalk_tts'].get('volume', 0.8)
        self.timeout = config['alltalk_tts'].get('timeout', 10)
        self.auto_play = config['alltalk_tts'].get('auto_play', True)
        
        # Audio playback management
        self.speaking = False
        self.current_audio_file = None
        self.speech_queue = []
        self.queue_lock = threading.Lock()
        
        # Initialize pygame for audio playback
        try:
            pygame.mixer.init()
            self.pygame_available = True
        except Exception as e:
            self.logger.warning(f"Pygame not available for audio: {e}")
            self.pygame_available = False
        
        # AllTalk installation status
        self.alltalk_installed = False
        self.alltalk_path = None
        
        self.logger.info(f"TTS Handler initialized - Enabled: {self.enabled}")
    
    def check_alltalk_installation(self) -> bool:
        """
        Check if AllTalk TTS is installed.
        
        Returns:
            True if installed, False otherwise
        """
        try:
            # Check if AllTalk is already running
            response = requests.get(f"{self.base_url}/api/voices", timeout=3)
            if response.status_code == 200:
                self.alltalk_installed = True
                self.logger.info("AllTalk TTS is already running")
                return True
        except:
            pass
        
        # Check if AllTalk is installed locally
        possible_paths = [
            "alltalk_tts",
            "../alltalk_tts", 
            "../../alltalk_tts",
            os.path.expanduser("~/alltalk_tts")
        ]
        
        for path in possible_paths:
            if os.path.exists(os.path.join(path, "start_alltalk.py")):
                self.alltalk_path = path
                self.alltalk_installed = True
                self.logger.info(f"Found AllTalk installation at: {path}")
                return True
        
        self.logger.warning("AllTalk TTS not found")
        return False
    
    def install_alltalk(self) -> bool:
        """
        Install AllTalk TTS from GitHub.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Starting AllTalk TTS installation...")
            
            # Clone repository
            clone_cmd = [
                "git", "clone", 
                "https://github.com/erew123/alltalk_tts.git",
                "alltalk_tts"
            ]
            
            result = subprocess.run(clone_cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                self.logger.error(f"Failed to clone AllTalk: {result.stderr}")
                return False
            
            # Install requirements
            self.logger.info("Installing AllTalk requirements...")
            install_cmd = [
                "pip", "install", "-r", "alltalk_tts/requirements.txt"
            ]
            
            result = subprocess.run(install_cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                self.logger.warning(f"Some requirements may have failed: {result.stderr}")
            
            self.alltalk_path = "alltalk_tts"
            self.alltalk_installed = True
            self.logger.info("AllTalk TTS installed successfully")
            return True
            
        except subprocess.TimeoutExpired:
            self.logger.error("AllTalk installation timed out")
            return False
        except Exception as e:
            self.logger.error(f"Error installing AllTalk: {e}")
            return False
    
    def debug_alltalk_startup(self) -> dict:
        """Comprehensive AllTalk startup debugging"""
        import sys
        from pathlib import Path
        
        debug_info = {
            'python_executable': sys.executable,
            'alltalk_path': str(Path("alltalk_tts").absolute()),
            'server_script_exists': Path("alltalk_tts/tts_server.py").exists(),
            'requirements_satisfied': [],
            'startup_error': None
        }
        
        # Check if main server file exists
        server_files = [
            "alltalk_tts/tts_server.py",
            "alltalk_tts/script.py", 
            "alltalk_tts/atsetup.py"
        ]
        
        for file_path in server_files:
            debug_info[f'{file_path}_exists'] = Path(file_path).exists()
            if Path(file_path).exists():
                self.logger.info(f"Found AllTalk file: {file_path}")
        
        return debug_info

    def start_alltalk_server(self) -> bool:
        """
        Enhanced AllTalk startup with comprehensive error handling and multiple startup methods.
        
        Returns:
            True if server is running, False otherwise
        """
        import sys
        from pathlib import Path
        
        try:
            # Check if already running
            response = requests.get(f"{self.base_url}/api/voices", timeout=3)
            if response.status_code == 200:
                self.logger.info("AllTalk server is already running")
                return True
        except:
            pass
        
        # Debug AllTalk installation
        debug_info = self.debug_alltalk_startup()
        self.logger.info(f"AllTalk debug info: {debug_info}")
        
        alltalk_dir = Path("alltalk_tts")
        
        if not alltalk_dir.exists():
            self.logger.error("AllTalk directory not found")
            return False
            
        # Method 1: Direct server startup via tts_server.py
        server_script = alltalk_dir / "tts_server.py"
        if server_script.exists():
            try:
                self.logger.info(f"Starting AllTalk via: {server_script}")
                
                # Start with detailed output capture
                process = subprocess.Popen([
                    sys.executable, str(server_script)
                ], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                cwd=str(alltalk_dir),
                text=True
                )
                
                # Wait and check if it started
                time.sleep(5)
                if self.check_alltalk_running():
                    self.logger.info("AllTalk started successfully via tts_server.py")
                    return True
                else:
                    # Capture any error output
                    try:
                        stdout, stderr = process.communicate(timeout=2)
                        self.logger.error(f"AllTalk startup failed - STDOUT: {stdout[:500]}")
                        self.logger.error(f"AllTalk startup failed - STDERR: {stderr[:500]}")
                    except subprocess.TimeoutExpired:
                        self.logger.error("AllTalk process still running but not responding")
                        
            except Exception as e:
                self.logger.error(f"Exception starting AllTalk via tts_server.py: {e}")
        
        # Method 2: Try script.py
        script_file = alltalk_dir / "script.py"
        if script_file.exists():
            try:
                self.logger.info(f"Starting AllTalk via: {script_file}")
                
                process = subprocess.Popen([
                    sys.executable, str(script_file)
                ], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                cwd=str(alltalk_dir),
                text=True
                )
                
                time.sleep(5)
                if self.check_alltalk_running():
                    self.logger.info("AllTalk started successfully via script.py")
                    return True
                else:
                    try:
                        stdout, stderr = process.communicate(timeout=2)
                        self.logger.error(f"AllTalk startup via script.py failed - STDOUT: {stdout[:500]}")
                        self.logger.error(f"AllTalk startup via script.py failed - STDERR: {stderr[:500]}")
                    except subprocess.TimeoutExpired:
                        self.logger.error("script.py process still running but not responding")
                        
            except Exception as e:
                self.logger.error(f"Exception starting AllTalk via script.py: {e}")
        
        # Method 3: Try Windows batch file
        batch_file = alltalk_dir / "atsetup.bat"
        if batch_file.exists() and os.name == 'nt':  # Windows only
            try:
                self.logger.info(f"Starting AllTalk via: {batch_file}")
                
                process = subprocess.Popen([
                    str(batch_file)
                ], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                cwd=str(alltalk_dir),
                text=True,
                shell=True
                )
                
                time.sleep(5)
                if self.check_alltalk_running():
                    self.logger.info("AllTalk started successfully via atsetup.bat")
                    return True
                else:
                    try:
                        stdout, stderr = process.communicate(timeout=2)
                        self.logger.error(f"AllTalk startup via batch failed - STDOUT: {stdout[:500]}")
                        self.logger.error(f"AllTalk startup via batch failed - STDERR: {stderr[:500]}")
                    except subprocess.TimeoutExpired:
                        self.logger.error("Batch process still running but not responding")
                        
            except Exception as e:
                self.logger.error(f"Exception starting AllTalk via batch: {e}")
        
        # Method 4: Try alternative port configurations
        alternative_ports = [7852, 7853, 7854]
        base_url_backup = self.base_url
        
        for port in alternative_ports:
            try:
                self.logger.info(f"Trying alternative port {port}")
                alternative_url = f"http://localhost:{port}"
                response = requests.get(f"{alternative_url}/api/voices", timeout=3)
                if response.status_code == 200:
                    self.logger.info(f"Found AllTalk running on port {port}")
                    self.base_url = alternative_url
                    # Update config if needed
                    if 'alltalk_tts' in self.config:
                        self.config['alltalk_tts']['base_url'] = alternative_url
                    return True
            except:
                continue
        
        # Restore original base_url if alternative ports didn't work
        self.base_url = base_url_backup
        
        self.logger.error("All AllTalk startup methods failed")
        return False
    
    def check_alltalk_running(self) -> bool:
        """Check if AllTalk is responding on the configured port"""
        try:
            response = requests.get(f"{self.base_url}/api/voices", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def test_connection(self) -> bool:
        """
        Test connection to AllTalk TTS API.
        
        Returns:
            True if connection successful, False otherwise
        """
        if not self.enabled:
            self.logger.info("TTS is disabled in configuration")
            return False
        
        try:
            # Test basic connectivity
            response = requests.get(f"{self.base_url}/api/voices", timeout=self.timeout)
            
            if response.status_code == 200:
                voices_data = response.json()
                available_voices = voices_data.get('voices', [])
                self.logger.info(f"Connected to AllTalk TTS - {len(available_voices)} voices available")
                
                # Test TTS generation with a simple phrase
                test_response = self.generate_audio("Test connection", test_mode=True)
                if test_response:
                    self.logger.info("TTS test generation successful")
                    return True
                else:
                    self.logger.warning("TTS test generation failed")
                    return False
            else:
                self.logger.error(f"AllTalk API returned status code: {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            self.logger.error("Cannot connect to AllTalk TTS server")
            return False
        except requests.exceptions.Timeout:
            self.logger.error("Connection to AllTalk TTS server timed out")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during TTS connection test: {e}")
            return False
    
    def generate_audio(self, text: str, test_mode: bool = False) -> Optional[str]:
        """
        Generate audio file from text using AllTalk TTS.
        
        Args:
            text: Text to convert to speech
            test_mode: If True, don't save file for playback
            
        Returns:
            Path to generated audio file or None if failed
        """
        try:
            if not self.enabled:
                return None
            
            # Clean text for TTS
            clean_text = self._clean_text_for_tts(text)
            if not clean_text:
                return None
            
            # Prepare API request
            tts_data = {
                "text_input": clean_text,
                "text_filtering": "standard",
                "character_voice_gen": self.voice,
                "narrator_enabled": False,
                "narrator_voice_gen": "",
                "text_not_inside": "",
                "language": "en",
                "output_file_name": "carlos_tts_output",
                "output_file_timestamp": True,
                "autoplay": False,  # We handle playback ourselves
                "autoplay_volume": self.volume
            }
            
            # Make TTS request
            response = requests.post(
                f"{self.base_url}/api/tts-generate",
                json=tts_data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                if test_mode:
                    return "test_success"  # Don't need actual file for test
                
                # Get the generated audio file path
                output_path = response_data.get("output_file_path")
                if output_path and os.path.exists(output_path):
                    self.logger.debug(f"TTS audio generated: {output_path}")
                    return output_path
                else:
                    self.logger.error("TTS audio file not found after generation")
                    return None
            else:
                self.logger.error(f"TTS generation failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating TTS audio: {e}")
            return None
    
    def _clean_text_for_tts(self, text: str) -> str:
        """
        Clean text for better TTS output.
        
        Args:
            text: Original text
            
        Returns:
            Cleaned text
        """
        if not text or not text.strip():
            return ""
        
        # Remove excessive whitespace
        clean_text = " ".join(text.split())
        
        # Remove emojis and special characters that might cause issues
        # Keep basic punctuation for natural speech
        allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?;:-()[]")
        clean_text = "".join(char for char in clean_text if char in allowed_chars)
        
        # Limit length to prevent timeout
        max_length = self.config['general'].get('max_response_length', 1000)
        if len(clean_text) > max_length:
            clean_text = clean_text[:max_length - 3] + "..."
        
        return clean_text.strip()
    
    def speak(self, text: str) -> bool:
        """
        Convert text to speech and play it.
        
        Args:
            text: Text to speak
            
        Returns:
            True if speech was initiated successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            # Generate audio file
            audio_file = self.generate_audio(text)
            if not audio_file:
                return False
            
            # Add to speech queue
            with self.queue_lock:
                self.speech_queue.append(audio_file)
            
            # Start playback if not already speaking
            if not self.speaking and self.auto_play:
                self._start_playback_thread()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in speak method: {e}")
            return False
    
    def _start_playback_thread(self) -> None:
        """Start audio playback in a separate thread."""
        if not self.pygame_available:
            self.logger.warning("Cannot play audio - pygame not available")
            return
        
        playback_thread = threading.Thread(target=self._playback_worker, daemon=True)
        playback_thread.start()
    
    def _playback_worker(self) -> None:
        """Worker thread for audio playback."""
        while True:
            with self.queue_lock:
                if not self.speech_queue:
                    self.speaking = False
                    break
                audio_file = self.speech_queue.pop(0)
            
            try:
                self.speaking = True
                self.current_audio_file = audio_file
                
                # Load and play audio
                pygame.mixer.music.load(audio_file)
                pygame.mixer.music.set_volume(self.volume)
                pygame.mixer.music.play()
                
                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                
                # Clean up audio file
                try:
                    os.remove(audio_file)
                except:
                    pass  # File cleanup is not critical
                
            except Exception as e:
                self.logger.error(f"Error during audio playback: {e}")
            finally:
                self.current_audio_file = None
        
        self.speaking = False
    
    def stop_speaking(self) -> None:
        """Stop current speech and clear queue."""
        try:
            if self.pygame_available and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            
            with self.queue_lock:
                self.speech_queue.clear()
            
            self.speaking = False
            self.current_audio_file = None
            self.logger.debug("Speech stopped and queue cleared")
            
        except Exception as e:
            self.logger.error(f"Error stopping speech: {e}")
    
    def is_speaking(self) -> bool:
        """
        Check if TTS is currently speaking.
        
        Returns:
            True if speaking, False otherwise
        """
        return self.speaking
    
    def get_available_voices(self) -> List[str]:
        """
        Get list of available voices from AllTalk.
        
        Returns:
            List of voice names
        """
        try:
            response = requests.get(f"{self.base_url}/api/voices", timeout=5)
            if response.status_code == 200:
                voices_data = response.json()
                return voices_data.get('voices', [])
            else:
                self.logger.error(f"Failed to get voices: {response.status_code}")
                return []
        except Exception as e:
            self.logger.error(f"Error getting available voices: {e}")
            return []
    
    def set_voice(self, voice_name: str) -> bool:
        """
        Set the voice for TTS.
        
        Args:
            voice_name: Name of the voice to use
            
        Returns:
            True if voice was set successfully, False otherwise
        """
        try:
            available_voices = self.get_available_voices()
            if voice_name in available_voices:
                self.voice = voice_name
                self.logger.info(f"Voice changed to: {voice_name}")
                return True
            else:
                self.logger.error(f"Voice '{voice_name}' not available. Available: {available_voices}")
                return False
        except Exception as e:
            self.logger.error(f"Error setting voice: {e}")
            return False
    
    def set_volume(self, volume: float) -> None:
        """
        Set the volume for TTS playback.
        
        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self.volume = max(0.0, min(1.0, volume))
        self.logger.debug(f"Volume set to: {self.volume}")
    
    def cleanup(self) -> None:
        """Clean up TTS resources."""
        try:
            self.stop_speaking()
            
            if self.pygame_available:
                pygame.mixer.quit()
            
            # Clean up any remaining audio files
            if self.current_audio_file and os.path.exists(self.current_audio_file):
                try:
                    os.remove(self.current_audio_file)
                except:
                    pass
            
            self.logger.info("TTS cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during TTS cleanup: {e}")