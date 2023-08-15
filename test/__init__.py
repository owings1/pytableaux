from __future__ import annotations

import os.path
import sys


addpath = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')
)
if addpath not in sys.path:
    sys.path.insert(1, addpath)




