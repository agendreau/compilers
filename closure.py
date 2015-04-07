from uniquify import *
from explicate import *
from heapify import *
from x86Nodes import *

lamby = "lambda_"
lambdaLabel = 0




def create_closure(ast):
    global lambdaLabel
    
    if isinstance(ast,Module):
        stmts,defs = create_closure(ast.node)
        return Module(ast.doc,stmts),defs
    
    elif isinstance(ast,Stmt):
        stmts = []
        defs = []
        
        for n in ast.nodes:
            #print n
            (s,nd) = create_closure(n)
            #print s
            
            stmts.append(s)
            #print stmts
            #exit(-1)
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
                (s1,nd1) = create_closure(n.expr)
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


    elif isinstance(ast,CallFunc):
        funcname,defsName = create_closure(ast.node)
        args = []
        defsArgs = []
        for arg in ast.args:
            newArg,newDefs = create_closure(arg)
            args.append(newArg)

        return CallFunc(funcname,args),defsName+defsArgs

    elif isinstance(ast,CallDef):
        funcName,defsName = create_closure(ast.node)
        args = []
        defsArgs = []
        for arg in ast.args:
            newArg,newDefs = create_closure(arg)
            args.append(newArg)
            defsArgs.extend(newDefs)

        def result(fName):
            return CallDef((CallFunc(Name('get_fun_ptr'),[fName])),
                           [CallFunc(Name('get_free_vars'),[fName])]+args)

        return letify(funcName,lambda fName:result(fName)),defsName+defsArgs

    
    elif isinstance(ast,Lambda):
        code,codeDefs = create_closure(ast.code)
        '''
        args = []
        defsArgs = []
        for arg in ast.argnames:
            newArg, newDefs = create_closure(arg)
            args.append(newArg)
            defsArgs.extend(newDefs)
        '''
        globalName = FuncName(lamby+str(lambdaLabel))
        lambdaLabel+=1
        local = varNames(ast.code)
        freeVars = free_vars(ast.code)
        trulyFree = sorted(freeVars - local-set(ast.argnames))
        freeNodes = []
        for v in trulyFree:
            freeNodes.append(Name(v))
        
        initFree = []
        for i,v in enumerate(freeNodes):
            newNode = Assign([AssName(v.name,'OP_ASSIGN')],
                              Subscript(Name('$free_vars'),'OP_APPLY',
                                        [InjectFrom('INT',Const(i))]))
            initFree.append(newNode)
        funcNode = Function(None,globalName.name,[Name('$free_vars')]+ast.argnames,None,0,None,
                            Stmt(initFree+code.nodes))
#print "LIST OF FREE NODES"
#       print freeNodes
        return InjectFrom('BIG',CallFunc(Name('create_closure'),
                                         [globalName, List(freeNodes)])),[funcNode]+codeDefs
    
    elif isinstance(ast,UnarySub):
        s,defs = create_closure(ast.expr)
        return UnarySub(s),defs
    
    elif isinstance(ast,IfExp):
        test,defsTest = create_closure(ast.test)
        then,defsThen = create_closure(ast.then)
        else_,defsElse = create_closure(ast.else_)
        return IfExp(test,then,else_),defsTest+defsThen+defsElse
    
    elif isinstance(ast,Subscript):
        expr,defsExpr = create_closure(ast.expr)
        index,defsIndex = create_closure(ast.subs[0])
        return Subscript(expr,ast.flags,[index]),defsExpr + defsIndex
    
    elif isinstance(ast,ProjectTo):
        s,defs = create_closure(ast.arg)
        return ProjectTo(ast.typ,s),defs

    elif isinstance(ast,InjectFrom):
        #print ast
        s,defs = create_closure(ast.arg)
        return InjectFrom(ast.typ,s),defs
    
    elif isinstance(ast,GetTag):
        s,defs = create_closure(ast.arg)
        return GetTag(s),defs

    elif isinstance(ast,Let):
        body,defsBody = create_closure(ast.body)
        rhs,defsRHS = create_closure(ast.rhs)
        return Let(ast.var,rhs,body), defsRHS+defsBody
    
    elif isinstance(ast,List):
        elements = []
        defs = []
        #print ast
        #print ast.nodes
        for exp in ast.nodes:
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

    