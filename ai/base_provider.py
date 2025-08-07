"""
Base AI Provider Abstract Class
Defines the interface for all AI providers in Carlos
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from utils.logger import CarlosLogger


class BaseAIProvider(ABC):
    """Abstract base class for AI providers."""
    
    def __init__(self, config: Dict[str, Any], logger: CarlosLogger):
        """
        Initialize the AI provider.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.conversation_history: List[Dict[str, str]] = []
        self.model_name: Optional[str] = None
        self.is_connected = False
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test connection to the AI provider.
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def send_message(self, message: str, context: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Send a message to the AI provider and get response.
        
        Args:
            message: User message
            context: Optional conversation context
            
        Returns:
            AI response text
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        Get list of available models.
        
        Returns:
            List of model names
        """
        pass
    
    @abstractmethod
    def switch_model(self, model_name: str) -> bool:
        """
        Switch to a different model.
        
        Args:
            model_name: Name of the model to switch to
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    def clear_conversation(self) -> None:
        """Clear conversation history."""
        self.conversation_history.clear()
        self.logger.info("Conversation history cleared")
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """
        Get conversation history.
        
        Returns:
            List of conversation entries
        """
        return self.conversation_history.copy()
    
    def add_to_history(self, role: str, content: str) -> None:
        """
        Add message to conversation history.
        
        Args:
            role: 'user' or 'assistant'
            content: Message content
        """
        self.conversation_history.append({
            "role": role,
            "content": content
        })
    
    def get_model_name(self) -> Optional[str]:
        """
        Get current model name.
        
        Returns:
            Current model name or None
        """
        return self.model_name
    
    def is_provider_connected(self) -> bool:
        """
        Check if provider is connected.
        
        Returns:
            True if connected, False otherwise
        """
        return self.is_connected
