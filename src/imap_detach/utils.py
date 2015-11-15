import six
from email.header import decode_header
from datetime import datetime

def decode(s):
    if isinstance(s, six.binary_type):
        return s.decode('UTF-8')
    return s

def email_decode(s):
    if not s:
        return six.u('')
    if isinstance(s, six.binary_type):
        s=s.decode('ascii')
    l=decode_header(s)
    parts=[(p.decode(e,'replace') if e else decode(p)) for p,e in l]
    return six.u('').join(parts)
    

def lower_all(*l):
    return map(lambda x: decode(x).string(), l)

def to_datetime(s):
    if s.find(':')>-1:
        dt= datetime.strptime(s, '%Y-%m-%d %H:%M')
    else:
        dt= datetime.strptime(s, '%Y-%m-%d')
    return dt

MONTHS=("Jan" , "Feb" , "Mar" , "Apr" , "May" , "Jun" ,
        "Jul" , "Aug" , "Sep" , "Oct" , "Nov" , "Dec")

def to_imap_date(d):
    return "%d-%s-%d" % (d.day, MONTHS[d.month-1], d.year)