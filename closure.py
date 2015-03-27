from uniquify import *
from explicate import *
from heapify import *

lamby = "lambda_"
label = 0


def create_closure(ast):
    global label
    
    if isinstance(ast,Module):
        stmts,defs = create_closure(ast.node)
        return Module(ast.doc,stmts),defs
    
    elif isinstance(ast,Stmt):
        stmts = []
        defs = []
        for n in ast.nodes:
            (s,nd) = create_closure(n)
            stmts.append(s)
            defs.extend(nd)
        
        return Stmt(stmts),defs
    
    
    elif isinstance(ast, Printnl):
        stmts = []
        defs = []
        for n in ast.nodes:
            (s,nd) = create_closure(n)
            stmts.append(s)
            defs.extend(nd)
        
        return Printnl(stmts,ast.dest),defs

    elif isinstance(ast, Assign):
        #print s
        stmts = []
        defs = []
        expr,defs = create_closure(ast.expr)
        for n in ast.nodes:
            if isinstance(n,Subscript):
                (s1,nd1) = create_closure(n.expr))
                (s2,nd2) = create_closure(n.subs[0])
                stmts.append(Subscript(s1,n.flags,[s2]))
                defs.extend(nd1)
                defs.extend(nd2)
            else:
                stmts.append(n)

        return Assign(stmts,expr),defs
    
    elif isinstance(ast,Discard):
        s,defs = create_closure(ast.expr)
        return Discard(s),defs

    elif isinstance(ast,Return):
        s,defs = create_closure(ast.value)
        return Return(s),defs

    elif isinstance(ast,Const):
        return ast, []

    elif isinstance(ast,Name):
        return ast,[]

    elif isinstance(ast,Add):
        left, defLeft = create_closure(ast.left)
        right,defRight = create_closure(ast.right)
        return Add((left,right)), defLeft+defRight

    elif isinstance(ast,AddInt):
        left, defLeft = create_closure(ast.left)
        right,defRight = create_closure(ast.right)
        return AddInt((left,right)), defLeft+defRight


elif isinstance(ast,CallFunc): #TODO
        fv_args = [create_closure(n) for n in ast.args]
        free_in_args = reduce(lambda a, b: a | b, fv_args, set([]))
        return free_in_args - create_closure(ast.node)
    
elif isinstance(ast,CallDef): #TODO
        fv_args = [create_closure(n) for n in ast.args]
        free_in_args = reduce(lambda a, b: a | b, fv_args, set([]))
        return free_in_args | create_closure(ast.node)
    
elif isinstance(ast,Lambda): #TODO
        local = varNames(ast.code)
        #print "lambda"
        print create_closure(ast.code) - set(ast.argnames) - local
        return create_closure(ast.code) - set(ast.argnames) - local
    
    elif isinstance(ast,UnarySub):
        s,defs = create_closure(ast.expr)
        return UnarySub(s),defs
    
elif isinstance(ast,IfExp): #TODO
        return create_closure(ast.test)|create_closure(ast.then)|create_closure(ast.else_)
    
elif isinstance(ast,Subscript): #TODO
        return create_closure(ast.subs[0]) | create_closure(ast.expr)
    
    elif isinstance(ast,ProjectTo):
        s,defs = create_closure(ast.arg)
        return ProjectTo(s),defs

    elif isinstance(ast,InjectFrom):
        s,defs = create_closure(ast.arg)
        return InjectTo(s),defs
    
    elif isinstance(ast,GetTag):
        s,defs = create_closure(ast.arg)
        return GetTag(s),defs

    elif isinstance(ast,Let): #TODO
        return (create_closure(ast.body)|create_closure(ast.rhs))-create_closure(ast.var)
    
    elif isinstance(ast,List):
        elements = []
        defs = []
        for exp in ast:
            s,nd = create_closure(exp)
            elements.append(s)
            defs.extend(nd)
        return List(elements),defs
    
    elif isinstance(ast,Dict):
        dic = []
        defs = []
        for exp in ast.items:
            k,nd1 = create_closure(exp[0])
            v,nd2 = create_closure(exp[1])
            dic.append((k,v))
            defs.extend(nd1)
            defs.extend(nd2)
        return Dict(dic),defs
    
    elif isinstance(ast,Compare):
        e1,nd1 = create_closure(ast.expr)
        e2,nd2 = create_closure(ast.ops[0][1])
        return Compare(e1,[(ast.ops[0][0],e2)]),nd1+nd2

    