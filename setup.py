"""
Carlos Assistant - One-Time Setup Script
Installs and configures all dependencies for Carlos AI Assistant
Run this once before using Carlos
"""

import os
import sys
import subprocess
import platform
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple


class CarlosSetup:
    """Comprehensive setup system for Carlos Assistant."""
    
    def __init__(self):
        """Initialize the setup system."""
        self.project_root = Path.cwd()
        self.setup_completed_flag = self.project_root / "setup_completed.flag"
        self.log_file = self.project_root / "logs" / "setup.log"
        
        # Ensure logs directory exists
        self.log_file.parent.mkdir(exist_ok=True)
        
        print("🚀 Carlos Assistant Setup - v1.0")
        print("=" * 50)
    
    def log(self, message: str) -> None:
        """Log message to file and console."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        # Write to log file
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_message + "\n")
        
        # Print to console
        print(message)
    
    def check_python_version(self) -> bool:
        """Check if Python version is compatible (3.8+)."""
        self.log("🔍 Checking Python version...")
        
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            self.log(f"❌ Python {version.major}.{version.minor} detected")
            self.log("❌ Carlos requires Python 3.8 or higher")
            self.log("📥 Download from: https://www.python.org/downloads/")
            return False
        
        self.log(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
        return True
    
    def check_admin_rights(self) -> bool:
        """Check if running with admin privileges."""
        self.log("🔍 Checking admin privileges...")
        
        try:
            # On Windows, check if we can write to system directories
            if platform.system() == "Windows":
                test_path = Path("C:/Windows/Temp/carlos_test")
                try:
                    test_path.write_text("test")
                    test_path.unlink()
                    self.log("✅ Admin privileges detected")
                    return True
                except (PermissionError, OSError):
                    self.log("⚠️ Admin privileges not detected")
                    return False
            else:
                # On Unix-like systems, check if we're root
                if os.geteuid() == 0:
                    self.log("✅ Admin privileges detected")
                    return True
                else:
                    self.log("⚠️ Admin privileges not detected")
                    return False
        except Exception as e:
            self.log(f"⚠️ Could not determine admin status: {e}")
            return False
    
    def request_elevation_if_needed(self) -> None:
        """Request admin elevation if needed for installations."""
        if self.check_admin_rights():
            return
        
        self.log("🔧 Some installations require admin privileges")
        self.log("💡 If installations fail, try running as administrator:")
        
        if platform.system() == "Windows":
            self.log("   Right-click PowerShell/Command Prompt -> 'Run as administrator'")
            self.log("   Then run: python setup.py")
        else:
            self.log("   Run: sudo python setup.py")
        
        input("\nPress Enter to continue anyway, or Ctrl+C to exit...")
    
    def install_chocolatey(self) -> bool:
        """Install Chocolatey package manager for Windows."""
        if platform.system() != "Windows":
            self.log("ℹ️ Chocolatey is Windows-only, skipping...")
            return True
        
        self.log("📦 Checking Chocolatey installation...")
        
        try:
            # Check if already installed
            result = subprocess.run(['choco', '--version'], 
                                  capture_output=True, text=True, 
                                  encoding='utf-8', errors='replace',
                                  timeout=10)
            if result.returncode == 0:
                self.log("✅ Chocolatey already installed")
                return True
            
            self.log("📦 Installing Chocolatey...")
            
            # PowerShell command to install Chocolatey
            ps_command = """
            Set-ExecutionPolicy Bypass -Scope Process -Force;
            [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072;
            iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
            """
            
            result = subprocess.run(['powershell', '-Command', ps_command], 
                                  capture_output=True, text=True, 
                                  encoding='utf-8', errors='replace',
                                  timeout=120)
            
            if result.returncode == 0:
                self.log("✅ Chocolatey installed successfully")
                return True
            else:
                self.log(f"❌ Chocolatey installation failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log("❌ Chocolatey installation timed out")
            return False
        except Exception as e:
            self.log(f"❌ Chocolatey installation error: {e}")
            return False
    
    def install_ollama(self) -> bool:
        """Install Ollama using appropriate method for the platform."""
        self.log("🧠 Checking Ollama installation...")
        
        try:
            # Check if already installed
            result = subprocess.run(['ollama', '--version'], 
                                  capture_output=True, text=True, 
                                  encoding='utf-8', errors='replace',
                                  timeout=10)
            if result.returncode == 0:
                self.log("✅ Ollama already installed")
                return True
            
            self.log("🧠 Installing Ollama...")
            
            if platform.system() == "Windows":
                # Use Chocolatey on Windows
                if not self.install_chocolatey():
                    self.log("❌ Cannot install Ollama without Chocolatey")
                    return False
                
                result = subprocess.run(['choco', 'install', 'ollama', '-y'], 
                                      capture_output=True, text=True, 
                                      encoding='utf-8', errors='replace',
                                      timeout=300)
                
                if result.returncode == 0:
                    self.log("✅ Ollama installed successfully via Chocolatey")
                    return True
                else:
                    self.log(f"❌ Ollama installation failed: {result.stderr}")
                    return False
                    
            elif platform.system() == "Darwin":  # macOS
                # Use Homebrew on macOS
                result = subprocess.run(['brew', 'install', 'ollama'], 
                                      capture_output=True, text=True, 
                                      encoding='utf-8', errors='replace',
                                      timeout=300)
                
                if result.returncode == 0:
                    self.log("✅ Ollama installed successfully via Homebrew")
                    return True
                else:
                    self.log(f"❌ Ollama installation failed: {result.stderr}")
                    return False
                    
            else:  # Linux
                # Use official install script
                install_script = """
                curl -fsSL https://ollama.ai/install.sh | sh
                """
                
                result = subprocess.run(['bash', '-c', install_script], 
                                      capture_output=True, text=True, 
                                      encoding='utf-8', errors='replace',
                                      timeout=300)
                
                if result.returncode == 0:
                    self.log("✅ Ollama installed successfully via install script")
                    return True
                else:
                    self.log(f"❌ Ollama installation failed: {result.stderr}")
                    return False
                    
        except subprocess.TimeoutExpired:
            self.log("❌ Ollama installation timed out")
            return False
        except Exception as e:
            self.log(f"❌ Ollama installation error: {e}")
            return False
    
    def download_ollama_model(self) -> bool:
        """Download the required Ollama model."""
        self.log("📥 Downloading gpt-oss:20b model...")
        
        try:
            # Start Ollama service if not running
            self.log("🔧 Starting Ollama service...")
            subprocess.Popen(['ollama', 'serve'], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            
            # Wait for service to start
            time.sleep(5)
            
            # Pull the model with proper encoding
            result = subprocess.run(['ollama', 'pull', 'gpt-oss:20b'], 
                                  capture_output=True, text=True, 
                                  encoding='utf-8', errors='replace',
                                  timeout=600)
            
            if result.returncode == 0:
                self.log("✅ Model downloaded successfully")
                return True
            else:
                self.log(f"❌ Model download failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log("❌ Model download timed out")
            return False
        except Exception as e:
            self.log(f"❌ Model download error: {e}")
            return False
    
    def setup_alltalk(self) -> bool:
        """Fix and complete AllTalk TTS setup."""
        self.log("🗣️ Setting up AllTalk TTS...")
        
        alltalk_dir = self.project_root / "alltalk_tts"
        
        # Clone AllTalk if not exists
        if not alltalk_dir.exists():
            self.log("📥 Cloning AllTalk TTS...")
            try:
                result = subprocess.run([
                    'git', 'clone', 
                    'https://github.com/erew123/alltalk_tts.git',
                    str(alltalk_dir)
                ], capture_output=True, text=True, 
                   encoding='utf-8', errors='replace',
                   timeout=300)
                
                if result.returncode != 0:
                    self.log(f"❌ Failed to clone AllTalk TTS: {result.stderr}")
                    return False
                    
                self.log("✅ AllTalk TTS cloned successfully")
            except subprocess.TimeoutExpired:
                self.log("❌ AllTalk clone timed out")
                return False
            except Exception as e:
                self.log(f"❌ AllTalk clone error: {e}")
                return False
        
        # Find the correct requirements file
        req_paths = [
            alltalk_dir / "requirements.txt",
            alltalk_dir / "system" / "requirements" / "requirements_standalone.txt",
            alltalk_dir / "system" / "requirements" / "requirements.txt"
        ]
        
        req_file = None
        for path in req_paths:
            if path.exists():
                req_file = path
                break
        
        if not req_file:
            self.log("⚠️ No requirements file found, creating basic one...")
            # Create basic requirements if none found
            basic_reqs = """torch
torchaudio
fastapi
uvicorn
pydantic
requests
numpy
"""
            with open(alltalk_dir / "requirements.txt", "w") as f:
                f.write(basic_reqs)
            req_file = alltalk_dir / "requirements.txt"
        
        self.log(f"📦 Installing AllTalk requirements from: {req_file}")
        
        # Install requirements
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(req_file)
            ], capture_output=True, text=True, 
               encoding='utf-8', errors='replace',
               timeout=300)
            
            if result.returncode == 0:
                self.log("✅ AllTalk requirements installed successfully")
                return True
            else:
                self.log(f"❌ AllTalk requirements installation failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log("❌ AllTalk requirements installation timed out")
            return False
        except Exception as e:
            self.log(f"❌ AllTalk requirements installation error: {e}")
            return False
    
    def install_python_requirements(self) -> bool:
        """Install Python requirements for Carlos."""
        self.log("📦 Installing Python requirements...")
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ], capture_output=True, text=True, 
               encoding='utf-8', errors='replace',
               timeout=300)
            
            if result.returncode == 0:
                self.log("✅ Python requirements installed successfully")
                return True
            else:
                self.log(f"❌ Python requirements installation failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log("❌ Python requirements installation timed out")
            return False
        except Exception as e:
            self.log(f"❌ Python requirements installation error: {e}")
            return False
    
    def test_all_components(self) -> bool:
        """Test all components to ensure they work."""
        self.log("🧪 Testing all components...")
        
        # Test 1: Ollama connection
        self.log("  🔍 Testing Ollama connection...")
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=10)
            if response.status_code == 200:
                self.log("  ✅ Ollama connection: OK")
            else:
                self.log("  ❌ Ollama connection: Failed")
                return False
        except Exception as e:
            self.log(f"  ❌ Ollama connection: Error - {e}")
            return False
        
        # Test 2: Model availability
        self.log("  🔍 Testing model availability...")
        try:
            result = subprocess.run(['ollama', 'list'], 
                                  capture_output=True, text=True, 
                                  encoding='utf-8', errors='replace',
                                  timeout=10)
            if result.returncode == 0 and 'gpt-oss:20b' in result.stdout:
                self.log("  ✅ gpt-oss:20b model: OK")
            else:
                self.log("  ❌ gpt-oss:20b model: Not found")
                return False
        except Exception as e:
            self.log(f"  ❌ Model test: Error - {e}")
            return False
        
        # Test 3: AllTalk TTS
        self.log("  🔍 Testing AllTalk TTS...")
        try:
            response = requests.get("http://localhost:7851/api/voices", timeout=10)
            if response.status_code == 200:
                self.log("  ✅ AllTalk TTS: OK")
            else:
                self.log("  ⚠️ AllTalk TTS: Not running (will be started on first run)")
        except Exception:
            self.log("  ⚠️ AllTalk TTS: Not running (will be started on first run)")
        
        self.log("✅ All component tests completed")
        return True
    
    def create_startup_scripts(self) -> None:
        """Create convenient startup scripts."""
        self.log("📝 Creating startup scripts...")
        
        # Create Windows batch file
        if platform.system() == "Windows":
            batch_content = """@echo off
echo Starting Carlos Assistant...
cd /d "%~dp0"
python main.py
pause
"""
            with open(self.project_root / "start_carlos.bat", "w") as f:
                f.write(batch_content)
            self.log("✅ Created: start_carlos.bat")
        
        # Create Unix shell script
        shell_content = """#!/bin/bash
echo "Starting Carlos Assistant..."
cd "$(dirname "$0")"
python3 main.py
"""
        with open(self.project_root / "start_carlos.sh", "w") as f:
            f.write(shell_content)
        
        # Make shell script executable on Unix systems
        if platform.system() != "Windows":
            os.chmod(self.project_root / "start_carlos.sh", 0o755)
        
        self.log("✅ Created: start_carlos.sh")
    
    def create_setup_completion_flag(self) -> None:
        """Create setup completion flag file."""
        completion_data = {
            "setup_completed": True,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": platform.system(),
            "platform_version": platform.version()
        }
        
        with open(self.setup_completed_flag, "w") as f:
            json.dump(completion_data, f, indent=2)
        
        self.log("✅ Created setup completion flag")
    
    def run_complete_setup(self) -> None:
        """Run the complete setup process."""
        try:
            # Step 1: Check Python version
            if not self.check_python_version():
                return
            
            # Step 2: Check admin rights
            self.request_elevation_if_needed()
            
            # Step 3: Install Ollama
            if not self.install_ollama():
                self.log("❌ Ollama installation failed")
                self.log("💡 Please install Ollama manually from: https://ollama.ai/")
                return
            
            # Step 4: Download model
            if not self.download_ollama_model():
                self.log("❌ Model download failed")
                self.log("💡 Please run manually: ollama pull gpt-oss:20b")
                return
            
            # Step 5: Setup AllTalk TTS
            if not self.setup_alltalk():
                self.log("⚠️ AllTalk TTS setup had issues, but continuing...")
            
            # Step 6: Install Python requirements
            if not self.install_python_requirements():
                self.log("❌ Python requirements installation failed")
                return
            
            # Step 7: Test components
            if not self.test_all_components():
                self.log("❌ Component tests failed")
                return
            
            # Step 8: Create startup scripts
            self.create_startup_scripts()
            
            # Step 9: Create completion flag
            self.create_setup_completion_flag()
            
            # Success!
            self.log("\n🎉 Setup completed successfully!")
            self.log("📝 Created startup script: start_carlos.bat (Windows) or start_carlos.sh (Unix)")
            
            self.log("\nNext steps:")
            self.log("1. Run: python main.py")
            self.log("2. Or double-click: start_carlos.bat (Windows) / start_carlos.sh (Unix)")
            self.log("\nCarlos is ready to assist you! 🤖")
            
        except KeyboardInterrupt:
            self.log("\n⚠️ Setup interrupted by user")
            return
        except Exception as e:
            self.log(f"\n❌ Setup failed with error: {e}")
            return


def main():
    """Main entry point for setup."""
    setup = CarlosSetup()
    setup.run_complete_setup()


if __name__ == "__main__":
    main()
