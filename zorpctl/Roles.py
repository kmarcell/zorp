class InstanceRole(object):
    @staticmethod
    def __str__():
        return None

class InstanceRoleMaster(InstanceRole):
    @staticmethod
    def __str__():
        return "--master"

class InstanceRoleSlave(InstanceRole):
    @staticmethod
    def __str__():
        return "--slave"