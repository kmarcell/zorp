import argparse
from UInterface import UInterface
from Instances import InstanceHandler
from subprocess import call

#TODO: Logging
"""
Questions:
- when reload default given and default has 4 process and 2 is not running
  which one do we want to reload? All or just the running ones?
- When does the instance considered running? (When all processes running or if there is)
- Do we want the @file option for files containing instance name lists?
- How does 3.4 handling instance processes?
"""

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
            UInterface.informUser(handler.startAll())
        else:
            for instance in params:
                UInterface.informUser(handler.start(instance))

    def stop(self):
        raise NotImplementedError()

    def restart(self):
        raise NotImplementedError()

    @staticmethod
    def reload(params):
        """
        Reloads Zorp instance(s) by instance name
        expects sequence of name(s)
        """
        UInterface.informUser("Reloading Zorp Firewall Suite:")

        handler = InstanceHandler()
        if not params:
            UInterface.informUser(handler.reloadAll())
        else:
            for instance in params:
                UInterface.informUser(handler.reload(instance))

    def force_start(self):
        raise NotImplementedError()

    def force_stop(self):
        raise NotImplementedError()

    def force_restart(self):
        raise NotImplementedError()

    @staticmethod
    def reload_or_restart(params):
        handler = InstanceHandler()
        if not params:
            status = handler.reloadAll()
        else:
            status = []
            for instance in params:
                status += handler.reload(instance)

        for success in status:
            if success:
                UInterface.informUser(success)
            else:
                result = Zorpctl.restart(str(success).split(':')[0])
                if result:
                    UInterface.informUser("%s: Restart successful" % result)
                else:
                    UInterface.informUser("Both reload and restart failed")
                    UInterface.informUser(result)

    def stop_session(self):
        raise NotImplementedError()

    def coredump(self):
        raise NotImplementedError()

    @staticmethod
    def status(params):
        s_parse = argparse.ArgumentParser(
             prog='zorpctl status',
             description="Displays status of the specified Zorp instance(s)." +
                  "For additional information use status -v or --verbose option")
        s_parse.add_argument('-v', '--verbose', action='store_true')
        s_parse.add_argument('params', nargs='*')
        s_args = s_parse.parse_args(params)

        handler = InstanceHandler()
        if s_args.params:
            for instance in s_args.params:
                status = handler.detailedStatus(instance) if s_args.verbose else handler.status(instance)
                UInterface.informUser(status)
        else:
            handler.detailedStatusAll() if s_args.verbose else handler.statusAll()

    def authorize(self):
        raise NotImplementedError()

    def gui_status(self):
        raise NotImplementedError()

    def version(self):
        call([InstanceHandler.install_path + 'zorp', "--version"])

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
parser.add_argument('params', nargs=argparse.REMAINDER)
args = parser.parse_args()

command_function = Commands.get(args.command)
command_function(args.params)
