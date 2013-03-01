import utils

class UInterface(object):
    def __init__(self):
        pass

    @staticmethod
    def informUser(message):
        if utils.isSequence(message):
            print(utils.makeStringFromSequence(message))
        else:
            print(message)