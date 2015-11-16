# coding=utf-8 
import unittest
import six
from imap_detach.utils import email_decode


class Test(unittest.TestCase):


    def test1(self):
        x=email_decode(six.b('=?ISO-8859-2?Q?Odpov=ECdi_na_dotazy=5FM=A9MT=5F2006.doc?='))
        self.assertTrue(isinstance(x, six.text_type))
        self.assertEqual(x, u'Odpovědi na dotazy_MŠMT_2006.doc')
        
    def test2(self):
        x=email_decode('=?UTF-8?B?dGVzdC3Em8WhxI3FmcW+w73DocOtw6nDusWvxaXEjy50eHQ=?=')
        self.assertTrue(isinstance(x, six.text_type))
        self.assertEqual(x, u'test-ěščřžýáíéúůťď.txt')
        
        x=email_decode('divny =?UTF-8?B?xI1lc2vDvQ==?=')
        self.assertTrue(isinstance(x, six.text_type))
        self.assertEqual(x, u'divny český')


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test1']
    unittest.main()