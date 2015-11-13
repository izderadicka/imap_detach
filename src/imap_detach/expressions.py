import parsimonious
import six
from imap_detach.utils import decode

ParserSyntaxError = parsimonious.ParseError
ParserEvalError = parsimonious.exceptions.VisitationError

GRAMMAR=r""" # Test grammar
expr = space or space
or = and   more_or
more_or = ( space "|" space and )*
and = term  more_and
more_and = ( space "&" space term )*
term = not / value
not = "!" space value
value =  contains  / equals / bracketed / name
bracketed = "(" space expr space ")"
contains  =  name space "~="  space literal
equals =  name space "="  space literal
# smaller =  name space "<"  space literal
name       = ~"[a-z]+"
literal    = "\"" chars "\""
# number =  ~"\d+"
space    = " "*
chars = ~"[^\"]*"

"""

def grammar():
    return parsimonious.Grammar(GRAMMAR)

class EvalError(Exception):
    def __init__(self, text, pos=0):
        super(EvalError, self).__init__(text+ ' at position %d'%pos)
        
        
def extract_err_msg(e):
    if isinstance(e, ParserEvalError):
        return e.args[0]
    
    return str(e)
        
        


class SimpleEvaluator(parsimonious.NodeVisitor):
    def __init__(self, ctx, strict=True):
        self.grammar=grammar()
        self._ctx=ctx
        self._strict=strict
    
    @property    
    def context(self):
        return self._ctx
    
    @context.setter
    def context(self, ctx):
        self._ctx = ctx
        

    
    def visit_name(self, node, chidren):
        if node.text in self._ctx :
            val=self._ctx[node.text]
            if isinstance(val, (six.string_types)+ (six.binary_type,)) :
                val = decode(val).lower()
            return val
        elif self._strict:
            raise EvalError('Unknown variable %s'%node.text, node.start)
        else:
            return ''
    
    def visit_literal(self,node, children):
        return decode(children[1]).lower()
        
    def visit_chars(self, node, children):
        return node.text
    
    def binary(fn):  # @NoSelf
        def _inner(self, node, children):
            if isinstance(children[0], bool):
                raise EvalError('Variable is boolean, should not be used here %s'% node.text, node.start)
            return fn(self, node, children)
        return _inner
    
    @binary
    def visit_contains(self, node, children):
        return children[0].find(children[-1]) > -1
    
    @binary
    def visit_equals(self, node, children):
        return children[0] == children[-1]
   
    def visit_expr(self, node, children):
        return children[1]
    
    def visit_or(self, node, children):
        return children[0] or children[1] 
    
    def visit_more_or(self,node, children):
        return any(children)
    
    def visit_and(self, node, children):
        return children[0] and (True if children[1] is None else children[1])
    
    def visit_more_and(self, node, children):
        return all(children)
        
    def visit_not(self, node, children):
        return not children[-1]
    
    def visit_bracketed(self, node, children):
        return children[2]
    
    def generic_visit(self, node, children):
        if children:
            return children[-1]
