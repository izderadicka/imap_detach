#!/usr/bin/env python

import six
import argparse
import imapclient
import string
import re
from six import print_ as p, u
import sys
import pprint



def split_host(host, ssl=True):
    port = 993 if ssl else 143
    host_list=host.split(':')
    if len(host_list)>2:
        raise ValueError('Invalid host string %s'%host)
    if len(host_list)>1:
        port=int(host_list[1])
    server=host_list[0]
    return server, port


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
            res=c.fetch(messages, [b'FLAGS', b'RFC822.SIZE', 'BODYSTRUCTURE'])
            for msgid, data in   six.iteritems(res):
                body=data[b'BODYSTRUCTURE']
                p(msgid,'-'*40, type(data[b'BODYSTRUCTURE']))
                pprint.pprint(data[b'BODYSTRUCTURE'])
               
        
            
    finally:
        c.logout()
    
    
    



    
if __name__ == '__main__':
    main()


    
    

    