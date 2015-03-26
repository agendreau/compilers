from compiler.ast import *

tempLabel=0
label="#tmp"
let = 0

INT = 0
BOOL = 1
BIG = 3

class GetTag(Node):
    def __init__(self,arg):
        self.arg = arg

    def getChildren(self):
        return self.arg
    
    def getChildNodes(self):
        return self.arg
    
    def __repr__(self):
        return "GetTag(%s)" % (repr(self.arg))

class InjectFrom(Node):
    def __init__(self,typ,arg):
        self.typ = typ
        self.arg = arg

    def getChildren(self):
        return self.typ, self.arg
    
    def getChildNodes(self):
        return self.typ, self.arg
    
    def __repr__(self):
        return "InjectFrom(%s, %s)" % (repr(self.typ), repr(self.arg))

class ProjectTo(Node):
    def __init__(self,typ,arg):
        self.typ = typ
        self.arg = arg

    def getChildren(self):
        return self.typ, self.arg
    
    def getChildNodes(self):
        return self.typ, self.arg
    
    def __repr__(self):
        return "ProjectTo(%s, %s)" % (repr(self.typ), repr(self.arg))

class Let(Node):
    def __init__(self,var,rhs,body):
        self.var = var
        self.rhs = rhs
        self.body = body

    def getChildren(self):
        children = []
        children.append(self.var)
        children.append(self.rhs)
        children.extend(flatten(self.body))
        return tuple(children)
    
    def getChildNodes(self):
        nodeList = []
        children.append(self.var)
        children.append(self.rhs)
        children.extend(flatten_nodes(self.body))
        return tuple(nodeList)
    
    def __repr__(self):
        return "Let(%s, %s, %s)" % (repr(self.var), repr(self.rhs),repr(self.body))

class AddInt(Node):
    def __init__(self,(left,right)):
        self.left = left
        self.right = right

    def getChildren(self):
        return self.left, self.right

    def getChildNodes(self):
        return self.left, self.right
            
    def __repr__(self):
        return "AddInteger((%s, %s))" % (repr(self.left), repr(self.right))

def explicate(astNode):
    if isinstance(astNode,Module):
        return Module(None,explicate(astNode.node))
    
    elif isinstance(astNode,Stmt):
        stmts = []
        for n in astNode.nodes:
            stmts.append(explicate_statement(n))
        
        return Stmt(stmts)

def explicate_statement(s):
    if isinstance(s,Printnl):
        toPrint = []
        for exp in s.nodes:
            toPrint.append(explicate_expression(exp))
        return Printnl(toPrint,None)
    
    elif isinstance(s,Assign):
        assignNode = s.nodes[0]
        exp = explicate_expression(s.expr)
        if isinstance(assignNode,Subscript):
            index = explicate_expression(assignNode.subs[0])
            return Assign([Subscript(assignNode.expr,assignNode.flags,[index])],exp)
        
        else:
            return Assign(s.nodes,exp)
    
    elif isinstance(s,Discard):
        return Discard(explicate_expression(s.expr))
    
    elif isinstance(s,Return):
        return Return(explicate_expression(s.value))

    elif isinstance(s,Function):
        return Assign([AssName(s.name,'OP_ASSIGN')],
                      Lambda(s.argnames,s.defaults,s.flags,
                             explicate(s.code)))

def explicate_expression(e):
    global tempLabel
    if isinstance(e,Const):
        return InjectFrom('INT',e)
    elif isinstance(e,Name):
        if e.name == 'True':
            return InjectFrom('BOOL',Const(1))
        elif e.name == 'False':
            return InjectFrom('BOOL',Const(0))
        else:
            return e

    elif isinstance(e,UnarySub):
        return InjectFrom('INT',UnarySub(ProjectTo('INT',explicate_expression(e.expr))))
    
    elif isinstance(e,CallFunc):
        nodelist= []
        for n in e.args:
            nodelist.append(explicate_expression(n))
            #if e.node.name == 'input':
            #return InjectFrom('INT',CallFunc(explicate_expression(e.node),nodelist))
            #else:
        return CallFunc(explicate_expression(e.node),nodelist)

    elif isinstance(e,Or): #assuming only one argument per side
        #or_ = []
        left = explicate_expression(e.nodes[0])
        right = explicate_expression(e.nodes[1])
        def result(l,r):
            return IfExp(Compare(GetTag(l),[('==',Const(1))]),IfExp(ProjectTo('BOOL',l),l,r),\
                         IfExp(Compare(GetTag(l),[('==', Const(0))]),IfExp(ProjectTo('BOOL',l),l,r), \
                               IfExp(CallFunc(Name('is_true'),[l]),l,r)))
        
        return letify(left,lambda l:letify(right,lambda r:result(l,r)))

    elif isinstance(e,And): #assuming only one argument per side
        #print e
        #and_ = []
        left = explicate_expression(e.nodes[0])
        right = explicate_expression(e.nodes[1])
        def result(l,r):
            return IfExp(Compare(GetTag(l),[('==',Const(1))]),IfExp(ProjectTo('BOOL',l),r,l),\
                         IfExp(Compare(GetTag(l),[('==', Const(0))]),IfExp(ProjectTo('BOOL',l),r,l), \
                               IfExp(CallFunc(Name('is_true'),[l]),r,l)))
        
        return letify(left,lambda l:letify(right,lambda r:result(l,r)))

    elif isinstance(e,Not):
        test = explicate_expression(e.expr)
        then = InjectFrom('BOOL',Const('False'))
        else_ = InjectFrom('BOOL',Const('True'))
        
        def result(guard):
            return IfExp(Compare(GetTag(guard),[('==',Const(1))]),IfExp(ProjectTo('BOOL',guard),then,else_),\
                     IfExp(Compare(GetTag(guard),[('==', Const(0))]),IfExp(ProjectTo('BOOL',guard),then,else_), \
                           IfExp(CallFunc(Name('is_true'),[guard]),then,else_)))

        return letify(test,lambda g:result(test))
        
#return IfExp(getGuard(value),Name('False'),Name('True'))

    elif isinstance(e,Subscript):
        expr = explicate_expression(e.expr)
        subs = explicate_expression(e.subs[0])
        #print Subscript(expr,'OP_APPLY',[subs])
        return Subscript(expr,'OP_APPLY',[subs])
                     

    elif isinstance(e,List):
        elements = []
        for exp in e.nodes:
            elements.append(explicate_expression(exp))
        return List(elements)

    elif isinstance(e,Dict):
        
        dict = [] #potentially supported the adding of keys?
        #print e
        for exp in e.items:
            value = explicate_expression(exp[1])
            key = explicate_expression(exp[0])
            dict.append((key,value))
        
        return Dict(dict)



    elif isinstance(e,IfExp): #ADD LETS
        test = explicate_expression(e.test)
        then = explicate_expression(e.then)
        else_ = explicate_expression(e.else_)
        
        return IfExp(CallFunc(Name('is_true'),[test]),then,else_)
        '''
        def result(guard):
            return IfExp(Compare(GetTag(guard),[('==',Const(1))]),IfExp(ProjectTo('BOOL',guard),then,else_),\
                         IfExp(Compare(GetTag(guard),[('==', Const(0))]),IfExp(ProjectTo('INT',guard),then,else_), \
                               IfExp(CallFunc(Name('is_true'),[guard]),then,else_)))
        return letify(test,lambda g:result(test))
        '''
     
#return IfExp(getGuard(test),toPyobj(then),toPyObj(else_))

    elif isinstance(e,Add):
        
        e1 = explicate_expression(e.left)
        e2 = explicate_expression(e.right)
        #print"DOCS"
        #printe
        #printe1
        #printe2
        def result(l,r):
            return IfExp(Compare(GetTag(l),[('==',Const(0))]),
                         InjectFrom('INT',AddInt((ProjectTo('INT',l), \
                                                  ProjectTo('INT',r)))),
                         IfExp(Compare(GetTag(l),[('==',Const(1))]),
                               InjectFrom('INT',AddInt((ProjectTo('INT',l),\
                                                        ProjectTo('INT',r)))),
                               InjectFrom('BIG',CallFunc(Name('add'),[ProjectTo('BIG',l),ProjectTo('BIG',r)]))))
        
        return letify(e1,lambda l:letify(e2,lambda r:result(l,r)))


    elif isinstance(e,Compare): #add lets
        expL = explicate_expression(e.expr)
        expR = explicate_expression(e.ops[0][1])
        op = e.ops[0][0]
        
        def result(lft,rgt):
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
                return IfExp(Compare(GetTag(lft),[('==',Const(INT))]),thenint,elseint)
            elif op == '==':
                return IfExp(Compare(GetTag(lft),[('==',Const(INT))]),IfExp(Compare(GetTag(rgt),[('==',Const(INT))]),
                                                                        InjectFrom('BOOL',Compare(ProjectTo('INT',lft),[(op,ProjectTo('INT',rgt))])),
                                                                        InjectFrom('BOOL',Compare(ProjectTo('INT',lft),[(op,ProjectTo('BOOL',rgt))]))),
                         IfExp(Compare(GetTag(lft),[('==',Const(BOOL))]),
                               IfExp(Compare(GetTag(rgt),[('==',Const(INT))]),
                                     InjectFrom('BOOL',Compare(ProjectTo('BOOL',lft),[(op,ProjectTo('INT',rgt))])),
                                     InjectFrom('BOOL',Compare(ProjectTo('BOOL',lft),[(op,ProjectTo('BOOL',rgt))]))),
                               InjectFrom('BOOL',CallFunc(Name('equal'),[ProjectTo('BIG',lft),ProjectTo('BIG',rgt)]))))
            elif op == '!=':
                return IfExp(Compare(GetTag(lft),[('==',Const(INT))]),IfExp(Compare(GetTag(rgt),[('==',Const(INT))]),
                                                                        InjectFrom('BOOL',Compare(ProjectTo('INT',lft),[(op,ProjectTo('INT',rgt))])),
                                                                        InjectFrom('BOOL',Compare(ProjectTo('INT',lft),[(op,ProjectTo('BOOL',rgt))]))),
                         IfExp(Compare(GetTag(lft),[('==',Const(BOOL))]),
                               IfExp(Compare(GetTag(rgt),[('==',Const(INT))]),
                                     InjectFrom('BOOL',Compare(ProjectTo('BOOL',lft),[(op,ProjectTo('INT',rgt))])),
                                     InjectFrom('BOOL',Compare(ProjectTo('BOOL',lft),[(op,ProjectTo('BOOL',rgt))]))),
                               InjectFrom('BOOL',CallFunc(Name('not_equal'),[ProjectTo('BIG',lft),ProjectTo('BIG',rgt)]))))


        return letify(expL,lambda l:letify(expR,lambda r:result(l,r)))

    elif isinstance(e,Lambda):
        return Lambda(e.argnames,e.defaults,e.flags,
                      Stmt([Return(explicate_expression(e.code))]))
    


def letify(expr,k):
    global let;
    #printexpr
        #if isinstance(expr,InjectFrom) or isinstance(expr,ProjectTo) and (isinstance(expr.arg,Const) or (isinstance(expr.arg,Name))):
    if isinstance(expr,Name) or isinstance(expr,Const):
        return k(expr)
    else:
        n = 'letify'+str(let)
        let+=1
        return Let(Name(n),expr,k(Name(n)))

'''
def toPyobj(value):
    return IfExp(Compare(GetTag(value),[('==',Const(0))]),InjectFrom('INT',value),
                 IfExp(Compare(GetTag(value),[('==',Const(1))]),InjectFrom('BOOL',value),
                       InjectFrom('BIG',value)))

def getGuard(value):
    return ProjectTo('BOOL',CallFunc(Name('is_true'),[toPyobj(value)]))

def bothBig(v1,v2):
    return IfExp(Compare(GetTag(v1),[('==',Const(3))]),
                 IfExp(Compare(GetTag(v2),[('==',Const(3))]),Name('True'),Name('False')),
                 Name('False'))

def bothPrim(v1,v2):
    return IfExp(Compare(GetTag(v1),[('!=',Const(3))]),
                 IfExp(Compare(GetTag(v2),[('!=',Const(3))]),Name('True'),Name('False')),
                 Name('False'))
'''
                         


    




