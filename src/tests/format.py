'''
Created on Dec 3, 2015

@author: ivan
'''
import unittest
from string import Formatter
from imap_detach.utils import AdvancedFormatter

class Str(str):
    pass

class Test(unittest.TestCase):


    def test_dot(self):
        f=Formatter()
        x=Str('bla')
        x.x='foo'
        self.assertEqual(f.vformat('{x}{x.x}',[], {'x':x}), 'blafoo')
        
    def test_1(self):
        f=AdvancedFormatter()
        self.assertEqual(f.format('x{test|guest}y', guest='bla'), 'xblay')
        self.assertEqual(f.format('x{test|guest}y', guest='bla', test='kilik'), 'xkiliky')
        self.assertEqual(f.format('x{guest}y', guest='bla', test='kilik'), 'xblay')
        self.assertEqual(f.format('x{hj}y', guest='bla', test='kilik'), 'xy')
        self.assertEqual(f.format('x{guest+test}y', guest='bla', test='kilik'), 'xbla_kiliky')
        self.assertEqual(f.format('x{xx|guest+test}y', guest='bla', test='kilik'), 'xbla_kiliky')
        self.assertEqual(f.format('x{guest+test|zz}y', guest='bla', test='kilik'), 'xbla_kiliky')
        self.assertEqual(f.format('x{test|guest}y', guest='bla', test=''), 'xblay')


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_dot']
    unittest.main()