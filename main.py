"""
Carlos Assistant - Phase 2: TTS Integration
A modular voice AI assistant with text-based conversation and TTS output.
"""

import os
import sys
import yaml
import signal
from typing import Dict, Any, Optional
from utils.logger import get_logger, CarlosLogger
from modules.llm_handler import LLMHandler
from modules.tts_handler import TTSHandler
from modules.service_manager import ServiceManager


class CarlosAssistant:
    """Main Carlos Assistant application."""
    
    def __init__(self):
        """Initialize the assistant."""
        self.config: Optional[Dict[str, Any]] = None
        self.logger: Optional[CarlosLogger] = None
        self.llm_handler: Optional[LLMHandler] = None
        self.tts_handler: Optional[TTSHandler] = None
        self.service_manager: Optional[ServiceManager] = None
        self.tts_enabled = True  # Can be toggled by user
        self.running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum: int, frame) -> None:
        """Fixed shutdown sequence - unload model before services shut down"""
        if self.logger:
            self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        
        print(f"\n[INFO] Received signal {signum}, shutting down gracefully...")
        
        # STEP 1: Stop conversation loop
        self.running = False
        
        # STEP 2: Unload model BEFORE services shut down
        if self.llm_handler:
            print("[INFO] Unloading model from memory...")
            if self.logger:
                self.logger.info("Attempting to unload model before shutdown")
            self.llm_handler.unload_model()  # Just attempt unload, don't verify
            print("[OK] Model unload attempted")
        
        # STEP 3: Clean up TTS resources
        if self.tts_handler:
            print("[INFO] Cleaning up TTS resources...")
            self.tts_handler.cleanup()
            print("[OK] TTS cleanup completed")
        
        # STEP 4: Clean shutdown message
        print("\n[INFO] Carlos Assistant shutting down...")
        if self.logger:
            self.logger.info("Carlos Assistant shutting down...")
        
        # STEP 5: Exit cleanly
        sys.exit(0)
    
    def load_configuration(self) -> bool:
        """
        Load configuration from config.yaml.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            config_path = "config.yaml"
            if not os.path.exists(config_path):
                print(f"[ERROR] Configuration file not found: {config_path}")
                return False
            
            with open(config_path, 'r', encoding='utf-8') as file:
                self.config = yaml.safe_load(file)
            
            # Validate required configuration sections
            required_sections = ['ollama', 'general', 'logging']
            for section in required_sections:
                if section not in self.config:
                    print(f"[ERROR] Missing required configuration section: {section}")
                    return False
            
            # TTS section is optional but recommended
            if 'alltalk_tts' not in self.config:
                print("[WARNING] No TTS configuration found - TTS will be disabled")
                self.tts_enabled = False
            
            print("[OK] Configuration loaded successfully")
            return True
            
        except yaml.YAMLError as e:
            print(f"[ERROR] Error parsing configuration file: {e}")
            return False
        except Exception as e:
            print(f"[ERROR] Error loading configuration: {e}")
            return False
    
    def initialize_logger(self) -> bool:
        """
        Initialize the logging system.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger = get_logger("Carlos", self.config)
            self.logger.info("Carlos Assistant starting up...")
            print("[OK] Logger initialized successfully")
            return True
        except Exception as e:
            print(f"[ERROR] Error initializing logger: {e}")
            return False
    
    def initialize_service_manager(self) -> bool:
        """
        Initialize the service manager.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.service_manager = ServiceManager(self.logger)
            print("[OK] Service Manager initialized successfully")
            return True
        except Exception as e:
            print(f"[ERROR] Error initializing service manager: {e}")
            return False
    
    def initialize_tts_handler(self) -> bool:
        """
        Initialize the TTS handler.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.tts_enabled or 'alltalk_tts' not in self.config:
            print("[INFO] TTS disabled - skipping TTS handler initialization")
            return True
        
        try:
            self.tts_handler = TTSHandler(self.config, self.logger)
            print("[OK] TTS Handler initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error initializing TTS handler: {e}", exc_info=True)
            print(f"[WARNING] Error initializing TTS handler: {e}")
            print("[INFO] Continuing without TTS functionality...")
            self.tts_enabled = False
            return True  # Don't fail startup for TTS issues
    
    def setup_alltalk_tts(self) -> bool:
        """
        Setup AllTalk TTS installation and server.
        
        Returns:
            True if successful or not needed, False if critical error
        """
        if not self.tts_enabled or not self.tts_handler:
            return True
        
        try:
            print("[INFO] Checking AllTalk TTS installation...")
            
            # Check if AllTalk is installed
            if not self.tts_handler.check_alltalk_installation():
                print("[INFO] AllTalk TTS not found. Installing...")
                if not self.tts_handler.install_alltalk():
                    print("[WARNING] Failed to install AllTalk TTS - continuing without TTS")
                    self.tts_enabled = False
                    return True
                print("[OK] AllTalk TTS installed successfully")
            
            # Start AllTalk server if needed
            print("[INFO] Starting AllTalk TTS server...")
            if not self.tts_handler.start_alltalk_server():
                print("[WARNING] Failed to start AllTalk server - continuing without TTS")
                self.tts_enabled = False
                return True
            
            print("[OK] AllTalk TTS server is running")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting up AllTalk TTS: {e}")
            print(f"[WARNING] Error setting up AllTalk TTS: {e}")
            print("[INFO] Continuing without TTS functionality...")
            self.tts_enabled = False
            return True
    
    def test_tts_connection(self) -> bool:
        """
        Test connection to AllTalk TTS.
        
        Returns:
            True if successful or not needed, False if critical error
        """
        if not self.tts_enabled or not self.tts_handler:
            return True
        
        print("[INFO] Testing connection to AllTalk TTS...")
        
        if not self.tts_handler.test_connection():
            print("[WARNING] Failed to connect to AllTalk TTS - continuing without TTS")
            self.tts_enabled = False
            return True
        
        print("[OK] Connected to AllTalk TTS successfully")
        return True
    
    def initialize_llm_handler(self) -> bool:
        """
        Initialize the LLM handler.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.llm_handler = LLMHandler(self.config, self.logger)
            print("[OK] LLM Handler initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error initializing LLM handler: {e}", exc_info=True)
            print(f"[ERROR] Error initializing LLM handler: {e}")
            return False
    
    def test_ollama_connection(self) -> bool:
        """
        Test connection to Ollama.
        
        Returns:
            True if successful, False otherwise
        """
        print("[INFO] Testing connection to Ollama...")
        
        if not self.llm_handler.test_connection():
            print("[ERROR] Failed to connect to Ollama")
            print("\nTroubleshooting steps:")
            print("1. Make sure Ollama is installed and running")
            print("2. Verify the model 'gpt-oss:20b' is available")
            print("3. Check if Ollama is running on http://localhost:11434")
            print("4. Try running: ollama list")
            return False
        
        print("[OK] Connected to Ollama successfully")
        return True
    
    def startup(self) -> bool:
        """
        Perform startup sequence.
        
        Returns:
            True if successful, False otherwise
        """
        print(">>> Carlos AI Assistant v1.0 - Phase 2")
        print("=" * 40)
        
        # Load configuration
        if not self.load_configuration():
            return False
        
        # Initialize logger
        if not self.initialize_logger():
            return False
        
        # Initialize service manager
        if not self.initialize_service_manager():
            return False
        
        # Check if setup was completed
        if not self.service_manager.check_setup_completion():
            print("❌ Setup not completed!")
            print("Please run: python setup.py")
            print("\nThis will install all required dependencies and configure Carlos.")
            return False
        
        # Smart service management
        print("[INFO] Checking and starting services...")
        service_status = self.service_manager.ensure_all_services()
        
        if not service_status['ollama']:
            print("❌ Cannot start Ollama. Please run setup.py again.")
            print("💡 Make sure Ollama is installed from: https://ollama.ai/")
            return False
        
        if not service_status['alltalk']:
            print("⚠️ AllTalk TTS unavailable - continuing in text-only mode")
            self.tts_enabled = False
        
        # Initialize LLM handler
        if not self.initialize_llm_handler():
            return False
        
        # Initialize TTS handler
        if not self.initialize_tts_handler():
            return False
        
        # Test Ollama connection
        if not self.test_ollama_connection():
            return False
        
        # Test TTS connection (only if enabled)
        if self.tts_enabled and not self.test_tts_connection():
            print("⚠️ TTS connection failed - continuing in text-only mode")
            self.tts_enabled = False
        
        # Show TTS status
        tts_status = "✅ Enabled" if self.tts_enabled else "❌ Disabled"
        voice_info = f" | Voice: {self.tts_handler.voice}" if self.tts_enabled and self.tts_handler else ""
        volume_info = f" | Volume: {int(self.tts_handler.volume * 100)}%" if self.tts_enabled and self.tts_handler else ""
        
        print(f"TTS: {tts_status}{voice_info}{volume_info}")
        print("=" * 40)
        print("[SUCCESS] Carlos is ready to chat with voice!")
        return True
    
    def conversation_loop(self) -> None:
        """Main conversation loop."""
        self.running = True
        
        print("\nType your message (or 'quit', 'exit', 'bye' to exit)")
        print("Commands: 'clear', 'history', 'mute', 'unmute', 'voices', 'voice <name>', 'stop'")
        
        # Show current TTS status
        tts_status = "✅ Enabled" if self.tts_enabled else "❌ Disabled"
        voice_info = f" | Voice: {self.tts_handler.voice}" if self.tts_enabled and self.tts_handler else ""
        volume_info = f" | Volume: {int(self.tts_handler.volume * 100)}%" if self.tts_enabled and self.tts_handler else ""
        print(f"TTS: {tts_status}{voice_info}{volume_info}")
        print("-" * 50)
        
        while self.running:
            try:
                # Get user input
                user_input = input("\nYou: ").strip()
                
                if not user_input:
                    continue
                
                # Handle exit commands
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("\n[INFO] Shutting down Carlos...")
                    self.logger.info("User requested shutdown")
                    
                    # Stop any current TTS
                    if self.tts_handler:
                        self.tts_handler.stop_speaking()
                    
                    # Unload model while Ollama is still running
                    print("[INFO] Unloading model from memory...")
                    self.llm_handler.unload_model()
                    print("[OK] Model unload attempted")
                    
                    # Clean up TTS
                    if self.tts_handler:
                        print("[INFO] Cleaning up TTS resources...")
                        self.tts_handler.cleanup()
                        print("[OK] TTS cleanup completed")
                    
                    print("[INFO] Goodbye!")
                    self.logger.info("Carlos Assistant shutting down normally")
                    break
                
                # Handle special commands
                if user_input.lower() == 'clear':
                    self.llm_handler.clear_conversation()
                    print("[INFO] Conversation history cleared")
                    continue
                
                if user_input.lower() == 'history':
                    self._show_conversation_history()
                    continue
                
                
                # TTS Commands
                if user_input.lower() == 'mute':
                    self.tts_enabled = False
                    if self.tts_handler:
                        self.tts_handler.stop_speaking()
                    print("[INFO] TTS muted - responses will be text only")
                    continue
                
                if user_input.lower() == 'unmute':
                    if self.tts_handler:
                        self.tts_enabled = True
                        print("[INFO] TTS enabled - responses will include speech")
                    else:
                        print("[WARNING] TTS handler not available - cannot unmute")
                    continue
                
                if user_input.lower() == 'stop':
                    if self.tts_handler:
                        self.tts_handler.stop_speaking()
                        print("[INFO] Speech stopped")
                    else:
                        print("[INFO] No TTS available to stop")
                    continue
                
                if user_input.lower() == 'voices':
                    if self.tts_handler:
                        voices = self.tts_handler.get_available_voices()
                        if voices:
                            print(f"\n[INFO] Available voices ({len(voices)}):")
                            for i, voice in enumerate(voices, 1):
                                current = " (current)" if voice == self.tts_handler.voice else ""
                                print(f"  {i}. {voice}{current}")
                        else:
                            print("[INFO] No voices available or unable to fetch voice list")
                    else:
                        print("[WARNING] TTS handler not available")
                    continue
                
                if user_input.lower().startswith('voice '):
                    voice_name = user_input[6:].strip()  # Remove 'voice ' prefix
                    if self.tts_handler and voice_name:
                        if self.tts_handler.set_voice(voice_name):
                            print(f"[OK] Voice changed to: {voice_name}")
                        else:
                            print(f"[ERROR] Failed to change voice to: {voice_name}")
                            voices = self.tts_handler.get_available_voices()
                            if voices:
                                print(f"Available voices: {', '.join(voices)}")
                    else:
                        if not self.tts_handler:
                            print("[WARNING] TTS handler not available")
                        else:
                            print("[ERROR] Please specify a voice name (e.g., 'voice default')")
                    continue
                
                # Send message to LLM
                print("[INFO] Carlos is thinking...")
                response = self.llm_handler.send_message(user_input)
                print(f"\nCarlos: {response}")
                
                # Speak the response if TTS is enabled
                if self.tts_enabled and self.tts_handler:
                    print("[🔊] Speaking...")
                    if not self.tts_handler.speak(response):
                        print("[WARNING] Failed to generate speech - continuing with text only")
                
            except (EOFError, KeyboardInterrupt):
                print("\n\n[INFO] Interrupted by user, shutting down...")
                self.logger.info("User interrupted with Ctrl+C")
                
                # Unload model before shutdown
                if self.llm_handler:
                    print("[INFO] Unloading model from memory...")
                    self.llm_handler.unload_model()
                    print("[OK] Model unload attempted")
                
                print("[INFO] Goodbye!")
                break
            except Exception as e:
                self.logger.error(f"Error in conversation loop: {e}", exc_info=True)
                print(f"\n[ERROR] An error occurred: {e}")
                print("Please try again or restart the application.")
    
    def _show_conversation_history(self) -> None:
        """Show conversation history."""
        history = self.llm_handler.get_conversation_history()
        
        if not history:
            print("[INFO] No conversation history yet")
            return
        
        print("\n[INFO] Conversation History:")
        print("-" * 30)
        
        for i, entry in enumerate(history, 1):
            role = "You" if entry["role"] == "user" else "Carlos"
            content = entry["content"]
            if len(content) > 100:
                content = content[:97] + "..."
            print(f"{i:2d}. {role}: {content}")
        
        print("-" * 30)
    
    def shutdown(self) -> None:
        """Simplified shutdown that ensures proper cleanup order."""
        self.running = False
        if self.logger:
            self.logger.info("Carlos Assistant shutting down...")
        print("\n[INFO] Shutting down Carlos Assistant...")
        
        # Unload model first while services are still running
        if self.llm_handler:
            print("[INFO] Unloading model from memory...")
            self.llm_handler.unload_model()
            print("[OK] Model unload attempted")
        
        # Clean up TTS resources
        if self.tts_handler:
            print("[INFO] Cleaning up TTS resources...")
            self.tts_handler.cleanup()
            print("[OK] TTS cleanup completed")
    
    def run(self) -> int:
        """
        Run the assistant.
        
        Returns:
            Exit code (0 for success, 1 for error)
        """
        try:
            # Startup sequence
            if not self.startup():
                return 1
            
            # Main conversation loop
            self.conversation_loop()
            
            # Graceful shutdown
            self.shutdown()
            return 0
            
        except Exception as e:
            if self.logger:
                self.logger.critical(f"Unexpected error: {e}", exc_info=True)
            else:
                print(f"[ERROR] Critical error: {e}")
            return 1


def main() -> int:
    """Main entry point."""
    assistant = CarlosAssistant()
    return assistant.run()


if __name__ == "__main__":
    sys.exit(main())