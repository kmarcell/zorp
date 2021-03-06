from zorpctl.InstancesConf import InstancesConf
from zorpctl.ProcessAlgorithms import (StartAlgorithm, StopAlgorithm,
                                LogLevelAlgorithm , DeadlockCheckAlgorithm,
                                StatusAlgorithm, ReloadAlgorithm, CoredumpAlgorithm,
                                SzigWalkAlgorithm, DetailedStatusAlgorithm)
from zorpctl.CommandResults import CommandResultFailure

class ZorpHandler(object):

    @staticmethod
    def start():
        return ZorpHandler.callAlgorithmToAllInstances(StartAlgorithm())

    @staticmethod
    def force_start():
        algorithm = StartAlgorithm()
        algorithm.force = True
        return ZorpHandler.callAlgorithmToAllInstances(algorithm)

    @staticmethod
    def stop():
        return ZorpHandler.callAlgorithmToAllInstances(StopAlgorithm())

    @staticmethod
    def force_stop():
        algorithm = StopAlgorithm()
        algorithm.force = True
        return ZorpHandler.callAlgorithmToAllInstances(algorithm)

    @staticmethod
    def reload():
        return ZorpHandler.callAlgorithmToAllInstances(ReloadAlgorithm())

    @staticmethod
    def status():
        return ZorpHandler.callAlgorithmToAllInstances(StatusAlgorithm())

    @staticmethod
    def detailedStatus():
        return ZorpHandler.callAlgorithmToAllInstances(DetailedStatusAlgorithm())

    @staticmethod
    def inclog():
        return ZorpHandler.callAlgorithmToAllInstances(LogLevelAlgorithm(LogLevelAlgorithm.INCREMENT))

    @staticmethod
    def declog():
        return ZorpHandler.callAlgorithmToAllInstances(LogLevelAlgorithm(LogLevelAlgorithm.DECREASE))

    @staticmethod
    def getlog():
        return ZorpHandler.callAlgorithmToAllInstances(LogLevelAlgorithm())

    @staticmethod
    def deadlockcheck(value=None):
        return ZorpHandler.callAlgorithmToAllInstances(DeadlockCheckAlgorithm(value))

    @staticmethod
    def coredump():
        return ZorpHandler.callAlgorithmToAllInstances(CoredumpAlgorithm())

    @staticmethod
    def szig_walk(root):
        return ZorpHandler.callAlgorithmToAllInstances(SzigWalkAlgorithm(root))

    @staticmethod
    def callAlgorithmToAllInstances(algorithm):
        result = []
        try:
            for instance in InstancesConf():
                result += InstanceHandler.executeAlgorithmOnInstanceProcesses(instance, algorithm)
            return result
        except BaseException as e:
            return CommandResultFailure(e.strerror)

class InstanceHandler(object):

    @staticmethod
    def executeAlgorithmOnInstanceProcesses(instance, algorithm):
        results = []
        for i in range(0, instance.number_of_processes):
            instance.process_num = i
            algorithm.setInstance(instance)
            result = algorithm.run()
            result.msg = "%s: %s" % (instance.process_name, result.msg)
            results.append(result)

        return results

    @staticmethod
    def searchInstance(instance_name):
        try:
            for instance in InstancesConf():
                if instance.name == instance_name:
                    return instance
            return CommandResultFailure("instance %s not found!" % instance_name)
        except IOError as e:
            return CommandResultFailure(e.strerror)
