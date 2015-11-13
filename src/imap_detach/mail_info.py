import six
from imap_detach.utils import decode
from imapclient.response_types import Address

def format_addresses(adr):
    def faddr(a):
        return decode(a.mailbox + b'@' + a.host)
    if not adr:
        return ''
    if isinstance(adr, (Address)):
        return faddr(adr)
    elif isinstance(adr, (tuple, list)):
        return ', '.join(map(lambda x:faddr(x),adr ))
    raise ValueError('Invalid address type')
    

def format_mime(type, sub_type):
    return decode(type).lower()+'/'+decode(sub_type).lower()

class MailInfo(dict):
    def __init__(self, search_response, part_info=None):
        super(MailInfo,self).__init__()
        
        self['date'] = search_response[b'INTERNALDATE']
        flags=search_response[b'FLAGS']
        self['answered']= b'\\Answered' in flags
        self['seen'] = b'\\Seen' in flags
        self['flagged'] = b'\\Flagged' in flags
        self['deleted'] = b'\\Deleted' in flags
        self['recent'] = b'\\Recent' in flags
        self['draft'] = b'\\Draft' in flags
        envelope=search_response[b'ENVELOPE']
        self['subject'] = decode(envelope.subject)
        self['from'] = format_addresses(envelope.from_)
        self['sender'] = format_addresses(envelope.sender)
        self['to'] = format_addresses(envelope.to)
        self['cc'] = format_addresses(envelope.cc)
        self['bcc'] = format_addresses(envelope.bcc)
        
        if part_info:
            self.update_part_info(part_info)
            
    def update_part_info(self, part_info):
        self['mime']= format_mime(part_info.type, part_info.sub_type )
        self['size'] = part_info.size
        self['name'] = decode(part_info.params.get(b'name', '') if part_info.params else '')
        att=part_info.disposition and part_info.disposition.get( b'disposition')
        att=decode(att).lower() if att else None
        self['attached'] = (att== 'attachment')
        
        
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
            'name': 'test_file.zip'}