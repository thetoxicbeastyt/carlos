#!/usr/bin/env python3
"""
Carlos AI Assistant - Main Entry Point
Modular voice AI assistant with extensible providers
"""

import os
import sys
import yaml
import signal
from typing import Dict, Any, Optional
from utils.logger import get_logger, CarlosLogger
from core.assistant import CarlosAssistant


def main() -> int:
    """Main entry point for Carlos AI Assistant."""
    try:
        # Create and run the assistant
        assistant = CarlosAssistant()
        return assistant.run()
        
    except KeyboardInterrupt:
        print("\n[INFO] Carlos interrupted by user")
        return 0
    except Exception as e:
        print(f"[ERROR] Critical error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
