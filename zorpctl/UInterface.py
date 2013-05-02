import zorpctl.utils

class UInterface(object):
    def __init__(self):
        pass

    @staticmethod
    def informUser(message):
        if zorpctl.utils.isSequence(message):
            for msg in message:
                print(str(msg))
        else:
            print(str(message))
