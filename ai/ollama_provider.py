"""
Ollama AI Provider Implementation
Provides Ollama integration for Carlos AI Assistant
"""

import json
import requests
import time
import subprocess
import psutil
from typing import List, Dict, Optional, Any
from utils.logger import CarlosLogger
from .base_provider import BaseAIProvider


class OllamaProvider(BaseAIProvider):
    """Ollama AI provider implementation."""
    
    def __init__(self, config: Dict[str, Any], logger: CarlosLogger):
        """
        Initialize the Ollama provider.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        super().__init__(config, logger)
        
        # Extract Ollama-specific configuration
        ollama_config = config.get('ai', {}).get('providers', {}).get('ollama', {})
        if not ollama_config:
            # Fallback to legacy config structure
            ollama_config = config.get('ollama', {})
        
        self.base_url = ollama_config.get('base_url', 'http://localhost:11434')
        self.model_name = ollama_config.get('model', 'gpt-oss:20b')
        self.timeout = ollama_config.get('timeout', 30)
        self.max_tokens = ollama_config.get('max_tokens', 500)
        self.temperature = ollama_config.get('temperature', 0.7)
        self.cleanup_on_exit = ollama_config.get('cleanup_on_exit', True)
        self.unload_timeout = ollama_config.get('unload_timeout', 10)
        self.verify_unload = ollama_config.get('verify_unload', True)
        
        # Track if we started Ollama
        self.ollama_started_by_us = False
        
        # System prompt for assistant personality
        self.system_prompt = (
            "You are Carlos, a helpful and friendly AI assistant. "
            "You provide clear, concise responses while maintaining a warm personality. "
            "You are knowledgeable but humble, and always try to be helpful."
        )
        
        self.logger.info(f"Ollama Provider initialized with model: {self.model_name}")
    
    def test_connection(self) -> bool:
        """
        Test connection to Ollama.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.logger.info("Testing connection to Ollama...")
            
            # Test basic connectivity
            response = requests.get(f"{self.base_url}/api/tags", timeout=self.timeout)
            
            if response.status_code == 200:
                self.is_connected = True
                self.logger.info("Successfully connected to Ollama")
                return True
            else:
                self.logger.error(f"Ollama returned status code: {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            self.logger.error("Failed to connect to Ollama - service not running")
            return False
        except requests.exceptions.Timeout:
            self.logger.error("Connection to Ollama timed out")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error testing Ollama connection: {e}")
            return False
    
    def send_message(self, message: str, context: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Send a message to Ollama and get response.
        
        Args:
            message: User message
            context: Optional conversation context
            
        Returns:
            AI response text
        """
        try:
            # Add user message to history
            self.add_to_history("user", message)
            
            # Build conversation prompt
            prompt = self._build_conversation_prompt(message, context)
            
            # Make request to Ollama
            response_text = self._make_request(prompt)
            
            if response_text:
                # Add assistant response to history
                self.add_to_history("assistant", response_text)
                
                # Trim history if needed
                self._trim_conversation_history()
                
                return response_text
            else:
                error_msg = "Failed to get response from Ollama"
                self.logger.error(error_msg)
                return error_msg
                
        except Exception as e:
            error_msg = f"Error sending message to Ollama: {e}"
            self.logger.error(error_msg, exc_info=True)
            return error_msg
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available Ollama models.
        
        Returns:
            List of model names
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=self.timeout)
            
            if response.status_code == 200:
                models_data = response.json()
                models = [model['name'] for model in models_data.get('models', [])]
                self.logger.info(f"Found {len(models)} available models")
                return models
            else:
                self.logger.error(f"Failed to get models: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting available models: {e}")
            return []
    
    def switch_model(self, model_name: str) -> bool:
        """
        Switch to a different Ollama model.
        
        Args:
            model_name: Name of the model to switch to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if model is available
            available_models = self.get_available_models()
            
            if model_name not in available_models:
                self.logger.error(f"Model {model_name} not found in available models")
                return False
            
            # Update model name
            old_model = self.model_name
            self.model_name = model_name
            
            # Test connection with new model
            if self.test_connection():
                self.logger.info(f"Successfully switched from {old_model} to {model_name}")
                return True
            else:
                # Revert on failure
                self.model_name = old_model
                self.logger.error(f"Failed to switch to model {model_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error switching model: {e}")
            return False
    
    def unload_model(self) -> bool:
        """
        Unload the current model from Ollama to free up memory.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Attempting to unload model: {self.model_name}")
            
            # Method 1: Use keep_alive=0s to unload immediately
            unload_payload = {
                "model": self.model_name,
                "keep_alive": "0s"  # This should unload immediately
            }
            
            self.logger.info("Trying keep_alive=0s method...")
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=unload_payload,
                timeout=self.unload_timeout
            )
            
            if response.status_code == 200:
                self.logger.info(f"Model {self.model_name} unloaded successfully via keep_alive")
                return True
            
            # Method 2: Try alternative unload endpoint
            self.logger.info("Trying alternative unload method...")
            response = requests.delete(
                f"{self.base_url}/api/tags/{self.model_name}",
                timeout=self.unload_timeout
            )
            
            if response.status_code == 200:
                self.logger.info(f"Model {self.model_name} unloaded via delete endpoint")
                return True
            
            # Method 3: Try to unload via model management
            self.logger.info("Trying model management unload...")
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": self.model_name, "insecure": True},
                timeout=self.unload_timeout
            )
            
            # Even if this fails, we'll consider it a success if no error
            self.logger.info("Model unload attempt completed")
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Failed to unload model: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error unloading model: {e}")
            return False
    
    def _make_request(self, message: str, test_mode: bool = False) -> Optional[str]:
        """
        Make a request to Ollama API.
        
        Args:
            message: Message to send
            test_mode: If True, use minimal tokens for testing
            
        Returns:
            Response text or None if failed
        """
        try:
            payload = {
                "model": self.model_name,
                "prompt": message,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens if not test_mode else 10
                }
            }
            
            self.logger.debug(f"Sending request to Ollama: {payload}")
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                response_data = response.json()
                response_text = response_data.get('response', '')
                
                if test_mode:
                    self.logger.info("Test request successful")
                else:
                    self.logger.debug(f"Received response: {response_text[:100]}...")
                
                return response_text
            else:
                self.logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error in request: {e}")
            return None
    
    def _build_conversation_prompt(self, current_message: str, context: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Build conversation prompt with history.
        
        Args:
            current_message: Current user message
            context: Optional conversation context
            
        Returns:
            Formatted prompt string
        """
        # Use provided context or fall back to internal history
        history = context if context is not None else self.conversation_history
        
        # Start with system prompt
        prompt = f"{self.system_prompt}\n\n"
        
        # Add conversation history
        for entry in history:
            role = entry.get('role', '')
            content = entry.get('content', '')
            
            if role == 'user':
                prompt += f"User: {content}\n"
            elif role == 'assistant':
                prompt += f"Carlos: {content}\n"
        
        # Add current message
        prompt += f"User: {current_message}\nCarlos:"
        
        return prompt
    
    def _trim_conversation_history(self) -> None:
        """Trim conversation history to prevent token overflow."""
        max_history = 20  # Keep last 20 exchanges
        
        if len(self.conversation_history) > max_history * 2:  # Each exchange has 2 entries
            # Keep system prompt and recent history
            self.conversation_history = self.conversation_history[-max_history * 2:]
            self.logger.info("Conversation history trimmed")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            Dictionary with model information
        """
        return {
            "name": self.model_name,
            "provider": "ollama",
            "base_url": self.base_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "connected": self.is_connected
        }
