
import unittest

class Some(object):
    
    def dec(fn):
        print( 'Calling deco')
        def x(self,*args):
            print ("Inner")
            r=fn(self,*args)
            return r+1
        return x
    
    @dec
    def f(self,x):
        return x+1


class Test(unittest.TestCase):


    def testName(self):
        o=Some()
        self.assertEqual(o.f(1),3)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()