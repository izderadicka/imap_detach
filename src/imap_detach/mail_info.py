import six
from imap_detach.utils import decode, email_decode, lower_safe
from imapclient.response_types import Address

import logging
from imap_detach.expressions import TagList
log=logging.getLogger('mail_info')

def format_addresses(adr):
    def faddr(a):
        if not a.mailbox:
            return ''
        if not a.host:
            return decode(a.mailbox)
        return decode(a.mailbox + b'@' + a.host)
    if not adr:
        return ''
    if isinstance(adr, (Address)):
        return faddr(adr)
    elif isinstance(adr, (tuple, list)):
        return ', '.join(map(lambda x:faddr(x),adr ))
    raise ValueError('Invalid address type')
    

def format_mime(type, sub_type):
    return type+'/'+sub_type

class MailInfo(dict):
    def __init__(self, search_response, part_info=None):
        super(MailInfo,self).__init__()
        date= search_response[b'INTERNALDATE']
        self['date'] = date
        self['year'] = date.year
        self['month'] = date.month
        self['day'] = date.day
        flags=search_response[b'FLAGS']
        self['answered']= b'\\Answered' in flags
        self['seen'] = b'\\Seen' in flags
        self['flagged'] = b'\\Flagged' in flags
        self['deleted'] = b'\\Deleted' in flags
        self['recent'] = b'\\Recent' in flags
        self['draft'] = b'\\Draft' in flags
        self['flags'] = TagList(flags)
        envelope=search_response[b'ENVELOPE']
        #log.debug('ENVELOPE %s', envelope)
        self['subject'] = email_decode(envelope.subject)
        self['from'] = format_addresses(envelope.from_)
        self['sender'] = format_addresses(envelope.sender)
        self['to'] = format_addresses(envelope.to)
        self['cc'] = format_addresses(envelope.cc)
        self['bcc'] = format_addresses(envelope.bcc)
        
        if part_info:
            self.update_part_info(part_info)
            
    def update_part_info(self, part_info):
        self['mime']= format_mime(part_info.type, part_info.sub_type )
        sz=part_info.size
        if part_info.encoding == 'base64':
            sz= (sz // 4) * 3  # aproximate would be enough - for exact size we'll need to check padding
        self['size'] = sz
        name = email_decode(part_info.params.get('name', '') if part_info.params else '')
        filename = email_decode(part_info.disposition.get('filename', '') if part_info.disposition else '')
        self['name'] = name or filename
        att=part_info.disposition and part_info.disposition.get('disposition')
        self['attached'] = (att== 'attachment')
        self['section'] = part_info.section
        
        
import datetime        
DUMMY_INFO={'to': 'ivan@example.com', 
            'mime': 'application/x-zip-compressed', 
            'flagged': False, 'bcc': '', 
            'sender': 'josef@example.com', 
            'seen': True, 
            'deleted': False, 
            'cc': '', 'from': 'josef@example.com', 
            'attached': True, 
            'subject': 'Test', 
            'answered': True, 
            'size': 1557472, 
            'draft': False, 
            'recent': False, 
            'date': datetime.datetime(2015, 10, 27, 11, 11, 8), 
            'year': 2015,
            'month': 10,
            'day' : 27,
            'name': 'test_file.zip',
            'section': '2.1',
            'flags': TagList(['$Forwarded'])}