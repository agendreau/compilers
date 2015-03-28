from compiler.ast import *
from explicateNodes import *

INT = 0
BOOL = 1
BIG = 3

class explicateVisitor():
    def __init__(self):
        self.node = None
        self._cache = {}
        self.numtemp = 0
        
        
    def default(self, node):
        return node
            
    def walk(self, node):
        self.node = node
        return self.visitModule(node)
    
    
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
        return Module(node.doc,self.dispatch(node.node))
    
    def visitStmt(self,node):
        nodelist = []
        for n in node.nodes:
            nodelist.append(self.dispatch(n))
        return Stmt(nodelist)
    
    def visitPrintnl(self,node):
        nodelist=[]
        for n in node.nodes:
            nodelist.append(self.dispatch(n))
        return Printnl(nodelist,node.dest)
        
    def visitAssign(self,node):
        nodelist=[]
        for n in node.nodes:
            nodelist.append(self.dispatch(n))
        return Assign(nodelist,self.dispatch(node.expr))
    
    def visitAssName(self,node):
        return node
    
    def visitDiscard(self,node):
        return Discard(self.dispatch(node.expr))
    
    def visitConst(self,node):
        if node.value == 'True' or node.value=='False':
            return InjectFrom('BOOL',node)
        return InjectFrom('INT', node)
    
    def visitName(self,node):
        if node.name == 'True' or node.name == 'False':
            return InjectFrom('BOOL',Const(node.name))
        return node
        
    def visitUnarySub(self,node):
        return InjectFrom('INT', UnarySub(ProjectTo('INT',self.dispatch(node.expr))))
        
    def visitCallFunc(self, node):
        nodelist=[]
        for n in node.args:
            nodelist.append(self.dispatch(n))
        if node.node.name == 'input':
            return InjectFrom('INT',CallFunc(self.dispatch(node.node),nodelist))
        return CallFunc(self.dispatch(node.node),nodelist)
        
    def visitAdd(self, node):
        letcount = 0
        
        lftexp = self.dispatch(node.left)
        if not (isinstance(node.left, Name) or isinstance(node.left, Const)):
            lft = Name('$addtemp'+str(self.numtemp))
            self.numtemp = self.numtemp + 1
            letcount = letcount + 1
        else:
            lft = lftexp
        
        rgtexp = self.dispatch(node.right)
        if not (isinstance(node.right, Name) or isinstance(node.right, Const)):
            rgt = Name('$addtemp'+str(self.numtemp))
            self.numtemp = self.numtemp + 1
            letcount = letcount + 1
        else:
            rgt = rgtexp
        
        ifexpr = IfExp(Compare(GetTag(lft),[('==', Const(INT))]), InjectFrom('INT', AddInt((ProjectTo('INT',lft),ProjectTo('INT',rgt)))),
                        IfExp(Compare(GetTag(lft),[('==', Const(BOOL))]),
                        InjectFrom('INT', AddInt((ProjectTo('BOOL',lft),ProjectTo('BOOL',rgt)))),
                        InjectFrom('BIG', CallFunc(Name('add'),[ProjectTo('BIG',lft),ProjectTo('BIG',rgt)]))))
        
        if letcount == 1:
            if lft==lftexp:
                return Let(rgt,rgtexp,ifexpr)
            else:
                return Let(lft,lftexp,ifexpr)
        elif letcount == 2:
            return Let(lft,lftexp,Let(rgt,rgtexp,ifexpr))
        return ifexpr
    
    def visitList(self, node):
        nodelist=[]
        for n in node.nodes:
            nodelist.append(self.dispatch(n))
        if len(nodelist)==0:
            nodelist=node.nodes
    #return InjectFrom('BIG',List(nodelist))
        return List(nodelist)
    
    def visitDict(self, node):
        nodelist=[]
        for n in node.items:
            nodelist.append((self.dispatch(n[0]),self.dispatch(n[1])))
        if len(nodelist)==0:
            nodelist=node.items
        return Dict(nodelist)
        
    def visitOr(self,node):
        letcount = 0
        lftexp = self.dispatch(node.nodes[0])
        if not (isinstance(node.nodes[0], Name) or isinstance(node.nodes[0], Const)):
            lft = Name('$addtemp'+str(self.numtemp))
            self.numtemp = self.numtemp + 1
            letcount = letcount + 1
        else:
            lft = lftexp
        
        rgtexp = self.dispatch(node.nodes[1])
        if not (isinstance(node.nodes[1], Name) or isinstance(node.nodes[1], Const)):
            rgt = Name('$addtemp'+str(self.numtemp))
            self.numtemp = self.numtemp + 1
            letcount = letcount + 1
        else:
            rgt = rgtexp
        
        orexpr = IfExp(CallFunc(Name('is_true'),[lft]),lft,rgt)
        if letcount == 1:
            if lft==lftexp:
                return Let(rgt,rgtexp,orexpr)
            else:
                return Let(lft,lftexp,orexpr)
        elif letcount == 2:
            return Let(lft,lftexp,Let(rgt,rgtexp,orexpr))
        return orexpr
    
    def visitAnd(self,node):
        letcount = 0
        lftexp = self.dispatch(node.nodes[0])
        if not (isinstance(node.nodes[0], Name) or isinstance(node.nodes[0], Const)):
            lft = Name('$addtemp'+str(self.numtemp))
            self.numtemp = self.numtemp + 1
            letcount = letcount + 1
        else:
            lft = lftexp
        
        rgtexp = self.dispatch(node.nodes[1])
        if not (isinstance(node.nodes[1], Name) or isinstance(node.nodes[1], Const)):
            rgt = Name('$addtemp'+str(self.numtemp))
            self.numtemp = self.numtemp + 1
            letcount = letcount + 1
        else:
            rgt = rgtexp
        
        andexpr = IfExp(CallFunc(Name('is_true'),[lft]),rgt,lft)
        if letcount == 1:
            if lft==lftexp:
                return Let(rgt,rgtexp,andexpr)
            else:
                return Let(lft,lftexp,andexpr)
        elif letcount == 2:
            return Let(lft,lftexp,Let(rgt,rgtexp,andexpr))
        return andexpr
    
    def visitNot(self,node):
        return IfExp(CallFunc(Name('is_true'),[self.dispatch(node.expr)]), InjectFrom('BOOL', Const('False')),InjectFrom('BOOL', Const('True')))
    
    def visitIfExp(self,node):
        letcount = 0
        test = self.dispatch(node.test)
        then = self.dispatch(node.then)
        else_= self.dispatch(node.else_)
        if not (isinstance(test,Name) or isinstance(test, Const)):
            tst = Name('$addtemp'+str(self.numtemp))
            self.numtemp = self.numtemp + 1
            letcount = letcount + 1
        else:
            tst = test
        ifexpr = IfExp(Compare(GetTag(tst),[('==', Const(BOOL))]),IfExp(ProjectTo('BOOL',tst),then,else_),IfExp(Compare(GetTag(tst),[('==', Const(INT))]),IfExp(ProjectTo('INT',tst),then,else_),IfExp(CallFunc(Name('is_true'),[tst]),then,else_)))
                    
                       
        if letcount == 1:
            return Let(tst,test,ifexpr)
        return ifexpr
    
    def visitCompare(self,node):
        lftexp = self.dispatch(node.expr)
        op = node.ops[0][0]
        rgtexp = self.dispatch(node.ops[0][1])
        
        letcount = 0
        if not (isinstance(node.expr, Name) or isinstance(node.expr, Const)):
            lft = Name('$addtemp'+str(self.numtemp))
            self.numtemp = self.numtemp + 1
            letcount = letcount + 1
        else:
            lft = lftexp
        
        if not (isinstance(node.ops[0][1], Name) or isinstance(node.ops[0][1], Const)):
            rgt = Name('$addtemp'+str(self.numtemp))
            self.numtemp = self.numtemp + 1
            letcount = letcount + 1
        else:
            rgt = rgtexp
            
        if op == 'is':
            thenint = IfExp(Compare(GetTag(rgt),[('==',Const(INT))]),
                    InjectFrom('BOOL',Compare(ProjectTo('INT',lft),[('==',ProjectTo('INT',rgt))])),
                    InjectFrom('BOOL', Const('False')))
            
            elseint = IfExp(Compare(GetTag(lft),[('==',Const(BOOL))]),
                    IfExp(Compare(GetTag(rgt),[('==',Const(BOOL))]),
                        InjectFrom('BOOL',Compare(ProjectTo('BOOL',lft),[('==',ProjectTo('BOOL',rgt))])),
                        InjectFrom('BOOL', Const('False'))),
                    IfExp(Compare(GetTag(rgt),[('==',Const(BIG))]),
                        InjectFrom('BOOL', Compare(ProjectTo('INT',ProjectTo('BIG',lft)),[('==',ProjectTo('INT',ProjectTo('BIG',rgt)))])),
                        InjectFrom('BOOL', Const('False'))))
            comp = IfExp(Compare(GetTag(lft),[('==',Const(INT))]),thenint,elseint)
            #comp = InjectFrom('BOOL', Compare(lft,[('is',rgt)]))
        elif op == '==':
            comp = IfExp(Compare(GetTag(lft),[('==',Const(INT))]),IfExp(Compare(GetTag(rgt),[('==',Const(INT))]),
                                                                        InjectFrom('BOOL',Compare(ProjectTo('INT',lft),[(op,ProjectTo('INT',rgt))])),
                                                                        InjectFrom('BOOL',Compare(ProjectTo('INT',lft),[(op,ProjectTo('BOOL',rgt))]))),
                            IfExp(Compare(GetTag(lft),[('==',Const(BOOL))]),
                                        IfExp(Compare(GetTag(rgt),[('==',Const(INT))]),
                                            InjectFrom('BOOL',Compare(ProjectTo('BOOL',lft),[(op,ProjectTo('INT',rgt))])),
                                            InjectFrom('BOOL',Compare(ProjectTo('BOOL',lft),[(op,ProjectTo('BOOL',rgt))]))),
                                        InjectFrom('BOOL',CallFunc(Name('equal'),[ProjectTo('BIG',lft),ProjectTo('BIG',rgt)]))))
            """comp = IfExp(Compare(GetTag(lft),[('==',Const(INT))]),InjectFrom('BOOL',Compare(lft,[(op,rgt)])),
                        IfExp(Compare(GetTag(lft),[('==',Const(BOOL))]),InjectFrom('BOOL',Compare(lft,[(op,rgt)])),
                                                                    InjectFrom('BOOL',CallFunc(Name('equal'),[ProjectTo('BIG',lft),ProjectTo('BIG',rgt)]))))"""
        elif op == '!=':
            comp = IfExp(Compare(GetTag(lft),[('==',Const(INT))]),IfExp(Compare(GetTag(rgt),[('==',Const(INT))]),
                                                                        InjectFrom('BOOL',Compare(ProjectTo('INT',lft),[(op,ProjectTo('INT',rgt))])),
                                                                        InjectFrom('BOOL',Compare(ProjectTo('INT',lft),[(op,ProjectTo('BOOL',rgt))]))),
                            IfExp(Compare(GetTag(lft),[('==',Const(BOOL))]),
                                        IfExp(Compare(GetTag(rgt),[('==',Const(INT))]),
                                            InjectFrom('BOOL',Compare(ProjectTo('BOOL',lft),[(op,ProjectTo('INT',rgt))])),
                                            InjectFrom('BOOL',Compare(ProjectTo('BOOL',lft),[(op,ProjectTo('BOOL',rgt))]))),
                                        InjectFrom('BOOL',CallFunc(Name('not_equal'),[ProjectTo('BIG',lft),ProjectTo('BIG',rgt)]))))
        
        if letcount == 1:
            if lft==lftexp:
                return Let(rgt,rgtexp,comp)
            else:
                return Let(lft,lftexp,comp)
        elif letcount == 2:
            return Let(lft,lftexp,Let(rgt,rgtexp,comp))
        return comp
    
    def visitSubscript(self,node):
        nodelist = []
        for n in node.subs:
            nodelist.append(self.dispatch(n))
        if len(nodelist)==0:
            nodelist=node.subs
        return Subscript(self.dispatch(node.expr),'OP_ASSIGN',nodelist)
