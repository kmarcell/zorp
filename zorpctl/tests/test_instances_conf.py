import unittest, os
from zorpctl.InstancesConf import InstancesConf

class TestInstancesConf(unittest.TestCase):

    def setUp(self):
        self.instance_name = 'default'
        self.zorp_argv = 'lots of options'
        self.zorpctl_argv = {
                             "num_of_processes" : 4,
                             "auto_restart" : False,
                             "auto_start" : False,
                             "enable_core" : True
                            }

        zorpctl_argv = "--parallel-instances 4"
        if not self.zorpctl_argv["auto_restart"]:
            zorpctl_argv += " --no-auto-restart"
        if not self.zorpctl_argv["auto_start"]:
            zorpctl_argv += " --no-auto-start"
        if self.zorpctl_argv["enable_core"]:
            zorpctl_argv += " --enable-core"

        self.filename = 'testfile_instances.conf'
        testfile = open(self.filename, 'w')
        testfile.write("%s %s -- %s" % (self.instance_name, self.zorp_argv, zorpctl_argv))
        testfile.close()

    def __del__(self):
        os.remove(self.filename)

    def test_instance_generation(self):
        instancesconf = InstancesConf()
        instancesconf.instances_conf_file = open(self.filename, 'r')
        for instance in instancesconf:
            self.assertEquals(instance.name, self.instance_name)
            self.assertEquals(instance.zorp_argv[len(instance.name) + 1:], self.zorp_argv)
            self.assertEquals(instance.number_of_processes, self.zorpctl_argv["num_of_processes"])
            self.assertEquals(instance.auto_restart, self.zorpctl_argv["auto_restart"])
            self.assertEquals(instance.auto_start, self.zorpctl_argv["auto_start"])
            self.assertEquals(instance.enable_core, self.zorpctl_argv["enable_core"])

if __name__ == '__main__':
    unittest.main()
