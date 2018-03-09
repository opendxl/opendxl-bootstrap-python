""" Abstraction layer for Python 2 / 3 compatibility. """

from __future__ import absolute_import
import sys

try:
    from configparser import ConfigParser
    from configparser import NoOptionError as ConfigParserNoOptionError
except ImportError:
    from ConfigParser import ConfigParser
    from ConfigParser import NoOptionError as ConfigParserNoOptionError

if sys.version_info[0] > 2:
    unicode = str
