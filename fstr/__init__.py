__version__ = "0.1.0-alpha2"  # evaluated in setup.py

import sys
from .fstr import fstr

fstr.__version__ = __version__
sys.modules[__name__] = fstr
