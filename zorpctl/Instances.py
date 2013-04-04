from InstancesConf import InstancesConf
from ProcessAlgorithms import (StartAlgorithm, StopAlgorithm,
                                LogLevelAlgorithm , DeadlockCheckAlgorithm,
                                StatusAlgorithm, ReloadAlgorithm)
from CommandResults import CommandResultFailure

class ZorpHandler(object):

    @staticmethod
    def start():
        return ZorpHandler._callAlgorithmToAllInstances(StartAlgorithm())

    @staticmethod
    def stop():
        return ZorpHandler._callAlgorithmToAllInstances(StopAlgorithm())

    @staticmethod
    def reload():
        return ZorpHandler._callAlgorithmToAllInstances(ReloadAlgorithm())

    @staticmethod
    def status():
        return ZorpHandler._callAlgorithmToAllInstances(StatusAlgorithm())

    @staticmethod
    def detailedStatus():
        return ZorpHandler._callAlgorithmToAllInstances(StatusAlgorithm(StatusAlgorithm.DETAILED))

    @staticmethod
    def inclog():
        return ZorpHandler._callAlgorithmToAllInstances(LogLevelAlgorithm(LogLevelAlgorithm.INCREMENT))

    @staticmethod
    def declog():
        return ZorpHandler._callAlgorithmToAllInstances(LogLevelAlgorithm(LogLevelAlgorithm.DECREASE))

    @staticmethod
    def getlog():
        return ZorpHandler._callAlgorithmToAllInstances(LogLevelAlgorithm())

    @staticmethod
    def deadlockcheck(value):
        return ZorpHandler._callFunctionToAllInstances(DeadlockCheckAlgorithm(value))

    @staticmethod
    def _callAlgorithmToAllInstances(algorithm):
        result = []
        try:
            for instance in InstancesConf():
                result += InstanceHandler.executeAlgorithmOnInstanceProcesses(instance, algorithm)
            return result
        except IOError as e:
            return CommandResultFailure(e.strerror)

class InstanceHandler(object):

    @staticmethod
    def executeAlgorithmOnInstanceProcesses(instance, algorithm):
        result = []
        for i in range(0, instance.number_of_processes):
            instance.process_num = i
            algorithm.setInstance(instance)
            result.append(algorithm.run())

        return result

    @staticmethod
    def searchInstance(instance_name):
        try:
            for instance in InstancesConf():
                if instance.name == instance_name:
                    return instance
            return CommandResultFailure("instance %s not found!" % instance_name)
        except IOError as e:
            return CommandResultFailure(e.strerror)
