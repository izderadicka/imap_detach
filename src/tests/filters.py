import unittest
from imap_detach.expressions import SimpleEvaluator, TagList
from imap_detach.filter import IMAPFilterGenerator
from imap_detach.utils import smart_join
from datetime import datetime


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
        
        t1='to ^= "myself"'
        self.assertEqual(g.parse(t1), 'TO "myself"')
        t1='to $= "myself"'
        self.assertEqual(g.parse(t1), 'TO "myself"')
        
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
        
        
    def test_flags(self):
        g=IMAPFilterGenerator()
        ctx={
             'recent': True,
          'seen': True,
          'answered' : True,
          'flagged': True,
          'deleted': True,
          'draft' : True,
          
             }
        p=SimpleEvaluator(ctx)
        t="recent & seen & answered & flagged & deleted & draft"
        self.assertEqual(g.parse(t), "(RECENT SEEN ANSWERED FLAGGED DELETED DRAFT)")
        self.assertTrue(p.parse(t))
        
        
    def test_date(self):
        
        g=IMAPFilterGenerator()
        ctx={'date' : datetime(2015,11,15)}
        p=SimpleEvaluator(ctx)
        t="date = 2015-11-15"
        self.assertEqual(g.parse(t), "ON 15-Nov-2015")
        self.assertTrue(p.parse(t))
        
        t="date < 2015-11-14"
        self.assertEqual(g.parse(t), 'BEFORE 14-Nov-2015')
        self.assertFalse(p.parse(t))
        
        t="date > 2015-11-14"
        self.assertEqual(g.parse(t), '(OR SINCE 14-Nov-2015 NOT (ON 14-Nov-2015))')
        self.assertTrue(p.parse(t))
        
        t="date <= 2015-11-15"
        self.assertEqual(g.parse(t), '(OR BEFORE 15-Nov-2015 ON 15-Nov-2015)')
        self.assertTrue(p.parse(t))
        
        t="date >= 2015-11-15"
        self.assertEqual(g.parse(t), 'SINCE 15-Nov-2015')
        self.assertTrue(p.parse(t))
        
        p=SimpleEvaluator({'date' : datetime(2015,11,15,15,10)})
        t="date <= 2015-11-15"
        self.assertEqual(g.parse(t), '(OR BEFORE 15-Nov-2015 ON 15-Nov-2015)')
        self.assertTrue(p.parse(t))
        
        
    def test_size(self):
        g=IMAPFilterGenerator()
        ctx={'size' : 5 * 1024}
        p=SimpleEvaluator(ctx)
        
        t="size > 4k"
        self.assertEqual(g.parse(t), "LARGER %d"% (4*1024))
        self.assertTrue(p.parse(t))
        
        t="size >= 4k"
        self.assertEqual(g.parse(t), "LARGER %d"% (4*1024))
        self.assertTrue(p.parse(t))
        
        t="size < 4k"
        self.assertEqual(g.parse(t), '')
        self.assertFalse(p.parse(t))
        
        t="size <= 4k"
        self.assertEqual(g.parse(t), '')
        self.assertFalse(p.parse(t))
        
    def test_custom_flags(self):
        g=IMAPFilterGenerator(unsafe=True)
        ctx={'flags':TagList(['$Forwarded', 'NotJunk'])}
        p=SimpleEvaluator(ctx)
        t='flags = "$Forwarded"'
        self.assertEqual(g.parse(t), 'KEYWORD "$Forwarded"')
        self.assertTrue(p.parse(t))
        
        t='flags ^= "$Forwarded"'
        self.assertEqual(g.parse(t), '')
        self.assertTrue(p.parse(t))
        
    def test_text(self):
        g=IMAPFilterGenerator(unsafe=True)
        ctx={'mime':'application/pdf', 'name':'soubor.pdf'}
        p=SimpleEvaluator(ctx)
        t='mime="application/pdf" & name ~= "soubor"'
        self.assertEqual(g.parse(t), '(TEXT "application/pdf" TEXT "soubor")')
        self.assertTrue(p.parse(t))
        
        t='mime^="application" & name $= ".pdf"'
        self.assertEqual(g.parse(t), '(TEXT "application" TEXT ".pdf")')
        self.assertTrue(p.parse(t))
        
    def test_year(self):
        g=IMAPFilterGenerator(unsafe=True)
        ctx={'year':2015}
        p=SimpleEvaluator(ctx)
        
        t='year=2015'
        self.assertEqual(g.parse(t), '(SINCE 1-Jan-2015 BEFORE 1-Jan-2016)')
        self.assertTrue(p.parse(t))
        
        t='year>2015'
        self.assertEqual(g.parse(t), 'SINCE 1-Jan-2016')
        self.assertFalse(p.parse(t))
        
        t='year>=2015'
        self.assertEqual(g.parse(t), 'SINCE 1-Jan-2015')
        self.assertTrue(p.parse(t))
        
        t='year<2016'
        self.assertEqual(g.parse(t), 'BEFORE 1-Jan-2016')
        self.assertTrue(p.parse(t))
        
        t='year<=2016'
        self.assertEqual(g.parse(t), 'BEFORE 1-Jan-2017')
        self.assertTrue(p.parse(t))
        
    def test_list(self):
        g=IMAPFilterGenerator()
        t1='to ~= "myself"'
        self.assertEqual(g.parse(t1, serialize='list'), ['TO', "myself"])
        
        t10='! subject ~= "test"'
        self.assertEqual(g.parse(t10, serialize='list'), ['(','NOT', 'SUBJECT', "test",')'])
        
        
        
        t="date <= 2015-11-15"
        self.assertEqual(g.parse(t,  serialize='list'), ['(','OR', 'BEFORE', '15-Nov-2015',  'ON', '15-Nov-2015', ')'])
        
        t='(! subject ~= "test" | from ~= "example.com") & ( ! recent |  seen)'
        self.assertEqual(g.parse(t, serialize = 'list'),['(','(','(','OR', '(' ,'NOT', 'SUBJECT', "test",')', 'FROM', "example.com",')',')', '(','(','OR', '(', 'NOT', 'RECENT',')', 'SEEN',')',')',')'])
        
    def test_notimap(self):
        g=IMAPFilterGenerator()
        ctx={'mime':'text/plain', 'date': datetime(2015,10,13), 'year':2015, 'subject':'mako','section':'1.1'}
        p=SimpleEvaluator(ctx)
        t='(section="1" | section~="1.")'
        self.assertEqual(g.parse(t), '')
        self.assertEqual(g.parse(t, serialize='list'), [])
        self.assertTrue(p.parse(t))
        t='mime="text/plain" & year=2015 & ! subject^="re:" & (section="1" | section~="1.")'    
        self.assertEqual(g.parse(t), '(SINCE 1-Jan-2015 BEFORE 1-Jan-2016) (NOT SUBJECT "re:")')
        self.assertEqual(g.parse(t, serialize='list'), ['(','SINCE', '1-Jan-2015', 'BEFORE',  '1-Jan-2016', ')', '(', 'NOT', 'SUBJECT', "re:", ')'])
        self.assertTrue(p.parse(t))
        
    def test_join(self):
        self.assertEqual(smart_join(['TO', "myself"]), b'TO myself')
        
    def test_or(self):
        g=IMAPFilterGenerator()
        ctx={'mime':'application/pdf', 'size': 200*1024, 'from':'test@example.com', 'cc':'','subject':'mako','section':'1.1'}
        p=SimpleEvaluator(ctx)
        
        t='from~="test" | mime="application/pdf"'
        self.assertEqual(g.parse(t), '')
        self.assertTrue(p.parse(t))
        
        t='from~="test" | (mime="application/pdf")'
        self.assertEqual(g.parse(t), '')
        self.assertTrue(p.parse(t))
        t='(mime="application/pdf") | from~="test"'
        self.assertEqual(g.parse(t), '')
        self.assertTrue(p.parse(t))
        t='(mime="application/pdf") | (from~="test")'
        self.assertEqual(g.parse(t), '')
        self.assertTrue(p.parse(t))
        
        t='(mime="application/pdf" & ! from ~= "siska" & ! cc~="nekdo" & size>100k & size<1M) | (mime="image/png")'
        self.assertEqual(g.parse(t), '')
        self.assertTrue(p.parse(t))
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()