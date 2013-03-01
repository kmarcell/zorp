from InstancesConf import InstancesConf
from Roles import InstanceRoleMaster, InstanceRoleSlave

class CommandResult(object):
    def __init__(self, msg = None):
        self.msg = msg

    def __str__(self):
        return self.msg

class CommandResultSuccess(CommandResult):
    def __init__(self, msg = None):
        super(CommandResultSuccess, self).__init__(msg)

    def __bool__(self):
        return True

class CommandResultFailure(CommandResult):
    def __init__(self, msg = None):
        super(CommandResultFailure, self).__init__(msg)

    def __bool__(self):
        return False

class InstanceHandler(object):
    def __init__(self):
        self.prefix = "" #TODO: @PREFIX@
        self.pidfile_dir = self.prefix + "/var/run/zorp"
        self.split_symbol = '#'

    def isRunning(self, process):
        """
        What should we do:
        Opening the right pidfile in the pidfile dir,
        checking if there is a running process with that pid,
        returning True if there is.

        Questions:
        - can we check that the running process with the pid is a Zorp?
        - is it the right Zorp or an other?
        - is that instance in the instances.conf, what if not?
        - what should we do with the pid file if there is no runnig processes with that pid?
        """
        return CommandResultFailure("Process %s is not running!" % process)

    def _splitInstanceName(self, instance_name):
        """
        Splits the instance name from the process number.
        example: 'default#0' -> ('default', 0)
        """
        name, number = instance_name.split(self.split_symbol)
        return name, number

    def _start_process(self, instance):
        cmd = ["zorp --as ", instance.zorp_argv,
               (InstanceRoleSlave if instance.process_num else InstanceRoleMaster),
               instance.process_name,
               ("--enable-core" if instance.enable_core else ""),
               ("--process-mode background" if not instance.auto_restart else "")
               ]
        return cmd

    def start(self, instance_name):
        result = []
        inst_name, process_num = self._splitInstanceName(instance_name)
        for instance in InstancesConf():
            if instance.name == inst_name:
                if process_num:
                    instance.process_num = int(process_num)
                    instance.process_name = instance_name
                    self._start_process(instance)
                    result = self.isRunning(instance_name)
                else:
                    for number in range(0, instance.number_of_processes):
                        instance.process_num = number
                        instance.process_name = instance.name + self.split_symbol + str(number)
                        self._start_process(instance)
                        result.append(self.isRunning(instance.process_name))
                break

        return result
