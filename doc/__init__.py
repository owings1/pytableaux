import os
import sys

_dir = os.path.abspath(os.path.dirname(__file__))
if _dir not in sys.path:
    sys.path.insert(1, _dir)

addpath = os.path.abspath(os.path.join(_dir, '..'))
if addpath not in sys.path:
    sys.path.insert(0, addpath)

_ = None