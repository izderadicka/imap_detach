import six
from email.header import decode_header

def decode(s):
    if isinstance(s, six.binary_type):
        return s.decode('UTF-8')
    return s

def email_decode(s):
    if isinstance(s, six.binary_type):
        s=s.decode('ascii')
    l=decode_header(s)
    parts=[(p.decode(e,'replace') if e else decode(p)) for p,e in l]
    return six.u('').join(parts)
    

def lower_all(*l):
    return map(lambda x: decode(x).lower(), l)
