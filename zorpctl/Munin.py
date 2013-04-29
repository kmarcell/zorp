from zorpctl.szig import SZIG
from zorpctl.ProcessAlgorithms import ProcessAlgorithm, GetProcInfoAlgorithm
from zorpctl.CommandResults import CommandResultFailure, CommandResultSuccess
from zorpctl.InstancesConf import InstancesConf

class RunningInstances(object):

    def __init__(self):
        self.instancesconf = InstancesConf()

    def __iter__(self):
        return self

    def next(self):
        instance = self.instancesconf.next()
        instance.process_num = 0
        algorithm = ProcessAlgorithm()
        algorithm.setInstance(instance)
        if algorithm.isRunning(instance.process_name):
            return instance
        else:
            return self.next()

class GetAlgorithm(ProcessAlgorithm):

    def __init__(self):
        super(GetAlgorithm, self).__init__()

    def get(self):
        raise NotImplementedError()

    def execute(self):
        running = self.isRunning(self.instance.process_name)
        if not running:
            return CommandResultFailure("%s: %s", (self.instance.process_name, running))
        try:
            self.szig = SZIG(self.instance.process_name)
        except IOError as e:
            return CommandResultFailure(e.strerror)
        return CommandResultSuccess("", self.get())

class GetSessionsRunningAlgorithm(GetAlgorithm):

    def get(self):
        result = self.szig.get_value('stats.sessions_running')
        return int(result) if result else 0

class GetThreadRateAlgorithm(GetAlgorithm):

    def get(self):
        """
        Minus one value shows some error happened.
        """
        result = {}
        _max = self.szig.get_value('stats.thread_rate_max')
        result["max"] = int(_max) if _max != None else -1
        _avg15 = self.szig.get_value('stats.thread_rate_avg15')
        result["avg15"] = int(_avg15) if _avg15 != None else -1
        _avg5 = self.szig.get_value('stats.thread_rate_avg5')
        result["avg5"] = int(_avg5) if _avg5 != None else -1
        _avg1 = self.szig.get_value('stats.thread_rate_avg1')
        result["avg1"] = int(_avg1) if _avg1 != None else -1

        return result

class GetThreadsRunningAlgorithm(GetAlgorithm):

    def get(self):
        result = self.szig.get_value('stats.threads_running')
        return int(result) if result else 0

class GetMemoryRSSAlgorithm(ProcessAlgorithm):

   def __init__(self):
       super(GetMemoryRSSAlgorithm, self).__init__()

   def get(self):
       algorithm = GetProcInfoAlgorithm()
       algorithm.setInstance(self.instance)
       proc_info = algorithm.run()
       if not proc_info:
           return proc_info
       return CommandResultSuccess("", int(proc_info["rss"]))

   def execute(self):
       running = self.isRunning(self.instance.process_name)
       if not running:
            return CommandResultFailure("%s: %s", (self.instance.process_name, running))
       return self.get()

class GetMemoryVSZAlgorithm(ProcessAlgorithm):

   def __init__(self):
       super(GetMemoryVSZAlgorithm, self).__init__()

   def get(self):
       algorithm = GetProcInfoAlgorithm()
       algorithm.setInstance(self.instance)
       proc_info = algorithm.run()
       if not proc_info:
           return proc_info
       return CommandResultSuccess("", int(proc_info["vsize"]))

   def execute(self):
       running = self.isRunning(self.instance.process_name)
       if not running:
            return CommandResultFailure("%s: %s", (self.instance.process_name, running))
       return self.get()
