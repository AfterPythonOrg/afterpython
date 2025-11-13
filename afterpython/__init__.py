# import builtins
# from pprint import pprint
from importlib.metadata import version

from afterpython._paths import Paths

# make pprint available in the global namespace
# builtins.pprint = pprint

paths = Paths()

__version__ = version("afterpython")
__all__ = ("__version__", "paths")
