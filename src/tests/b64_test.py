'''
Created on Nov 27, 2015

@author: ivan
'''
import unittest
from imap_detach.download import decode_part
from base64 import b64decode, b64encode


class Test(unittest.TestCase):


    def test(self):
        x=b'a'
        y=b64encode(x)
        self.assertEqual(y,b'YQ==' )
        self.assertEqual(decode_part(y, 'base64'), b'a')
        self.assertEqual(decode_part(y[:-1], 'base64'), b'a')
        self.assertEqual(decode_part(y[:-2], 'base64'), b'a')
        
        self.assertEqual(decode_part(y[:-3], 'base64'), b'')
        
        x=b'ab'
        y=b64encode(x)
        self.assertEqual(y, b'YWI=')
        self.assertEqual(decode_part(y, 'base64'), b'ab')
        self.assertEqual(decode_part(y[:-1], 'base64'), b'ab')
        
        self.assertNotEqual(decode_part(y[:-2], 'base64'), b'ab')
        
        x=b'abc'
        y=b64encode(x)
        self.assertEqual(y, b'YWJj')
        self.assertEqual(decode_part(y, 'base64'), b'abc')
        self.assertNotEqual(decode_part(y[:-1], 'base64'), b'abc')
        
        x=b'a quick brown fox jumps over the lazy dog'
        y=b64encode(x)
        step=7
        lines=[y[i:i+step] for i in range(0, len(y), step)]
        ny=b'\r\n'.join(lines)
        self.assertEqual(decode_part(ny, 'base64'), x)
        self.assertEqual(decode_part(ny[:-1], 'base64'), x)
        self.assertNotEqual(decode_part(ny[:-2], 'base64'), x)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test']
    unittest.main()