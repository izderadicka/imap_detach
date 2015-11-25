'''
Created on Nov 25, 2015

@author: ivan
'''
import unittest
from imap_detach.expressions import SimpleEvaluator, TagList


class Test(unittest.TestCase):


    def test(self):
        p=SimpleEvaluator({'flags':TagList(['quick', 'BROWN', 'fox', 'JUMPS', 'over', 'LAZY', 'dog'])})
        
        self.assertTrue(p.parse('flags = "over" & flags= "brown"'))
        self.assertTrue(p.parse('flags~="row" & flags^="jump" & flags$="zy"'))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()