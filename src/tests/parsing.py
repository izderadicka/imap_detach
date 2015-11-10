import unittest as unit
import parsimonious
from imap_detach.expressions import SimpleEvaluator


JSON=r"""# JSON grammar
value = space (string / number / object / array / true_false_null) space
object = "{" members "}"
members = (pair ("," pair)*)?
pair = string ":" value
array = "[" elements "]"
elements = (value ("," value)*)?
true_false_null = "true" / "false" / "null"
string = space "\"" chars "\"" space
chars = ~"[^\"]*"  # TODO implement the real thing
number = (int frac exp) / (int exp) / (int frac) / int
int = "-"? ((digit1to9 digits) / digit)
frac = "." digits
exp = e digits
digits = digit+
e = "e+" / "e-" / "e" / "E+" / "E-" / "E"
digit1to9 = ~"[1-9]"
digit = ~"[0-9]"
space = ~"\s*"
"""


class Test(unit.TestCase):
    
    def setUp(self):
        pass
        
    def test_1(self):
        p=SimpleEvaluator({'a':'b', 'c':''})
        res = p.parse('a="b"')
        self.assertTrue(res)
        res= p.parse('c="b"')
        self.assertFalse(res)
        
    def test_2(self):
        p=SimpleEvaluator({'a':'1', 'b':'2', 'dummy':'dummy test'})
        self.assertTrue(p.parse('(a="1")'))
        self.assertFalse(p.parse('! (a="1")'))
        self.assertFalse(p.parse('! a="1" '))
        self.assertTrue(p.parse('!(! a="1")'))
        
        self.assertTrue(p.parse('a="1" & b="2"'))
        
    def test_3(self):
        p=SimpleEvaluator({'a':'1', 'b':'2', 'dummy':'dummy test'})
        self.assertFalse(p.parse('a="1" & b="3"'))
        self.assertTrue(p.parse('a="2" | b="2"'))
        self.assertTrue(p.parse('a="1" & b="2" & dummy ~= "test"'))
        
    def test_4(self):
        p=SimpleEvaluator({'a':'1', 'b':'2', 'dummy':'dummy test', 'd':'', 'c':''})
        self.assertTrue(p.parse('(a="1" | d="3") & (a="2" | b="2")'))
        self.assertFalse(p.parse('(a="1" | d="3") & !(a="2" | b="2")'))
        self.assertTrue(p.parse('(a = "1" | (! d="3")) & (a = "2" | b="2")'))
        self.assertFalse(p.parse('a="2" | b="2" & dummy="xxx"' ))
        self.assertTrue(p.parse('a="2" | b="2" & dummy~="test"' ))
        
        self.assertTrue(p.parse('a="1" | b="2" & dummy="xxx" | c="x"' ))
        
        self.assertTrue(p.parse('a="1" | ( b="2" & dummy="xxx"  )| c="x"' ))
        
        self.assertFalse(p.parse('(a="1" | b="2") & dummy="xxx" | c="x"' ))
        self.assertTrue(p.parse('a="1" | b="2" & ( dummy="xxx" | c="x" )' ))
        self.assertTrue(p.parse('a="1" | b="3" & dummy="xxx" | c="x"' ))
        self.assertFalse(p.parse('( a="1" | b="3" ) & dummy="xxx" | c="x"' ))
        
    def test_6(self):
         
        p=SimpleEvaluator({'a':'1', 'b':'2', 'dummy':'dummy test', 'd':'', 'c':''})   
        self.assertTrue(p.parse('(b="2" & dummy="xxx" )|a="1"' ))
        self.assertTrue(p.parse('((b="2" & dummy="xxx" )|a="1") | c="x"' ))
        self.assertTrue(p.parse('(b="2" & dummy="xxx" )|(a="1" | c="x")' ))
        self.assertTrue(p.parse('b="2" | a="1" | c="x"' ))
        self.assertTrue(p.parse('(b="2" & dummy="xxx" )| c="x" | a="1" ' ))
        
    def test_7(self):
        p=SimpleEvaluator({'a':'1', 'b':'2', 'dummy':'dummy test', 'd':'', 'c':''}) 
        self.assertTrue(p.parse('(b="2" & dummy="xxx" )|a="1" | c="x"' ))
        
        self.assertTrue(p.parse('b="2" & dummy="xxx" |a="1" | c="x"' )) 
        self.assertFalse(p.parse('a="1" & b="2" &c="3" & dummy ~= "test"'))
        
    def test_5(self):
        p=SimpleEvaluator({'a':'1', 'b':'2', 'dummy':'dummy test', 'unknown':''})
        self.assertTrue(p.parse('a'))
        self.assertFalse(p.parse('unknown'))
        self.assertFalse(p.parse('unknown & a'))
        self.assertTrue(p.parse('unknown | a'))
        
    def test_errors(self):
        p=SimpleEvaluator({'a':'1', 'b':'2', 'dummy':'dummy test', "uni":True})
        try:
            self.assertTrue(p.parse('(a="2" | b="x" & dummy="test' ))
            self.fail('Should rise parse exception')
        except parsimonious.ParseError as e:
            print(e)
            
        try:
            self.assertTrue(p.parse('!! a="1"')) # this should not be possible  inner expression should be in ()
            self.fail('Should rise parse exception')
        except parsimonious.ParseError as e:
            print(e)
               
        try:
            self.assertTrue(p.parse('a="2" | b="x" & dummy="test" | c' ))
            self.fail('Should rise eval exception')
        except parsimonious.exceptions.VisitationError as e:
            print(e)
             
         
        try:
            self.assertTrue(p.parse('a="2" | b="x" & uni="y" ' ))
            self.fail('Should rise eval exception')
        except parsimonious.exceptions.VisitationError as e:
            print(e)
            
        
    def test_json(self):
        res=parsimonious.Grammar(JSON).parse('{"x":1, "y":[0,1,2]}')
        
        