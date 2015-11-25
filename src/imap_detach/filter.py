import parsimonious
from imap_detach.expressions import EvalError, grammar
from six.moves import reduce  # @UnresolvedImport
from imap_detach.utils import to_datetime, to_imap_date, to_int
from datetime import datetime, date
import six


class BoolVar(str):
    pass

class NotIMAP(str):
    pass

class SpecialVar(str):
    pass

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
        return '(SINCE 1-Jan-%d BEFORE 1-Jan-%d)' % (val, val+1)
    
    @isyear
    def smaller(self, val):
        return 'BEFORE 1-Jan-%d' % val
    
    @isyear
    def smaller_equal(self, val):
        return 'BEFORE 1-Jan-%d' % (val+1)
    
    @isyear
    def bigger(self,val):
        return 'SINCE 1-Jan-%d' % (val+1)
    
    @isyear
    def bigger_equal(self,val):
        return 'SINCE 1-Jan-%d' % val

class DateVar(SpecialVar):
    
    def isdate(fn):  # @NoSelf
        def _inner(self, val):
            if not isinstance(val, (datetime,date)):
                raise ValueError('val should be datetime or date')
            return fn(self, val)
        return _inner
    
    @isdate        
    def equals(self,val):
        
        return "ON %s" % to_imap_date(val)
    
    @isdate
    def smaller(self,val):
        d=to_imap_date(val)
        return "BEFORE %s" % d
    
    @isdate
    def smaller_equal(self,val):
        d=to_imap_date(val)
        return "(OR BEFORE %s ON %s)" % (d,d)
    
    @isdate
    def bigger(self,val):
        d=to_imap_date(val)
        return "(OR SINCE %s NOT (ON %s))" % (d,d)
    
    @isdate
    def bigger_equal(self,val):
        d=to_imap_date(val)
        return "SINCE %s" % d
    
class SizeVar(SpecialVar):
    
    def bigger(self,val):
        if not isinstance(val, int):
            raise ValueError('Need integer value')
        return 'LARGER %d' % val
    
    bigger_equal=bigger
    
class FlagsVar(SpecialVar):
    def equals(self,val):
        if not isinstance(val, six.string_types):
            raise ValueError('Need string value')
        return 'KEYWORD %s' % val

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
              }
    
    def __init__(self, unsafe=False):
        self.grammar=grammar()
        self._vars=IMAPFilterGenerator.VARS
        if unsafe:
            self._vars.update(IMAPFilterGenerator.EXT_VARS)
        
    def visit_name(self, node, chidren):
        return self._vars.get(node.text, NOT_IMAP)
    
    def visit_literal(self,node, children):
        return '"%s"'%children[1]
    
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
        return '%s %s' % (children[0], children[-1])
    
    @binary
    def visit_contains (self, node, children): 
        return '%s %s' % (children[0], children[-1])
    
    @binary
    def visit_starts (self, node, children): 
        return '%s %s' % (children[0], children[-1])
    
    @binary
    def visit_ends(self, node, children): 
        return '%s %s' % (children[0], children[-1])
   
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
