'''
Created on Nov 26, 2015

@author: ivan
'''
import logging
from threading import Thread, current_thread
import imapclient
from collections import namedtuple
import six
from six.moves.queue import Queue  # @UnresolvedImport
import socket
from imap_detach.download import download
from copy import copy
from imap_detach.utils import IMAP_client_factory

log=logging.getLogger('pool')

# DownloadItem=namedtuple('DownloadItem', ('msgid', 'part_infos', 'msg_info', 'filename', 'command',  'delete', 'max_time',
#              'message_action', 'message_action_args'))

SOFT_ERRORS=(imapclient.IMAPClient.Error, socket.error)

class UIDExpired(Exception):
    Exception

class Downloader(Thread):
    def __init__(self, queue,host, port, ssl, user, password):
        super(Downloader,self).__init__(name='Downloader thread')
        self._client=IMAP_client_factory(host,port, use_ssl=ssl)
        self._client.login(user, password)
        self.daemon=True
        self._queue=queue
        self.running=True
        self._selected_folder=None
    
    def stop(self): 
        self.running=False  
        
    def select_folder(self,folder, uid_validity):
        selected=self._client.select_folder(folder)
        if selected[b'UIDVALIDITY'] != uid_validity:
            raise UIDExpired('Message UID expired, restart')
        self._selected_folder=folder
         
    def run(self):
        while self.running:
            item=self._queue.get()
            log.debug('Thread %s - got item %s', current_thread().name, item)
            try:
                folder=item['folder']
                uid_validity = item['uid_validity']
                if folder != self._selected_folder:
                    self.select_folder(folder, uid_validity)
                kwargs=copy(item)   
                del kwargs['folder']
                del kwargs['uid_validity']
                del kwargs['retry'] 
                kwargs['client']=self._client
                download(**kwargs)
            except SOFT_ERRORS as e:
                self._queue.task_done()
                msgid=item['msgid']
                log.warn('Download of message %d problem: %s', msgid, e)
                if item['retry'] < 3:
                    item['retry']+=1
                    self._queue.put(item)
                else:
                    log.exception('Download of message %d failed: %s', msgid, e) 
            except Exception as e:
                self._queue.task_done()
                log.exception('Download of message %d failed: %s', item['msgid'], e) 
            else:
                self._queue.task_done()
        
class Pool(object):
    class Error(Exception):
        pass
    
    def __init__(self, threads, host, port, ssl, user, password):
        self._threads=[]
        self._queue = Queue(maxsize=1000)
        count=0
        while len(self._threads) < threads and count < 3* threads:
            try:
                count+=1
                w=Downloader(self._queue, host, port, ssl, user, password)
                w.start()
                self._threads.append(w)
            except SOFT_ERRORS as e:
                log.warn('Cannot create downloder thread: %s', e)
                
        if len(self._threads) != threads:
            log.error('Cannot create enough workers')
            raise Pool.Error('Cannot create enough workers')
        
    def wait_finish(self):
        self._queue.join()
        
    def stop(self):
        for t in self._threads:
            t.stop()
        
    def download(self, **kwargs):
        kwargs['retry']=0
        self._queue.put(kwargs)
                
        
        