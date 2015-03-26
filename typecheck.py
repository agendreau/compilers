from compiler.ast import *
from explicateNodes import *

INT = 0
BOOL = 1
BIG = 3
PYOBJ = 4
ERROR = 5

class typecheckVisitor():
    def __init__(self):
        self.node = None
        self._cache = {}
        self.env = {}
        
    def default(self, node):
        return True,node
            
    def walk(self, node):
        self.node = node
        self.visitModule(node)
    
    
    def dispatch(self, node):
        if node is None:
            return None
        klass = node.__class__
        meth = self._cache.get(klass, None)
        if meth is None:
            className = klass.__name__
            meth = getattr(self, 'visit' + className, self.default)
            self._cache[klass] = meth
        return meth(node)
    
    def visitModule(self,node):
        self.dispatch(node.node)
    
    def visitStmt(self,node):
        for n in node.nodes:
            self.dispatch(n)
        return None
    
    def visitPrintnl(self,node):
        for n in node.nodes:
            self.dispatch(n)
        return None
        
    def visitAssign(self,node):
        rgttype = self.dispatch(node.expr)
        for n in node.nodes:
            if isinstance(n,Subscript):
                self.env[n.expr.name] =rgttype    
            else:
                self.env[n.name] =rgttype
        return None
    
    def visitAssName(self,node):
        return None
    
    def visitDiscard(self,node):
        self.dispatch(node.expr)
        return None
    
    def visitConst(self,node):
        if node.value == 'True' or node.value=='False':
            return BOOL
        return INT
    
    def visitName(self,node):
        if node.name == 'False' or node.name == 'True':
            return BOOL
        t = self.env[node.name]
        return t
        
    def visitUnarySub(self,node):
        valtype = self.dispatch(node.expr)
        if valtype==INT:
            return INT
        print "Error in Usub, expected type: INT , Found:",valtype
        return INT
        
    def visitCallFunc(self, node):
        if node.node.name=='add':
            for n in node.args:
                valtype = self.dispatch(n)
                if  valtype != BIG:
                    print "Error in CallFunc, expected type: BIG , Found:",valtype
            return BIG
        elif node.node.name =='equal':
            for n in node.args:
                valtype = self.dispatch(n)
                if  valtype != BIG:
                    print "Error in CallFunc, expected type: BIG , Found:",valtype
            return BOOL
        elif node.node.name =='not_equal':
            for n in node.args:
                valtype = self.dispatch(n)
                if  valtype != BIG:
                    print "Error in CallFunc, expected type: BIG , Found:",valtype
            return BOOL
        elif node.node.name =='input':
            return INT
        elif node.node.name == '$error':
            return ERROR
        elif node.node.name == 'is_true':
            return BOOL
        return None
        
    def visitAddint(self, node):
        lft = self.dispatch(node.left)
        rgt = self.dispatch(node.right)
        if lft == rgt == INT:
            return INT
        else:
            print "Error in AddInt, expected type: (INT,INT) , Found:", (lgt,rgt)
        return None
    
    def visitList(self, node):
        return BIG
    
    def visitDict(self, node):
        return BIG
        
    def visitOr(self,node):
        for n in node.nodes:
            self.dispatch(n)
        return PYOBJ
    
    def visitAnd(self,node):
        for n in node.nodes:
            self.dispatch(n)
        return PYOBJ
    
    def visitNot(self,node):
        self.dispatch(node.expr)
        return BOOL
    
    def visitIfExp(self,node):
        testtype = self.dispatch(node.test)
        thentype = self.dispatch(node.then)
        elsetype = self.dispatch(node.else_)
        if (testtype == BOOL) and thentype == elsetype:
            return elsetype
        elif elsetype == ERROR:
            return thentype
        else:
            print "Error in IfExp, expected type: (BOOL,X,X) , Found:", (testtype,thentype,elsetype)
        return thentype
    
    def visitCompare(self,node):
        e1 = self.dispatch(node.expr)
        e2 = self.dispatch(node.ops[0][1])
        if ((e1==BOOL) or (e1==INT)) and ((e2==BOOL) or (e2==INT)):
            return BOOL
        else:
            print "Error in Compare, expected type: (e1= BOOL/INT, e2= BOOL/INT) , Found:", (e1,e2)
            print node
        return BOOL
        
    def visitSubscript(self,node):
        e1 = self.dispatch(node.expr)
        e2 = self.dispatch(node.subs[0])
        if e1==e2==PYOBJ:
            return PYOBJ
        else:
            print "Error in Compare, expected type: (PYOBJ,PYOBJ) , Found:", (e1,e2)
        return PYOBJ
    
    def visitInjectFrom(self,node):
        if node.typ == 'INT':
            typeval = self.dispatch(node.arg)
            if typeval == INT:
                return PYOBJ
            else:
                print node
                print "Error in InjectFrom, expected type: INT, Found:", typeval
        elif node.typ == 'BOOL':
            typeval = self.dispatch(node.arg)
            if typeval == BOOL:
                return PYOBJ
            else:
                print node.arg
                print "Error in InjectFrom, expected type: BOOL, Found:", typeval
        elif node.typ == 'BIG':
            typeval = self.dispatch(node.arg)
            if typeval == BIG:
                return PYOBJ
            else:
                print node
                print "Error in InjectFrom, expected type: BIG, Found:", typeval
        return PYOBJ
    
    def visitProjectTo(self,node):
        typeval = self.dispatch(node.arg)
        if typeval != PYOBJ:
            print "Error in ProjectTo, expected type: PYOBJ, Found:", typeval, "\n"
            print node
        if node.typ == 'INT':
            return INT
        elif node.typ == 'BOOL':
            return BOOL
        elif node.typ == 'BIG':
            return BIG
        return node.typ
    
    def visitGetTag(self,node):
        typeval = self.dispatch(node.arg)
        if typeval != PYOBJ:
            print "Error in GetTag, expected type: PYOBJ, Found:", typeval
        return INT
    
    def visitLet(self,node):
        e1 = self.dispatch(node.rhs)
        self.env[node.var.name] = e1
        e2 = self.dispatch(node.body)
        return e2
    
    def visitAddInt(self,node):
        e1 = self.dispatch(node.left)
        e2 = self.dispatch(node.right)
        if e1 == e2 == INT:
            return INT
        else:
            print "Error in AddInt, expected type: (INT,INT), Found:",(e1,e2) 
        return INT
