import six
from six import print_ as p
from base64 import b64decode
from quopri import decodestring
import re
import os.path
import shutil
from imap_detach.utils import decode
import logging
log=logging.getLogger('download')

RE_REPLACE=re.compile(r'[/\\?%*|]')
RE_SKIP=re.compile('["]')
def escape_path(p):
    return RE_REPLACE.sub('_', RE_SKIP.sub('',p))
    


def download(msgid, part_info, msg_info, filename, command=None, client=None):
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
    if decode(part_info.encoding) == 'base64':
        part=b64decode(part)
    elif decode(part_info.encoding) == 'quoted-printable':
        part=decodestring(part)
        
    with open(fname, 'wb') as f:
        f.write(part)
    log.debug("Save file %s from part %s (%s, %s)", fname, part_info.section, msg_info['mime'], part_info.encoding)
    