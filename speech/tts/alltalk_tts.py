"""
AllTalk TTS Provider Implementation
Provides AllTalk TTS integration for Carlos AI Assistant
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
from .base_tts import BaseTTS


class AllTalkTTS(BaseTTS):
    """AllTalk TTS provider implementation."""
    
    def __init__(self, config: Dict[str, Any], logger: CarlosLogger):
        """
        Initialize the AllTalk TTS provider.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        super().__init__(config, logger)
        
        # Extract AllTalk-specific configuration
        alltalk_config = config.get('speech', {}).get('tts', {}).get('providers', {}).get('alltalk', {})
        if not alltalk_config:
            # Fallback to legacy config structure
            alltalk_config = config.get('alltalk_tts', {})
        
        self.base_url = alltalk_config.get('base_url', 'http://localhost:7851')
        self.enabled = alltalk_config.get('enabled', True)
        self.voice = alltalk_config.get('voice', 'default')
        self.speed = alltalk_config.get('speed', 1.0)
        self.pitch = alltalk_config.get('pitch', 1.0)
        self.volume = alltalk_config.get('volume', 0.8)
        self.timeout = alltalk_config.get('timeout', 10)
        self.auto_play = alltalk_config.get('auto_play', True)
        
        # Audio playback management
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
        
        self.logger.info(f"AllTalk TTS Provider initialized - Enabled: {self.enabled}")
    
    def test_connection(self) -> bool:
        """
        Test connection to AllTalk TTS.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.logger.info("Testing connection to AllTalk TTS...")
            
            # Test basic connectivity
            response = requests.get(f"{self.base_url}/api/voices", timeout=self.timeout)
            
            if response.status_code == 200:
                self.is_connected = True
                self.logger.info("Successfully connected to AllTalk TTS")
                return True
            else:
                self.logger.error(f"AllTalk TTS returned status code: {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            self.logger.error("Failed to connect to AllTalk TTS - service not running")
            return False
        except requests.exceptions.Timeout:
            self.logger.error("Connection to AllTalk TTS timed out")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error testing AllTalk TTS connection: {e}")
            return False
    
    def speak(self, text: str) -> bool:
        """
        Convert text to speech and play it.
        
        Args:
            text: Text to convert to speech
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.is_connected:
                self.logger.error("AllTalk TTS not connected")
                return False
            
            # Clean text for TTS
            cleaned_text = self._clean_text_for_tts(text)
            
            if not cleaned_text:
                self.logger.warning("No text to speak after cleaning")
                return False
            
            # Generate audio
            audio_file = self.generate_audio(cleaned_text)
            
            if not audio_file:
                self.logger.error("Failed to generate audio")
                return False
            
            # Play audio
            self.is_speaking = True
            success = self._play_audio_file(audio_file)
            self.is_speaking = False
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error in speak: {e}", exc_info=True)
            self.is_speaking = False
            return False
    
    def get_available_voices(self) -> List[str]:
        """
        Get list of available AllTalk voices.
        
        Returns:
            List of voice names
        """
        try:
            response = requests.get(f"{self.base_url}/api/voices", timeout=self.timeout)
            
            if response.status_code == 200:
                voices_data = response.json()
                voices = [voice.get('name', voice.get('id', '')) for voice in voices_data]
                self.logger.info(f"Found {len(voices)} available voices")
                return voices
            else:
                self.logger.error(f"Failed to get voices: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting available voices: {e}")
            return []
    
    def set_voice(self, voice: str) -> bool:
        """
        Set the voice to use for speech.
        
        Args:
            voice: Name of the voice to use
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if voice is available
            available_voices = self.get_available_voices()
            
            if voice not in available_voices:
                self.logger.error(f"Voice {voice} not found in available voices")
                return False
            
            # Update voice
            old_voice = self.voice
            self.voice = voice
            
            self.logger.info(f"Successfully switched from {old_voice} to {voice}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting voice: {e}")
            return False
    
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
            self.logger.info("Installing AllTalk TTS...")
            
            # Clone AllTalk repository
            install_cmd = [
                "git", "clone", 
                "https://github.com/erew123/alltalk_tts.git"
            ]
            
            result = subprocess.run(install_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.alltalk_path = "alltalk_tts"
                self.alltalk_installed = True
                self.logger.info("AllTalk TTS installed successfully")
                return True
            else:
                self.logger.error(f"Failed to install AllTalk TTS: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error installing AllTalk TTS: {e}")
            return False
    
    def start_alltalk_server(self) -> bool:
        """
        Start AllTalk TTS server.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.alltalk_installed:
                self.logger.error("AllTalk TTS not installed")
                return False
            
            # Check if server is already running
            if self.check_alltalk_running():
                self.logger.info("AllTalk TTS server is already running")
                return True
            
            # Start server
            start_cmd = [
                "python", "start_alltalk.py"
            ]
            
            # Change to AllTalk directory
            original_dir = os.getcwd()
            os.chdir(self.alltalk_path)
            
            # Start server in background
            process = subprocess.Popen(
                start_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server to start
            time.sleep(5)
            
            # Check if server started successfully
            if self.check_alltalk_running():
                self.logger.info("AllTalk TTS server started successfully")
                os.chdir(original_dir)
                return True
            else:
                self.logger.error("Failed to start AllTalk TTS server")
                os.chdir(original_dir)
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting AllTalk TTS server: {e}")
            return False
    
    def check_alltalk_running(self) -> bool:
        """
        Check if AllTalk TTS server is running.
        
        Returns:
            True if running, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/api/voices", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def generate_audio(self, text: str, test_mode: bool = False) -> Optional[str]:
        """
        Generate audio from text using AllTalk TTS.
        
        Args:
            text: Text to convert to speech
            test_mode: If True, use minimal text for testing
            
        Returns:
            Path to generated audio file or None if failed
        """
        try:
            # Prepare request payload
            payload = {
                "text": text[:100] if test_mode else text,
                "voice": self.voice,
                "speed": self.speed,
                "pitch": self.pitch,
                "volume": self.volume
            }
            
            self.logger.debug(f"Generating audio for text: {text[:50]}...")
            
            # Make request to AllTalk TTS
            response = requests.post(
                f"{self.base_url}/api/tts",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                # Save audio file
                audio_data = response.content
                audio_file = f"temp_audio/speech_{int(time.time())}.wav"
                
                # Ensure temp_audio directory exists
                os.makedirs("temp_audio", exist_ok=True)
                
                with open(audio_file, "wb") as f:
                    f.write(audio_data)
                
                self.logger.debug(f"Audio generated: {audio_file}")
                return audio_file
            else:
                self.logger.error(f"AllTalk TTS API error: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating audio: {e}")
            return None
    
    def _clean_text_for_tts(self, text: str) -> str:
        """
        Clean text for TTS processing.
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        # Remove markdown formatting
        import re
        
        # Remove markdown links
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        
        # Remove markdown bold/italic
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        
        # Remove code blocks
        text = re.sub(r'```[^`]*```', '', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def _play_audio_file(self, audio_file: str) -> bool:
        """
        Play audio file using pygame.
        
        Args:
            audio_file: Path to audio file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.pygame_available:
                self.logger.error("Pygame not available for audio playback")
                return False
            
            # Load and play audio
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            
            # Wait for playback to complete
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            # Clean up audio file
            try:
                os.remove(audio_file)
            except:
                pass
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error playing audio: {e}")
            return False
    
    def stop_speaking(self) -> bool:
        """
        Stop current speech playback.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.pygame_available:
                pygame.mixer.music.stop()
            
            self.is_speaking = False
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping speech: {e}")
            return False
    
    def cleanup(self) -> None:
        """Clean up AllTalk TTS resources."""
        self.stop_speaking()
        
        # Clean up temp audio files
        try:
            import glob
            for audio_file in glob.glob("temp_audio/*.wav"):
                try:
                    os.remove(audio_file)
                except:
                    pass
        except:
            pass
        
        super().cleanup()
