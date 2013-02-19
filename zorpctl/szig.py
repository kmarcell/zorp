import socket

class SZIG():
    def __init__(self, **kwargs):
        self.max_command_length = 4096
        self.response_length = 4096
        #self.max_value_length = 16384
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    def write_request(self, request):
        if len(request) > self.max_command_length:
            raise SZIGError("Given request is longer than " + str(self.max_command_length))

        if self.socket.send(request) < len(request):
            raise SZIGError("There was an error while sending the request!")

    def read_response(self, response_length):
        if response_length < 1:
            raise SZIGError("Response length should be greater than 0")
        response = self.socket.recv(response_length)
        if not response:
            raise SZIGError("There was an error while receiving the answer!")
        return response

    def get_value(self, key, response_length = self.response_length):
        write_request("GETVALUE %s\n" % key)
        return read_response(response_length)

    def get_sibling(self, key, response_length = self.response_length):
        write_request("GETSBLING %s\n" % key)
        return read_response(response_length)

    def get_child(self, key, response_length = self.response_length):
        write_request("GETCHILD %s\n" % key)
        return read_response(response_length)

    def logging(self, sub_command, parameters, response_length = self.response_length):
        write_request("LOGGING %s %s" % (sub_command, parameters))
        return _validateResponse(read_response(response_length))

    def deadlock_check(self, sub_command, response_length = self.response_length):
        write_request("DEADLOCKCHECK %s\n" % sub_command)
        return _validateResponse(read_response(response_length))

    def reload(self, sub_command = "", response_length = self.response_length):
        write_request("RELOAD %s\n" % sub_command)
        return _validateResponse(read_response(response_length))

    def stop_session(self, instance, response_length = self.response_length):
        write_request("STOPSESSION %s\n" % instance)
        return _validateResponse(read_response(response_length))

    def authorize(self, instance, accept_reject, description, response_length = self.response_length):
        write_request("AUTHORIZE %s %s %s\n", accept_reject, instance, description)
        return _validateResponse(read_response(response_length))

    def coredump(self):
        write_request("COREDUMP\n")
        return _validateResponse(read_response(response_length))

    def _validateResponse(response):
        if response[:3] != "OK ":
            raise SZIGError("Command failed!", response)

        return result[3:]

class SZIGError(Exception):
    def __init__(self, msg, value = None):
        self.msg = msg
        self.value = value
    def __str__(self):
        return msg + repr(value)
