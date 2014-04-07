
__version__ = 0.1
__author__ = "Andrei Z <andrei@spoton.com>"

from .base import *
from .chrome import ChromeDriver

DRIVERS = {
    "chrome": ChromeDriver
}

def new_driver(name="chrome"):
    """
    Function that returns a driver instance based on a name (string) of
    the driver. Throws exception if the driver is not recognized.
    """
    if not name in DRIVERS:
        raise Exception("No driver support for '%s'" % name)
    return DRIVERS[name]()
