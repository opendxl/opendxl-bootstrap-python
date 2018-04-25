""" Abstraction layer for Python 2 / 3 compatibility. """

from __future__ import absolute_import
import sys

# pylint: disable=unused-import
try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser

if sys.version_info[0] > 2:
    UnicodeString = str
else:
    UnicodeString = unicode # pylint: disable=invalid-name, undefined-variable
