class CommandResult(object):
    def __init__(self, msg = None, value = None):
        self.msg = msg
        self.value = value

    def __str__(self):
        return self.msg

class CommandResultSuccess(CommandResult):
    def __init__(self, msg = None, value = None):
        super(CommandResultSuccess, self).__init__(msg, value)

    def __bool__(self):
        return True

class CommandResultFailure(CommandResult):
    def __init__(self, msg = None, value = None):
        super(CommandResultFailure, self).__init__(msg, value)

    def __bool__(self):
        return False
