"""
Base TTS Provider Abstract Class
Defines the interface for all TTS providers in Carlos
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from utils.logger import CarlosLogger


class BaseTTS(ABC):
    """Abstract base class for TTS providers."""
    
    def __init__(self, config: Dict[str, Any], logger: CarlosLogger):
        """
        Initialize the TTS provider.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.voice: Optional[str] = None
        self.speed: float = 1.0
        self.pitch: float = 1.0
        self.volume: float = 0.8
        self.is_connected = False
        self.is_speaking = False
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test connection to the TTS provider.
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def speak(self, text: str) -> bool:
        """
        Convert text to speech and play it.
        
        Args:
            text: Text to convert to speech
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_available_voices(self) -> List[str]:
        """
        Get list of available voices.
        
        Returns:
            List of voice names
        """
        pass
    
    @abstractmethod
    def set_voice(self, voice: str) -> bool:
        """
        Set the voice to use for speech.
        
        Args:
            voice: Name of the voice to use
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    def stop_speaking(self) -> bool:
        """
        Stop current speech playback.
        
        Returns:
            True if successful, False otherwise
        """
        self.is_speaking = False
        return True
    
    def cleanup(self) -> None:
        """Clean up TTS resources."""
        self.stop_speaking()
        self.logger.info("TTS cleanup completed")
    
    def set_speed(self, speed: float) -> bool:
        """
        Set speech speed.
        
        Args:
            speed: Speed multiplier (0.5 to 2.0)
            
        Returns:
            True if successful, False otherwise
        """
        if 0.5 <= speed <= 2.0:
            self.speed = speed
            return True
        return False
    
    def set_pitch(self, pitch: float) -> bool:
        """
        Set speech pitch.
        
        Args:
            pitch: Pitch multiplier (0.5 to 2.0)
            
        Returns:
            True if successful, False otherwise
        """
        if 0.5 <= pitch <= 2.0:
            self.pitch = pitch
            return True
        return False
    
    def set_volume(self, volume: float) -> bool:
        """
        Set speech volume.
        
        Args:
            volume: Volume level (0.0 to 1.0)
            
        Returns:
            True if successful, False otherwise
        """
        if 0.0 <= volume <= 1.0:
            self.volume = volume
            return True
        return False
    
    def get_current_voice(self) -> Optional[str]:
        """
        Get current voice name.
        
        Returns:
            Current voice name or None
        """
        return self.voice
    
    def is_tts_connected(self) -> bool:
        """
        Check if TTS provider is connected.
        
        Returns:
            True if connected, False otherwise
        """
        return self.is_connected
    
    def is_currently_speaking(self) -> bool:
        """
        Check if currently speaking.
        
        Returns:
            True if speaking, False otherwise
        """
        return self.is_speaking
