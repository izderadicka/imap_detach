#!/usr/bin/env python

import argparse
from six import print_ as p
import sys
import logging
from imap_detach.mail_info import DUMMY_INFO
from imap_detach.imap_client import main as client_main
from argparse import RawTextHelpFormatter
import time
import imap_detach

log=logging.getLogger('cmd')


def split_host(host, ssl=True):
    port = 993 if ssl else 143
    host_list=host.split(':')
    if len(host_list)>2:
        raise ValueError('Invalid host string %s'%host)
    if len(host_list)>1:
        port=int(host_list[1])
    server=host_list[0]
    return server, port

def define_arguments(parser):
    parser.add_argument('filter', help='Filter for mail parts to get, simple expression with variables comparisons ~=, = , > etc. and  logical operators & | ! and brackets ')
    parser.add_argument('-H', '--host', help="IMAP server - host name or host:port", required=True)
    parser.add_argument('-u', '--user', help='User name', required=True)
    parser.add_argument('-p', '--password', help='User password')
    parser.add_argument('--no-ssl', action='store_true',  help='Do not use SSL, use plain unencrypted connection')
    parser.add_argument('--insecure-ssl', action='store_true',  help='Use insecure SSL - certificates are not checked')
    parser.add_argument('--folder', action='append', help='mail folder(s), can specify more, or pattern with ?, * or **,  default is INBOX')
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
    
    
    client_main(opts)
        
    if opts.timeit:
        p('Total Time: %f s' % (time.time()-start))
    
if __name__ == '__main__':
    main()


    
    

    