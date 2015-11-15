import unittest as unit
import parsimonious
from datetime import datetime

from imap_detach.expressions import SimpleEvaluator, ParserSyntaxError, ParserEvalError  


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
        except ParserSyntaxError as e:
            print(e)
            
            
        try:
            self.assertTrue(p.parse('a > "1"' ))
            self.fail('Should rise parse exception')
        except ParserSyntaxError as e:
            print(e)
            
        try:
            self.assertTrue(p.parse('!! a="1"')) # this should not be possible  inner expression should be in ()
            self.fail('Should rise parse exception')
        except ParserSyntaxError as e:
            print(e)
               
        try:
            self.assertTrue(p.parse('a="2" | b="x" & dummy="test" | c' ))
            self.fail('Should rise eval exception')
        except ParserEvalError as e:
            print(e)
             
         
        try:
            self.assertTrue(p.parse('a="2" | b="x" & uni="y" ' ))
            self.fail('Should rise eval exception')
        except ParserEvalError as e:
            print(e)
            
    def test_errors2(self):
        p= p=SimpleEvaluator({"number":100, 'date':datetime(2015,11,15), 'string':"something"})
        
        try:
            self.assertTrue(p.parse('number ~="1"' ))
            self.fail('Should rise eval exception')
        except ParserEvalError as e:
            print(e)
            
        try:
            self.assertTrue(p.parse('number ^="1"' ))
            self.fail('Should rise eval exception')
        except ParserEvalError as e:
            print(e)
            
        try:
            self.assertTrue(p.parse('number $="1"' ))
            self.fail('Should rise eval exception')
        except ParserEvalError as e:
            print(e)
            
        
        try:
            self.assertTrue(p.parse('date $="2"' ))
            self.fail('Should rise eval exception')
        except ParserEvalError as e:
            print(e)   
            
        try:
            self.assertTrue(p.parse('string < 1' ))
            self.fail('Should rise eval exception')
        except ParserEvalError as e:
            print(e) 
            
        try:
            self.assertTrue(p.parse('string <= 1' ))
            self.fail('Should rise eval exception')
        except ParserEvalError as e:
            print(e) 
            
        try:
            self.assertTrue(p.parse('string > 1' ))
            self.fail('Should rise eval exception')
        except ParserEvalError as e:
            print(e) 
            
        try:
            self.assertTrue(p.parse('string >= 1' ))
            self.fail('Should rise eval exception')
        except ParserEvalError as e:
            print(e) 
            
            
    def test_8(self):
        p=SimpleEvaluator({"number":100, 'date':datetime(2015,11,15), 'adate': datetime(2015,11,15,9,5)})
        
        self.assertFalse(p.parse("number < 9"))
        self.assertTrue(p.parse("number < 200"))
        self.assertTrue(p.parse("date < 2015-12-01"))
        self.assertTrue(p.parse("date < 2015-12-1"))
        self.assertFalse(p.parse("date < 2015-1-1"))
        self.assertTrue(p.parse("adate < 2015-11-15 9:10"))
        self.assertFalse(p.parse("adate < 2015-11-15 9:01"))
        
        self.assertTrue(p.parse("number < 200 & adate < 2015-11-15 9:10"))
        
    def test_9(self):
        p=SimpleEvaluator({"number":100, 'date':datetime(2015,11,15), 'adate': datetime(2015,11,15,9,5)})
        self.assertFalse(p.parse("adate < 2015-11-15 8:10"))
        self.assertFalse(p.parse("adate < 2015-11-15 8:10 & number < 200  "))
        
        self.assertTrue(p.parse("number = 100"))
        self.assertTrue(p.parse("date = 2015-11-15"))
        self.assertTrue(p.parse("adate = 2015-11-15 09:05"))
        
        self.assertFalse(p.parse("date = 2015-11-15 01:59"))
        self.assertFalse(p.parse("adate = 2015-11-15 09:06"))
        
    def test_10(self):
        p=SimpleEvaluator({"number":100, 'date':datetime(2015,11,15), 'adate': datetime(2015,11,15,9,5)})
        
        self.assertFalse(p.parse("number <= 9"))
        self.assertTrue(p.parse("number <= 100"))
        self.assertTrue(p.parse("number <= 200"))
        
        self.assertTrue(p.parse("number > 9"))
        self.assertFalse(p.parse("number > 200"))
        
        self.assertTrue(p.parse("number >= 9"))
        self.assertTrue(p.parse("number >= 100"))
        self.assertFalse(p.parse("number >= 200"))
        
        self.assertFalse(p.parse("date >= 2015-11-15 01:59"))
        self.assertTrue(p.parse("date <= 2015-11-15 01:59"))
        
    def test_11(self):
        p=SimpleEvaluator({"text":"start lorem ipsum neco end"})
        self.assertFalse(p.parse('text ^= "end"'))
        self.assertTrue(p.parse('text ^= "start"'))
        
        self.assertTrue(p.parse('text ^= "START"'))
        
        self.assertTrue(p.parse('text ~= "IPSUM"'))
        
        self.assertTrue(p.parse('text $= "end"'))
        self.assertFalse(p.parse('text $= "start"'))
        
    def test_12(self):
        
        p=SimpleEvaluator({"small":100, 'large':1024*1024*10, 'kilo':1024, 'mega':1024*1024, 'giga':1024*1024*1024})
        
        self.assertTrue(p.parse('small < 1k'))
        self.assertFalse(p.parse('small > 1k'))
        
        self.assertTrue(p.parse('large > 9M'))
        
        self.assertTrue(p.parse('kilo=1k & mega=1M & giga=1G'))
        
            
        
    def test_json(self):
        res=parsimonious.Grammar(JSON).parse('{"x":1, "y":[0,1,2]}')
        
        