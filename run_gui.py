#!/usr/bin/env python3
"""
VideoGenFX GUI Launcher
Simple script to launch the Tkinter GUI application
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from vidgenfx import main
    main()
except ImportError as e:
    print(f"Error importing vidgenfx: {e}")
    print("Please make sure all dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"Error starting VideoGenFX GUI: {e}")
    sys.exit(1)