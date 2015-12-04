import six
from email.header import decode_header
from datetime import datetime, date
import imapclient
from backports import ssl
import re
from string import Formatter

class AdvancedFormatter(Formatter):
    def fmt(self, fmt, *args, **kwargs):
        return self.vformat(fmt, [], kwargs)
    def get_field(self, field_name, args, kwargs):
        parts=field_name.split('.')
        for p in parts:
            res=[]
            names=p.split('_')
            for n in names:
                if n in kwargs and kwargs[n]:
                    res.append(kwargs[n])
            if res:
                return '_'.join(res), n
        return '', None


def decode(s):
    if isinstance(s, six.binary_type):
        return s.decode('UTF-8')
    return s

def lower_safe(s):
    if not s:
        return s
    return decode(s).lower()


def email_decode(s):
    if not s:
        return u''
    if isinstance(s, six.binary_type):
        s=s.decode('ascii')
    l=decode_header(s)
    parts=[(p.decode(e,'replace') if e else decode(p)) for p,e in l]
    return (u'' if six.PY3 else u' ').join(parts)
    

def lower_all(*l):
    return map(lambda x: decode(x).string(), l)

def to_datetime(s):
    if s.find(':')>-1:
        dt= datetime.strptime(s, '%Y-%m-%d %H:%M')
    else:
        dt= datetime.strptime(s, '%Y-%m-%d')
        dt=date(dt.year,dt.month, dt.day)
    return dt

MONTHS=("Jan" , "Feb" , "Mar" , "Apr" , "May" , "Jun" ,
        "Jul" , "Aug" , "Sep" , "Oct" , "Nov" , "Dec")

def to_imap_date(d):
    return "%d-%s-%d" % (d.day, MONTHS[d.month-1], d.year)

MULTIPLIERS={'k':1024, 'm':1024*1024,'g':1024*1024*1024 }
def to_int(n):
    n=n.lower()
    if n[-1] in 'kmg':
        m=MULTIPLIERS[n[-1]]
        return int(n[:-1]) * m
    else:
        return int(n)

def IMAP_client_factory(host, port, use_ssl=None):
    ssl_context=None
    if use_ssl:
        ssl_context=imapclient.create_default_context()
    
    if use_ssl=='insecure':
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
    return imapclient.IMAPClient(host,port,ssl=use_ssl, ssl_context=ssl_context)


def matched_folders(folders, patterns):
    regs=[]
    for p in patterns:
        r=re.sub(r'\?','.',p)
        r=re.sub(r'(?<!\*)\*(?!\*)','[^/]*',r)
        r=re.sub(r'\*\*', '.*', r)
        
        regs.append(r+'$')
    def m(f):
        for r in regs:
            if re.match(r,f, re.IGNORECASE|re.UNICODE):
                return True
            return False
    return list(filter(m, folders))

def normalize_folders(folders):
    l=[]
    for flags,sep,name in folders:
        if b'\\Noselect' in flags:
            continue
        sep=decode(sep)
        if sep != '/':
            name=name.replace(sep, '/')
        l.append(name)
    return l

def smart_join(l):
    l=list(map(lambda i: i.encode('UTF-8') if isinstance(i, six.text_type) else i, l))
    res=[]
    for i,p in enumerate(l):
        if p==b'(':
            res.append(p)
        elif p==b')' and res and res[-1]==b' ':
            res.pop()
        elif i <len(l)-1:
            res.extend([p, b' '])
        else:
            res.append(p)
    return b''.join(res)
    
    
        
        