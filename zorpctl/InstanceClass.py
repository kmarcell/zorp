from Roles import InstanceRole

class Instance(object):
    def __init__(self, **kwargs):
        self.name = kwargs.pop('name')
        self.process_name = kwargs.pop('process_name', None)
        self.process_num = kwargs.pop('process_num', None)
        self.zorp_argv = kwargs.pop('zorp_argv')

        self.auto_restart = kwargs.pop('auto_restart', True)
        self.auto_start = kwargs.pop('auto_start', True)
        self.number_of_processes = kwargs.pop('number_of_processes', 1)
        self.enable_core = kwargs.pop('enable_core', False)
        self.role = kwargs.pop('role', InstanceRole)