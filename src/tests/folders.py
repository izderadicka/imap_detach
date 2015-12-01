'''
Created on Dec 1, 2015

@author: ivan
'''
import unittest
from imap_detach.utils import normalize_folders, matched_folders

FOLDERS=[((b'\\Noselect', ), b'/', 'Invalid'),
         (( b'\\HasChildren',), b'/', 'IMBOX'),
 ((b'\\NoInferiors', b'\\Marked'), b'/', 'IMBOX/processed'),
 ((b'\\NoInferiors', b'\\UnMarked', b'\\Trash'), b'/', 'Trash'),
 ((b'\\NoInferiors', b'\\Marked'), b'/', 'INBOX/processed'),
 ((b'\\NoInferiors', b'\\UnMarked', b'\\Drafts'), b'/', 'Drafts'),
 ((b'\\NoInferiors', b'\\Marked', b'\\Sent'), b'/', 'Sent'),
 ((b'\\HasNoChildren', b'\\Junk'), b'/', 'Spam'),
 ((b'\\HasChildren',), b'/', 'INBOX')]


class Test(unittest.TestCase):


    def test_norm(self):
        f=normalize_folders(FOLDERS)
        self.assertEqual(len(f), 8)
        self.assertTrue('IMBOX/processed' in f)
        self.assertFalse('Invalid' in f)
        
    def test_norm2(self):
        folders=FOLDERS=[((b'\\Marked', b'\\HasChildren'), b'\\', 'IMBOX'),
 ((b'\\NoInferiors', b'\\Marked'), b'\\', 'IMBOX\\processed'),
 ((b'\\NoInferiors', b'\\UnMarked', b'\\Trash'), b'\\', 'Trash')]
        f=normalize_folders(folders)
        self.assertEqual(len(f), 3)
        self.assertTrue('IMBOX/processed' in f)
        
    def test_match(self):
        f=normalize_folders(FOLDERS)
        r=matched_folders(f, ['INBOX'])
        self.assertEqual(r, ['INBOX'])
        r=matched_folders(f, ['INBOX*'])
        self.assertEqual(r, ['INBOX'])
        r=matched_folders(f, ['inbox*'])
        self.assertEqual(r, ['INBOX'])
        r=matched_folders(f, ['INBOX**'])
        self.assertEqual(r, ['INBOX/processed','INBOX'])
        r=matched_folders(f, ['*'])
        self.assertEqual(len(r),6)
        r=matched_folders(f, ['**'])
        self.assertEqual(len(r),8)
        



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()