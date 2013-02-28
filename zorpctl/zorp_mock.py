import socket
import os
import threading

class ZorpMock(threading.Thread):

    def __init__(self):
        self.server_address = './uds_socket'
        self.command_length = 4096
        # Make sure the socket does not already exist
        try:
            os.unlink(self.server_address)
        except OSError:
            if os.path.exists(self.server_address):
                raise
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        super(ZorpMock, self).__init__()

    def listen(self):
        self.socket.bind(self.server_address)

        self.socket.listen(1)

        connection, client_address = self.socket.accept()
        try:
            while True:
                question = connection.recv(self.command_length)
                if question:
                    answer = self.makeAnswer(question)
                    connection.sendall(answer)
                else:
                    break
        finally:
            connection.close()

    def makeAnswer(self, question):
        dic = {"LOGGING VGET\n":"3",
               "LOGGING GETSPEC\n":"*.accounting:4",
               "DEADLOCKCHECK GET\n":"1",
               "RELOAD\n":"Reload initiated",
               "RELOAD RESULT\n":"successful"}

        answer = dic.get(question)
        return "FAIL " if not answer else "OK " + answer

    def run(self):
        self.listen()