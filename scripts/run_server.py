#!/usr/bin/env python3
"""
Simple runner script to start the newsletter personalization server.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.web.server import main

if __name__ == "__main__":
    main()
