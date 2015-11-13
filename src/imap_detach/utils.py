import six

def decode(s):
    if isinstance(s, six.binary_type):
        return s.decode('UTF-8')
    return s

def lower_all(*l):
    return map(lambda x: decode(x).lower(), l)
