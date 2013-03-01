import unittest
#import szig
#import zorp_mock
#import time
from Zorpctl import Zorpctl

class Test(unittest.TestCase):

#    def test_SZIG(self):
#        zorp = zorp_mock.ZorpMock()
#        zorp.start()
#        self.assertTrue(zorp.isAlive())
#        time.sleep(1)
#        s = szig.SZIG()
#
#        self.assertEqual(s.loglevel, 3)
#        self.assertEqual(s.logspec, "*.accounting:4")
#        self.assertEqual(s.deadlockcheck, True)
#        s.reload()
#        self.assertEqual(s.reload_result(), "successful")


    def test_Zorpctl(self):
        Zorpctl().start(['default#0'])

if __name__ == "__main__":
    unittest.main()