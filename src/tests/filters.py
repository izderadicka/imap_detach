import unittest
from imap_detach.expressions import SimpleEvaluator
from imap_detach.filter import IMAPFilterGenerator


CONTEXT={'from': 'test@example.com',
          'to': 'myself@sample.com',
          'cc': '',
          'bcc': '',
          'subject': 'Test Mail',
          'recent': False,
          'seen': True,
          'mime': 'image/png'}

class Test(unittest.TestCase):


    def test_imap(self):
        g=IMAPFilterGenerator()
        p=SimpleEvaluator( CONTEXT)
        t1='to ~= "myself"'
        self.assertEqual(g.parse(t1), 'TO "myself"')
        self.assertTrue(p.parse(t1))
        
        t2='mime = "image/png"'
        self.assertEqual(g.parse(t2), '')
        self.assertTrue(p.parse(t2))
        
        t3='to = "myself"'
        self.assertEqual(g.parse(t3), 'TO "myself"')
        self.assertFalse(p.parse(t3))
        
        t4='to ~= "myself" & subject ~= "test"'
        self.assertEqual(g.parse(t4), '(TO "myself" SUBJECT "test")')
        self.assertTrue(p.parse(t4))
        
        t5='to ~= "myself" | subject ~= "test"'
        self.assertEqual(g.parse(t5), '(OR TO "myself" SUBJECT "test")')
        self.assertTrue(p.parse(t5))
        
        t6='to ~= "myself" & mime ~= "image"'
        self.assertEqual(g.parse(t6), 'TO "myself"')
        self.assertTrue(p.parse(t6))
        
        t7='mime~="image" & subject ~= "test"'
        self.assertEqual(g.parse(t7), 'SUBJECT "test"')
        self.assertTrue(p.parse(t7))
        
    def test_imap2(self):
        g=IMAPFilterGenerator()
        p=SimpleEvaluator( CONTEXT)
           
        t8='to ~= "myself" | mime ~= "image"'
        self.assertEqual(g.parse(t8), '')
        self.assertTrue(p.parse(t8))
        
        t9='mime~="image" | subject ~= "test"'
        self.assertEqual(g.parse(t9), '')
        self.assertTrue(p.parse(t9))
        
        t10='! subject ~= "test"'
        self.assertEqual(g.parse(t10), '(NOT SUBJECT "test")')
        self.assertFalse(p.parse(t10))
        
    
    def test_imap3(self):
        g=IMAPFilterGenerator()
        p=SimpleEvaluator( CONTEXT)    
        
        t='(! subject ~= "test" | from ~= "example.com") & ( ! recent |  seen)'
        self.assertEqual(g.parse(t),'(((OR (NOT SUBJECT "test") FROM "example.com")) ((OR (NOT RECENT) SEEN)))')
        self.assertTrue(p.parse(t))
        
        
        t='subject ~= "test" & from ~= "example.com" & to ~= "myself"' 
        self.assertEqual(g.parse(t), '(SUBJECT "test" FROM "example.com" TO "myself")')
        self.assertTrue(p.parse(t))
        
        t='subject ~= "test" | from ~= "example.com" | to ~= "myself"' 
        self.assertEqual(g.parse(t), '(OR SUBJECT "test" (OR FROM "example.com" TO "myself"))')
        self.assertTrue(p.parse(t))
        
        
    def test_imap4(self):
        g=IMAPFilterGenerator()
        p=SimpleEvaluator( CONTEXT)
        
        t='subject~= "test" & mime ~= "image" |  to ~= "myself"'
        self.assertEqual(g.parse(t), '(OR SUBJECT "test" TO "myself")')
        self.assertTrue(p.parse(t))
        
        t='subject~= "test" |  mime ~= "image" &  to ~= "myself"'
        self.assertEqual(g.parse(t), '(OR SUBJECT "test" TO "myself")')
        self.assertTrue(p.parse(t))
        
        t='subject~="test" & seen | to~="myself" &  ! recent'
        self.assertEqual( g.parse(t), '(OR (SUBJECT "test" SEEN) (TO "myself" (NOT RECENT)))')
        self.assertTrue(p.parse(t))
        
        
        
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()