import argparse

class Zorpctl(object):
    def __init__(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def restart(self):
        pass

    def reload(self):
        pass

    def force_start(self):
        pass

    def force_stop(self):
        pass

    def force_restart(self):
        pass

    def reload_or_restart(self):
        pass

    def stop_session(self):
        pass

    def coredump(self):
        pass

    def status(self):
        pass

    def authorize(self):
        pass

    def gui_status(self):
        pass

    def version(self):
        pass

    def inclog(self):
        pass

    def declog(self):
        pass

    def log(self):
        pass

    def deadlockcheck(self):
        pass

    def szig(self):
        pass

HelpMessage =  ('start' + '\t\t  Starts the specified Zorp instance(s)\n' +
                'stop' + '\t\t  Stops the specified Zorp instance(s)\n' +
                'restart' + '\t\t  Restart the specified Zorp instance(s)\n' +
                'reload' + '\t\t  Reload the specified Zorp instance(s)\n' +
                'force-start' + '\t  Starts the specified Zorp instance(s) even if they are disabled\n' +
                'force-stop' + '\t  Forces the specified Zorp instance(s) to stop (SIGKILL)\n' +
                'force-restart' + '\t  Forces the specified Zorp instance(s) to restart (SIGKILL)\n' +
                'reload-or-restart' + ' Reload or restart the specified Zorp instance(s)\n' +
                'stop-session' + '\t  Stops the specified Zorp proxy session\n' +
                'coredump' + '\t  Create core dumps of the specified Zorp instance(s)\n' +
                'status' + '\t\t  Status of the specified Zorp instance(s). For additional information use status -v or --verbose option\n' +
                'authorize' + '\t  Lists and manages authorizations\n' +
                'gui-status' + '\t  Status of the specified Zorp instance(s)\n' +
                'version' + '\t\t  Display Zorp version information\n' +
                'inclog' + '\t\t  Raise the specified Zorp instance(s) log level by one\n' +
                'declog' + '\t\t  Lower the specified Zorp instance(s) log level by one\n' +
                'log' + '\t\t  Change and query Zorp log settings\n' +
                'deadlockchek' + '\t  Change and query Zorp deadlock checking settings\n' +
                'szig' + '\t\t  Display internal information from the given Zorp instance(s)'
                )

parser = argparse.ArgumentParser(prog='zorpctl', description="Zorp Control tool.", usage='%(prog)s [command [options]] [-h] \n\n' + HelpMessage)
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
            'szig' : Zorpctl.szig
            }

parser.add_argument('command', choices=Commands.keys())
parser.add_argument('params', nargs='*')

#args = parser.parse_args(['start', 'default#0', 'default#3'])
#print(args)
parser.print_help()