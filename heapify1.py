from compiler.ast import *
from explicate import *
from x86Nodes import *
from heapify import *

heaplabel = 0
'''
def free_vars(n):
    if isinstance(n, Stmt):
        frev = set([])
        bound = set([])
        for x in n.nodes:
            frev |= free_vars(x)
            if isinstance(x,Assign):
                if isinstance(x.nodes[0],AssName):
                    bound |= set([x.nodes[0].name]) 
        return frev-bound
    
    elif isinstance(n, Printnl):
        frev = set([])
        for x in n.nodes:
            frev |= free_vars(x)
        return frev
    
    elif isinstance(n, Assign):
        if isinstance(n.nodes[0], AssName):
            return free_vars(n.expr) - set([n.nodes[0].name])
        else:
            return free_vars(n.expr) - set([n.nodes[0].expr])
    
    elif isinstance(n,Discard):
        return free_vars(n.expr)
    
    elif isinstance(n,Const):
        return set([])
        
    elif isinstance(n, Name):
        if n.name in ['True' , 'False' ,'add', 'not_equal', 'equal']:
            return set([])
        else:
            return set([n.name])
        
    elif isinstance(n, AddInt):
        return free_vars(n.left) | free_vars(n.right)
    
    elif isinstance(n, CallFunc):
        fv_args = [free_vars(e) for e in n.args]
        free_in_args = reduce(lambda a, b: a | b, fv_args, set([]))
        return free_vars(n.node) | free_in_args
    
    elif isinstance(n, Lambda):
        return free_vars(n.code) - set(n.argnames)
    
    elif isinstance(n,UnarySub):
        return free_vars(n.expr)
    
    elif isinstance(n,IfExp):
        return free_vars(n.test) |  free_vars(n.then) | free_vars(n.else_)
    
    elif isinstance(n,Subscript):
        return free_vars(n.expr) | free_vars(n.subs[0])
    
    elif isinstance(n,ProjectTo):
        return free_vars(n.arg)
    
    elif isinstance(n,InjectFrom):
        return free_vars(n.arg)
        
    elif isinstance(n,GetTag):
        return free_vars(n.arg)
    
    elif isinstance(n,Let):
        return (free_vars(n.rhs) | free_vars(n.body)) - set([n.var.name])
        
    elif isinstance(n,List):
        return set([])
    
    elif isinstance(n,Dict):
        return set([])
    
    elif isinstance(n,Compare):
        return free_vars(n.expr) | free_vars(n.ops[0][1])
    
    elif isinstance(n,Return):
        return free_vars(n.value)
    
    else:
        return set([])
'''

def get_heapvars(n):
    if isinstance(n,Stmt):
        free = set([])
        for x in n.nodes:
            if isinstance(x, Assign):
                if isinstance(x.expr, Lambda):
                    free |= free_vars(x.expr)
        return free
    
    elif isinstance(n,Lambda):
        return get_heapvars(n.code)
        
    else:
        return set([])
    
def heapify(n, heaplist):
    global heaplabel
    if isinstance(n,Module):
        st = []
        heapvars = get_heapvars(n.node)
        for x in heapvars:
            alloc = Assign([AssName(x,'OP_ASSIGN')],List([InjectFrom('INT', Const(0))]))
            st = st + [alloc]
        st = st + heapify(n.node,heaplist).nodes
        return (Module(n.doc,Stmt(st)),heapvars)
    
    elif isinstance(n, Stmt):
        newheap = heaplist.copy() | get_heapvars(n)
        stmt = []
        for x in n.nodes:
            stmt.append(heapify(x,newheap))
        return Stmt(stmt)
    
    elif isinstance(n, Printnl):
        stmt = []
        for x in n.nodes:
            stmt.append(heapify(x,heaplist))
        return Printnl(stmt,n.dest)
    
    elif isinstance(n, Assign):
        if isinstance(n.nodes[0],AssName):
            if n.nodes[0].name in heaplist:
                return Assign([Subscript(Name(n.nodes[0].name), 'OP_ASSIGN', [InjectFrom('INT', Const(0))])], heapify(n.expr,heaplist))
        return Assign(n.nodes,heapify(n.expr,heaplist))
    
    elif isinstance(n,Discard):
        return Discard(heapify(n.expr,heaplist))
    
    elif isinstance(n, Lambda):
        newdict = {}
        heapifyvars = get_heapvars(n)
        newheap = heaplist.copy() | heapifyvars
        argheap = []
        for i,x in enumerate(n.argnames):
            if x in newheap:
                newdict[x] = heaplabel
                heaplabel += 1
                argheap.append(x)
                n.argnames[i] = '$heap'+str(newdict[x])
        
        params = []
        for x in heapifyvars-heaplist:
            if x in argheap:
                alloc = Assign([AssName(x,'OP_ASSIGN')],List([InjectFrom('INT', Const(0))]))
                init = Assign([Subscript(Name(x), 'OP_ASSIGN', [InjectFrom('INT', Const(0))])], Name('$heap'+str(newdict[x])))
                params = params + [alloc,init]
            else:
                alloc = Assign([AssName(x,'OP_ASSIGN')],List([InjectFrom('INT', Const(0))]))
                params = params + [alloc]
        params = params + (heapify(n.code,newheap)).nodes
        return Lambda(n.argnames, n.defaults, n.flags, Stmt(params))
    
    elif isinstance(n,Return):
        return Return(heapify(n.value,heaplist))
    
    elif isinstance(n,Const):
        return n
       
    elif isinstance(n, Name):
        if n.name in heaplist:
            return Subscript(Name(n.name), 'OP_APPLY', [InjectFrom('INT', Const(0))])
        else:
            return n   
    
    elif isinstance(n,AddInt):
        return AddInt((heapify(n.left,heaplist),heapify(n.right,heaplist)))

    elif isinstance(n,Add):
        return Add((heapify(n.left,heaplist),heapify(n.right,heaplist)))
    
    elif isinstance(n,UnarySub):
        return UnarySub(heapify(n.expr,heaplist))
    
    elif isinstance(n,IfExp):
        return IfExp(heapify(n.test,heaplist),heapify(n.then,heaplist),heapify(n.else_,heaplist))
    
    elif isinstance(n,Subscript):
        return Subscript(heapify(n.expr,heaplist),n.flags,[heapify(n.subs[0],heaplist)])
        
    elif isinstance(n,ProjectTo):
        return ProjectTo(n.typ,heapify(n.arg,heaplist))
        
    elif isinstance(n,InjectFrom):
        return InjectFrom(n.typ,heapify(n.arg,heaplist))
    
    elif isinstance(n,GetTag):
        return GetTag(heapify(n.arg,heaplist))
    
    elif isinstance(n,Let):
        return Let(heapify(n.var,heaplist),heapify(n.rhs,heaplist),heapify(n.body,heaplist))
    
    elif isinstance(n,List):
        elements = []
        for exp in n.nodes:
            elements.append(heapify(exp,heaplist))
        return List(elements)
    
    elif isinstance(n,Dict):
        return n
        
    elif isinstance(n,Compare):
        return Compare(heapify(n.expr,heaplist),[(n.ops[0][0],heapify(n.ops[0][1],heaplist))])
    
    elif isinstance(n,Or):
        orlist = []
        for x in n.nodes:
            orlist.append(heapify(x,heaplist))
        return Or(orlist)
    
    elif isinstance(n,And):
        andlist = []
        for x in n.nodes:
            andlist.append(heapify(x,heaplist))
        return And(andlist)
    
    elif isinstance(n,Not):
        return Not(heapify(n.expr,heaplist))
    
    elif isinstance(n,CallFunc):
        arglist = []
        for x in n.args:
            arglist.append(heapify(x,heaplist))
        return CallFunc(heapify(n.node,heaplist),arglist)

        
    elif isinstance(n,CallDef):
        arglist = []
        for x in n.args:
            arglist.append(heapify(x,heaplist))
        return CallDef(heapify(n.node,heaplist),arglist)

    elif isinstance(n,While):
        test = heapify(n.test,heaplist)
        body = heapify(n.body,heaplist)
        return While(test,body,n.else_)
    
    elif isinstance(n,If):
        heap_test = []
        for t in n.tests:
            test = heapify(t[0],heaplist)
            stmts = heapify(t[1],heaplist)
            heap_test.append((test,stmts))
        else_ = heapify(n.else_,heaplist)
        return If(heap_test,else_)
    
    else:
        return n
