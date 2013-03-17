import argparse
from InstanceClass import Instance

class InstancesConf(object):
    def __init__(self):
        self.prefix = "" #TODO: @PREFIX@
        self.instances_conf_path = self.prefix + "/etc/zorp/instances.conf"
        self.instances_conf_file = None
        self.instances_conf_file = open(self.instances_conf_path, 'r')

    def __del__(self):
        if self.instances_conf_file:
            self.instances_conf_file.close()

    def __iter__(self):
        return self

    def __next__(self):
        line = self._read()
        if line:
            return self._createInstance(line)
        else:
            raise StopIteration

    def _read(self):
        line = self.instances_conf_file.readline()
        while line.startswith('#') or line == '\n':
            line = self.instances_conf_file.readline()
        return line

    def _parseZorpctlArgs(self, zorpctl_argv):
        parser = argparse.ArgumentParser()
        parser.add_argument('--num-of-processes', type=int,
                            dest='number_of_processes', default=None
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
        zorp_argv, zorpctl_argv = line.split(' -- ')
        #FIXME: is there ' -- ' when does not have zorpctl args ?
        params['name'] = zorp_argv.split()[0]
        params['zorp_argv'] = zorp_argv

        if zorpctl_argv:
            params.update(self._parseZorpctlArgs(zorpctl_argv))

        return Instance(**params)