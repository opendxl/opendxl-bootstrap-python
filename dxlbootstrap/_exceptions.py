class NoOptionError(Exception):
    """
    Exception raised when an option is not present in a configuration file
    """
    def __init__(self, option, section):
        """
        Constructor parameters:

        :param str option: The option which could not be found.
        :param str section: The section in which the option was expected to reside.
        """
        self.message = "No option %r in section: %r" % (option, section)
        super(NoOptionError, self).__init__(self.message)
        self.option = option
        self.section = section
        self.args = (option, section)

    def __repr__(self):
        return self.message

    __str__ = __repr__
