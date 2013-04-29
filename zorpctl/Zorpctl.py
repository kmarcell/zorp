#!/usr/bin/env python
# vim: ft=python

import argparse
import subprocess
import json
import zorpctl.utils as utils
from zorpctl.UInterface import UInterface
from zorpctl.Instances import ZorpHandler, InstanceHandler
from zorpctl.InstanceClass import Instance
from zorpctl.ProcessAlgorithms import (StartAlgorithm, StopAlgorithm,
                                LogLevelAlgorithm , DeadlockCheckAlgorithm,
                                StatusAlgorithm, ReloadAlgorithm,
                                CoredumpAlgorithm, SzigWalkAlgorithm)

#TODO: Logging
"""
Questions:
- Do we want the @file option for files containing instance name lists?
- Is it a case when an instance does not have --num-of-processes?
- how can i determine detailedStatus?
"""

class Zorpctl(object):

    @staticmethod
    def runAlgorithmOnProcessOrInstance(instance_name, algorithm):
        try:
            name, number = Instance.splitInstanceName(instance_name)
        except ValueError:
            return "Instance: %s NOT RECOGNIZED!" % instance_name
        instance = InstanceHandler.searchInstance(name)
        if not instance:
            return instance
        if number != None:
            #number can be 0 which is false too
            instance.process_num = number
            algorithm.setInstance(instance)
            return algorithm.run()
        else:
            return InstanceHandler.executeAlgorithmOnInstanceProcesses(instance, algorithm)

    @staticmethod
    def runAlgorithmOnList(listofinstances, algorithm):
        for instance in listofinstances:
            result = Zorpctl.runAlgorithmOnProcessOrInstance(instance, algorithm)
            UInterface.informUser(result)

    @staticmethod
    def start(listofinstances):
        """
        Starts Zorp instance(s) by instance name
        expects sequence of name(s)
        """
        UInterface.informUser("Starting Zorp Firewall Suite:")

        if not listofinstances:
            UInterface.informUser(ZorpHandler.start())
        else:
            algorithm = StartAlgorithm()
            Zorpctl.runAlgorithmOnList(listofinstances, algorithm)

    @staticmethod
    def stop(listofinstances):
        """
        Stops Zorp instance(s) by instance name
        expects sequence of name(s)
        """
        UInterface.informUser("Stopping Zorp Firewall Suite:")

        if not listofinstances:
            UInterface.informUser(ZorpHandler.stop())
        else:
            algorithm = StopAlgorithm()
            Zorpctl.runAlgorithmOnList(listofinstances, algorithm)

    @staticmethod
    def restart(listofinstances):
        """
        Restarts Zorp instance(s) by instance name
        expects sequence of name(s)
        """
        UInterface.informUser("Restarting Zorp Firewall Suite:")
        Zorpctl.stop(listofinstances)
        Zorpctl.start(listofinstances)

    @staticmethod
    def reload(listofinstances):
        """
        Reloads Zorp instance(s) by instance name
        expects sequence of name(s)
        """
        UInterface.informUser("Reloading Zorp Firewall Suite:")

        if not listofinstances:
            UInterface.informUser(ZorpHandler.reload())
        else:
            algorithm = ReloadAlgorithm()
            Zorpctl.runAlgorithmOnList(listofinstances, algorithm)

    @staticmethod
    def force_start(listofinstances):
        """
        Starts Zorp instance(s) by instance name
        even if no-auto-start is set
        expects sequence of name(s)
        """
        UInterface.informUser("Starting Zorp Firewall Suite:")

        if not listofinstances:
            UInterface.informUser(ZorpHandler.force_start())
        else:
            algorithm = StartAlgorithm()
            algorithm.force
            Zorpctl.runAlgorithmOnList(listofinstances, algorithm)

    @staticmethod
    def force_stop(listofinstances):
        """
        Stops Zorp instance(s) by instance name
        with SIGKILL
        expects sequence of name(s)
        """
        UInterface.informUser("Stopping Zorp Firewall Suite:")

        if not listofinstances:
            UInterface.informUser(ZorpHandler.force_stop())
        else:
            algorithm = StopAlgorithm()
            algorithm.force = True
            Zorpctl.runAlgorithmOnList(listofinstances, algorithm)

    @staticmethod
    def force_restart(listofinstances):
        """
        Restarts Zorp instance(s) by instance name
        with force_stop and force_start
        expects sequence of name(s)
        """
        UInterface.informUser("Restarting Zorp Firewall Suite:")
        Zorpctl.force_stop(listofinstances)
        Zorpctl.force_start(listofinstances)


    @staticmethod
    def _restartWhichNotReloaded(reload_result):
        for result in reload_result:
            if result:
                UInterface.informUser(result)
            else:
                process_name = result.value
                Zorpctl.restart([process_name])

    @staticmethod
    def reload_or_restart(listofinstances):
        """
        Tries to reload Zorp instance(s) by instance name
        if not succeeded than tries to restart instance(s)
        expects sequence of name(s)
        """

        UInterface.informUser("Reloading or Restarting Zorp Firewall Suite:")
        if not listofinstances:
            reload_result = ZorpHandler.reload()
            Zorpctl._restartWhichNotReloaded(reload_result)
        else:
            for instance_name in listofinstances:
                reload_result = Zorpctl.runAlgorithmOnProcessOrInstance(instance_name, ReloadAlgorithm())
                if utils.isSequence(reload_result):
                    Zorpctl._restartWhichNotReloaded(reload_result)
                else:
                    if reload_result:
                        UInterface.informUser(reload_result)
                    else:
                        Zorpctl.restart([instance_name])

    def stop_session(self):
        raise NotImplementedError()

    @staticmethod
    def coredump(listofinstances):
        """
        Instructs Zorp instance(s) to dump core by instance_name
        expects sequence of name(s)
        """

        UInterface.informUser("Creating Zorp core dumps:")
        if not listofinstances:
            UInterface.informUser(ZorpHandler.coredump())
        else:
            algorithm = CoredumpAlgorithm()
            Zorpctl.runAlgorithmOnList(listofinstances, algorithm)

    @staticmethod
    def status(params):
        """
        Displays status of Zorp instance(s) by instance name
        expects sequence of name(s)
        can display more detailed status with -v or --verbose option
        """
        s_parse = argparse.ArgumentParser(
             prog='zorpctl status',
             description="Displays status of the specified Zorp instance(s)." +
                  "For additional information use status -v or --verbose option")
        s_parse.add_argument('-v', '--verbose', action='store_true')
        s_parse.add_argument('listofinstances', nargs='*')
        s_args = s_parse.parse_args(params)

        if not s_args.listofinstances:
            UInterface.informUser(ZorpHandler.detailedStatus() if s_args.verbose else ZorpHandler.status())
        else:
            algorithm = StatusAlgorithm(StatusAlgorithm.DETAILED) if s_args.verbose else StatusAlgorithm()
            Zorpctl.runAlgorithmOnList(s_args.listofinstances, algorithm)

    @staticmethod
    def authorize(params):
        """
        Lists and manages authorizations of Zorp instance(s) by instance name
        expects sequence of name(s)
        """
        a_parse = argparse.ArgumentParser(
             prog='zorpctl authorize',
             description="Lists and manages authorizations")
        a_parse.add_argument('--accept', dest='value', action='store_true', default=None)
        a_parse.add_argument('--reject', dest='value', action='store_false', default=None)
        a_parse.add_argument('description')
        a_parse.add_argument('listofinstances', nargs=argparse.REMAINDER)
        a_args = a_parse.parse_args(params)
        if a_args.value == None:
            UInterface.informUser("usage: zorpctl authorize [-h] --accept [--reject] description ...\n" +
                                  "zorpctl authorize: either the '--accept' or '--reject' option has to be specified")
            return
        print(a_args)

    def gui_status(self):
        raise NotImplementedError()

    @staticmethod
    def version(params):
        subprocess.call(['/usr/lib/zorp/zorp', "--version"])

    @staticmethod
    def inclog(listofinstances):
        """
        Raises log level of Zorp instance(s) by instance name
        expects sequence of name(s)
        """
        UInterface.informUser("Raising Zorp loglevel:")

        if not listofinstances:
            UInterface.informUser(ZorpHandler.inclog())
        else:
            algorithm = LogLevelAlgorithm(LogLevelAlgorithm.INCREMENT)
            Zorpctl.runAlgorithmOnList(listofinstances, algorithm)

    @staticmethod
    def declog(listofinstances):
        """
        Lowers log level of Zorp instance(s) by instance name
        expects sequence of name(s)
        """
        UInterface.informUser("Decreasing Zorp loglevel:")

        if not listofinstances:
            UInterface.informUser(ZorpHandler.declog())
        else:
            algorithm = LogLevelAlgorithm(LogLevelAlgorithm.DECREASE)
            Zorpctl.runAlgorithmOnList(listofinstances, algorithm)

    @staticmethod
    def log(listofinstances):
        """
        Displays log level of Zorp instance(s) by instance name
        expects sequence of name(s)
        """

        if not listofinstances:
            UInterface.informUser(ZorpHandler.getlog())
        else:
            algorithm = LogLevelAlgorithm()
            Zorpctl.runAlgorithmOnList(listofinstances, algorithm)

    @staticmethod
    def deadlockcheck(params):
        d_parse = argparse.ArgumentParser(
             prog='zorpctl deadlockcheck',
             description="Change and query Zorp deadlock checking settings")
        d_parse.add_argument('-d', '--disable', dest='value', action='store_false', default=None)
        d_parse.add_argument('-e', '--enable', dest='value', action='store_true', default=None)
        d_parse.add_argument('listofinstances', nargs=argparse.REMAINDER)
        d_args = d_parse.parse_args(params)

        if d_args.value != None:
            UInterface.informUser("Changing Zorp deadlock checking settings:")
            if not d_args.listofinstances:
                UInterface.informUser(ZorpHandler.deadlockcheck(d_args.value))
            else:
                algorithm = DeadlockCheckAlgorithm(d_args.value)
                Zorpctl.runAlgorithmOnList(d_args.listofinstances, algorithm)
        else:
            if not d_args.listofinstances:
                UInterface.informUser(ZorpHandler.deadlockcheck())
            else:
                algorithm = DeadlockCheckAlgorithm()
                Zorpctl.runAlgorithmOnList(d_args.listofinstances, algorithm)

    @staticmethod
    def szig(params):
        sz_parser = argparse.ArgumentParser(
                        prog='zorpctl szig',
                        description="Display internal information from the given Zorp instance(s)")
        sz_parser.add_argument('-w', '--walk', help='Walk the specified tree', nargs='*')
        sz_parser.add_argument('-r', '--root', help='Set the root node of the walk operation', type=str)
        sz_args = sz_parser.parse_args(params)

        if not sz_args.walk:
            for result in ZorpHandler.szig_walk(sz_args.root):
                UInterface.informUser(json.dumps(result.value, indent=4) if result else result)
        else:
            algorithm = SzigWalkAlgorithm(sz_args.root)
            for instance in sz_args.walk:
                results = Zorpctl.runAlgorithmOnProcessOrInstance(instance, algorithm)
                if utils.isSequence(results):
                    for result in results:
                        UInterface.informUser(json.dumps(result.value, indent=4) if result else result)
                else:
                    UInterface.informUser(json.dumps(results.value, indent=4) if results else results)

HelpMessage = (
'start' + '\t\t  Starts the specified Zorp instance(s)\n' +
'stop' + '\t\t  Stops the specified Zorp instance(s)\n' +
'restart' + '\t\t  Restart the specified Zorp instance(s)\n' +
'reload' + '\t\t  Reload the specified Zorp instance(s)\n' +
'force-start' + '\t  Starts the specified Zorp instance(s) even if they are disabled\n' +
'force-stop' + '\t  Forces the specified Zorp instance(s) to stop (SIGKILL)\n' +
'force-restart' + '\t  Forces the specified Zorp instance(s) to restart (SIGKILL)\n' +
'reload-or-restart' + ' Reload or restart the specified Zorp instance(s)\n' +
#'stop-session' + '\t  Stops the specified Zorp proxy session\n' +
'coredump' + '\t  Create core dumps of the specified Zorp instance(s)\n' +
'status' + '\t\t  Status of the specified Zorp instance(s). '+
            'For additional information use status -v or --verbose option\n' +
'authorize' + '\t  Lists and manages authorizations\n' +
#'gui-status' + '\t  Status of the specified Zorp instance(s)\n' +
'version' + '\t\t  Display Zorp version information\n' +
'inclog' + '\t\t  Raise the specified Zorp instance(s) log level by one\n' +
'declog' + '\t\t  Lower the specified Zorp instance(s) log level by one\n' +
'log' + '\t\t  Change and query Zorp log settings\n' +
'deadlockchek' + '\t  Change and query Zorp deadlock checking settings\n' +
'szig' + '\t\t  Display internal information from the given Zorp instance(s)'
)

parser = argparse.ArgumentParser(prog='zorpctl',
                                 description="Zorp Control tool.",
                                 usage='%(prog)s [command [options]] [-h] \n\n' + HelpMessage)
Commands = {
            'start' : Zorpctl.start,
            'stop' : Zorpctl.stop,
            'restart' : Zorpctl.restart,
            'reload' : Zorpctl.reload,
            'force-start' : Zorpctl.force_start,
            'force-stop' : Zorpctl.force_stop,
            'force-restart' : Zorpctl.force_restart,
            'reload-or-restart' : Zorpctl.reload_or_restart,
            #'stop-session' : Zorpctl.stop_session,
            'coredump' : Zorpctl.coredump,
            'status' : Zorpctl.status,
            'authorize' : Zorpctl.authorize,
            #'gui-status' : Zorpctl.gui_status,
            'version' : Zorpctl.version,
            'inclog' : Zorpctl.inclog,
            'declog' : Zorpctl.declog,
            'log' : Zorpctl.log,
            'deadlockcheck' : Zorpctl.deadlockcheck,
            'szig' : Zorpctl.szig,
            }

parser.add_argument('command', choices=Commands.keys())
parser.add_argument('params', nargs=argparse.REMAINDER)
args = parser.parse_args()

command_function = Commands.get(args.command)
command_function(args.params)
