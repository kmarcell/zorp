import os, signal, time, subprocess
from szig import SZIG, SZIGError
from CommandResults import CommandResultSuccess, CommandResultFailure

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

class ProcessAlgorithm(object):

    def __init__(self):
        self.prefix = "" #TODO: @PREFIX@
        self.install_path = self.prefix + "/usr/lib/zorp/"
        self.force = False
        self.instance = None
        #variable indicates if force is active by force commands

    def isRunning(self, process):
        """
        Opening the right pidfile in the pidfile dir,
        checking if there is a running process with that pid,
        returning True if there is.

        FIXME: Delete pid file if there is no runnig processes with that pid
        """
        try:
            pid = self.getProcessPid(process)
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

    def getProcessPid(self, process):
        pid_file = open(self.prefix + '/var/run/zorp/zorp-' + process + '.pid')
        pid = int(pid_file.read())
        pid_file.close()

        return pid

    def setInstance(self, instance):
        self.instance = instance

    def run(self):
        if self.instance:
            return self.execute()
        else:
            return CommandResultFailure("No instance added!")

class StartAlgorithm(ProcessAlgorithm):

    def __init__(self):
        self.start_timeout = 5
        super(StartAlgorithm, self).__init__()

    def isValidInstanceForStart(self):
        if self.isRunning(self.instance.process_name):
            return CommandResultFailure("Process %s: is already running" % self.instance.process_name)
        if not self.instance.auto_start and not self.force:
            return CommandResultFailure("Process %s: has no-auto-start" % self.instance.process_name)
        if not 0 <= self.instance.process_num < self.instance.number_of_processes:
            return CommandResultFailure("Process number %d must be between 0 and %d"
                                        % (self.instance.process_num, self.instance.number_of_processes))
        return CommandResultSuccess()

    def assembleStartCommand(self):
        command = [self.install_path + "zorp", "--as"]
        command += self.instance.zorp_argv.split()
        command.append("--slave" if self.instance.process_num else "--master")
        command.append(self.instance.process_name)
        if self.instance.enable_core:
            command.append("--enable-core")
        if self.instance.auto_restart:
            command += ["--process-mode", "background"]
        return command

    def waitTilTimoutToStart(self):
        t = 1
        while t <= self.start_timeout and not self.isRunning(self.instance.process_name):
            time.sleep(1)
            t += 1

    def start(self):
        valid = self.isValidInstanceForStart()
        if not valid:
            return valid
        args = self.assembleStartCommand()

        subprocess.Popen(args, stderr=open("/dev/null", 'w'))
        self.waitTilTimoutToStart()

        running = self.isRunning(self.instance.process_name)
        return running if running else CommandResultFailure(
                                        "%s: did not start in time" % self.instance.process_name)

    def execute(self):
        return self.start()

class StopAlgorithm(ProcessAlgorithm):

    def __init__(self):
        self.stop_timeout = 5
        super(StopAlgorithm, self).__init__()

    def waitTilTimeoutToStop(self):
        t = 1
        while t <= self.stop_timeout and self.isRunning(self.instance.process_name):
            time.sleep(1)
            t += 1

    def stop(self):
        running = self.isRunning(self.instance.process_name)
        if not running:
            return CommandResultFailure(str(running))

        pid = self.getProcessPid(self.instance.process_name)
        sig = signal.SIGKILL if self.force else signal.SIGTERM
        os.kill(pid, sig)
        self.waitTilTimeoutToStop()

        if self.isRunning(self.instance.process_name):
            return CommandResultFailure(
                    "%s: did not exit in time (pid='%d', signo='%d', timeout='%d')" %
                    (self.instance.process_name, pid, sig, self.stop_timout))
        else:
            result = CommandResultSuccess("%s: stopped" % self.instance.process_name)
            return result

    def execute(self):
        return self.stop()

class ReloadAlgorithm(ProcessAlgorithm):

    def __init__(self):
        super(ReloadAlgorithm, self).__init__()

    def reload(self):
        running = self.isRunning(self.instance.process_name)
        if not running:
            return CommandResultFailure("%s: %s" % (self.instance.process_name, running),
                                        self.instance.process_name)
        szig = SZIG(self.instance.process_name)
        szig.reload()
        if szig.reload_result():
            result = CommandResultSuccess("%s: Reload successful" % self.instance.process_name)
        else:
            result = CommandResultFailure("%s: Reload failed" % self.instance.process_name,
                                          self.instance.process_name)
        return result

    def execute(self):
        return self.reload()

class DeadlockCheckAlgorithm(ProcessAlgorithm):

    def __init__(self, value=None):
        self.value = value
        super(DeadlockCheckAlgorithm, self).__init__()

    def getDeadlockcheck(self):
        running = self.isRunning(self.instance.process_name)
        if not running:
            return CommandResultFailure(str(running), self.instance.process_name)
        return "Instance: %s: deadlockcheck=%s" % (self.instance.process_name,
                                                   self.szig.deadlockcheck)

    def setDeadlockcheck(self, value):
        running = self.isRunning(self.instance.process_name)
        if not running:
            return CommandResultFailure(str(running), self.instance.process_name)
        self.szig.deadlockcheck = value
        return CommandResultSuccess(self.instance.process_name)

    def execute(self):
        try:
            self.szig = SZIG(self.instance.process_name)
        except IOError as e:
            return CommandResultFailure(e.strerror)
        if self.value != None:
            return self.setDeadlockcheck(self.value)
        else:
            return self.getDeadlockcheck()

class LogLevelAlgorithm(ProcessAlgorithm):

    INCREMENT = "I"
    DECREASE = "D"

    def __init__(self, value=None):
        self.value = value
        super(LogLevelAlgorithm, self).__init__()

    def modifyloglevel(self, value):
        running = self.isRunning(self.instance.process_name)
        if not running:
            return CommandResultFailure(str(running), self.instance.process_name)
        self.szig.loglevel = value
        return CommandResultSuccess(self.instance.process_name)

    def getloglevel(self):
        running = self.isRunning(self.instance.process_name)
        if not running:
            return CommandResultFailure(str(running), self.instance.process_name)
        return CommandResultSuccess("Instance: %s: verbose_level=%d, logspec='%s'" %
                                    (self.instance.process_name, self.szig.loglevel,
                                     self.szig.logspec), self.szig.loglevel)

    def execute(self):
        running = self.isRunning(self.instance.process_name)
        if not running:
            return running
        try:
            self.szig = SZIG(self.instance.process_name)
        except IOError as e:
            return CommandResultFailure(e.strerror)
        if not self.value:
            return self.getloglevel()
        else:
            value = self.getloglevel().value
            if self.value == "I":
                return self.modifyloglevel(value + 1) if value else value
            if self.value == "D":
                return self.modifyloglevel(value - 1) if value else value
            return self.modifyloglevel(self.value)

class StatusAlgorithm(ProcessAlgorithm):

    DETAILED = True

    def __init__(self, detailed=False):
        self.detailed = detailed
        super(StatusAlgorithm, self).__init__()

    def status(self):
        running = self.isRunning(self.instance.process_name)
        status = ProcessStatus(running)
        if running:
            status.pid = self.getProcessPid(self.instance.process_name)
            try:
                szig = SZIG(self.instance.process_name)
                status.threads = int(szig.get_value('stats.threads_running'))
                status.policy_file = szig.get_value('info.policy.file')
                timestamp_szig = szig.get_value('info.policy.file_stamp')
                timestamp_os = os.path.getmtime(status.policy_file)
                status.reloaded = str(timestamp_szig) == str(timestamp_os).split('.')[0]
            except IOError:
                return CommandResultFailure(
                        "Process %s: running, but error in socket communication" %
                        self.instance.process_name)

        return status

    def detailedStatus(self, status):
        raise NotImplementedError()


    def execute(self):
        if self.detailed:
            return self.detailedStatus()
        else:
            return self.status()

class CoredumpAlgorithm(ProcessAlgorithm):

    def coredump(self):
        szig = SZIG(self.instance.process_name)
        try:
            szig.coredump()
        except SZIGError as e:
            return CommandResultFailure(e.msg)
        return CommandResultSuccess("Instance:%s dumped core")

    def execute(self):
        return self.coredump()