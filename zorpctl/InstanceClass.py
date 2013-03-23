class Instance(object):
    def __init__(self, **kwargs):
        self.name = kwargs.pop('name')
        self.process_name = kwargs.pop('process_name', None)
        self.process_num = kwargs.pop('process_num', None)
        self.zorp_argv = kwargs.pop('zorp_argv', None)

        self.auto_restart = kwargs.pop('auto_restart', True)
        self.auto_start = kwargs.pop('auto_start', True)
        self.number_of_processes = kwargs.pop('number_of_processes', 1)
        self.enable_core = kwargs.pop('enable_core', False)
        self.role = kwargs.pop('role', None)

    @staticmethod
    def splitInstanceName(instance_name):
        """
        Splits the instance name from the process number.
        example: 'default#0' -> ('default', 0)
                 'default'   -> ('default', None)
        """
        splitted = instance_name.split('#')
        return splitted[0], int(splitted[1]) if len(splitted) > 1 else None

    @property
    def process_name(self):
        self._process_name = self.name + '#' + str(self.process_num)
        return self._process_name

    @process_name.setter
    def process_name(self, value):
        self._process_name = value