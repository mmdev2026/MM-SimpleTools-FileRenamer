"""Compatibility entry point for MM SimpleTools DokumentenSortierer Pro.

PyInstaller currently points to this file, so it remains the stable launcher
while the code is split into smaller modules.
"""

import os
import sys


if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import main


if __name__ == "__main__":
    main()
