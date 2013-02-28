from Roles import *

class Instance(object):
    def __init__(self, **kwargs):
        self.name = kwargs.pop('name')
        self.process_name = kwargs.pop('process_name')
        self.process_num = kwargs.pop('process_num')
        self.auto_restart = kwargs.pop('auto_restart')
        self.auto_start = kwargs.pop('auto_start')
        self.enable_core = kwargs.pop('enable_core')
        self.role = kwargs.pop('role')

class InstanceHandler(object):
    def __init__(self):
        self.prefix = @PREFIX@
        self.pidfile_dir = self.prefix + "/var/run/zorp"
        self.instances_conf = self.prefix + "/etc/zorp/instances.conf"

    def isRunning(self):
        raise NotImplementedError()

    def start(self, instance_name):
        raise NotImplementedError()

"auto-restart"
"no-auto-restart"
"no-auto-start"
"enable-core"
"num-of-processes"
