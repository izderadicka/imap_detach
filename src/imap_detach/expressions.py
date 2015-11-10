import parsimonious
import six
from imap_detach.utils import decode

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
name       = ~"\w+"
literal    = "\"" chars "\""
space    = " "*
chars = ~"[^\"]*"

"""

def grammar():
    return parsimonious.Grammar(GRAMMAR)

class EvalError(Exception):
    def __init__(self, text, pos=0):
        super(EvalError, self).__init__(text+ ' at position %d'%pos)
        
        
# class Var(object):
#     def __init__(self, name):
#         self.name=name
#     def eq(self, var1, var2):
#         return var1 == var2
#     def bool(self,v):
#         return bool(v)
#         
# class StrVar (Var):
#     def contains (self, val1, val2):
#         if not isinstance(val1, (six.binary_type, six.string_types)) or \
#            not isinstance(val2, (six.binary_type, six.string_types)):
#             raise EvalError('Contains operation is valid only for string like types')
#         val1=decode(val1).lower()
#         val2=val2.decode(val2).lower()
#         return val1.find(val2)
#     
# class ImapVar(object):
#     def imap_name(self):
#         return self.name.upper()
#         
# class ImapEq(ImapVar):
#     def eq(self, val1, val2):
#         return '(%s "%s")' % (self.imap_name(val1), val2)
#     
# class ImapStr(ImapEq):
#     def contains(self, val1, val2):
#         return '(%s "%s")' % (self.imap_name(val1), val2)
#     
# class ImapBool(ImapVar):
#     def bool(self,v):
#         return self.imap_name()


class SimpleEvaluator(parsimonious.NodeVisitor):
    def __init__(self, ctx, strict=True):
        self.grammar=grammar()
        self._ctx=ctx
        self._strict=strict
        
    def visit_name(self, node, chidren):
        if node.text in self._ctx :
            return self._ctx[node.text]
        elif self._strict:
            raise EvalError('Unknown variable %s'%node.text, node.start)
        else:
            return ''
    
    def visit_literal(self,node, children):
        return children[1]
        
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
        a=decode(children[0]).lower()
        b=decode(children[-1]).lower()
        return a.find(b) > -1
    
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
