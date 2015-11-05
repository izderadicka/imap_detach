#!/usr/bin/env python

import six
import argparse
import imaplib
import string
import re
import email.errors, email.header, email.utils
from six import print_ as p, u
import sys
import time
from email._parseaddr  import AddressList




def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('-s', '--server', help="IMAP server - host name or host:port", required=True)
    parser.add_argument('-u', '--user', help='User name', required=True)
    parser.add_argument('-p', '--password', help='User password')
    parser.add_argument('--no-ssl', action='store_true',  help='Do not use SSL, use plain unencrypted connection')
    
    opts=parser.parse_args()
    
    c=MailLister(opts.server, opts.user, opts.password)
    p('FOLDERS',  c.listFolders())
    try:
        c.selectFolder('INBOX/back')
        for h in c:
            p('Header:',h)
            
    finally:
        c.close()
    
    
    


class ProtocolError(Exception): pass


class Token(object):
    def __init__(self):
        self.l=[]
        
    def add(self,char):
        self.l.append(char)
        
    def finish(self, line):
        if len( self.l )>0:
            line.append( ''.join( self.l ) )
            self.l=[]

def parseList(inline):
    stack=[]
    root=[]
    line=root
    token=Token()
    separators=string.whitespace
    escapes='"'
    listStart='('
    listEnd=')'
    escaped=False
    for ch in inline:
        
        if not escaped and ch in separators: token.finish(line)
        elif ch in escapes: escaped=not escaped
        elif not escaped and ch in listStart:
            token.finish(line)
            stack.append(line)
            newline=[]
            line.append(newline)
            line=newline
        elif not escaped and ch in listEnd:
            token.finish(line)
            line=stack.pop()
        else:
            token.add( ch )
    token.finish(line)
    return root        
    
class MailLister(six.Iterator):
        
    def __init__(self, host, user, password='', ssl=True, root_folder='INBOX'):
        
        port = 993 if ssl else 143
        host_list=host.split(':')
        if len(host_list)>2:
            raise ValueError('Invalid host string %s'%host)
        if len(host_list)>1:
            port=int(host_list[1])
        server=host_list[0]
        if ssl:
            self.mclient=imaplib.IMAP4_SSL(server, port)
        else:
            self.mclient=imaplib.IMAP4(server, port)
        self.mclient.login(user, password)
        self.count=0
        self.list=None
        self.folder=root_folder
       
    def _getFolderName(self, inline):
        return parseList(inline)[2]
    
    def listFolders(self):  
        if self.folder.count('*')>0:
            code,data = self.mclient.list()
            if code=='OK':
                lst= map(self._getFolderName,data)
                self.pattern =re.compile("^"+self.folder.replace('*', '.*')+"$")
                return filter(self._match,lst)
            else:
                raise ProtocolError("List operation failed")
        else:
            return [self.folder]
        
    def _match(self,str): 
        return self.pattern.search(str)
        
    def selectFolder(self,folder,search='(ALL)'):
        self.count=0
        code,data= self.mclient.select(folder,True)
        if code!='OK':
            raise ProtocolError("Select operation failed for folder "+folder)
        code,data = self.mclient.search(None, search)
        if code=='OK':
            self.list=data[0].split()
        else:
            raise ProtocolError("Search operation failed")
        self.folder=folder
        return len(self.list)
    
    def getMessageHeader(self, seqId):
        code,data=  self.mclient.fetch(seqId, '(UID INTERNALDATE FLAGS RFC822.SIZE RFC822.HEADER)')
        if code=='OK':
            try:
                return DecodedHeader(data[0], self.folder)
            except email.errors.MessageError as e:
                raise ProtocolError("RFC822 Headers error:"+str(e))
        else:
            raise ProtocolError("Fetch operation failed")
        
    def __iter__(self): return self
    
    def __next__(self): 
        if (self.list==None): raise ProtocolError("No folder selected!")
        try:
            mh= self.getMessageHeader(self.list[self.count])
            self.count+=1
            return mh
        except IndexError:
            raise StopIteration()
        
    def close(self):
        try:
            if self.mclient.state in imaplib.Commands['CLOSE']: self.mclient.close()
            self.mclient.logout()
        except imaplib.IMAP4.error as e:
            p("Error while closing IMAP", e, file=sys.stderr)
            
class DecodedHeader(object):
    def __init__(self, s, folder):
        self.msg=email.message_from_string(s[1].decode('utf-8'))
        self.info=parseList(s[0].decode('utf-8'))
        self.folder=folder
        
    def __getitem__(self,name):
        if name.lower()=='folder': return self.folder
        elif name.lower()=='uid': return self.info[1][3]
        elif name.lower()=='flags': return ','.join(self.info[1][1])
        elif name.lower()=='internal-date':
            ds= self.info[1][5]
#             if Options.dateFormat:            if Options.dateFormat:
#                 ds= time.strftime(Options.dateFormat,
#                 ds= time.strftime(Options.dateFormat,imaplib.Internaldate2tuple('INTERNALDATE "'+ds+'"'))
            return ds
        elif name.lower()=='size': return self.info[1][7]
        val= self.msg.__getitem__(name)
        if val==None: return None
        return self._convert(email.header.decode_header(val),name)
    def get(self,key,default=None):
        return self.__getitem__(key)
        
    def _convert(self, list, name):
        l=[]
        for s, encoding in list:
            try:    
                if (encoding!=None):
                    s=s.decode(encoding, 'replace')
            except Exception as e:
                print >>sys.stderr, "Decoding error", e
            l.append(s)
        
        res= "".join(l)
        if name.lower() in ('from','to', 'cc', 'return-path','reply-to' ): res=self._modifyAddr(res)
        #if name.lower() in ('date'): res = self._formatDate(res)
        return res  

    
    def _modifyAddr(self, res):
        o=[]
        al= AddressList(res).addresslist
        for item in al:
            o.append(item[1])
        return ','.join(o)
    
    
if __name__ == '__main__':
    main()


    
    

    