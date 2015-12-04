import parsimonious
from imap_detach.expressions import EvalError, grammar
from six.moves import reduce  # @UnresolvedImport
from imap_detach.utils import to_datetime, to_imap_date, to_int
from datetime import datetime, date
import six
from copy import copy

class StringLiteral(six.text_type):
    pass

class BoolVar(str):
    pass

class NotIMAP(str):
    pass

class SpecialVar(str):
    pass


class TextVar(SpecialVar):
    def equals(self,  val):
        return ['TEXT', StringLiteral(str(val))]
    
    contains=equals
    starts=equals
    ends=equals

class YearVar(SpecialVar):
    def isyear(fn):  # @NoSelf
        def _inner(self, val):
            if not isinstance(val, int):
                raise ValueError('val should be int')
            if val < 1900 or val > 10000:
                raise ValueError('val is out of range for year')
            return fn(self, val)
        return _inner
    
    @isyear
    def equals(self, val):
        return ('SINCE', '1-Jan-%d' %val, 'BEFORE',  '1-Jan-%d' % (val+1) )
    
    @isyear
    def smaller(self, val):
        return ['BEFORE', '1-Jan-%d' % val]
    
    @isyear
    def smaller_equal(self, val):
        return ['BEFORE', '1-Jan-%d' % (val+1)]
    
    @isyear
    def bigger(self,val):
        return ['SINCE', '1-Jan-%d' % (val+1)]
    
    @isyear
    def bigger_equal(self,val):
        return ['SINCE',  '1-Jan-%d' % val]

class DateVar(SpecialVar):
    
    def isdate(fn):  # @NoSelf
        def _inner(self, val):
            if not isinstance(val, (datetime,date)):
                raise ValueError('val should be datetime or date')
            return fn(self, val)
        return _inner
    
    @isdate        
    def equals(self,val):
        
        return ["ON", "%s" % to_imap_date(val)]
    
    @isdate
    def smaller(self,val):
        d=to_imap_date(val)
        return ["BEFORE", d]
    
    @isdate
    def smaller_equal(self,val):
        d=to_imap_date(val)
        return ("OR", "BEFORE",d, "ON",d)
    
    @isdate
    def bigger(self,val):
        d=to_imap_date(val)
        return ("OR", "SINCE", d,  "NOT", ( "ON",d))
    
    @isdate
    def bigger_equal(self,val):
        d=to_imap_date(val)
        return ["SINCE", d]
    
class SizeVar(SpecialVar):
    
    def bigger(self,val):
        if not isinstance(val, int):
            raise ValueError('Need integer value')
        return ['LARGER',  '%d' % val]
    
    bigger_equal=bigger
    
class FlagsVar(SpecialVar):
    def equals(self,val):
        if not isinstance(val, six.string_types):
            raise ValueError('Need string value')
        return ['KEYWORD', val]

NOT_IMAP=NotIMAP('')

class IMAPFilterGenerator(parsimonious.NodeVisitor):
    VARS={'from': 'FROM',
          'to': 'TO',
          'cc': 'CC',
          'bcc': 'BCC',
          'subject': 'SUBJECT',
          'seen': BoolVar('SEEN'),
          'answered' : BoolVar('ANSWERED'),
          'flagged': BoolVar("FLAGGED"),
          'deleted': BoolVar('DELETED'),
          'draft' : BoolVar('DRAFT'),
          'recent' : BoolVar('RECENT'),
          'date' : DateVar(),
          'size' : SizeVar(),
          'year' : YearVar()
          }
    EXT_VARS={'flags': FlagsVar(),
              'mime': TextVar(),
              'name': TextVar()
              }
    
    def __init__(self, unsafe=False):
        self.grammar=grammar()
        self._vars=copy(IMAPFilterGenerator.VARS)
        if unsafe:
            self._vars.update(IMAPFilterGenerator.EXT_VARS)
        
    def visit_name(self, node, chidren):
        return self._vars.get(node.text, NOT_IMAP)
    
    def visit_literal(self,node, children):
        return StringLiteral(children[1])
    
    def visit_number(self, node, children):
        return to_int(node.text)
    
    def visit_date(self,node, children):
        return to_datetime(node.text)
        
    def visit_chars(self, node, children):
        return node.text
    
    def binary(fn):  # @NoSelf
        def _inner(self, node, children):
            var=children[0]
            op=fn.__name__.split('_',1)[1]
            if isinstance (children[0], BoolVar):
                raise EvalError('Variable is boolean, should not be used here %s'% node.text, node.start)
            elif isinstance(children[0], NotIMAP):
                return NOT_IMAP
            elif isinstance(var, SpecialVar):
                if hasattr(var, op):
                    m=getattr(var, op)
                    return m(children[-1])
                else:
                    return NOT_IMAP
            return fn(self, node, children)
        return _inner
            
    @binary   
    def visit_equals(self, node, children): 
        return [children[0], children[-1]]
    
    @binary
    def visit_contains (self, node, children): 
        return [children[0], children[-1]]
    
    @binary
    def visit_starts (self, node, children): 
        return [children[0], children[-1]]
    
    @binary
    def visit_ends(self, node, children): 
        return [children[0], children[-1]]
   
    def visit_expr(self, node, children):
        return children[1]
    
    @binary
    def visit_smaller(self, node, children):
        return NOT_IMAP
    
    @binary
    def visit_smaller_equal(self, node, children):
        return NOT_IMAP
    
    @binary
    def visit_bigger(self, node, children):
        return NOT_IMAP
    
    @binary
    def visit_bigger_equal(self, node, children):
        return NOT_IMAP
  
    def visit_or(self, node, children):
        if any(map(lambda x:isinstance(x, NotIMAP), children)):
            return NOT_IMAP
        if not children[1]:
            return children[0]
            
        return tuple([ 'OR'] +children)
    
    def visit_and(self, node, children):
        if not children[1]:
            return children[0]
        remains= list(filter(lambda x: x and not isinstance(x, NotIMAP), children))
        if len(remains)>1:
            return tuple(remains)
        else:
            return remains[0]
    
    def visit_more_and(self, node, children):
        return list(filter(lambda x: not isinstance(x, NotIMAP), children))
        
    def visit_not(self, node, children):
        if isinstance(children[-1], NotIMAP):
            return NOT_IMAP
        return ('NOT',  children[-1])
    
    def visit_more_or(self, node, children):
        if not children:
            return []
        if any(map(lambda x: isinstance(x, NotIMAP),children)):
            return NOT_IMAP
        return reduce(lambda a,b: ('OR', a, b), children)
    
    def visit_bracketed(self, node, children):
        return (children[2],)
    
    def generic_visit(self, node, children):
        #print ('GENERIC', node.text, children)
        if children:
            return children[-1]
        
    def parse(self, text, pos=0, serialize='string'):
        r= parsimonious.NodeVisitor.parse(self, text, pos=pos)
        if not serialize:
            return r
        elif serialize == 'string':
            return string_serializer(r)
        elif serialize == 'list':
            return list_serializer(r)
        
        raise ValueError('Invalid Serialization')
    
def string_serializer(t):
    if isinstance(t,tuple):
        l=list(filter(lambda x:x,[string_serializer(x) for x in t ]))
        return '(%s)' % ' '.join(l) if l else ''
    elif isinstance(t, list):
        l=list(filter(lambda x:x,[string_serializer(x) for x in t ]))
        return ' '.join(l)
    elif isinstance(t, StringLiteral):
        return '"%s"' % t
    elif isinstance(t, NotIMAP):
        return ''
    else:
        return str(t)
    
def list_serializer(t):
    ret=[]
    def walk(t):
        if isinstance(t,tuple):
            ret.append ('(')
            x=[walk(x) for x in t ]
            if ret[-1]=='(':
                ret.pop()
            else:
                ret.append(')')
        elif isinstance(t, list):
            [walk(x) for x in t ]
        elif isinstance(t, StringLiteral):
            ret.append(t)
        elif isinstance(t, NotIMAP):
            pass
        else:
            ret.append( str(t))
    walk(t)
    return ret

