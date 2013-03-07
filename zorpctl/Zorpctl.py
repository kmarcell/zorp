import argparse
from UInterface import UInterface
from Instances import InstanceHandler

#TODO: Logging

class Zorpctl(object):

    @staticmethod
    def start(params):
        """
        Starts Zorp instance(s) by instance name
        expects sequence of name(s)
        """
        UInterface.informUser("Starting Zorp Firewall Suite:")

        handler = InstanceHandler()
        if not params:
            handler.startAll()
        else:
            for instance in params:
                if handler.isRunning(instance):
                    UInterface.informUser("%s instance is already running!" % instance)
                else:
                    result = handler.start(instance)
                    UInterface.informUser(result)
        for instance in params:
            handler = InstanceHandler()
            if handler.isRunning(instance):
                UInterface.informUser("%s instance is already running!" % instance)
            else:
                result = handler.start(instance)
                UInterface.informUser(result)

    def stop(self):
        raise NotImplementedError()

    def restart(self):
        raise NotImplementedError()

    def reload(self):
        raise NotImplementedError()

    def force_start(self):
        raise NotImplementedError()

    def force_stop(self):
        raise NotImplementedError()

    def force_restart(self):
        raise NotImplementedError()

    def reload_or_restart(self):
        raise NotImplementedError()

    def stop_session(self):
        raise NotImplementedError()

    def coredump(self):
        raise NotImplementedError()

    def status(self):
        raise NotImplementedError()

    def authorize(self):
        raise NotImplementedError()

    def gui_status(self):
        raise NotImplementedError()

    def version(self):
        raise NotImplementedError()

    def inclog(self):
        raise NotImplementedError()

    def declog(self):
        raise NotImplementedError()

    def log(self):
        raise NotImplementedError()

    def deadlockcheck(self):
        raise NotImplementedError()

    def szig(self):
        raise NotImplementedError()

HelpMessage = (
'start' + '\t\t  Starts the specified Zorp instance(s)\n' +
'stop' + '\t\t  Stops the specified Zorp instance(s)\n' +
'restart' + '\t\t  Restart the specified Zorp instance(s)\n' +
'reload' + '\t\t  Reload the specified Zorp instance(s)\n' +
'force-start' + '\t  Starts the specified Zorp instance(s) even if they are disabled\n' +
'force-stop' + '\t  Forces the specified Zorp instance(s) to stop (SIGKILL)\n' +
'force-restart' + '\t  Forces the specified Zorp instance(s) to restart (SIGKILL)\n' +
'reload-or-restart' + ' Reload or restart the specified Zorp instance(s)\n' +
'stop-session' + '\t  Stops the specified Zorp proxy session\n' +
'coredump' + '\t  Create core dumps of the specified Zorp instance(s)\n' +
'status' + '\t\t  Status of the specified Zorp instance(s). '+
            'For additional information use status -v or --verbose option\n' +
'authorize' + '\t  Lists and manages authorizations\n' +
'gui-status' + '\t  Status of the specified Zorp instance(s)\n' +
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
            'stop-session' : Zorpctl.stop_session,
            'coredump' : Zorpctl.coredump,
            'status' : Zorpctl.status,
            'authorize' : Zorpctl.authorize,
            'gui-status' : Zorpctl.gui_status,
            'version' : Zorpctl.version,
            'inclog' : Zorpctl.inclog,
            'declog' : Zorpctl.declog,
            'log' : Zorpctl.log,
            'deadlockcheck' : Zorpctl.deadlockcheck,
            'szig' : Zorpctl.szig,
            }

parser.add_argument('command', choices=Commands.keys())
parser.add_argument('params', nargs='*')
#args = parser.parse_args()
#
##zorpctl = Zorpctl()
#command_function = Commands.get(args.command)
#command_function(args.params)