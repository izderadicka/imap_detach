import six
from six import print_ as p
from base64 import b64decode
from quopri import decodestring
import re
import os.path
import shutil
from imap_detach.utils import decode, lower_safe, AdvancedFormatter
import logging
import subprocess
from threading import Timer
log=logging.getLogger('download')

RE_REPLACE=re.compile(r'[/\\?%*|]')
RE_SKIP=re.compile('["]')
def escape_path(p):
    return RE_REPLACE.sub('_', RE_SKIP.sub('',p))
    
def download(msgid, part_infos, msg_info, filename, command=None, client=None, delete=False, max_time=60,
             message_action=None, message_action_args=None):
        def check_seen():
            res=client.get_flags(msgid)
            flags=res.get(msgid,)
            return b'\\Seen' in flags if flags else False
        
        seen=check_seen()
        for part_info in part_infos:
            try:
                msg_info.update_part_info(part_info)
                download_part(msgid, part_info, msg_info, filename, command, client, delete, max_time)
            except Exception:
                log.exception('Download of message id %d: "%s" from %s received %s,  part %s failed', msgid, msg_info['subject'], msg_info['from'], msg_info['date'], part_info.section)
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

def download_part(msgid, part_info, msg_info, filename, command=None, client=None, 
                  delete_file=False, max_time=60):

    part_id=('BODY[%s]'%part_info.section).encode('ascii')
    
    try:
        cmd=CommandRunner(command, filename, msg_info, delete_file, max_time)
    except ValueError as e:
        log.exception("Cannot download message: %s",e)
        return
    
    part=client.fetch(msgid, [part_id])
    part=part[msgid][part_id]
    part=decode_part(part, part_info.encoding)
    if lower_safe(part_info.type) == 'text':
        charset=lower_safe(part_info.params.get('charset') )
        if charset:
            part=reencode_charset(part, charset)
    
    try:
        cmd.run(part)
    except CommandRunner.Error as e:
        pass
    if command:
        log.debug('Command stdout:\n%s\nCommand stderr:\n%s\n', cmd.stdout, cmd.stderr)
        
def reencode_charset(part, encoding, encoding_out='UTF-8'):    
    log.debug('Reencoding text from %s to %s', encoding, encoding_out)
    text=part.decode(encoding, 'replace')    
    return text.encode(encoding_out, 'replace')
    
def decode_part(part, encoding):
    if encoding == 'base64':
        part = part.replace(b'\r\n', b'')
        missing_padding = 4 - len(part) % 4
        #log.debug ('PAD!! %d %d, %s',len(part), missing_padding, part[-8:]) 
        if missing_padding and missing_padding < 3:
            log.debug ('Fixing padding: len: %d missing: %d, end: %s', len(part), missing_padding, part[-8:]) 
            part += b'='* missing_padding
        elif missing_padding == 3:
            log.error('Invalid base64 length - can be damaged')
            part=part[:-1]
        
        try:
            part=b64decode(part)
        except Exception as e:
            log.error('B64 error: %s\nStart of data: %s\nEnd of data:%s', e, part[:500], part[-500:])
            raise e
    elif encoding == 'quoted-printable':
        part=decodestring(part)  
    return part

class CommandRunner(object):
    class Error(Exception):
        pass
    class Terminated(Error):
        pass
    def __init__(self, command, file_name, context, delete=False, max_time=60):
        if not (command or file_name):
            raise ValueError('File or command must be specified')
        file_name, command = decode(file_name), decode(command)
        self._file=None
        self._command=None
        v={v: (escape_path(x) if isinstance(x, six.text_type) else str(x)) for v,x in six.iteritems(context) }
        dirname=None
        f=AdvancedFormatter()
        if file_name:
            fname=f.fmt(file_name,**v)
            if not fname:
                raise ValueError('No filename available after vars expansion')
            dirname=os.path.dirname(fname)
            if dirname and not os.path.exists(dirname):
                os.makedirs(dirname)
            if os.path.isdir(fname):
                raise ValueError('Filename %s is directory', 
                          fname)
            self._file=fname
        v['file_name'] = self._file or ''
        v['file_base_name'] = os.path.splitext(os.path.basename(self._file))[0] if self._file else ''
        v['file_dir'] = dirname or ''
        if command:
            cmd = f.fmt(command,**v)
            if not cmd:
                raise ValueError('No command available after vars expansion')
            self._command = cmd
            
        self._process=None
        self._stdout=''
        self._stderr=''
        self._killed=False
        self._timer=Timer(max_time, self.terminate)
        self._delete=delete
    
    def terminate(self):
        self._process.kill()
        self._killed=True
        
    def run(self, part):
        if self._file:
            with open(self._file, 'wb') as f:
                f.write(part)
            log.debug("Save file %s", self._file)
        if self._command:
            self._timer.start()
            input_pipe=subprocess.PIPE if not self._file else None
            self._process = subprocess.Popen(self._command, shell=True, 
                            stdin=input_pipe, stderr=subprocess.PIPE, stdout= subprocess.PIPE, 
                            close_fds=True)
            self._stdout, self._stderr =self._process.communicate(None if self._file else part ) 
            self._timer.cancel()
            if self._killed:
                msg= 'Command %s timeouted'% (self._command,)
                log.error(msg)
                raise CommandRunner.Terminated('msg')
            if self._process.returncode != 0:
                msg= 'Command %s failed  with code %d'% (self._command, self._process.returncode)
                log.error(msg)
                raise CommandRunner.Error(msg)
            if self._delete and self._file and os.access(self._file, os.W_OK):
                os.remove(self._file)
            
    @property
    def stdout(self):
        return self._stdout
    
    @property
    def stderr(self):
        return self._stderr
                
            

            
            