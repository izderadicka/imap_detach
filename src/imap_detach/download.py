import six
from six import print_ as p
from base64 import b64decode
from quopri import decodestring
import re
import os.path
import shutil
from imap_detach.utils import decode, lower_safe
import logging
log=logging.getLogger('download')

RE_REPLACE=re.compile(r'[/\\?%*|]')
RE_SKIP=re.compile('["]')
def escape_path(p):
    return RE_REPLACE.sub('_', RE_SKIP.sub('',p))
    
def download(msgid, part_infos, msg_info, filename, command=None, client=None, 
             message_action=None, message_action_args=None):
        def check_seen():
            res=client.get_flags(msgid)
            flags=res[msgid]
            return b'\\Seen' in flags
        
        seen=check_seen()
        for part_info in part_infos:
            try:
                msg_info.update_part_info(part_info)
                download_part(msgid, part_info, msg_info, filename, command, client)
            except Exception:
                log.exception('Download failed')
        try:
            if message_action == 'unseen' and not seen:
                log.debug("Marking message id: %s unseen", msgid)
                client.remove_flags(msgid, ['\\Seen'])
            elif message_action == 'delete':
                log.debug("Deleting  message id: %s", msgid)
                client.delete_messages(msgid)
            elif message_action == 'move':
                folder=message_action_args[0]
                log.debug("Moving message id: %s to folder %s", msgid, folder)
                client.copy(msgid, folder)
                client.delete_messages(msgid)
        except Exception:
            log.exception('Message update failed')

def download_part(msgid, part_info, msg_info, filename, command=None, client=None):

    part_id=('BODY[%s]'%part_info.section).encode('ascii')
    v={v: (escape_path(x) if isinstance(x, six.text_type) else str(x)) for v,x in six.iteritems(msg_info) }
    fname=(filename or '').format(**v)
    if not fname:
        log.error('No filename available for part %s %s of message "%s" from %s', 
                  part_info.section, msg_info['mime'], msg_info['subject'], msg_info['from'])
        return
    
    dirname=os.path.dirname(filename)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)
    if os.path.isdir(fname):
        log.error('Filename %s is directory for part %s %s of message "%s" from %s', 
                  fname, part_info.section, msg_info['mime'], msg_info['subject'], msg_info['from'])
        return
    part=client.fetch(msgid, [part_id])
    part=part[msgid][part_id]
    part=decode_part(part, part_info.encoding, fname)
        
    with open(fname, 'wb') as f:
        f.write(part)
    log.debug("Save file %s from part %s (%s, %s)", fname, part_info.section, msg_info['mime'], part_info.encoding)

def decode_part(part, encoding, fname):
    if lower_safe(encoding) == 'base64':
        
        missing_padding = 4 - len(part) % 4
        #log.debug ('PAD1: %d %d, %s', len(part), missing_padding, part[-8:]) 
        if missing_padding and missing_padding < 3:
            part += b'='* missing_padding
        elif missing_padding == 3:
            log.error('Invalid base64 padding on file %s  - can be damaged',
                      fname)
            part=part[:-1]
        #log.debug ('PAD2 %d %d, %s',len(part), missing_padding, part[-8:]) 
        part=b64decode(part)
    elif lower_safe(encoding) == 'quoted-printable':
        part=decodestring(part)  
    return part