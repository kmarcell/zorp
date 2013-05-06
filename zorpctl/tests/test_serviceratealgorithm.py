import unittest
from HandlerMock import HandlerMock
from zorpctl.szig import SZIG
from zorpctl.Munin import GetServiceRateAlgorithm
from zorpctl.CommandResults import CommandResultSuccess

class TestServiceRateAlgorithm(unittest.TestCase):

    def setUp(self):
        handler_mock = HandlerMock
        szig = SZIG("", handler_mock)
        self.algorithm = GetServiceRateAlgorithm()
        self.algorithm.szig = szig
        data = handler_mock().data

        self.services = data['service'].keys()

        self.avg_test_data = {}
        for service in self.services:
            avg1 = data['service']['service_http_transparent']['rate_avg1']
            avg5 = data['service']['service_http_transparent']['rate_avg5']
            avg15 = data['service']['service_http_transparent']['rate_avg15']
            self.avg_test_data[service] = {"avg1": avg1, "avg5" : avg5, "avg15" : avg15}

    def test_service_rate(self):
        services = CommandResultSuccess("", self.services)
        self.assertEquals(self.algorithm.getServiceRate(services), self.avg_test_data)

if __name__ == '__main__':
    unittest.main()
