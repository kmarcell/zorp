from InstancesConf import InstancesConf
from Roles import InstanceRoleMaster, InstanceRoleSlave
import utils
from UInterface import UInterface
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
    pidfile_dir = prefix + "/var/run/zorp/"

    def isRunning(self, process):
        """
        Opening the right pidfile in the pidfile dir,
        checking if there is a running process with that pid,
        returning True if there is.

        FIXME: Delete pid file if there is no runnig processes with that pid
        """
        try:
            pid_file = open(self.pidfile_dir + 'zorp-' + process + '.pid')
        except IOError:
            return CommandResultFailure("Process %s is not running!" % process)

        pid = int(pid_file.read())
        pid_file.close()
        try:
            open('/proc/' + str(pid) + '/status')
        except IOError:
            return CommandResultFailure("Invalid pid file no running process with pid %d!" % pid)

        return CommandResultSuccess("Process %s is running!" % process)

    def _searchInstanceThanCallFunctionWithParamsToInstance(self, instance_name, function, args):
        try:
            for instance in InstancesConf():
                if instance.name == instance_name:
                    result = function(instance, *args)
                    break
            return result
        except IOError as e:
            return CommandResultFailure(e.strerror)

    def _callFunctionToInstanceProcesses(self, instance, function):
        result = []
        for i in range(0, instance.number_of_processes):
            instance.process_num = i
            result.append(function(instance))

        return result

    def _setProcessNumThanStart(self, instance, process_num):
        if process_num >= 0 and process_num < instance.number_of_processes:
            instance.process_num = process_num
            return self._start_process(instance)
        else:
            return CommandResultFailure("Process number %d must be between 0 and %d"
                                        % (process_num, instance.number_of_processes))

    def _start_process(self, instance):

        cmd = [self.install_path + "zorp --as ", instance.zorp_argv,
               (InstanceRoleSlave() if instance.process_num else InstanceRoleMaster()),
               instance.process_name,
               ("--enable-core" if instance.enable_core else ""),
               ("--process-mode background" if not instance.auto_restart else "")]

        return CommandResultSuccess(utils.makeStringFromSequence(cmd))

    def startAll(self):
        try:
            for instance in InstancesConf():
                result = self._callFunctionToInstanceProcesses(instance, self._start_process)
                UInterface.informUser(result)
        except IOError as e:
            return CommandResultFailure(e.strerror)

    def start(self, instance_name):
        inst_name, process_num = Instance.splitInstanceName(instance_name)
        common_method = self._searchInstanceThanCallFunctionWithParamsToInstance
        if process_num != None:
            #process_num can be zero which is not None but it is a False in statements
            function =  self._setProcessNumThanStart
            args = [process_num]
        else:
            function = self._callFunctionToInstanceProcesses
            args = [self._start_process]

        result = common_method(inst_name, function, args)
        return result

    def reloadAll(self):
        raise NotImplementedError()

    def _reload_process(self, instance):
        if not self.isRunning(instance.process_name):
            return CommandResultFailure("Instance %s is not running! You can not reload it." % instance.process_name)
        szig = SZIG(self.pidfile_dir + 'zorpctl.' + instance.process_name)
        szig.reload()
        return instance.process_name + ": " + szig.reload_result()

    def reload(self, instance_name):
        inst_name, process_num = Instance.splitInstanceName(instance_name)
        if process_num != None:
            result = self._reload_process(Instance(name=inst_name, process_num=process_num))
        else:
            func1 = self._searchInstanceThanCallFunctionWithParamsToInstance
            func2 = self._callFunctionToInstanceProcesses
            result = func1(inst_name, func2, [self._reload_process])

        return result