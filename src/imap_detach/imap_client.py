#!/usr/bin/env python

import six
import argparse
import imapclient
import string
import re
from six import print_ as p, u
import sys
import pprint
from collections import namedtuple



def split_host(host, ssl=True):
    port = 993 if ssl else 143
    host_list=host.split(':')
    if len(host_list)>2:
        raise ValueError('Invalid host string %s'%host)
    if len(host_list)>1:
        port=int(host_list[1])
    server=host_list[0]
    return server, port


def walker(body, level='', count=1):
    res=[]
    if isinstance(body, list):
        for part in body:
            res.extend(walker(part, level+('.%d' if level else '%d')%count , count ))
            count+=1
    elif isinstance(body, tuple):
        if body[0]:
            i=1 if isinstance(body[0], list) else 0
            info=extract_mime_info(level, body)
            res.append(info)
            res.extend(walker(body[0], level, 1))
            
    return res

base_fields=('section', 'type', 'sub_type', 'params',)
MultiBodyInfo=namedtuple('MultiBodyInfo', base_fields+('disposition', 'language', 'location' ))
body_fields=base_fields+( 'id', 'description', 'encoding', 'size', )
ext_fields=('md5', 'disposition', 'language', 'location')
BodyInfo=namedtuple('BodyInfo', body_fields+ext_fields)
TextBodyInfo=namedtuple('TextBodyInfo', body_fields+('lines',)+ext_fields)

def extract_mime_info(level, body):
    def conv_dict(d):
        if not d:
            return {}
        if not isinstance(d, tuple):
            raise ValueError('Expected tuple as value')
        res={}
        for i in range(0,len(d)-1, 2):
            res[d[i]]=d[i+1]
        return res
            
    def conv_disp(d):
        if not d:
            return {}
        res={}
        res[b'DISPOSITION']=d[0]
        res.update(conv_dict(d[1]))
        return res
        
            
    if isinstance(body[0], list):
        info= MultiBodyInfo(level, b'MULTIPART', body[1], conv_dict(body[2]), conv_disp(body[3]), body[4], body[5])
    elif body[0]==b'TEXT':
        info=TextBodyInfo(level, body[0], body[1], conv_dict(body[2]), body[3], body[4], body[5], body[6], body[7], body[8], conv_disp(body[9]), body[10], body[11],  )
    else:
        info=BodyInfo(level, body[0], body[1], conv_dict(body[2]), body[3], body[4], body[5], body[6], body[7], conv_disp(body[8]), body[9], body[10] )
        
    return info


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('-H', '--host', help="IMAP server - host name or host:port", required=True)
    parser.add_argument('-u', '--user', help='User name', required=True)
    parser.add_argument('-p', '--password', help='User password')
    parser.add_argument('--no-ssl', action='store_true',  help='Do not use SSL, use plain unencrypted connection')
    
    opts=parser.parse_args()
    host, port= split_host(opts.host, ssl=not opts.no_ssl)
    c=imapclient.IMAPClient(host,port, ssl= not opts.no_ssl)
    try:
        c.login(opts.user, opts.password)
    
        selected=c.select_folder('INBOX')
        if selected[b'EXISTS']>0:
            messages=c.search('NOT DELETED') 
            res=c.fetch(messages, [b'INTERNALDATE', b'FLAGS', b'RFC822.SIZE', b'ENVELOPE', b'BODYSTRUCTURE'])
            for msgid, data in   six.iteritems(res):
                body=data[b'BODYSTRUCTURE']
                p(msgid,'-'*40)
                for info in walker(body):
                    p(info)
#                 part_id=b'BODY[1.2]'
#                 part=c.fetch(msgid, [part_id])
#                 p(part[msgid][part_id][:80*5])
                
                
               
        
            
    finally:
        c.logout()
    
    
    



    
if __name__ == '__main__':
    main()


    
    

    