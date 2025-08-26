#!/usr/bin/env python3
"""
Simple runner script to start the newsletter personalization server.
"""

import sys
import os
import subprocess
from pathlib import Path

# Get the project root directory
project_root = Path(__file__).parent.parent

if __name__ == "__main__":
    # Change to project root directory and run server
    os.chdir(project_root)
    
    # Run the server directly from the web directory
    server_path = project_root / "src" / "web" / "server.py"
    
    # Use subprocess to run with proper Python path
    result = subprocess.run([
        sys.executable, 
        str(server_path)
    ], cwd=project_root)
    
    if result.returncode != 0:
        print(f"❌ Server exited with code {result.returncode}")
        sys.exit(result.returncode)
