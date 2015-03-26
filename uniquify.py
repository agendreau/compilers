from compiler.ast import *


varLabel = 0

def varNames(astNode):
    if isinstance(astNode,Module):
        return varNames(astNode.node)

    elif isinstance(astNode,Stmt):
        vars = set([])
        for n in astNode.nodes:
            vars.update(varNames(n))
        return vars

    elif isinstance(astNode,Assign):
        vars = []
        for n in astNode.nodes:
            if isinstance(n,AssName):
                vars.append(n.name)
        return set(vars)

    elif isinstance(astNode,Function):
        return set([astNode.name])

    else:
        return set([])

def uniquify(astNode,varMap):
    global varLabel
    
    if isinstance(astNode,Module):
        vars = varNames(astNode)
        for v in vars:
            uniName = v+"$"+str(varLabel)
            varLabel+=1
            varMap[v] = uniName
        return Module(astNode.doc,uniquify(astNode.node,varMap))

    elif isinstance(astNode,Stmt):
        uniquified = []
        for n in astNode.nodes:
            uni = uniquify_stmt(n,varMap)
            uniquified.append(uni)

        return Stmt(uniquified)

def uniquify_stmt(s,varMap):
    global varLabel
    if isinstance(s,Printnl):
        uniquified = []
        for n in s.nodes:
            uni = uniquify_exp(n,varMap)
            uniquified.append(uni)
        return Printnl(uniquified,None)

    elif isinstance(s,Assign):
        expr = uniquify_exp(s.expr,varMap)
        uniquified = []
        for n in s.nodes:
            if isinstance(n, AssName):
                uniquified.append(AssName(varMap[n.name], 'OP_ASSIGN'))
            else:
                uniquified.append(Subscript(uniquify_exp(n.exp,varMap),'OP_ASSIGN',[uniquify_exp(n.subs[0],varMap)]))

        return Assign(uniquified,expr)

    elif isinstance(s,Discard):
        return Discard(uniquify_exp(s.expr))

    elif isinstance(s,Return):
        return Return(uniquify_exp(s.value,varMap))

    elif isinstance(s,Function):
        #compute locals
        name = varMap[s.name]
        localVars = varNames(s.code) | set(s.argnames)
        print localVars
        for v in localVars:
            uniName = v + "$" + str(varLabel)
            varLabel+=1
            varMap[v]=uniName
        print varMap
        print s.code
        return Function(s.decorators,name,[varMap[a] for a in s.argnames],
                        s.defaults,s.flags,s.doc,uniquify(s.code,varMap))

def uniquify_exp(e,varMap):
    global varLabel
    
    if isinstance(e,Const):
        return e
    
    elif isinstance(e,Name):
        if varMap.has_key(e.name):
            return Name(varMap[e.name])
        else:
            return e
    
    elif isinstance(e,Add):
        return Add((uniquify_exp(e.left,varMap),uniquify_exp(e.right,varMap)))
    
    elif isinstance(e,UnarySub):
        return UnarySub(uniquify_exp(e.expr,varMap))
    
    elif isinstance(e,IfExp):
        return IfExp(uniquify_exp(e.test,varMap),uniquify_exp(e.then,varMap),uniquify_exp(e.else_,varMap))
    
    elif isinstance(e,Subscript):
        return Subscript(uniquify_exp(e.expr,varMap),e.flags,[uniquify_exp(e.subs[0],varMap)])

    elif isinstance(e,List):
        elements = []
        for exp in e.nodes:
            elements.append(uniquify_exp(exp,varMap))
        return List(elements)

    elif isinstance(e,Dict):
        dic = []
        for exp in e.items:
            dic.append((uniquify_exp(exp[0],varMap),uniquify_exp(exp[1],varMap)))
        return Dict(dic)

    elif isinstance(e,CallFunc):
        args = []
        for exp in e.args:
            print exp
            args.append(uniquify_exp(exp,varMap))
        
        return CallFunc(uniquify_exp(e.node,varMap),args,e.star_args,e.dstar_args)

    elif isinstance(e,Compare):
        expr = uniquify_exp(e.expr,varMap)
        ops = []
        for (op,exp) in e.ops:
            ops.append((uniquify_exp(op,varMap),uniquify_exp(exp,varMap)))
        return Compare(expr,ops)

    elif isinstance(e,And):
        return And([uniquify_exp(e.nodes[0],varMap),uniquify_exp(e.nodes[1],varMap)])

    elif isinstance(e,Or):
        return Or([uniquify_exp(e.nodes[0],varMap),uniquify_exp(e.nodes[1],varMap)])

    elif isinstance(e,Not):
        return Not(uniquify_exp(e.expr,varMap))

    elif isinstance(e,Lambda):

        for a in e.argnames:
            uniName = a + "$" + str(varLabel)
            varLabel+=1
            varMap[a]=uniName
        return Lambda([varMap[a] for a in e.argnames],e.defaults,
                      e.flags,uniquify_exp(e.code,varMap))


'''

if __name__ == '__main__':
    import compiler
    import sys
    print
    ast = compiler.parseFile(sys.argv[1])
    print ast
    print
    varMap = {}
    unique = uniquify(ast,varMap)

    print unique
    

'''






