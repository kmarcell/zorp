import os, sys, signal, time, subprocess, datetime
from zorpctl.szig import SZIG, SZIGError
from zorpctl.CommandResults import CommandResultSuccess, CommandResultFailure
import zorpctl.prefix

PATH_PREFIX = zorpctl.prefix.PATH_PREFIX
sys.path.append(PATH_PREFIX + '/etc/zorp')
import zorpctl_conf as ZORPCTLCONF

class ProcessStatus(object):
    def __init__(self, name):
        self.name = name
        self.reload_timestamp = 0
        self.details = None
        self.msg = ""

    def __str__(self):
        status = self.msg + "running"
        if not self.reloaded:
            status += ", policy NOT reloaded"
        status += ", %d threads active, pid %d" % (self.threads, self.pid)
        if self.details:
            status += "\n%s" % self.details
        return status

class ProcessAlgorithm(object):

    def __init__(self):
        self.prefix = PATH_PREFIX
        self.install_path = self.prefix + ZORPCTLCONF.INSTALL_DIR + '/'
        self.pidfiledir = ZORPCTLCONF.PIDFILE_DIR
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

        pid = self.getProcessPid(process)
        if not pid:
            if pid.value == "Permission denied":
                return CommandResultFailure(pid.value)
            else:
                return CommandResultFailure("Process not running")

        try:
            open('/proc/' + str(pid) + '/status')
        except IOError:
            return CommandResultFailure("Invalid pid file no running process with pid %d!" % pid)

        return CommandResultSuccess("running")

    def getProcessPid(self, process):
        try:
            file_name = self.prefix + self.pidfiledir  + '/zorp-' + process + '.pid'
            pid_file = open(file_name)
            pid = int(pid_file.read())
            pid_file.close()
        except IOError as e:
            return CommandResultFailure("Can not open %s" % file_name, e.strerror)

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

    def errorHandling(self):
        running = self.isRunning(self.instance.process_name)
        if running:
            return CommandResultSuccess("process is already running")
        valid = self.isValidInstanceForStart()
        if not valid:
            return valid

    def isValidInstanceForStart(self):
        if not 0 <= self.instance.process_num < self.instance.number_of_processes:
            return CommandResultFailure("number %d must be between [0..%d)"
                                        % (self.instance.process_num, self.instance.number_of_processes))
        if not self.instance.auto_start and not self.force:
            return CommandResultFailure("not started, because no-auto-start is set")

        return CommandResultSuccess()

    def assembleStartCommand(self):
        command = [self.install_path + "zorp", "--as", self.instance.name]
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
        args = self.assembleStartCommand()
        try:
            subprocess.Popen(args, stderr=open("/dev/null", 'w'))
        except OSError:
            pass
        self.waitTilTimoutToStart()
        running = self.isRunning(self.instance.process_name)
        if running:
            return CommandResultSuccess(running)
        else:
            return  CommandResultFailure("did not start in time")

    def execute(self):
        error = self.errorHandling()
        if error != None:
            return error

        return self.start()

class StopAlgorithm(ProcessAlgorithm):

    def __init__(self):
        self.stop_timeout = 5
        super(StopAlgorithm, self).__init__()

        self.pid = None

    def errorHandling(self):
        running = self.isRunning(self.instance.process_name)
        if not running:
            return running

    def waitTilTimeoutToStop(self):
        t = 1
        while t <= self.stop_timeout and self.isRunning(self.instance.process_name):
            time.sleep(1)
            t += 1

    def killProcess(self, sig):
        self.pid = self.getProcessPid(self.instance.process_name)
        try:
            os.kill(self.pid, sig)
            return CommandResultSuccess()
        except OSError as e:
            return CommandResultFailure(e.strerror)

    def stop(self):
        sig = signal.SIGKILL if self.force else signal.SIGTERM
        isKilled = self.killProcess(sig)
        if not isKilled:
            return isKilled

        self.waitTilTimeoutToStop()
        if self.isRunning(self.instance.process_name):
            return CommandResultFailure(
                    "did not exit in time (pid='%d', signo='%d', timeout='%d')" %
                    (self.pid, sig, self.stop_timout))
        else:
            return CommandResultSuccess("stopped")

    def execute(self):
        error = self.errorHandling()
        if error != None:
            return error

        return self.stop()

class ReloadAlgorithm(ProcessAlgorithm):

    def __init__(self):
        super(ReloadAlgorithm, self).__init__()

    def errorHandling(self):
        running = self.isRunning(self.instance.process_name)
        if not running:
            return running
        try:
            self.szig = SZIG(self.instance.process_name)
        except IOError as e:
            return CommandResultFailure(e.strerror)

    def reload(self):
        self.szig.reload()
        if self.szig.reload_result():
            result = CommandResultSuccess("Reload successful")
        else:
            result = CommandResultFailure("Reload failed")
        return result

    def execute(self):
        error = self.errorHandling()
        if error != None:
            error.value = self.instance.process_name
            return error

        try:
            reloaded = self.reload()
        except SZIGError as e:
            reloaded = CommandResultFailure("error while communicating through szig: %s" % e.msg)
        if not reloaded:
            reloaded.value = self.instance.process_name
        return reloaded

class DeadlockCheckAlgorithm(ProcessAlgorithm):

    def __init__(self, value=None):
        self.value = value
        super(DeadlockCheckAlgorithm, self).__init__()

    def errorHandling(self):
        running = self.isRunning(self.instance.process_name)
        if not running:
            return running
        try:
            self.szig = SZIG(self.instance.process_name)
        except IOError as e:
            return CommandResultFailure(e.strerror)

    def getDeadlockcheck(self):
        return CommandResultSuccess("deadlockcheck=%s" % self.szig.deadlockcheck)

    def setDeadlockcheck(self, value):
        self.szig.deadlockcheck = value
        return CommandResultSuccess("")

    def execute(self):
        error = self.errorHandling()
        if error != None:
            return error

        try:
            if self.value != None:
                return self.setDeadlockcheck(self.value)
            else:
                return self.getDeadlockcheck()
        except SZIGError as e:
            return CommandResultFailure("error while communicating through szig: %s" % e.msg)

class LogLevelAlgorithm(ProcessAlgorithm):

    INCREMENT = "I"
    DECREASE = "D"

    def __init__(self, value=None):
        self.value = value
        super(LogLevelAlgorithm, self).__init__()

    def errorHandling(self):
        running = self.isRunning(self.instance.process_name)
        if not running:
            return running
        try:
            self.szig = SZIG(self.instance.process_name)
        except IOError as e:
            return CommandResultFailure(e.strerror)

    def modifyloglevel(self, value):
        self.szig.loglevel = value
        return CommandResultSuccess()

    def getloglevel(self):
        return CommandResultSuccess("verbose_level=%d, logspec='%s'" %
                                    (self.szig.loglevel, self.szig.logspec),
                                    self.szig.loglevel)

    def execute(self):
        error = self.errorHandling()
        if error != None:
            return error

        try:
            if not self.value:
                return self.getloglevel()
            else:
                value = self.getloglevel().value
                if self.value == "I":
                    return self.modifyloglevel(value + 1) if value else value
                if self.value == "D":
                    return self.modifyloglevel(value - 1) if value else value
                return self.modifyloglevel(self.value)
        except SZIGError as e:
            return CommandResultFailure("error while communicating through szig: %s" % e.msg)

class GetProcInfoAlgorithm(ProcessAlgorithm):

    def __init__(self):
        super(GetProcInfoAlgorithm, self).__init__()

    def errorHandling(self):
        running = self.isRunning(self.instance.process_name)
        if not running:
            return running
        pid = self.getProcessPid(self.instance.process_name)
        try:
            self.procinfo_file = open("/proc/%s/stat" % pid, 'r')
        except IOError:
            return CommandResultFailure("Can not open /proc/%s/stat" % pid)

    def getProcInfo(self):
        values = self.procinfo_file.read().split()
        self.procinfo_file.close()
        keys = ("pid", "comm", "state", "ppid", "pgrp", "session", "tty_nr",
                "tpgid", "flags", "minflt", "cminflt", "majflt", "cmajflt",
                "utime", "stime", "cutime", "cstime", "priority", "nice",
                "_dummyzero", "itrealvalue", "starttime", "vsize", "rss",
                "rlim", "startcode", "endcode", "startstack", "kstkesp",
                "kstkeip", "signal", "blocked", "sigignore", "sigcatch",
                "wchan", "nswap", "cnswap", "exit_signal", "processor")
        proc_info = {}
        for value, key in zip(values, keys):
            proc_info[key] = value
        return proc_info

    def execute(self):
        error = self.errorHandling()
        if error != None:
            return error

        return self.getProcInfo()

class StatusAlgorithm(ProcessAlgorithm):

    def __init__(self):
        super(StatusAlgorithm, self).__init__()

    def errorHandling(self):
        running = self.isRunning(self.instance.process_name)
        if not running:
            return running
        try:
            self.szig = SZIG(self.instance.process_name)
        except IOError as e:
            return CommandResultFailure(e.strerror)

    def status(self):
        status = ProcessStatus(self.instance.process_name)
        status.pid = self.getProcessPid(self.instance.process_name)

        status.threads = int(self.szig.get_value('stats.threads_running'))
        status.policy_file = self.szig.get_value('info.policy.file')
        status.timestamp_szig = self.szig.get_value('info.policy.file_stamp')
        status.reload_timestamp = self.szig.get_value('info.policy.reload_stamp')
        status.timestamp_os = os.path.getmtime(status.policy_file)
        status.reloaded = str(status.timestamp_szig) == str(status.timestamp_os).split('.')[0]

        return status

    def execute(self):
        error = self.errorHandling()
        if error != None:
            return error

        try:
            return self.status()
        except SZIGError as e:
            return CommandResultFailure("error while communicating through szig: %s" % e.msg)

class DetailedStatusAlgorithm(ProcessAlgorithm):

    def __init__(self):
        super(DetailedStatusAlgorithm, self).__init__()
        self.uptime_filename = '/proc/uptime'
        self.proc_stat_filename = '/proc/stat'

    def errorHandling(self):
        running = self.isRunning(self.instance.process_name)
        if not running:
            return running
        try:
            self.stat_file = open(self.proc_stat_filename, 'r')
        except IOError:
            return CommandResultFailure("Can not open %s" % self.proc_stat_filename)
        try:
            uptime_file = open(self.uptime_filename, 'r')
            uptime_file.close()
        except IOError:
            return CommandResultFailure("Can not open %s" % self.uptime_filename)

    def _getIdleJiffies(self):
        for buf in self.stat_file:
            if (buf[:4] == "cpu "):
                idle_jiffies = float(buf.split()[4])
                break
        self.stat_file.close()
        return idle_jiffies

    def _getIdleSec(self):
        uptime_file = open(self.uptime_filename, 'r')
        idle_sec = float(uptime_file.readline().split()[1])
        uptime_file.close()

        return idle_sec

    def getJiffiesPerSec(self):
        idle_jiffies = self._getIdleJiffies()
        idle_sec = self._getIdleSec()

        jiffies_per_sec = int(round(5 + (idle_jiffies/idle_sec), -1))
        return jiffies_per_sec

    def _getProcInfo(self):
        algorithm = GetProcInfoAlgorithm()
        algorithm.setInstance(self.instance)
        return algorithm.run()

    def _getLoaded(self, stamp):
        return datetime.datetime.fromtimestamp(float(stamp))

    def _getTimes(self, proc_info, jps):
        usertime = float(proc_info['utime']) / jps
        usermin = int(usertime / 60)
        usertime -= usermin * 60

        systime = float(proc_info["stime"]) / jps
        sysmin = int(systime / 60)
        systime -= sysmin * 60

        realtime = usertime + systime
        realmin = int(realtime / 60)
        realtime -= realmin * 60

        return (realmin, realtime, usermin, usertime, sysmin, systime)

    def _getStartTime(self, proc_info, jps):
        uptime_file = open(self.uptime_filename, 'r')
        uptime_float = float(uptime_file.readline().split()[0])
        uptime_file.close()
        uptime = datetime.datetime.fromtimestamp(uptime_float)
        uptime_timedelta = uptime - datetime.datetime.fromtimestamp(0)

        now = datetime.datetime.now()
        starttime = (now - (uptime_timedelta) +
                            (datetime.datetime.fromtimestamp(float(proc_info["starttime"]) / jps) -
                             datetime.datetime.fromtimestamp(0)))
        return starttime

    def assembleDetails(self, status, proc_info, jps):
        PAGESIZE = 4 #getconf PAGESIZE in kB (40940966)
        details = "started at: %s\n" % self._getStartTime(proc_info, jps)
        details += "policy: file=%s, loaded=%s\n" % (status.policy_file, self._getLoaded(status.reload_timestamp))
        details += "cpu: real=%d:%f, user=%d:%f, sys=%d:%f\n" % self._getTimes(proc_info, jps)
        details += "memory: vsz=%skB, rss=%skB" % (int(proc_info["vsize"])/1024, int(proc_info["rss"]) * PAGESIZE)

        return details

    def detailedStatus(self):
        statusalgorithm = StatusAlgorithm()
        statusalgorithm.setInstance(self.instance)
        status = statusalgorithm.run()

        jps = self.getJiffiesPerSec()
        proc_info = self._getProcInfo()

        status.details = self.assembleDetails(status, proc_info, jps)

        return status

    def execute(self):
        error = self.errorHandling()
        if error != None:
            return error

        return self.detailedStatus()

class CoredumpAlgorithm(ProcessAlgorithm):

    def __init__(self):
        super(CoredumpAlgorithm, self).__init__()

    def errorHandling(self):
        running = self.isRunning(self.instance.process_name)
        if not running:
            return running
        try:
            self.szig = SZIG(self.instance.process_name)
        except IOError as e:
            return CommandResultFailure(e.strerror)
        return None

    def coredump(self):
        try:
            self.szig.coredump()
        except SZIGError as e:
            return CommandResultFailure(e.msg)
        return CommandResultSuccess("core successfully dumped")

    def execute(self):
        error = self.errorHandling()
        if error != None:
            return error

        try:
            return self.coredump()
        except SZIGError as e:
            return CommandResultFailure("error while communicating through szig: %s" % e.msg)

class SzigWalkAlgorithm(ProcessAlgorithm):

    def __init__(self, root=""):
        self.root = root
        super(SzigWalkAlgorithm, self).__init__()

    def errorHandling(self):
        running = self.isRunning(self.instance.process_name)
        if not running:
            return running
        try:
            self.szig = SZIG(self.instance.process_name)
        except IOError as e:
            return CommandResultFailure(e.strerror)
        return None

    def getChilds(self, node):
        child = self.szig.get_child(node)
        if child:
            result = {}
            result[child.split('.')[-1]] = self.walk(child)
            sibling = self.szig.get_sibling(child)
            while sibling:
                result[sibling.split('.')[-1]] = self.walk(sibling)
                sibling = self.szig.get_sibling(sibling)
            return result
        else:
            return None

    def walk(self, node):
        value = self.szig.get_value(node)
        if value != None:
            return value
        else:
            return self.getChilds(node)

    def execute(self):
        error = self.errorHandling()
        if error != None:
            return error

        try:
            return CommandResultSuccess("",
                {self.root if self.root else self.instance.process_name : self.walk(self.root)})
        except SZIGError as e:
            return CommandResultFailure("error while communicating through szig: %s" % e.msg)

class AuthorizeAlgorithm(ProcessAlgorithm):

    ACCEPT = True
    REJECT = False

    def __init__(self, accept, description):
        self.accept = accept
        self.description = description
        super(AuthorizeAlgorithm, self).__init__()

    def errorHandling(self):
        running = self.isRunning(self.instance.process_name)
        if not running:
            return running
        try:
            self.szig = SZIG(self.instance.process_name)
        except IOError as e:
            return CommandResultFailure(e.strerror)
        return None

    def accept(self):
        raise NotImplementedError()

    def reject(self):
        raise NotImplementedError()

    def execute(self):
        error = self.errorHandling()
        if error != None:
            return error

        try:
            if self.accept:
                self.accept()
            else:
                self.reject()
        except SZIGError as e:
            return CommandResultFailure("error while communicating through szig: %s" % e.msg)
