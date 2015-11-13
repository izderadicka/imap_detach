import parsimonious
from imap_detach.expressions import EvalError, grammar
from six.moves import reduce  # @UnresolvedImport


class BoolVar(str):
    pass

class NotIMAP(str):
    pass

NOT_IMAP=NotIMAP('')

class IMAPFilterGenerator(parsimonious.NodeVisitor):
    VARS={'from': 'FROM',
          'to': 'TO',
          'cc': 'CC',
          'bcc': 'BCC',
          'subject': 'SUBJECT',
          'recent': BoolVar('RECENT'),
          'seen': BoolVar('SEEN')}
    
    def __init__(self):
        self.grammar=grammar()
        
        
    def visit_name(self, node, chidren):
        return self.VARS.get(node.text, NOT_IMAP)
    
    def visit_literal(self,node, children):
        return '"%s"'%children[1]
        
    def visit_chars(self, node, children):
        return node.text
    
    def binary(fn):  # @NoSelf
        def _inner(self, node, children):
            if isinstance (children[0], BoolVar):
                raise EvalError('Variable is boolean, should not be used here %s'% node.text, node.start)
            elif isinstance(children[0], NotIMAP):
                return NOT_IMAP
            return fn(self, node, children)
        return _inner
            
    @binary    
    def visit_contains(self, node, children):
        txt=children[-1].encode('ascii')
        return "%s %s" % (children[0], children[-1])
       
    visit_equals = visit_contains
   
    def visit_expr(self, node, children):
        return children[1]
  
    def visit_or(self, node, children):
        if any(map(lambda x:isinstance(x, NotIMAP), children)):
            return NOT_IMAP
        if not children[1]:
            return children[0]
            
        return '(OR %s)' %  ' '.join(children)
    
    def visit_and(self, node, children):
        if not children[1]:
            return children[0]
        remains= list(filter(lambda x: x and not isinstance(x, NotIMAP), children))
        if len(remains)>1:
            return '(%s)' % (' '.join (remains))
        else:
            return remains[0]
    
    def visit_more_and(self, node, children):
        return ' '.join (filter(lambda x: not isinstance(x, NotIMAP), children))
        
    def visit_not(self, node, children):
        if isinstance(children[-1], NotIMAP):
            return NOT_IMAP
        return '(NOT %s)' % children[-1]
    
    def visit_more_or(self, node, children):
        if not children:
            return ''
        if any(map(lambda x: isinstance(x, NotIMAP),children)):
            return NOT_IMAP
        return reduce(lambda a,b: '(OR %s %s)' % (a,b), children)
    
    def visit_bracketed(self, node, children):
        return '(%s)'% children[2]
    
    def generic_visit(self, node, children):
        #print ('GENERIC', node.text, children)
        if children:
            return children[-1]
