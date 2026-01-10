#!/usr/bin/env python3
"""
GUI Launcher Setup and Installation Guide
"""

import subprocess
import sys
from pathlib import Path


def install_gui_dependencies():
    """Install PyQt6 and required packages."""
    packages = [
        'PyQt6>=6.0.0',
        'PyQt6-sip',
        'numpy',
        'pandas',
    ]
    
    print("Installing GUI dependencies...")
    for package in packages:
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', '-q', package
            ])
            print(f"✓ {package}")
        except subprocess.CalledProcessError:
            print(f"✗ Failed to install {package}")


def verify_installation():
    """Verify all dependencies are installed."""
    try:
        import PyQt6
        print("✓ PyQt6 is installed")
        return True
    except ImportError:
        print("✗ PyQt6 is not installed")
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("Aventa Trading System - GUI Launcher Setup")
    print("=" * 60)
    
    print("\nChecking dependencies...")
    if not verify_installation():
        print("\nInstalling missing dependencies...")
        install_gui_dependencies()
        
        if verify_installation():
            print("\n✓ All dependencies installed successfully!")
        else:
            print("\n✗ Failed to install dependencies")
            sys.exit(1)
    else:
        print("\n✓ All dependencies are already installed!")
    
    print("\n" + "=" * 60)
    print("Setup complete! To launch the GUI, run:")
    print("  python gui_launcher.py")
    print("=" * 60)
