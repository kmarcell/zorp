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
    def __init__(self, msg = None, value = None):
        self.value = value
        super(CommandResultSuccess, self).__init__(msg)

    def __nonzero__(self):
        return True

class CommandResultFailure(CommandResult):
    def __init__(self, msg = None, value = None):
        self.value = value
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

    def startAll(self):
        return self._callFunctionToAllInstances(self.start)

    def stopAll(self):
        return self._callFunctionToAllInstances(self.stop)

    def reloadAll(self):
        return self._callFunctionToAllInstances(self.reload)

    def statusAll(self):
        return self._callFunctionToAllInstances(self.status)

    def detailedStatusAll(self):
        return self._callFunctionToAllInstances(self.detailedStatus)

    def inclogAll(self):
        return self._callFunctionToAllInstances(self.inclog)

    def declogAll(self):
        return self._callFunctionToAllInstances(self.declog)

    def getlogAll(self):
        return self._callFunctionToAllInstances(self.getlog)

    def deadlockcheckAll(self, value):
        return self._callFunctionToAllInstances(self.deadlockcheck, value)

    def start(self, instance_name):
        inst_name, process_num = Instance.splitInstanceName(instance_name)
        instance = self._searchInstance(inst_name)
        if not instance:
            return instance
        if process_num != None:
            #process_num can be zero which is not None but it is a False in statements
            result = self._setProcessNumThanStart(instance, process_num)
        else:
            result = self._callFunctionToInstanceProcesses(instance, self._start_process)

        return result

    def stop(self, instance_name):
        return self._callFuntionToProcessOrInstance(instance_name, self._stop_process)

    def reload(self, instance_name):
        return self._callFuntionToProcessOrInstance(instance_name, self._reload_process)

    def status(self, instance_name):
        return self._callFuntionToProcessOrInstance(instance_name, self._process_status)

    def detailedStatus(self, instance_name):
        inst_name, process_num = Instance.splitInstanceName(instance_name)
        if process_num != None:
            result = self._setDetailedStatus(self.status(instance_name))
        else:
            result = []
            for status in self.status(inst_name):
                result.append(self._setDetailedStatus(status))

        return result

    def inclog(self, instance_name):
        return self._callFuntionToProcessOrInstance(instance_name, self._raiseloglevel)

    def declog(self, instance_name):
        return self._callFuntionToProcessOrInstance(instance_name, self._lowerloglevel)

    def getlog(self, instance_name):
        return self._callFuntionToProcessOrInstance(instance_name, self._getloglevel)

    def deadlockcheck(self, instance_name, value):
        if value == None:
            function = self._getDeadlockcheck
        else:
            function = self._enableDeadlockcheck if value else self._disableDeadlockcheck

        return self._callFuntionToProcessOrInstance(instance_name, function)

    def _callFuntionToProcessOrInstance(self, instance_name, function):
        inst_name, process_num = Instance.splitInstanceName(instance_name)
        if process_num != None:
            #process_num can be zero which is not None but it is a False in statements
            result = function(Instance(name=inst_name, process_num=process_num))
        else:
            instance = self._searchInstance(inst_name)
            if not instance:
                return CommandResultFailure("instance %s not found!" % instance_name)
            result = self._callFunctionToInstanceProcesses(instance, function)

        return result

    def _start_process(self, instance):
        if self.isRunning(instance.process_name):
            return CommandResultFailure("Process %s: is already running" % instance.process_name,
                                        instance.process_name)
        if not instance.auto_start and not self.force:
            return CommandResultFailure("Process %s: has no-auto-start" % instance.process_name,
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

    def _stop_process(self, instance):
        running = self.isRunning(instance.process_name)
        if not running:
            return CommandResultFailure(str(running), instance.process_name)
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
                                         (pid, sig, timeout), instance.process_name)
        else:
            return CommandResultSuccess("%s: stopped" % instance.process_name,
                                        instance.process_name)

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

    def _process_status(self, instance):
        running = self.isRunning(instance.process_name)
        status = ProcessStatus(running)
        if running:
            status.pid = self._getProcessPid(instance.process_name)
            try:
                szig = SZIG(self.pidfile_dir + 'zorpctl.' + instance.process_name)
                status.threads = int(szig.get_value('stats.threads_running'))
                status.policy_file = szig.get_value('info.policy.file')
                timestamp_szig = szig.get_value('info.policy.file_stamp')
                timestamp_os = os.path.getmtime(status.policy_file)
                status.reloaded = str(timestamp_szig) == str(timestamp_os).split('.')[0]
            except IOError:
                return CommandResultFailure(
                        "Process %s: running, but error in socket communication" % instance.process_name)

        return status

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

    def _getProcessPid(self, process):
        pid_file = open(self.pidfile_dir + 'zorp-' + process + '.pid')
        pid = int(pid_file.read())
        pid_file.close()

        return pid

    def _setDetailedStatus(self, status):
        raise NotImplementedError()

    def _modifyloglevel(self, process, value):
        running = self.isRunning(process)
        if not running:
            return CommandResultFailure(str(running), process)
        szig = SZIG(self.pidfile_dir + 'zorpctl.' + process)
        szig.loglevel = szig.loglevel + value
        return CommandResultSuccess(process)

    def _raiseloglevel(self, instance):
        return self._modifyloglevel(instance.process_name, 1)

    def _lowerloglevel(self, instance):
        return self._modifyloglevel(instance.process_name, -1)

    def _getloglevel(self, instance):
        running = self.isRunning(instance.process_name)
        if not running:
            return CommandResultFailure(str(running), instance.process_name)
        szig = SZIG(self.pidfile_dir + 'zorpctl.' + instance.process_name)
        return CommandResultSuccess("Instance: %s: verbose_level=%d, logspec='%s'" %
                                    (instance.process_name, szig.loglevel, szig.logspec))

    def _searchInstance(self, instance_name):
        try:
            for instance in InstancesConf():
                if instance.name == instance_name:
                    return instance
            return None
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

    def _callFunctionToAllInstances(self, function, args=None):
        result = []
        try:
            for instance in InstancesConf():
                if args:
                    result += function(instance.name, args)
                else:
                    result += function(instance.name)
            return result
        except IOError as e:
            return CommandResultFailure(e.strerror)

    def _getDeadlockcheck(self, instance):
        running = self.isRunning(instance.process_name)
        if not running:
            return CommandResultFailure(str(running), instance.process_name)
        szig = SZIG(self.pidfile_dir + 'zorpctl.' + instance.process_name)
        return "Instance: %s: deadlockcheck=%s" % (instance.process_name, szig.deadlockcheck)

    def _setDeadlockcheck(self, instance, value):
        running = self.isRunning(instance.process_name)
        if not running:
            return CommandResultFailure(str(running), instance.process_name)
        szig = SZIG(self.pidfile_dir + 'zorpctl.' + instance.process_name)
        szig.deadlockcheck = value
        return CommandResultSuccess(instance.process_name)

    def _enableDeadlockcheck(self, instance):
        return self._setDeadlockcheck(instance, True)

    def _disableDeadlockcheck(self, instance):
        return self._setDeadlockcheck(instance, False)
