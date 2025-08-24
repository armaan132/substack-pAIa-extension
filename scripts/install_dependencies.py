#!/usr/bin/env python3
"""
Install Dependencies Script for Daily Briefing pAIa

This script installs the required Python packages for the incremental update system.
"""

import subprocess
import sys
from pathlib import Path

def install_package(package_name):
    """Install a Python package using pip."""
    try:
        print(f"📦 Installing {package_name}...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", package_name], 
                              capture_output=True, text=True, check=True)
        print(f"✅ {package_name} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package_name}: {e}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    """Install all required dependencies."""
    print("🚀 Installing dependencies for Daily Briefing pAIa...")
    print()
    
    # Required packages
    packages = [
        "substack-api",
        "requests",
        "selenium",  # For web automation if needed
        "chromedriver-autoinstaller"  # For browser automation if needed
    ]
    
    success_count = 0
    total_count = len(packages)
    
    for package in packages:
        if install_package(package):
            success_count += 1
        print()
    
    print(f"📊 Installation Summary: {success_count}/{total_count} packages installed successfully")
    
    if success_count == total_count:
        print("🎉 All dependencies installed successfully!")
        print("\nYou can now run incremental updates:")
        print("  python scripts/incremental_update.py")
    else:
        print("⚠️ Some packages failed to install. Check the errors above.")
        print("\nYou may need to install missing packages manually or check your Python environment.")
        sys.exit(1)

if __name__ == "__main__":
    main()
