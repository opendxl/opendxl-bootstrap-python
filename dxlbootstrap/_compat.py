""" Abstraction layer for Python 2 / 3 compatibility. """

try:
    from configparser import ConfigParser
    from configparser import NoOptionError as ConfigParserNoOptionError
except ImportError:
    from ConfigParser import ConfigParser
    from ConfigParser import NoOptionError as ConfigParserNoOptionError
