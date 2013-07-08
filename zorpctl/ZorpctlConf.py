import zorpctl.prefix, ConfigParser

def getConfig(path=zorpctl.prefix.PATH_PREFIX + '/etc/zorp/'):
    config = ConfigParser.ConfigParser(allow_no_value=True)
    if not config.read(path + 'zorpctl.conf'):
        if not config.read(path):
            raise EnvironmentError("The given directory does not \
contain a zorpctl.conf file! (Also check permissions!)")
    return ZorpctlConfig(config)

class ZorpctlConfig(object):

    def __init__(self, config):
        self.config = config

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
