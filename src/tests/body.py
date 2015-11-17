from six import print_ as p
import unittest
from imap_detach.imap_client import walk_structure

BODY=([([(b'TEXT',
     b'PLAIN',
     (b'CHARSET', b'ISO-8859-1', b'FORMAT', b'flowed'),
     None,
     None,
     b'7BIT',
     1145,
     22,
     None,
     None,
     None,
     None),
    ([(b'TEXT',
       b'HTML',
       (b'CHARSET', b'ISO-8859-1'),
       None,
       None,
       b'7BIT',
       7447,
       180,
       None,
       None,
       None,
       None),
      (b'IMAGE',
       b'GIF',
       (b'NAME', b'haedjgag.gif'),
       b'<part1.01050901.01000603@example.com>',
       None,
       b'BASE64',
       18158,
       None,
       (b'INLINE', (b'FILENAME', b'haedjgag.gif')),
       None,
       None),
      (b'IMAGE',
       b'PNG',
       (b'NAME', b'cgjhfabb.png'),
       b'<part5.09080607.06070109@example.com>',
       None,
       b'BASE64',
       1808,
       None,
       (b'INLINE', (b'FILENAME', b'cgjhfabb.png')),
       None,
       None),
      (b'IMAGE',
       b'JPG',
       (b'NAME', b'ijcbgecj.'),
       b'<part6.05040701.09070509@example.com>',
       None,
       b'BASE64',
       12020,
       None,
       (b'INLINE', (b'FILENAME', b'ijcbgecj.')),
       None,
       None),
      (b'IMAGE',
       b'JPG',
       (b'NAME', b'icfhaegi.'),
       b'<part8.00030901.09000500@example.com>',
       None,
       b'BASE64',
       12542,
       None,
       (b'INLINE', (b'FILENAME', b'icfhaegi.')),
       None,
       None),
      (b'IMAGE',
       b'JPG',
       (b'NAME', b'jdhhjfih.'),
       b'<part10.06070505.03070702@example.com>',
       None,
       b'BASE64',
       15004,
       None,
       (b'INLINE', (b'FILENAME', b'jdhhjfih.')),
       None,
       None),
      (b'IMAGE',
       b'JPG',
       (b'NAME', b'biiddjee.'),
       b'<part12.09060909.01040008@example.com>',
       None,
       b'BASE64',
       12846,
       None,
       (b'INLINE', (b'FILENAME', b'biiddjee.')),
       None,
       None),
      (b'IMAGE',
       b'JPG',
       (b'NAME', b'hidffibg.'),
       b'<part14.03000507.06070001@example.com>',
       None,
       b'BASE64',
       9902,
       None,
       (b'INLINE', (b'FILENAME', b'hidffibg.')),
       None,
       None)],
     b'RELATED',
     (b'BOUNDARY', b'------------090804090502080900080501'),
     None,
     None,
     None)],
   b'ALTERNATIVE',
   (b'BOUNDARY', b'------------020403030206060806080603'),
   None,
   None,
   None),
  (b'TEXT',
   b'CSV',
   (b'NAME', b'PDF_checker.csv'),
   None,
   None,
   b'8BIT',
   7517136,
   39211,
   None,
   (b'ATTACHMENT', (b'FILENAME', b'PDF_checker.csv')),
   None,
   None)],
 b'MIXED',
 (b'BOUNDARY', b'------------010808060905080909070704'),
 None,
 None,
 None)

BODY2=([(b'text',
     b'plain',
     (b'charset', b'ISO-8859-1', b'format', b'flowed'),
     None,
     None,
     b'7bit',
     23,
     1,
     None,
     None,
     None,
     None),
    (b'message',
     b'rfc822',
     (b'name', b'Attached Message'),
     None,
     None,
     b'7bit',
     228843,
     (b'Tue, 17 Nov 2015 06:42:04 +0100',
      b'S prilohou',
      ((b'Test', None, b'test', b'example.com'),),
      ((b'Test', None, b'test', b'example.com'),),
      ((b'Test', None, b'test', b'example.com'),),
      ((None, None, b'test', b'example.com'),),
      None,
      None,
      None,
      b'<564ABE2C.5080008@example.com>'),
     (((b'text',
        b'plain',
        (b'charset', b'ISO-8859-1', b'format', b'flowed'),
        None,
        None,
        b'7bit',
        33,
        3,
        None,
        None,
        None,
        None),
       (b'text',
        b'html',
        (b'charset', b'ISO-8859-1'),
        None,
        None,
        b'7bit',
        234,
        11,
        None,
        None,
        None,
        None),
       b'alternative',
       (b'boundary', b'------------090506020908060504060000'),
       None,
       None,
       None),
      (b'application',
       b'pdf',
       (b'name', b'Lovosice-Praha.pdf'),
       None,
       None,
       b'base64',
       176124,
       None,
       (b'attachment', (b'filename', b'Lovosice-Praha.pdf')),
       None,
       None),
      (b'image',
       b'png',
       (b'name', b'ui.png'),
       None,
       None,
       b'base64',
       50932,
       None,
       (b'attachment', (b'filename', b'ui.png')),
       None,
       None),
      b'mixed',
      (b'boundary', b'------------040807040203050000060506'),
      None,
      None,
      None),
     3133,
     None,
     (b'attachment', (b'filename', b'Attached Message')),
     None,
     None)],
   b'mixed',
   (b'boundary', b'------------000807080405000207090301'),
   None,
   None,
   None)


BODY3 =  ([(b'TEXT', b'HTML', (b'CHARSET', b'iso-8859-2'), None, None, b'QUOTED-PRINTABLE', 320, 8, 
            None, None, None), (b'MESSAGE', b'RFC822', None, None, None, b'7BIT', 266568, None, 
        (b'ATTACHMENT', None), None)], b'MIXED', (b'BOUNDARY', b'----=_NextPart_000_001E_01C51019.1E6EC590'), 
          None, None)


class Test(unittest.TestCase):

    def test(self):
        sec_2=False
        sec_122=False
        for info in walk_structure(BODY):
            p(info)
            if info.section =='2':
                self.assertEqual(info.type, 'text')
                self.assertEqual(info.sub_type, 'csv')
                sec_2=True
            if info.section =='1.2.2':
                self.assertEqual(info.type, 'image')
                self.assertEqual(info.sub_type, 'gif')
                sec_122=True
        self.assertTrue(sec_2)
        self.assertTrue(sec_122)
        
    
    def test_msg(self):
        sec_2=False
        sec_23=False
        for info in walk_structure(BODY2, multipart=True):
            p(info)
            if info.section =='2':
                self.assertEqual(info.type, 'multipart')
                self.assertEqual(info.sub_type, 'mixed')
                sec_2=True
            if info.section =='2.3':
                self.assertEqual(info.type, 'image')
                self.assertEqual(info.sub_type, 'png')
                sec_23=True
        self.assertTrue(sec_2)
        self.assertTrue(sec_23)
        
        
    def test_gmail(self):
        sec_2 = False
        for info in walk_structure(BODY3, multipart=True):
            p(info)
            if info.section =='2':
                self.assertEqual(info.type, 'message')
                self.assertEqual(info.sub_type, 'rfc822')
                sec_2=True
        self.assertTrue(sec_2)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()