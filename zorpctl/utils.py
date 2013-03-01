import collections

def isSequence(value):
    if isinstance(value, str):
        return False
    return isinstance(value, collections.Sequence)

def makeStringFromSequence(sequence):
    params = ""
    for p in sequence:
        params += str(p) + " "
    return params