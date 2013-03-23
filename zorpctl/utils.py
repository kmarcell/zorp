import collections

def isSequence(value):
    if isinstance(value, str):
        return False
    return isinstance(value, collections.Sequence)