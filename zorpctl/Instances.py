from InstancesConf import InstancesConf
import os, signal, time, subprocess
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

    def __nonzero__(self):
        return True

class CommandResultFailure(CommandResult):
    def __init__(self, msg = None, value = None):
        super(CommandResultFailure, self).__init__(msg)

    def __nonzero__(self):
        return False

class ProcessStatus(object):
    def __init__(self, running, reloaded=None, pid=None, threads=None):
        self.running = running
        self.reloaded = reloaded
        self.pid = pid
        self.threads = threads

    def __str__(self):
        if not self.running:
            return str(self.running)
        else:
            status = str(self.running) + ", "
            if not self.reloaded:
                status += "policy NOT reloaded, "
            status += "%d threads active, pid %d" % (self.threads, self.pid)
            return status

class InstanceHandler(object):
    prefix = "" #TODO: @PREFIX@
    install_path = prefix + "/usr/lib/zorp/"
    pidfile_dir = prefix + "/var/run/zorp/"

    def __init__(self):
        self.force = False
        #variable indicates if force is active by force commands

    def _getProcessPid(self, process):
        pid_file = open(self.pidfile_dir + 'zorp-' + process + '.pid')
        pid = int(pid_file.read())
        pid_file.close()

        return pid

    def isRunning(self, process):
        """
        Opening the right pidfile in the pidfile dir,
        checking if there is a running process with that pid,
        returning True if there is.

        FIXME: Delete pid file if there is no runnig processes with that pid
        """
        try:
            pid = self._getProcessPid(process)
        except IOError as e:
            if e.strerror == "Permission denied":
                return CommandResultFailure(e.strerror)
            else:
                return CommandResultFailure("Process %s: not running" % process)

        try:
            open('/proc/' + str(pid) + '/status')
        except IOError:
            return CommandResultFailure("Invalid pid file no running process with pid %d!" % pid)

        return CommandResultSuccess("Process %s: running" % process)

    def _searchInstanceThanCallFunctionWithParamsToInstance(self, instance_name, function, args):
        result = None
        try:
            for instance in InstancesConf():
                if instance.name == instance_name:
                    result = function(instance, *args)
                    break
            return result if result != None else CommandResultFailure("instance %s not found!" % instance_name)
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
        if self.isRunning(instance.process_name):
            return CommandResultFailure("Process %s: is already running" % instance.process_name,
                                        instance.process_name)
        args = [self.install_path + "zorp", "--as"]
        args += instance.zorp_argv.split()
        args.append("--slave" if instance.process_num else "--master")
        args.append(instance.process_name)
        if instance.enable_core:
            args.append("--enable-core")
        if instance.auto_restart:
            args += ["--process-mode" ,"background"]

        subprocess.Popen(args, stderr=open("/dev/null", 'w'))
        timeout = 1
        while timeout <= 5 and not self.isRunning(instance.process_name):
            time.sleep(1)
            timeout += 1

        running = self.isRunning(instance.process_name)
        if running:
            return running
        else:
            return CommandResultFailure(
                    "%s: did not start in time (%s seconds)" %
                    (instance.process_name, timeout),
                    instance.process_name)

    def startAll(self):
        result = []
        try:
            for instance in InstancesConf():
                result += self._callFunctionToInstanceProcesses(instance, self._start_process)
            return result
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
        result = []
        try:
            for instance in InstancesConf():
                result += self._callFunctionToInstanceProcesses(instance, self._reload_process)
            return result
        except IOError as e:
            return CommandResultFailure(e.strerror)

    def _reload_process(self, instance):
        running = self.isRunning(instance.process_name)
        if not running:
            return CommandResultFailure("%s: %s" % (instance.process_name, running),
                                        instance.process_name)
        szig = SZIG(self.pidfile_dir + 'zorpctl.' + instance.process_name)
        szig.reload()
        if szig.reload_result():
            result = CommandResultSuccess("%s: Reload successful" % instance.process_name)
        else:
            result = CommandResultFailure("%s: Reload failed" % instance.process_name,
                                          instance.process_name)
        return result

    def reload(self, instance_name):
        inst_name, process_num = Instance.splitInstanceName(instance_name)
        if process_num != None:
            instance = Instance(name=inst_name, process_num=process_num)
            result = self._reload_process(instance)
        else:
            func1 = self._searchInstanceThanCallFunctionWithParamsToInstance
            func2 = self._callFunctionToInstanceProcesses
            result = func1(inst_name, func2, [self._reload_process])

        return result

    def _process_status(self, instance):
        running = self.isRunning(instance.process_name)
        status = ProcessStatus(running)
        if running:
            status.pid = self._getProcessPid(instance.process_name)
            try:
                szig = SZIG(self.pidfile_dir + 'zorpctl.' + instance.process_name)
                status.threads = int(szig.get_value('stats.threads_running'))
                policy_file = szig.get_value('info.policy.file')
                timestamp_szig = szig.get_value('info.policy.file_stamp')
                timestamp_os = os.path.getmtime(policy_file)
                status.reloaded = str(timestamp_szig) == str(timestamp_os).split('.')[0]
            except IOError:
                return CommandResultFailure(
                        "Process %s: running, but error in socket communication" % instance.process_name)

        return status

    def status(self, instance_name):
        inst_name, process_num = Instance.splitInstanceName(instance_name)
        if process_num != None:
            result = self._process_status(Instance(name=inst_name, process_num=process_num))
        else:
            func1 = self._searchInstanceThanCallFunctionWithParamsToInstance
            func2 = self._callFunctionToInstanceProcesses
            result = func1(inst_name, func2, [self._process_status])

        return result

    def detailedStatus(self, instance_name):
        raise NotImplementedError()

    def statusAll(self):
        result = []
        try:
            for instance in InstancesConf():
                result += self._callFunctionToInstanceProcesses(instance, self._process_status)
            return result
        except IOError as e:
            return CommandResultFailure(e.strerror)

    def detailedStatusAll(self):
        raise NotImplementedError()

    def _stop_process(self, instance):
        running = self.isRunning(instance.process_name)
        if not running:
            return CommandResultFailure(running)
        pid = self._getProcessPid(instance.process_name)
        sig = signal.SIGKILL if self.force else signal.SIGTERM
        os.kill(pid, sig)
        timeout = 1
        while timeout <= 5 and self.isRunning(instance.process_name):
            time.sleep(1)
            timeout += 1
        if self.isRunning(instance.process_name):
            return CommandResultFailure("%s: did not exit in time" % instance.process_name +
                                        "(pid='%d', signo='%d', timeout='%d')" %
                                         (pid, sig, timeout))
        else:
            return CommandResultSuccess("Instance %s stopped" % instance.process_name)

    def stop(self, instance_name):
        inst_name, process_num = Instance.splitInstanceName(instance_name)
        if process_num != None:
            result = self._stop_process(Instance(name=inst_name, process_num=process_num))
        else:
            func1 = self._searchInstanceThanCallFunctionWithParamsToInstance
            func2 = self._callFunctionToInstanceProcesses
            result = func1(inst_name, func2, [self._stop_process])

        return result

    def stopAll(self):
        result = []
        try:
            for instance in InstancesConf():
                result += self._callFunctionToInstanceProcesses(instance, self._stop_process)
            return result
        except IOError as e:
            return CommandResultFailure(e.strerror)
