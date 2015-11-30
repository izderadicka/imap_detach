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
from imap_detach.utils import decode, lower_safe, IMAP_client_factory
from imap_detach.pool import Pool
from argparse import RawTextHelpFormatter
import time
import imap_detach

#increase message size limit
import imaplib
from threading import Thread
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


def walk_structure(body, level='', count=1, multipart=False):
    def next_level():
        return level+('.%d' if level else '%d')%count
    res=[]
    first=body[0]
    if isinstance(first, tuple):
        parts=[]
        i=0
        while i < len (body):
            if not isinstance(body[i], tuple):
                break
            parts.append(body[i])
            i+=1
        nbody = (parts,) + body[i:]
        res.extend(walk_structure(nbody, level , count, multipart ))
    if isinstance(first, (list)):
        if multipart:
            res.append(extract_mime_info(level, body))
        for part in first:
            res.extend(walk_structure(part, next_level() , 1, multipart ))
            count+=1
    elif isinstance(first, six.string_types+(six.binary_type,)):
        if lower_safe(first) == 'message' and lower_safe(body[1]) == 'rfc822' and body[8] \
            and isinstance(body[8], tuple) and isinstance(body[8][0], tuple):
#             if multipart:
#                 res.append(extract_mime_info(level, body))
            res.extend(walk_structure(body[8],level,1, multipart))
            
        elif first:
            res.append(extract_mime_info(level, body))
            
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
            res[lower_safe(d[i])]=decode(d[i+1])
        return res
            
    def conv_disp(d):
        if not d:
            return {}
        res={}
        res['disposition']=lower_safe(d[0])
        res.update(conv_dict(d[1]))
        return res

    def get(t,i):
        if i >= len(t):
            return None
        return t[i]
    
    
        
    body = [lower_safe(p) if isinstance(p, six.binary_type) else p for p in body]    
    log.debug('Body info %s', body)        
    if isinstance(body[0], list):
        info= MultiBodyInfo(level, 'multipart', body[1], conv_dict(body[2]), conv_disp(body[3]), get(body,4), get(body,5))
    elif body[0]=='text':
        info=TextBodyInfo(level, body[0], body[1], conv_dict(body[2]), body[3], body[4], body[5], int(body[6]), body[7], body[8], conv_disp(body[9]), get(body,10), get(body,11),  )
#     elif body[0]=='message' and body[1]=='rfc822':
#         info=BodyInfo(level, body[0], body[1], conv_dict(body[2]), body[3], body[4], body[5], int(body[6]), body[7], None, get(body,9), get(body,10) )
    else:
        info=BodyInfo(level, body[0], body[1], conv_dict(body[2]), body[3], body[4], body[5], int(body[6]), body[7], conv_disp(body[8]), get(body,9), get(body,10) )
        
    return info

def define_arguments(parser):
    parser.add_argument('filter', help='Filter for mail parts to get, simple expression with variables comparisons ~=, = , > etc. and  logical operators & | ! and brackets ')
    parser.add_argument('-H', '--host', help="IMAP server - host name or host:port", required=True)
    parser.add_argument('-u', '--user', help='User name', required=True)
    parser.add_argument('-p', '--password', help='User password')
    parser.add_argument('--no-ssl', action='store_true',  help='Do not use SSL, use plain unencrypted connection')
    parser.add_argument('--insecure-ssl', action='store_true',  help='Use insecure SSL - certificates are not checked')
    parser.add_argument('--folder', default='INBOX', help='mail folder, default is INBOX')
    parser.add_argument('-f','--file-name', help="Pattern for outgoing files - supports {var} replacement - same variables as for filter")
    parser.add_argument('-c', '--command', help='Command to be executed on downloaded file, supports {var} replacement - same variables as for filter, if output file is not specified, data are sent via standard input ')
    parser.add_argument('-t', '--threads', type=int, help='Download message parts in x separate threads')
    parser.add_argument('-v', '--verbose', action="store_true", help= 'Verbose messaging')
    parser.add_argument('--debug', action="store_true", help= 'Debug logging')
    parser.add_argument('--log-file', help="Log is written to this file (otherwise it's stdout)")
    parser.add_argument('--test', action="store_true", help= ' Do not download and process - just show found email parts')
    parser.add_argument('--seen', action="store_true", help= 'Marks processed messages (matching filter) as seen')
    parser.add_argument('--delete', action="store_true", help= 'Deletes processed messages (matching filter)')
    parser.add_argument('--delete-file', action="store_true", help= 'Deletes downloaded file after command')
    parser.add_argument('--move', help= 'Moves processed messages (matching filter) to specified folder')
    parser.add_argument('--timeit', action="store_true", help="Will measure time tool is running and print it at the end" )
    parser.add_argument('--no-imap-search', action="store_true", help="Will not use IMAP search - slow, but will assure exact filter match on any server")
    parser.add_argument('--unsafe-imap-search', action="store_true", help="Advanced IMAP search features, requiring full IMAPv4 compliance, which are supported only by some servers (dovecot)")
    parser.add_argument('--version', action='version', version='%s' % imap_detach.__version__)
def extra_help():
    lines=[]
    lines.append("Variables for filter: %s" % ' '.join(sorted(DUMMY_INFO.keys())))
    lines.append("Operators for filter: = ~= (contains) ^= (starts with) $= (ends with) > < >= <= ")
    lines.append("Date(time) format: YYYY-MM-DD or YYYY-MM-DD HH:SS - enter without quotes")
    lines.append("Additional variables for command: file_name file_base_name file_dir")
    
    return ('\n'.join(lines))

def main():
    start=time.time()
    parser=argparse.ArgumentParser(epilog=extra_help(), formatter_class=RawTextHelpFormatter)
    define_arguments(parser)
    opts=parser.parse_args()
    
    if opts.debug:
        logging.basicConfig(level=logging.DEBUG, filename=opts.log_file)
    elif opts.verbose:
        logging.basicConfig(level=logging.INFO, format="%(message)s", filename=opts.log_file)
    else:
        logging.basicConfig(level=logging.ERROR, stream=sys.stderr)
    
    
    host, port= split_host(opts.host, ssl=not opts.no_ssl)
    ssl= not opts.no_ssl
    if opts.insecure_ssl:
        ssl='insecure'
    log.debug('SSL status is %s', ssl)
    # test filter parsing
    eval_parser=SimpleEvaluator(DUMMY_INFO)
    filter=opts.filter
    
    try:
        imap_filter=IMAPFilterGenerator(opts.unsafe_imap_search).parse(filter, serialize='list') if not opts.no_imap_search else None
        _ = eval_parser.parse(filter)
    except ParserSyntaxError as e:
        msg = "Invalid syntax of filter: %s" %extract_err_msg(e)
        log.error(msg)
#        p(msg, file=sys.stderr)
        sys.exit(1)
    except ParserEvalError as e:
        msg = "Invalid semantics of filter: %s" % extract_err_msg(e)
        log.error(msg)
        #p(msg, file=sys.stderr)
        sys.exit(2)
    
    charset=None    
    if  imap_filter:
        try:
            [part.encode('ascii') for part in imap_filter]
        except UnicodeEncodeError:
            log.warn('Your search contains non-ascii characters, will try UTF-8, but it may not work on some servers')
            try:
                [part.encode('utf-8') for part in imap_filter]
                charset='UTF-8'
            except UnicodeEncodeError as e:
                log.error('Invalid characters in filter: %e',e)
                sys.exit(3)   
        
        
    log.debug('IMAP filter: %s', imap_filter) 
    pool=None
    try:   
        c=IMAP_client_factory(host,port,use_ssl=ssl)
        try:
            c.login(opts.user, opts.password)
            if opts.move and  not c.folder_exists(opts.move):
                c.create_folder(opts.move)
            folder=opts.folder
           
            if opts.threads:
                pool=Pool(opts.threads, host, port, ssl, opts.user, opts.password, folder)
            process_folder(c, pool, folder, imap_filter, charset, eval_parser, opts)  
            
            if pool:
                if opts.verbose:
                    p('Finished searching, now wait until all parts download in separate threads')
                def report():
                    while True:
                        log.debug('Pool status - size %d, unfinished %d', pool._queue.qsize(), pool._queue.unfinished_tasks)
                        time.sleep(5)
                if logging.getLogger().isEnabledFor(logging.DEBUG):
                    t=Thread(target=report, name='Debug reporting')
                    t.daemon=True
                    t.start()
                pool.wait_finish()   
                log.debug('Pool is finished')
        finally:
            if opts.delete or opts.move:
                c.expunge()
            c.logout()
            
    except Exception:
        log.exception('Runtime Error')     
        sys.exit(4)
        
    if opts.timeit:
        p('Total Time: %f s' % (time.time()-start))
    
def process_folder(c, pool, folder, imap_filter, charset, eval_parser, opts):    
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
    
    selected=c.select_folder(folder)
    msg_count=selected[b'EXISTS']
    if msg_count>0:
        log.debug('Folder %s has %d messages', folder, msg_count  )
        # this is workaround for imapclient 13.0 -  since it has bug in charset in search
        messages=c.search(imap_filter or 'ALL', charset)
        if not messages:
            log.warn('No messages found')
        else:
            res=c.fetch(messages, [b'INTERNALDATE', b'FLAGS', b'RFC822.SIZE', b'ENVELOPE', b'BODYSTRUCTURE'])
            for msgid, data in   six.iteritems(res):
                body=data[b'BODYSTRUCTURE']
                msg_info=MailInfo(data)
                log.debug('Got message %s', msg_info)
                
                part_infos=process_parts(body, msg_info, eval_parser, opts.filter, opts.test)
                if part_infos:
                    if pool:
                        pool.download(folder=folder, msgid=msgid, part_infos=part_infos, msg_info=msg_info, 
                                      filename=opts.file_name,  command= opts.command,
                                 delete=opts.delete_file, **msg_action(opts))
                    else:
                        download(msgid, part_infos, msg_info, opts.file_name,  command= opts.command, client=c, 
                                 delete=opts.delete_file, **msg_action(opts))
                    
            
                        
    else:
        log.info('No messages in folder %s', opts.folder) 
        
def process_parts(body, msg_info, eval_parser, filter, test=False):
    def msg(part_info):
        msg = u'File "{name}" of type {mime} and size {size} in email "{subject}" from {from}'.format(**msg_info)
        if six.PY2:
            msg=msg.encode('ascii', 'replace')
        return msg
    log.debug('Body Structure: %s', body)
    part_infos=[]
    for part_info in walk_structure(body):
        if part_info.type == 'multipart': #or (part_info.type=='message' and part_info.sub_type =='rfc822'):
            log.error('We should not get multiparts here - %s', part_info.sub_type)
        else:
            log.debug('Message part %s', part_info)
            msg_info.update_part_info(part_info)
            eval_parser.context=msg_info
            if eval_parser.parse(filter):
                log.debug('Will process this part')
                if test:
                    p(msg(part_info))
                else:
                    log.info(msg(part_info))
                    part_infos.append(part_info)
            else:
                log.debug('Will skip this part')
    return part_infos



    
if __name__ == '__main__':
    main()


    
    

    