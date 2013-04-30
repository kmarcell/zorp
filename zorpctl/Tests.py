import unittest, os
from zorpctl.InstancesConf import InstancesConf
from zorpctl.InstanceClass import Instance
from zorpctl.ProcessAlgorithms import (StartAlgorithm, StopAlgorithm,
                                LogLevelAlgorithm , DeadlockCheckAlgorithm,
                                StatusAlgorithm, ReloadAlgorithm, CoredumpAlgorithm,
                                SzigWalkAlgorithm)

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

        zorpctl_argv = "--num-of-processes 4"
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


class TestStartAlgorithm(unittest.TestCase):

    def setUp(self):
        self.params = {
                       "name" : "default",
                       "zorp_argv" : "default some options",
                       "auto_restart" : True,
                       "number_of_processes" : 4,
                       "enable_core" : True
                      }

    def test_assemble_start_command(self):
        algorithm = StartAlgorithm()
        algorithm.setInstance(Instance(**self.params))
        algorithm.instance.process_num = 0
        self.assertEquals(" ".join(algorithm.assembleStartCommand()),
                          '/usr/lib/zorp/zorp --as default some options --master default#0 --enable-core --process-mode background')
        algorithm.instance.process_num = 1
        self.assertEquals(" ".join(algorithm.assembleStartCommand()),
                          '/usr/lib/zorp/zorp --as default some options --slave default#1 --enable-core --process-mode background')
 
    def test_invalid_instance_for_start(self):
        instance = Instance(**self.params)
        wrong_number = instance.number_of_processes
        algorithm = StartAlgorithm()
        algorithm.setInstance(instance)
        algorithm.instance.process_num = wrong_number
        self.assertEquals(str(algorithm.isValidInstanceForStart()),
                          "%s: number %d must be between [0..%d)" %
                          (instance.process_name, wrong_number, instance.number_of_processes))

        algorithm.instance.process_num = 0
        algorithm.instance.auto_start = False
        self.assertEquals(str(algorithm.isValidInstanceForStart()),
                          "%s: not started, because no-auto-start is set" % instance.process_name)

        algorithm.force = True
        self.assertTrue(algorithm.isValidInstanceForStart())

if __name__ == '__main__':
    unittest.main()
