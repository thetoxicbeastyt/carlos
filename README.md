# Carlos Assistant - Phase 2: TTS Integration

A modular voice AI assistant with text-based conversation and Text-to-Speech output using Ollama and AllTalk TTS integration.

## 🚀 Quick Start

### First Time Setup
```bash
# Run the comprehensive setup script
python setup.py
```

### Daily Usage
```bash
# Start Carlos Assistant
python main.py

# Or use the convenient startup scripts:
# Windows: double-click start_carlos.bat
# Unix: ./start_carlos.sh
```

## 🚀 Features

- **Text-based conversation** with AI assistant "Carlos"
- **Text-to-Speech (TTS)** output using AllTalk TTS
- **Ollama integration** with gpt-oss:20b model
- **Conversation history** management with context preservation
- **Voice control commands** (mute, unmute, voice selection, stop)
- **Automated AllTalk installation** and setup
- **Colored logging** with file rotation
- **Graceful error handling** for all failure scenarios
- **Configuration management** via YAML
- **Clean shutdown** with signal handling

## 📋 Prerequisites

The setup script will automatically install and configure all dependencies, but you can also install manually:

### 1. Install Ollama
Download and install Ollama from [ollama.ai](https://ollama.ai/)

### 2. Pull the Required Model
```bash
ollama pull gpt-oss:20b
```

### 3. Verify Ollama is Running
```bash
ollama list
# Should show gpt-oss:20b in the list
```

### 4. Audio System Requirements
Ensure you have:
- **Speakers or headphones** for TTS output
- **Audio drivers** properly installed
- **Python audio support** (pygame will be installed automatically)

## 🛠️ Installation

### Automated Setup (Recommended)
```bash
# Run the comprehensive setup script
python setup.py
```

This will automatically:
- ✅ Check Python version (3.8+)
- ✅ Install Ollama via Chocolatey (Windows) or Homebrew (macOS)
- ✅ Download the gpt-oss:20b model
- ✅ Clone and configure AllTalk TTS
- ✅ Install all Python dependencies
- ✅ Test all components
- ✅ Create convenient startup scripts

### Manual Installation
If you prefer to install manually:

#### 1. Clone/Download the Project
```bash
git clone <repository-url>
cd carlos
```

#### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

#### 3. AllTalk TTS Installation
The assistant will automatically install and configure AllTalk TTS on first run. You can also install manually:

```bash
# AllTalk will be cloned and installed automatically
# Or install manually:
git clone https://github.com/erew123/alltalk_tts.git
cd alltalk_tts
pip install -r requirements.txt
```

#### 4. Verify Configuration
The `config.yaml` file should already be configured with appropriate defaults:
- Ollama URL: http://localhost:11434
- Model: gpt-oss:20b
- AllTalk TTS URL: http://localhost:7851
- TTS enabled by default
- Logging: logs/carlos.log with rotation

## 🎯 Usage

### Starting the Assistant
```bash
# After running setup.py
python main.py

# Or use the convenient startup scripts:
# Windows: double-click start_carlos.bat
# Unix: ./start_carlos.sh
```

### Expected Startup Output
```
>>> Carlos AI Assistant v1.0 - Phase 2
========================================
[OK] Configuration loaded successfully
[OK] Logger initialized successfully
[OK] LLM Handler initialized successfully
[OK] TTS Handler initialized successfully
[INFO] Checking AllTalk TTS installation...
[OK] AllTalk TTS server is running
[INFO] Testing connection to Ollama...
[OK] Connected to Ollama successfully
[INFO] Testing connection to AllTalk TTS...
[OK] Connected to AllTalk TTS successfully
TTS: ✅ Enabled | Voice: default | Volume: 80%
========================================
[SUCCESS] Carlos is ready to chat with voice!

Type your message (or 'quit', 'exit', 'bye' to exit)
Commands: 'clear', 'history', 'mute', 'unmute', 'voices', 'voice <name>', 'stop'
TTS: ✅ Enabled | Voice: default | Volume: 80%
--------------------------------------------------

You: 
```

### Interactive Commands

#### Basic Commands
- **Regular chat**: Type any message and press Enter
- **Exit**: Type `quit`, `exit`, or `bye`
- **Clear history**: Type `clear`
- **Show history**: Type `history`
- **Keyboard interrupt**: Press Ctrl+C for graceful shutdown

#### TTS Commands
- **Mute TTS**: Type `mute` - disables speech output, keeps text
- **Unmute TTS**: Type `unmute` - re-enables speech output
- **Stop speech**: Type `stop` - stops current speech immediately
- **List voices**: Type `voices` - shows available TTS voices
- **Change voice**: Type `voice <name>` - changes TTS voice (e.g., `voice female`)

#### Special Commands
- **Memory check**: Type `memory` - shows Ollama memory usage
- **Manual unload**: Type `unload` - manually unloads the model

### Example Conversation
```
You: Hello, how are you today?
[INFO] Carlos is thinking...

Carlos: Hello! I'm doing well, thank you for asking. I'm Carlos, your AI assistant, and I'm here to help you with whatever you need. How are you doing today?
[🔊] Speaking...

You: Tell me a joke
[INFO] Carlos is thinking...

Carlos: Sure! Here's one for you:

Why don't scientists trust atoms?
Because they make up everything! 😄

Would you like to hear another one, or is there something else I can help you with?
[🔊] Speaking...

You: mute
[INFO] TTS muted - responses will be text only

You: voices
[INFO] Available voices (3):
  1. default (current)
  2. male
  3. female

You: voice female
[OK] Voice changed to: female

You: unmute
[INFO] TTS enabled - responses will include speech
```

## ⚙️ Configuration

### config.yaml Structure
```yaml
ollama:
  base_url: "http://localhost:11434"  # Ollama server URL
  model: "gpt-oss:20b"               # Model name
  timeout: 30                        # Request timeout (seconds)
  max_tokens: 500                    # Maximum response tokens
  temperature: 0.7                   # Response creativity (0-1)
  cleanup_on_exit: true              # Unload model on exit

alltalk_tts:
  base_url: "http://localhost:7851"  # AllTalk TTS server URL
  enabled: true                      # Enable/disable TTS
  voice: "default"                   # Default voice name
  speed: 1.0                         # Speech speed (0.5-2.0)
  pitch: 1.0                         # Speech pitch (0.5-2.0)
  volume: 0.8                        # Speech volume (0.0-1.0)
  timeout: 10                        # TTS request timeout
  auto_play: true                    # Auto-play generated speech

general:
  assistant_name: "Carlos"           # Assistant name
  log_level: "INFO"                  # DEBUG, INFO, WARNING, ERROR
  response_timeout: 10               # Response timeout (seconds)
  max_response_length: 1000          # Maximum response length
  text_output: true                  # Always show text responses

logging:
  log_file: "logs/carlos.log"        # Log file path
  max_log_size: "10MB"              # Log file size before rotation
  backup_count: 5                    # Number of backup log files
```

### Customizing the Assistant
To modify Carlos's personality, edit the `system_prompt` in `modules/llm_handler.py`:

```python
self.system_prompt = (
    "You are Carlos, a helpful and friendly AI assistant. "
    "You provide clear, concise responses while maintaining a warm personality. "
    "You are knowledgeable but humble, and always try to be helpful."
)
```

## 🔧 Troubleshooting

### Setup Issues

#### ❌ "Setup not completed!"
**Solution:**
1. Run the setup script: `python setup.py`
2. Follow the prompts and wait for completion
3. Try running Carlos again: `python main.py`

#### ❌ "Ollama installation failed"
**Solution:**
1. Install Ollama manually from [ollama.ai](https://ollama.ai/)
2. Run setup again: `python setup.py`
3. Or try running as administrator (Windows) or with sudo (Unix)

#### ❌ "AllTalk TTS installation failed"
**Solution:**
1. Check internet connection for GitHub access
2. Ensure Git is installed: `git --version`
3. Try manual installation:
   ```bash
   git clone https://github.com/erew123/alltalk_tts.git
   cd alltalk_tts
   pip install -r requirements.txt
   ```

### Common Issues

#### ❌ "Cannot connect to Ollama server"
**Solution:**
1. Start Ollama service: `ollama serve`
2. Verify it's running: `curl http://localhost:11434/api/tags`
3. Check if port 11434 is available

#### ❌ "Model gpt-oss:20b not found"
**Solution:**
1. Pull the model: `ollama pull gpt-oss:20b`
2. List available models: `ollama list`
3. Verify the model name matches exactly

#### ❌ "Failed to connect to AllTalk TTS"
**Solution:**
1. Check if AllTalk server is running: `curl http://localhost:7851/api/voices`
2. Restart the assistant to auto-install AllTalk TTS
3. Manually start AllTalk: `cd alltalk_tts && python start_alltalk.py`
4. Check if port 7851 is available

#### ❌ "TTS audio not playing" / "No audio output"
**Solution:**
1. Check your speakers/headphones are connected
2. Verify system audio is not muted
3. Test with: `python -c "import pygame; pygame.mixer.init(); print('Audio OK')"`
4. Check Windows audio drivers are installed
5. Try changing TTS voice with `voices` and `voice <name>` commands

#### ❌ "AllTalk TTS installation failed"
**Solution:**
1. Check internet connection for GitHub access
2. Ensure Git is installed: `git --version`
3. Try manual installation:
   ```bash
   git clone https://github.com/erew123/alltalk_tts.git
   cd alltalk_tts
   pip install -r requirements.txt
   ```
4. Check Python version compatibility (3.8+)

#### ❌ "Configuration file not found"
**Solution:**
1. Ensure `config.yaml` is in the same directory as `main.py`
2. Check file permissions
3. Verify YAML syntax is valid

#### ❌ "Request timeout"
**Solution:**
1. Increase timeout in `config.yaml`
2. Check system resources (CPU/Memory)
3. Try a smaller model if performance is poor

#### ❌ "Permission denied" for logs
**Solution:**
1. Create logs directory: `mkdir logs`
2. Check write permissions in the project directory
3. Update log path in `config.yaml` if needed

### TTS-Specific Troubleshooting

#### ❌ "Speech is too fast/slow"
**Solution:**
1. Adjust `speed` setting in config.yaml (0.5-2.0)
2. Restart the assistant to apply changes

#### ❌ "TTS voice sounds distorted"
**Solution:**
1. Try different voice: `voices` then `voice <name>`
2. Adjust `volume` in config.yaml (0.0-1.0)
3. Check system audio settings

#### ❌ "TTS speech cuts off mid-sentence"
**Solution:**
1. Increase `timeout` in alltalk_tts config section
2. Check system resources during speech generation
3. Try shorter response lengths

#### ❌ "Multiple speech overlapping"
**Solution:**
1. Use `stop` command to halt current speech
2. Wait for current speech to finish before new input
3. Use `mute` temporarily if needed

### Debug Mode
Enable detailed logging by changing `log_level` to `"DEBUG"` in `config.yaml`:

```yaml
general:
  log_level: "DEBUG"
```

This will show detailed request/response information and connection details.

## 📁 Project Architecture

### Directory Structure
```
jarvis_assistant/
├── setup.py                       # NEW - One-time setup script
├── main.py                        # Enhanced with service management
├── config.yaml                    # Configuration settings
├── setup_completed.flag           # NEW - Setup completion marker
├── start_carlos.bat              # NEW - Windows startup script
├── start_carlos.sh               # NEW - Unix startup script
├── requirements.txt               # Python dependencies
├── README.md                      # This file
├── alltalk_tts/                   # AllTalk TTS installation (auto-created)
├── logs/                          # Log files (auto-created)
│   ├── carlos.log                 # Main log file
│   └── setup.log                  # NEW - Setup log file
├── modules/                       # Core modules
│   ├── __init__.py                # Package initialization
│   ├── llm_handler.py             # LLM interaction logic
│   ├── tts_handler.py             # TTS interaction logic
│   └── service_manager.py         # NEW - Service management
└── utils/                         # Utility modules
    ├── __init__.py                # Package initialization
    └── logger.py                  # Logging system
```

### Module Responsibilities

#### main.py
- Application lifecycle management
- Configuration loading and validation
- User interface and conversation loop
- Signal handling and graceful shutdown

#### modules/llm_handler.py
- Ollama API communication
- Conversation history management
- Context building and token management
- Error handling and retry logic

#### modules/tts_handler.py
- AllTalk TTS API communication
- Audio generation and playback
- Voice management and selection
- Speech queue and interrupt handling
- TTS installation automation

#### modules/service_manager.py
- Auto-starting external services (Ollama, AllTalk TTS)
- Service status monitoring and health checks
- Intelligent fallbacks when services are unavailable
- Setup completion verification
- Cross-platform service management

#### utils/logger.py
- Colored console output
- File rotation and management
- Multiple log levels
- Separate loggers for different modules

## 🧪 Testing the System

### Manual Testing Checklist

1. **✅ Startup Test**
   - Configuration loads without errors
   - Logger initializes successfully
   - LLM handler connects to Ollama
   - TTS handler initializes successfully
   - AllTalk TTS installs/connects automatically
   - Model responds to test query

2. **✅ Conversation Test**
   - Single message gets appropriate response with speech
   - Multi-turn conversation maintains context
   - History is preserved across messages
   - Responses are coherent and relevant
   - TTS audio plays correctly

3. **✅ TTS Command Test**
   - 'mute' command disables speech output
   - 'unmute' command re-enables speech
   - 'voices' command lists available voices
   - 'voice <name>' changes TTS voice
   - 'stop' command interrupts current speech

4. **✅ Basic Command Test**
   - 'clear' command resets conversation
   - 'history' command shows past messages
   - Exit commands ('quit', 'exit', 'bye') work
   - Ctrl+C triggers graceful shutdown
   - 'memory' and 'unload' commands work

5. **✅ Error Handling Test**
   - Graceful failure when Ollama is offline
   - Graceful fallback when AllTalk TTS is unavailable
   - Timeout handling works correctly
   - Invalid configuration is caught
   - Network errors are handled properly
   - Audio device issues are handled gracefully

6. **✅ Logging Test**
   - Console output is colored and readable
   - Log files are created in logs/ directory
   - Log rotation works when file size limit reached
   - Different log levels work correctly

### Quick Test Commands

```bash
# Test 1: Verify Ollama connection
python -c "
import yaml
from utils.logger import get_logger
from modules.llm_handler import LLMHandler
config = yaml.safe_load(open('config.yaml'))
logger = get_logger('Test', config)
llm = LLMHandler(config, logger)
print('Connection test:', llm.test_connection())
"

# Test 2: Simple conversation
python main.py
# Then type: Hello, this is a test
```

## 🔄 Next Steps (Phase 3 Preview)

Phase 2 adds Text-to-Speech output capability. Future phases will add:

- **Speech-to-Text (STT)** input for voice commands
- **Voice activity detection** for hands-free operation
- **Audio processing pipeline** optimization
- **Wake word detection** ("Hey Carlos")
- **Multi-modal capabilities** (images, documents)
- **Advanced voice synthesis** options

## 📝 Development Notes

### Code Quality Standards
- **Type hints** for all function parameters and returns
- **Docstrings** following Google/NumPy style
- **Exception handling** at appropriate levels
- **Logging** for debugging and monitoring
- **Configuration-driven** behavior

### Performance Considerations
- Conversation history is automatically trimmed to prevent token overflow
- Request timeouts prevent hanging
- File log rotation prevents disk space issues
- Connection pooling for HTTP requests

### Security Notes
- No API keys or credentials stored in plain text
- Input validation for user messages
- Proper error handling prevents information leakage
- Logs exclude sensitive information

## 🤝 Contributing

1. Follow the existing code style and patterns
2. Add comprehensive docstrings to new functions
3. Include error handling for all external calls
4. Update this README if adding new features
5. Test thoroughly before submitting changes

## 🔧 Setup System

### Automated Setup Process
The `setup.py` script provides a comprehensive one-time setup that:

1. **System Checks**
   - Verifies Python version (3.8+)
   - Checks admin privileges for installations
   - Validates system requirements

2. **Dependency Installation**
   - Installs Chocolatey (Windows) or Homebrew (macOS)
   - Installs Ollama via package manager
   - Downloads the gpt-oss:20b model
   - Clones and configures AllTalk TTS

3. **Python Environment**
   - Installs all Python requirements
   - Configures virtual environment if needed
   - Tests all components

4. **Convenience Features**
   - Creates startup scripts for easy access
   - Generates setup completion flag
   - Provides detailed logging of the setup process

### Setup Script Features
- **Cross-platform support** (Windows, macOS, Linux)
- **Intelligent fallbacks** when installations fail
- **Detailed logging** to `logs/setup.log`
- **Progress indicators** with clear status messages
- **Error handling** with helpful troubleshooting tips

### Service Management
The enhanced `main.py` now includes smart service management:

- **Auto-start services** when Carlos starts
- **Graceful fallbacks** when services are unavailable
- **Service health monitoring** during runtime
- **Setup verification** to ensure proper installation

## 📄 License

This project is licensed under the MIT License.

---

**Status**: Phase 2 Complete ✅ (TTS Integration + Setup System)
**Next Phase**: STT Integration (Phase 3)