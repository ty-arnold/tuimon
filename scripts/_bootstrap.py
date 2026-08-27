"""Acts as a first import - puts src/ on sys.path so scripts/ can import first party party package (core, models, battle, etc.)"""

import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
)
