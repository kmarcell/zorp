from InstancesConf import InstancesConf
from Roles import InstanceRoleMaster, InstanceRoleSlave
import utils
from szig import SZIG
from InstanceClass import Instance

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
    prefix = "" #TODO: @PREFIX@
    install_path = prefix + "/usr/lib/zorp/"

    def __init__(self):
        self.pidfile_dir = self.prefix + "/var/run/zorp"

    def isRunning(self, process):
        """
        What should we do:
        Opening the right pidfile in the pidfile dir,
        checking if there is a running process with that pid,
        returning True if there is.

        Questions:
        - can we check that the running process with the pid is a Zorp?
        + ANSWER: /proc/<pid>/status
        - what should we do with the pid file if there is no runnig processes with that pid?
        + Delete it, from other method
        """
        return CommandResultFailure("Process %s is not running!" % process)

    def _start_process(self, instance):

        cmd = [self.install_path + "zorp --as ", instance.zorp_argv,
               (InstanceRoleSlave() if instance.process_num else InstanceRoleMaster()),
               instance.process_name,
               ("--enable-core" if instance.enable_core else ""),
               ("--process-mode background" if not instance.auto_restart else "")
               ]

        return utils.makeStringFromSequence(cmd)

    def startAll(self):
        raise NotImplementedError()

    def _searchInstanceThanCallFunctionWithParamsToInstance(self, instance_name, function, args):
        for instance in InstancesConf():
            if instance.name == instance_name:
                result = function(instance, *args)
                break
        return result

    def _callFunctionToInstanceProcesses(self, instance, function):
        result = []
        for i in range(0, instance.number_of_processes):
            instance.process_num = i
            result.append(function(instance))

        return result

    def __setProcessNumThanStart(self, instance, process_num):
        instance.process_num = process_num
        return self._start_process(instance)

    def start(self, instance_name):
        inst_name, process_num = Instance.splitInstanceName(instance_name)
        if process_num != None:
            #process_num can be zero which is not None but it is a False in statements
            func = self._searchInstanceThanCallFunctionWithParamsToInstance
            result = func(inst_name, self.__setProcessNumThanStart, [process_num])
        else:
            func1 = self._searchInstanceThanCallFunctionWithParamsToInstance
            func2 = self._callFunctionToInstanceProcesses
            result = func1(inst_name, func2, [self._start_process])

        return result

    def reloadAll(self):
        raise NotImplementedError()

    def _reload_process(self, instance):
        #szig = SZIG(self.pidfile_dir + '/zorpctl.' + instance.process_name)
        return self.pidfile_dir + '/zorpctl.' + instance.process_name

    def reload(self, instance_name):
        inst_name, process_num = Instance.splitInstanceName(instance_name)
        if process_num != None:
            result = self._reload_process(Instance(name=inst_name, process_num=process_num))
        else:
            func1 = self._searchInstanceThanCallFunctionWithParamsToInstance
            func2 = self._callFunctionToInstanceProcesses
            result = func1(inst_name, func2, [self._reload_process])

        return result