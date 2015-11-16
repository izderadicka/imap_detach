#!/usr/bin/env python

import six
import argparse
import imapclient
from six import print_ as p, u
import sys
from collections import namedtuple
import logging
from imap_detach.mail_info import MailInfo, DUMMY_INFO
from imap_detach.expressions import SimpleEvaluator, ParserSyntaxError, ParserEvalError,\
    extract_err_msg
from imap_detach.filter import IMAPFilterGenerator
from imap_detach.download import download
from imap_detach.utils import decode

#increase message size limit
import imaplib
from argparse import RawTextHelpFormatter
imaplib._MAXLINE = 100000

log=logging.getLogger('imap_client')


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
            res[decode(d[i]).lower()]=decode(d[i+1])
        return res
            
    def conv_disp(d):
        if not d:
            return {}
        res={}
        res['disposition']=decode(d[0])
        res.update(conv_dict(d[1]))
        return res

    def get(t,i):
        if i >= len(t):
            return None
        return t[i]
        
        
    #log.debug('Body info %s', body)        
    if isinstance(body[0], list):
        info= MultiBodyInfo(level, b'MULTIPART', body[1], conv_dict(body[2]), conv_disp(body[3]), get(body,4), get(body,5))
    elif body[0]==b'TEXT':
        info=TextBodyInfo(level, body[0], body[1], conv_dict(body[2]), body[3], body[4], body[5], int(body[6]), body[7], body[8], conv_disp(body[9]), get(body,10), get(body,11),  )
    elif body[0]==b'MESSAGE' and body[1]==b'RFC822':
        info=BodyInfo(level, body[0], body[1], conv_dict(body[2]), body[3], body[4], body[5], int(body[6]), body[7], None, get(body,9), get(body,10) )
    else:
        info=BodyInfo(level, body[0], body[1], conv_dict(body[2]), body[3], body[4], body[5], int(body[6]), body[7], conv_disp(body[8]), get(body,9), get(body,10) )
        
    return info

def define_arguments(parser):
    parser.add_argument('filter', help='Filter for mail parts to get, simple expression with variables comparison ~=, =  logical operators & | ! and brackets ')
    parser.add_argument('-H', '--host', help="IMAP server - host name or host:port", required=True)
    parser.add_argument('-u', '--user', help='User name', required=True)
    parser.add_argument('-p', '--password', help='User password')
    parser.add_argument('--folder', default='INBOX', help='mail folder, default is INBOX')
    parser.add_argument('-f','--file-name', default='{name}', help="Pattern for outgoing files - support {var} replacement - same variables as for filter, default is name of attachment")
    parser.add_argument('--no-ssl', action='store_true',  help='Do not use SSL, use plain unencrypted connection')
    parser.add_argument('-v', '--verbose', action="store_true", help= 'Verbose messaging')
    parser.add_argument('--debug', action="store_true", help= 'Debug logging')
    parser.add_argument('--test', action="store_true", help= ' Do not download and process - just show found email parts')
    parser.add_argument('--seen', action="store_true", help= 'Marks processed messages (matching filter) as seen')
    parser.add_argument('--delete', action="store_true", help= 'Deletes processed messages (matching filter)')
    parser.add_argument('--move', help= 'Moves processed messages (matching filter) to specified folder')
    
    
def extra_help():
    lines=[]
    lines.append("Variables for filter: %s" % ' '.join(sorted(DUMMY_INFO.keys())))
    lines.append("Operators for filter: = ~= (contains) ^= (starts with) $= (ends with) > < >= <= ")
    lines.append("Date(time) format: YYYY-MM-DD or YYYY-MM-DD HH:SS - enter without quotes")
    
    return ('\n\n'.join(lines))

def main():
    def msg_action(opts):
        action=None
        params=[]
        
        if opts.move:
            action='move'
            params.append(opts.move)
        elif opts.delete:
            action='delete'
        elif not opts.seen:
            action='unseen'
        return {'message_action':action, 'message_action_args': tuple(params)}
    
    parser=argparse.ArgumentParser(epilog=extra_help(), formatter_class=RawTextHelpFormatter)
    define_arguments(parser)
    opts=parser.parse_args()
    if opts.verbose:
        logging.basicConfig(level=logging.INFO, format="%(message)s")
    if opts.debug:
        logging.basicConfig(level=logging.DEBUG)
    
    host, port= split_host(opts.host, ssl=not opts.no_ssl)
    
    # test filter parsing
    eval_parser=SimpleEvaluator(DUMMY_INFO)
    filter=opts.filter
    try:
        imap_filter=IMAPFilterGenerator().parse(filter)
        _ = eval_parser.parse(filter)
    except ParserSyntaxError as e:
        msg = "Invalid syntax of filter: %s" %extract_err_msg(e)
        log.error(msg)
#        p(msg, file=sys.stderr)
        sys.exit(1)
        
    except ParserEvalError as e:
        msg = "Invalid sematic of filter: %s" % extract_err_msg(e)
        log.error(msg)
        #p(msg, file=sys.stderr)
        sys.exit(2)
        
    log.debug('IMAP filter: %s', imap_filter) 
    try:
        c=imapclient.IMAPClient(host,port, ssl= not opts.no_ssl)
        try:
            c.login(opts.user, opts.password)
            if opts.move and  not c.folder_exists(opts.move):
                c.create_folder(opts.move)
            selected=c.select_folder(opts.folder)
            msg_count=selected[b'EXISTS']
            if msg_count>0:
                log.debug('Folder %s has %d messages', opts.folder, msg_count  )
                messages=c.search(imap_filter or 'ALL') 
                res=c.fetch(messages, [b'INTERNALDATE', b'FLAGS', b'RFC822.SIZE', b'ENVELOPE', b'BODYSTRUCTURE'])
                for msgid, data in   six.iteritems(res):
                    body=data[b'BODYSTRUCTURE']
                    msg_info=MailInfo(data)
                    log.debug('Got message %s', msg_info)
                    
                    part_infos=process_parts(body, msg_info, eval_parser, opts.filter, opts.test)
                    if part_infos:
                        download(msgid, part_infos, msg_info, opts.file_name,  client=c, **msg_action(opts))
                    
                                
            else:
                log.info('No messages in folder %s', opts.folder)               
        finally:
            if opts.delete or opts.move:
                c.expunge()
            c.logout()
            
    except Exception:
        log.exception('Runtime Error')     
    
    
def process_parts(body, msg_info, eval_parser, filter, test=False):
    part_infos=[]
    for part_info in walker(body):
        if part_info.type == b'MULTIPART':
            log.debug('Multipart - %s', part_info.sub_type)
        else:
            log.debug('Message part %s', part_info)
            msg_info.update_part_info(part_info)
            eval_parser.context=msg_info
            if eval_parser.parse(filter):
                log.debug('Will process this part')
                if test:
                    p('File "{name}" of type {mime} and size {size} in email "{subject}" from {from}'.format(**msg_info))
                else:
                    log.info('File "{name}" of type {mime} and size {size} in email "{subject}" from {from}'.format(**msg_info))
                    part_infos.append(part_info)
            else:
                log.debug('Will skip this part')
    return part_infos



    
if __name__ == '__main__':
    main()


    
    

    