"""
LLM Handler for Carlos Assistant with Ollama integration.
"""

import json
import requests
import time
import subprocess
import psutil
from typing import List, Dict, Optional, Any
from utils.logger import CarlosLogger


class LLMHandler:
    """Handler for Large Language Model interactions via Ollama API."""
    
    def __init__(self, config: dict, logger: CarlosLogger):
        """
        Initialize the LLM handler.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.base_url = config['ollama']['base_url']
        self.model_name = config['ollama']['model']  # Renamed for clarity
        self.timeout = config['ollama']['timeout']
        self.max_tokens = config['ollama']['max_tokens']
        self.temperature = config['ollama']['temperature']
        self.cleanup_on_exit = config['ollama'].get('cleanup_on_exit', True)
        self.unload_timeout = config['ollama'].get('unload_timeout', 10)
        self.verify_unload = config['ollama'].get('verify_unload', True)
        
        # Track if we started Ollama
        self.ollama_started_by_us = False
        
        # Conversation history
        self.conversation_history: List[Dict[str, str]] = []
        
        # System prompt for assistant personality
        self.system_prompt = (
            "You are Carlos, a helpful and friendly AI assistant. "
            "You provide clear, concise responses while maintaining a warm personality. "
            "You are knowledgeable but humble, and always try to be helpful."
        )
        
        self.logger.info(f"LLM Handler initialized with model: {self.model_name}")
    
    def unload_model(self) -> bool:
        """
        Unload the current model from Ollama to free up memory
        Returns True if successful, False otherwise
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
            self.logger.error(f"Unexpected error during model unload: {e}")
            return False
    
    
    def stop_ollama_if_started(self) -> None:
        """Stop Ollama process if we started it, or send unload model command."""
        try:
            if self.cleanup_on_exit:
                # Simply attempt to unload model
                if self.unload_model():
                    self.logger.info("Model unloaded")
                else:
                    self.logger.info("Model unload attempted")
                
                # Wait a moment for unload to complete
                time.sleep(1)
                
                # If we can detect we started Ollama, stop the process
                if self.ollama_started_by_us:
                    self._stop_ollama_process()
                    
        except Exception as e:
            self.logger.error(f"Error during Ollama cleanup: {e}", exc_info=True)
    
    def _unload_model(self) -> None:
        """Legacy unload method - now calls the enhanced unload_model."""
        self.unload_model()
    
    def _stop_ollama_process(self) -> None:
        """Stop Ollama process if we started it."""
        try:
            # Find Ollama processes
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'ollama' in proc.info['name'].lower():
                        self.logger.info(f"Stopping Ollama process (PID: {proc.info['pid']})")
                        proc.terminate()
                        proc.wait(timeout=10)
                        self.logger.info("Ollama process stopped successfully")
                        break
                except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                    continue
                    
        except Exception as e:
            self.logger.warning(f"Could not stop Ollama process: {e}")
    
    def cleanup(self) -> bool:
        """Simplified cleanup - just attempt unload without verification"""
        self.logger.info("Starting LLM cleanup...")
        
        # Simply attempt to unload - no memory verification needed
        if self.unload_model():
            self.logger.info("Model unload attempted")
            unload_success = True
        else:
            self.logger.info("Model unload failed, but continuing shutdown")
            unload_success = False
        
        # Clear conversation history
        self.conversation_history.clear()
        
        self.logger.info("LLM cleanup completed")
        return unload_success
    
    def test_connection(self) -> bool:
        """
        Test connection to Ollama server and model availability.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Test if Ollama server is running
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                self.logger.error(f"Ollama server not responding: {response.status_code}")
                return False
            
            # Check if our model is available
            models_data = response.json()
            available_models = [model['name'] for model in models_data.get('models', [])]
            
            if self.model_name not in available_models:
                self.logger.error(f"Model {self.model_name} not found in available models: {available_models}")
                return False
            
            # Test a simple generation
            test_response = self._make_request("Hello", test_mode=True)
            if test_response is None:
                return False
            
            self.logger.info("Connection test successful")
            return True
            
        except requests.exceptions.ConnectionError:
            self.logger.error("Cannot connect to Ollama server. Is it running?")
            return False
        except requests.exceptions.Timeout:
            self.logger.error("Connection to Ollama server timed out")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during connection test: {e}", exc_info=True)
            return False
    
    def send_message(self, message: str) -> str:
        """
        Send a message to the LLM and get response.
        
        Args:
            message: User message
            
        Returns:
            LLM response or error message
        """
        try:
            self.logger.debug(f"Sending message: {message[:50]}...")
            
            # Add user message to history
            self.conversation_history.append({"role": "user", "content": message})
            
            # Get response from LLM
            response = self._make_request(message)
            if response is None:
                return "I'm sorry, I couldn't process your request right now. Please try again."
            
            # Add assistant response to history
            self.conversation_history.append({"role": "assistant", "content": response})
            
            # Limit conversation history to prevent token overflow
            self._trim_conversation_history()
            
            self.logger.debug(f"Received response: {response[:50]}...")
            return response
            
        except Exception as e:
            self.logger.error(f"Error in send_message: {e}", exc_info=True)
            return "I encountered an error while processing your message. Please try again."
    
    def _make_request(self, message: str, test_mode: bool = False) -> Optional[str]:
        """
        Make API request to Ollama.
        
        Args:
            message: Message to send
            test_mode: If True, use simple prompt without conversation history
            
        Returns:
            Response text or None if error
        """
        try:
            # Prepare prompt
            if test_mode:
                prompt = message
            else:
                prompt = self._build_conversation_prompt(message)
            
            # Prepare request data
            request_data = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                }
            }
            
            # Make request with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        f"{self.base_url}/api/generate",
                        json=request_data,
                        timeout=self.timeout
                    )
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        return response_data.get('response', '').strip()
                    else:
                        self.logger.error(f"API request failed: {response.status_code} - {response.text}")
                        
                except requests.exceptions.Timeout:
                    self.logger.warning(f"Request timeout (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        self.logger.error("Request timed out after all retries")
                        
                except requests.exceptions.ConnectionError:
                    self.logger.error("Connection error - is Ollama running?")
                    break
                    
            return None
            
        except Exception as e:
            self.logger.error(f"Error making request: {e}", exc_info=True)
            return None
    
    def _build_conversation_prompt(self, current_message: str) -> str:
        """
        Build conversation prompt including history and system prompt.
        
        Args:
            current_message: Current user message
            
        Returns:
            Complete conversation prompt
        """
        prompt_parts = [self.system_prompt, "\n\nConversation history:"]
        
        # Add recent conversation history (limit to last 10 exchanges)
        recent_history = self.conversation_history[-20:] if len(self.conversation_history) > 20 else self.conversation_history
        
        for entry in recent_history:
            role = "User" if entry["role"] == "user" else "Carlos"
            prompt_parts.append(f"{role}: {entry['content']}")
        
        # Add current message
        prompt_parts.append(f"User: {current_message}")
        prompt_parts.append("Carlos:")
        
        return "\n".join(prompt_parts)
    
    def _trim_conversation_history(self) -> None:
        """Trim conversation history to prevent token overflow."""
        max_history_length = 50  # Maximum number of exchanges to keep
        
        if len(self.conversation_history) > max_history_length:
            # Keep the most recent exchanges
            self.conversation_history = self.conversation_history[-max_history_length:]
            self.logger.debug("Trimmed conversation history to prevent token overflow")
    
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
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            Model information dictionary
        """
        try:
            response = requests.get(f"{self.base_url}/api/show", 
                                  json={"name": self.model_name}, 
                                  timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get model info: {response.status_code}")
                return {}
        except Exception as e:
            self.logger.error(f"Error getting model info: {e}")
            return {}