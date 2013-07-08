import zorpctl.prefix, ConfigParser

class Singleton(object):
    """
    A non-thread-safe helper class to ease implementing singletons.
    This should be used as a decorator -- not a metaclass -- to the
    class that should be a singleton.

    The decorated class can define one `__init__` function that
    takes only the `self` argument. Other than that, there are
    no restrictions that apply to the decorated class.

    To get the singleton instance, use the `Instance` method. Trying
    to use `__call__` will result in a `TypeError` being raised.

    Limitations: The decorated class cannot be inherited from.

    """

    def __init__(self, decorated):
        self._decorated = decorated

    def Instance(self):
        """
        Returns the singleton instance. Upon its first call, it creates a
        new instance of the decorated class and calls its `__init__` method.
        On all subsequent calls, the already created instance is returned.

        """
        try:
            return self._instance
        except AttributeError:
            self._instance = self._decorated()
            return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `Instance()`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)


@Singleton
class ZorpctlConfig(object):

    def __init__(self):
        self.config = ConfigParser.ConfigParser(allow_no_value=True)
        self.path = zorpctl.prefix.PATH_PREFIX + '/etc/zorp/'

    def __getitem__(self, key):
        try:
             value = self.config.get('zorpctl', key)
        except ConfigParser.NoOptionError:
            raise KeyError(key)

        try:
             value = int(value)
        except ValueError:
             pass

        return value

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        self._path = value
        self.parse()

    def parse(self):
        if not self.config.read(self.path + '/zorpctl.conf'):
            if not self.config.read(self.path):
                raise EnvironmentError("The given directory does not \
contain a zorpctl.conf file! (Also check permissions!)")
