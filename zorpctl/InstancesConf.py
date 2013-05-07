import argparse
from zorpctl.InstanceClass import Instance

class InstancesConf(object):
    def __init__(self):
        self.prefix = "" #TODO: @PREFIX@
        self.instances_conf_path = self.prefix + "/etc/zorp/instances.conf"
        try:
            self.instances_conf_file = open(self.instances_conf_path, 'r')
        except IOError as e:
            self.instances_conf_file = None
            e.strerror = "%s %s" % (self.instances_conf_path, e.strerror)
            raise e

    def __del__(self):
        if self.instances_conf_file:
            self.instances_conf_file.close()

    def __iter__(self):
        return self

    def next(self):
        line = self._read()
        if line:
            return self._createInstance(line)
        else:
            raise StopIteration

    def _read(self):
        line = self.instances_conf_file.readline()
        while line.startswith('#') or line == '\n':
            line = self.instances_conf_file.readline()
        return line[:-1] if line[-1:] == '\n' else line

    def _parseZorpctlArgs(self, zorpctl_argv):
        parser = argparse.ArgumentParser()
        parser.add_argument('--parallel-instances', type=int,
                            dest='number_of_processes', default=1
                            )
        parser.add_argument('--auto-restart', dest='auto_restart',
                            action='store_true', default=None
                            )
        parser.add_argument('--no-auto-restart', dest='auto_restart',
                            action='store_false', default=None
                            )
        parser.add_argument('--no-auto-start', dest='auto_start',
                            action='store_false'
                            )
        parser.add_argument('--enable-core', dest='enable_core',
                            action='store_true'
                            )

        return vars(parser.parse_args(zorpctl_argv.split()))

    def _createInstance(self, line):
        params = {}
        splitted_line = line.split(' -- ')
        zorp_argv = splitted_line[0]
        params['name'] = zorp_argv.split()[0]
        params['zorp_argv'] = zorp_argv

        if len(splitted_line) > 1:
            params.update(self._parseZorpctlArgs(splitted_line[1]))

        return Instance(**params)
