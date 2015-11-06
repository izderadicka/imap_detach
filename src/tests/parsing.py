import unittest as unit
import parsimonious

GRAMMAR=r""" # Test grammar
expr = or
or = and  ( space "|" space and )*
and = value  ( space "&" space value )*
value = not / contains  / bracketed
not = "!" space expr
bracketed = "(" space expr space ")"
contains  =  name space "="  space literal
name       = ~"\w+"
literal    = "\"" chars "\""
space    = " "*
chars = ~"[^\"]*"

"""

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

class SimpleEvaluator(parsimonious.NodeVisitor):
    def __init__(self, grammar, ctx):
        self.grammar=parsimonious.Grammar(grammar)
        self._ctx=ctx
        
    def visit_name(self, node, chidren):
        return self._ctx.get(node.text, '')
    
    def visit_literal(self,node, children):
        return children[1]
        
    def visit_chars(self, node, children):
        return node.text
    
    def visit_contains(self, node, children):
        return children[0].find(children[-1]) > -1
   
    def visit_expr(self, node, children):
        return children[1]
    
    def visit_or(self, node, children):
        #print( 'OR', node.text, children)
        return any(filter(lambda x: not x is None, children))
    
    def visit_and(self, node, children):
        #print( 'AND', node.text, children)
        return all(filter(lambda x: not x is None, children))
        
    def visit_not(self, node, children):
        return not children[-1]
    
    def visit_bracketed(self, node, children):
        return children[2]
    
    def generic_visit(self, node, children):
        #print ('GENERIC', node.text, children)
        if children:
            return children[-1]

class Test(unit.TestCase):
    
    def setUp(self):
        pass
        
    def test_1(self):
        p=SimpleEvaluator(GRAMMAR, {'a':'b'})
        res = p.parse('a="b"')
        self.assertTrue(res)
        res= p.parse('c="b"')
        self.assertFalse(res)
        
    def test_2(self):
        p=SimpleEvaluator(GRAMMAR, {'a':'1', 'b':'2', 'dummy':'dummy test'})
        self.assertTrue(p.parse('(a="1")'))
        self.assertTrue(p.parse('!(! a="1")'))
        self.assertTrue(p.parse('!! a="1"'))
        self.assertTrue(p.parse('a="1" & b="2"'))
        
    def test_3(self):
        p=SimpleEvaluator(GRAMMAR, {'a':'1', 'b':'2', 'dummy':'dummy test'})
        self.assertFalse(p.parse('a="1" & b="3"'))
        self.assertTrue(p.parse('a="2" | b="2"'))
        self.assertTrue(p.parse('a="1" & b="2" & dummy="test"'))
        
    def test_4(self):
        p=SimpleEvaluator(GRAMMAR, {'a':'1', 'b':'2', 'dummy':'dummy test'})
        self.assertTrue(p.parse('(a="1" | d="3") & (a="2" | b="2")'))
        self.assertFalse(p.parse('(a="1" | d="3") & !(a="2" | b="2")'))
        self.assertTrue(p.parse('(a = "1" | (! d="3")) & (a = "2" | b="2")'))
        self.assertFalse(p.parse('a="2" | b="2" & dummy="xxx"' ))
        self.assertTrue(p.parse('a="2" | b="2" & dummy="test"' ))
        self.assertTrue(p.parse('a="1" | b="2" & dummy="xxx" | c="x"' ))
        self.assertTrue(p.parse('a="1" | ( b="2" & dummy="xxx"  )| c="x"' ))
        self.assertFalse(p.parse('(a="1" | b="2") & dummy="xxx" | c="x"' ))
        self.assertTrue(p.parse('a="1" | b="2" & ( dummy="xxx" | c="x" )' ))
        self.assertTrue(p.parse('a="1" | b="3" & dummy="xxx" | c="x"' ))
        self.assertFalse(p.parse('( a="1" | b="3" ) & dummy="xxx" | c="x"' ))
        
    def test_errors(self):
        p=SimpleEvaluator(GRAMMAR, {'a':'1', 'b':'2', 'dummy':'dummy test'})
        try:
            self.assertTrue(p.parse('(a="2" | b="x" & dummy="test' ))
            self.fail('Should rise parse exception')
        except parsimonious.ParseError as e:
            print(e)
        
        
    def test_json(self):
        res=parsimonious.Grammar(JSON).parse('{"x":1, "y":[0,1,2]}')
        
        