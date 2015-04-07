from compiler.ast import *
from explicate import *
from uniquify import *

def free_vars(ast):
    
    if isinstance(ast,Module):
        assigned = varNames(ast)
        #print "assigned"
        #print assigned
        return free_vars(ast.node)-assigned

    elif isinstance(ast,Stmt):
        vars = set([])
        for n in ast.nodes:
            vars.update(free_vars(n))
        
        return vars
    

    elif isinstance(ast, Printnl):
        vars = set([])
        for n in ast.nodes:
            vars.update(free_vars(n))
        
        return vars
    
    elif isinstance(ast, Assign):
        #print s
        vars = set([])
        for n in ast.nodes:
            if isinstance(n,Subscript):
                vars.update(free_vars(n.expr))
                vars.update(free_vars(n.subs[0]))
    
        return vars | free_vars(ast.expr)
    
    elif isinstance(ast,Discard):
        return free_vars(ast.expr)

    elif isinstance(ast,Return):
        return free_vars(ast.value)


    elif isinstance(ast,Const):
        return set([])
    elif isinstance(ast,Name):
        if ast.name=='True' or ast.name=='False':
            return set([])
        else:
            return set([ast.name])

    elif isinstance(ast,Add) or isinstance(ast,AddInt):
        return free_vars(ast.left)|free_vars(ast.right)

    elif isinstance(ast,CallFunc):
        fv_args = [free_vars(n) for n in ast.args]
        free_in_args = reduce(lambda a, b: a | b, fv_args, set([]))
        return free_in_args - free_vars(ast.node)

    elif isinstance(ast,CallDef):
        fv_args = [free_vars(n) for n in ast.args]
        free_in_args = reduce(lambda a, b: a | b, fv_args, set([]))
        return free_in_args | free_vars(ast.node)

    elif isinstance(ast,Lambda):
        local = varNames(ast.code)
        print "lambda: "
        print free_vars(ast.code) - set(ast.argnames) - local
        return free_vars(ast.code) - set(ast.argnames) - local

    elif isinstance(ast,UnarySub):
        return free_vars(ast.expr)

    elif isinstance(ast,IfExp):
        return free_vars(ast.test)|free_vars(ast.then)|free_vars(ast.else_)

    elif isinstance(ast,Subscript):
        return free_vars(ast.subs[0]) | free_vars(ast.expr)
    
    elif isinstance(ast,ProjectTo):
        return free_vars(ast.arg)

    elif isinstance(ast,InjectFrom):
        return free_vars(ast.arg)
    
    elif isinstance(ast,GetTag):
        return free_vars(ast.arg)

    elif isinstance(ast,Let):
        #print ast
        return (free_vars(ast.body)|free_vars(ast.rhs))-free_vars(ast.var)

    elif isinstance(ast,List):
        elements = set([])
        pre = []
        for exp in ast:
             elements.update(free_vars(exp))
        return elements

    elif isinstance(ast,Dict):
        dic = set([])
        for exp in ast.items:
            dic.update(free_vars(exp[0]))
            dic.update(free_vars(exp[1]))
        return dic

    elif isinstance(ast,Compare):
        #print e
        return free_vars(ast.expr)|free_vars(ast.ops[0][1])


'''
def toHeapify(ast,toHeap):

def toHeapify_stmt(ast,toHeap):

def toHeapify_exp(ast,toHeap):


'''





