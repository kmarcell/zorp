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
        return self.get()
 
class GetServicesAlgorithm(ProcessAlgorithm):

    def __init__(self):
        super(GetServicesAlgorithm, self).__init__()

    def services(self):
        services = []
        service = self.szig.get_child("service")
        while service:
            services.append(service)
            service = self.szig.get_sibling(service)
        return CommandResultSuccess("", services)

    def execute(self):
        try:
            self.szig = SZIG(self.instance.process_name)
        except IOError as e:
            return CommandResultFailure(e.strerror)
        try:
            return self.services() 
        except SZIGError as e:
            return CommandResultFailure("error while communicating through szig: %s" % e.msg)

class GetServiceRateAlgorithm(GetAlgorithm):

    def __init__(self):
        super(GetServiceRateAlgorithm, self).__init__()

    def get(self):
        avg = {}
        algorithm = GetServicesAlgorithm()
        algorithm.setInstance(self.instance)
        services = algorithm.run()
        if not services:
            return services
        for service in services.value:
            avg1 = int(self.szig.get_value("service." + service + ".rate_avg1"))
            avg5 = int(self.szig.get_value("service." + service + ".rate_avg5"))
            avg15 = int(self.szig.get_value("service." + service + ".rate_avg15"))
            avg[service] = {"avg1" : avg1, "avg5" : avg5, "avg15" : avg15}

        return avg
