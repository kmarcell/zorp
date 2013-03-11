import utils

class UInterface(object):
    def __init__(self):
        pass

    @staticmethod
    def informUser(message):
        if utils.isSequence(message):
            for msg in message:
                print(msg)
        else:
            print(message)