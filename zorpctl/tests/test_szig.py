import unittest
from zorpctl.szig import SZIG, Response
from zorpctl.SZIGMessages import *

class HandlerMock(object):

    def __init__(self, server_address=None):
        self.siblings = {}
        self.data = {
            "conns": {
                "service_http_transparent": {
                    "outbound_zones": "clients(1)", 
                    "inbound_zones": "servers(1)"
                }
            }, 
            "info": {
                "policy": {
                    "reload_stamp": 1367664125, 
                    "file_stamp": 1322391262, 
                    "file": "/etc/zorp/policy.py"
                }
            }, 
            "stats": {
                "threads_running": 4, 
                "thread_rate_max": 0, 
                "thread_number": 5, 
                "audit_number": None, 
                "audit_running": None, 
                "thread_rate_avg1": 0, 
                "sessions_running": 0, 
                "thread_rate_avg5": 0, 
                "threads_max": 5, 
                "thread_rate_avg15": 0
            }, 
            "service": {
                "service_http_transparent": {
                    "rate_max": 0, 
                    "session_number": 1, 
                    "sessions_max": 1, 
                    "sessions_running": 0, 
                    "rate_avg1": 0, 
                    "rate_avg5": 0, 
                    "last_started": 1367675872.63, 
                    "rate_avg15": 0
                }
            }
        }

    def _get(self, key):
        result = self.data
        if not key:
            return result
        parts = key.split('.')
        for part in parts:
            result = result[part]
        return result

    def getvalue(self, key):
        if key == "":
            return None
        result = self._get(key)
        if type(result) == dict:
            return None
        return result

    def _getmembers(self, key):
        last_dot_position = key.rfind('.')
        if last_dot_position == -1:
            members = self.data.keys()
        else:
            members = self._get(key[:last_dot_position]).keys()
        return members

    def getsibling(self, key):
        members = self._getmembers(key)

        position = members.index(key.split('.')[-1])
        try:
            sibling = members[position + 1]
        except IndexError:
            return None
        last_dot_position = key.rfind('.')
        return ((key[:last_dot_position] + ".") if last_dot_position != -1 else "") + sibling

    def getchild(self, key):
        value = self._get(key)
        if type(value) != dict:
            return None
        childs = value.keys()
        return (key + "." if key else "") + childs[0]

    def talk(self, message):
        if type(message) == MessageGetValue:
            return Response(True, self.getvalue(message.params))
        if type(message) == MessageGetSibling:
            return Response(True, self.getsibling(message.params))
        if type(message) == MessageGetChild:
            return Response(True, self.getchild(message.params))

class TestSzig(unittest.TestCase):

    def setUp(self):
        self.szig = SZIG("", HandlerMock)

    def test_get_value(self):
        self.assertEquals(self.szig.get_value(""), None)
        self.assertEquals(self.szig.get_value("service"), None)
        self.assertEquals(self.szig.get_value("info.policy.file"), "/etc/zorp/policy.py")
        self.assertEquals(self.szig.get_value("stats.thread_number"), 5)
        self.assertEquals(self.szig.get_value("service.service_http_transparent.sessions_running"), 0)

    def test_get_sibling(self):
        self.assertEquals(self.szig.get_sibling("conns"), "info")
        self.assertEquals(self.szig.get_sibling("stats.threads_running"), "stats.thread_rate_max")
        self.assertEquals(self.szig.get_sibling("stats.thread_rate_max"), "stats.audit_number")
        self.assertEquals(self.szig.get_sibling("stats.thread_number"), None)

    def test_get_child(self):
        self.assertEquals(self.szig.get_child(""), "conns")
        self.assertEquals(self.szig.get_child("info"), "info.policy")
        self.assertEquals(self.szig.get_child("info.policy"), "info.policy.reload_stamp")
        self.assertEquals(self.szig.get_child("info.policy.reload_stamp"), None)

if __name__ == '__main__':
    unittest.main()