import os
from os import path

version_info = (2, 0, 0)
__version__ = '.'.join(version_info)

package_dir = path.abspath(path.dirname(__file__))

# https://www.python.org/dev/peps/pep-0420/
# from pkgutil import extend_path