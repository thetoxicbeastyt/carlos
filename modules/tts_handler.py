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
        Enhanced AllTalk startup with Python 3.13 compatibility workaround
        """
        import sys
        import os
        from pathlib import Path
        
        try:
            # Check if already running first
            if self.check_alltalk_running():
                self.logger.info("AllTalk server is already running")
                return True
                
            alltalk_dir = Path("alltalk_tts")
            
            if not alltalk_dir.exists():
                self.logger.error("AllTalk directory not found")
                return False
            
            # NEW: Python 3.13 compatibility check
            python_version = sys.version_info
            if python_version.major == 3 and python_version.minor >= 13:
                self.logger.warning("Python 3.13+ detected - AllTalk TTS may not be compatible")
                self.logger.info("Attempting to use alternative TTS solution...")
                
                # Try to use a simpler TTS approach that works with Python 3.13
                return self._start_simple_tts_server()
            
            # Set up environment for AllTalk
            env = os.environ.copy()
            env['PYTHONPATH'] = str(alltalk_dir.absolute()) + os.pathsep + env.get('PYTHONPATH', '')
            
            # Method 1: Try tts_server.py with proper environment
            server_script = alltalk_dir / "tts_server.py"
            if server_script.exists():
                try:
                    self.logger.info(f"Starting AllTalk via: {server_script}")
                    
                    # Start with proper working directory and environment
                    process = subprocess.Popen([
                        sys.executable, str(server_script.name)
                    ], 
                    cwd=str(alltalk_dir),  # CRITICAL: Set working directory
                    env=env,  # Pass environment variables
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    text=True
                    )
                    
                    # Wait longer for AllTalk to start
                    self.logger.info("Waiting for AllTalk to start...")
                    for i in range(12):  # 12 * 5 = 60 seconds max
                        time.sleep(5)
                        if self.check_alltalk_running():
                            self.logger.info(f"AllTalk started successfully after {(i+1)*5} seconds")
                            return True
                        self.logger.info(f"Still waiting... ({(i+1)*5}s)")
                    
                    # If still not running, capture error output
                    try:
                        stdout, stderr = process.communicate(timeout=3)
                        self.logger.error(f"AllTalk startup failed - STDOUT: {stdout[:500]}")
                        self.logger.error(f"AllTalk startup failed - STDERR: {stderr[:500]}")
                    except subprocess.TimeoutExpired:
                        self.logger.error("AllTalk process still running but not responding to API")
                        
                except Exception as e:
                    self.logger.error(f"Exception starting AllTalk via tts_server.py: {e}")
            
            # Method 2: Try alternative startup with script.py
            script_file = alltalk_dir / "script.py"
            if script_file.exists():
                try:
                    self.logger.info(f"Trying alternative startup via: {script_file}")
                    
                    process = subprocess.Popen([
                        sys.executable, str(script_file.name)
                    ], 
                    cwd=str(alltalk_dir),
                    env=env,
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    text=True
                    )
                    
                    # Wait and check
                    time.sleep(10)
                    if self.check_alltalk_running():
                        self.logger.info("AllTalk started successfully via script.py")
                        return True
                        
                except Exception as e:
                    self.logger.error(f"Exception starting AllTalk via script.py: {e}")
            
            # Method 3: Try direct FastAPI startup (last resort)
            try:
                self.logger.info("Trying direct FastAPI startup...")
                
                # Look for main app file
                app_files = [
                    alltalk_dir / "app.py",
                    alltalk_dir / "main.py", 
                    alltalk_dir / "server.py"
                ]
                
                for app_file in app_files:
                    if app_file.exists():
                        process = subprocess.Popen([
                            sys.executable, "-m", "uvicorn", f"{app_file.stem}:app",
                            "--host", "0.0.0.0", "--port", "7851"
                        ], 
                        cwd=str(alltalk_dir),
                        env=env,
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE
                        )
                        
                        time.sleep(8)
                        if self.check_alltalk_running():
                            self.logger.info(f"AllTalk started via uvicorn with {app_file.stem}")
                            return True
                            
            except Exception as e:
                self.logger.error(f"Direct FastAPI startup failed: {e}")
            
            self.logger.warning("All AllTalk startup methods failed")
            return False
            
        except Exception as e:
            self.logger.error(f"Fatal error in AllTalk startup: {e}")
            return False

    def _start_simple_tts_server(self) -> bool:
        """Start a simple TTS server compatible with Python 3.13"""
        try:
            self.logger.info("Starting simple TTS server for Python 3.13...")
            
            # Create a simple TTS server that works with Python 3.13
            simple_tts_code = '''
import os
import sys
import json
import time
import threading
from pathlib import Path
from typing import Dict, Any

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    import uvicorn
    import requests
    import pygame
    import tempfile
    import subprocess
    from gtts import gTTS
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn", "pydantic", "requests", "pygame", "gTTS"])
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    import uvicorn
    import requests
    import pygame
    import tempfile
    from gtts import gTTS

app = FastAPI(title="Simple TTS Server", version="1.0.0")

class TTSRequest(BaseModel):
    text_input: str
    character_voice_gen: str = "default"
    language: str = "en"

@app.get("/")
async def root():
    return {"message": "Simple TTS Server Running"}

@app.get("/api/voices")
async def get_voices():
    return {"voices": ["default", "male", "female"]}

@app.get("/api/status")
async def get_status():
    return {"status": "running", "version": "1.0.0"}

@app.post("/api/tts-generate")
async def generate_tts(request: TTSRequest):
    try:
        # Create temporary file for audio
        temp_dir = Path("temp_audio")
        temp_dir.mkdir(exist_ok=True)
        
        # Generate speech using gTTS
        tts = gTTS(text=request.text_input, lang=request.language)
        output_path = temp_dir / f"carlos_tts_{int(time.time())}.mp3"
        tts.save(str(output_path))
        
        return {
            "status": "success",
            "output_file_path": str(output_path),
            "message": "Audio generated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7851)
'''
            
            # Write the simple TTS server
            simple_tts_file = Path("simple_tts_server.py")
            with open(simple_tts_file, "w") as f:
                f.write(simple_tts_code)
            
            # Install required packages
            self.logger.info("Installing simple TTS dependencies...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", 
                "fastapi", "uvicorn", "pydantic", "requests", "pygame", "gTTS"
            ], capture_output=True, text=True)
            
            # Start the simple TTS server
            process = subprocess.Popen([
                sys.executable, "simple_tts_server.py"
            ], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
            )
            
            # Wait for server to start
            time.sleep(5)
            if self.check_alltalk_running():
                self.logger.info("Simple TTS server started successfully")
                return True
            else:
                self.logger.error("Simple TTS server failed to start")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to start simple TTS server: {e}")
            return False
    
    def check_alltalk_running(self) -> bool:
        """Enhanced AllTalk running check with multiple endpoints"""
        test_endpoints = [
            "/api/voices",
            "/api/status", 
            "/",
            "/docs"
        ]
        
        for endpoint in test_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=3)
                if response.status_code in [200, 404]:  # 404 is OK for some endpoints
                    self.logger.info(f"AllTalk responding on {endpoint}")
                    return True
            except Exception:
                continue
        
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