import utils

class Message(object):
    def __init__(self, params = None):
        self.params = params

    def _strParams(self):
        return " ".join(self.params) if utils.isSequence(self.params) else self.params

    def __str__(self):
        return "%s%s\n" % (self.command, " " + (self._strParams() if self.params else ""))

class MessageGetValue(Message):
    command = "GETVALUE"
    param_name = ""

    def __init__(self, key):
        super(MessageGetValue, self).__init__(key)

class MessageGetSibling(Message):
    command = "GETSBLNG"
    param_name = ""

    def __init__(self, node):
        super(MessageGetSibling, self).__init__(node)

class MessageGetChild(Message):
    command = "GETCHILD"
    param_name = ""

    def __init__(self, node):
        super(MessageGetChild, self).__init__(node)

class MessageGetLogLevel(Message):
    command = "LOGGING"
    param_name = "VGET"

    def __init__(self):
        super(MessageGetLogLevel, self).__init__(self.param_name)

class MessageSetLogLevel(Message):
    command = "LOGGING"
    param_name = "VSET"

    def __init__(self, level):
        super(MessageSetLogLevel, self).__init__([self.param_name, str(level)])

class MessageGetLogSpec(Message):
    command = "LOGGING"
    param_name = "GETSPEC"

    def __init__(self):
        super(MessageGetLogSpec, self).__init__(self.param_name)

class MessageSetLogSpec(Message):
    command = "LOGGING"
    param_name = "SETSPEC"

    def __init__(self, value):
        super(MessageSetLogSpec, self).__init__([self.param_name, value])

class MessageGetDeadLockCheck(Message):
    command = "DEADLOCKCHECK"
    param_name = "GET"

    def __init__(self):
        super(MessageGetDeadLockCheck, self).__init__(self.param_name)

class MessageSetDeadLockCheck(Message):
    command = "DEADLOCKCHECK"
    param_name = ""

    def __init__(self, value):
        self.param_name = "ENABLE" if value else "DISABLE"
        super(MessageSetDeadLockCheck, self).__init__(self.param_name)

class MessageReload(Message):
    command = "RELOAD"
    param_name = ""

    def __init__(self):
        super(MessageReload, self).__init__()

class MessageReloadResult(Message):
    command = "RELOAD"
    param_name = "RESULT"

    def __init__(self):
        super(MessageReloadResult, self).__init__(self.param_name)

class MessageStopSession(Message):
    command = "STOPSESSION"
    param_name = ""

    def __init__(self, param):
        super(MessageStopSession, self).__init__(param)

class MessageAuthorizeAbstract(Message):
    command = "AUTHORIZE"

    def __init__(self):
        super(MessageAuthorizeAbstract, self).__init__([self.param_name, self.instance, self.description])

class MessageAuthorizeAccept(MessageAuthorizeAbstract):
    param_name = "ACCEPT"

    def __init__(self, instance, description):
        self.instance = instance
        self.description = description
        super(MessageAuthorizeAccept, self).__init__()

class MessageAuthorizeReject(MessageAuthorizeAbstract):
    param_name = "REJECT"

    def __init__(self, instance, description):
        self.instance = instance
        self.description = description
        super(MessageAuthorizeReject, self).__init__()

class MessageCoredump(Message):
    command = "COREDUMP"
    param_name = ""

    def __init__(self):
        super(MessageCoredump, self).__init__()
