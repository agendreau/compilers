from compiler.ast import *
#from explicateNodes import *
from explicate import *
from x86Nodes import *

templabel=0
label="$tmp"

#print "HERE"

def flatten(n):
    if isinstance(n,Module):
        return flatten(n.node)
    
    elif isinstance(n, Stmt):
        flat = []
        for x in n.nodes:
            y = flatten_stmt(x)
            flat.extend(y)
        #print "total temps: " + str(templabel)
        return flat

    elif isinstance(n,Function):
        flatCode = flatten(n.code)
        return Function(n.decorators, n.name,n.argnames,n.defaults,n.flags,n.doc,
                        Stmt(flatCode))

def flatten_stmt(s):
    if isinstance(s, Printnl):
        flat = []
        for n in s.nodes:
            (v,a) = flatten_exp(n)
            pnode = Printnl([a],None)
            flat =  flat + v
            flat.append(pnode)
        return flat
    
    elif isinstance(s, Assign):
        #print s
        (v,a) = flatten_exp(s.expr)
        for n in s.nodes:
            if isinstance(n,Subscript):
                (vn,an) = flatten_exp(n.subs[0])
                newNode = Assign([Subscript(n.expr.name,'OP_ASSIGN',[an])],a)
                v = v + vn + [newNode]
            else:
                #print n
                newNode = Assign([AssName(n.name,'OP_ASSIGN')],a)
                v.append(newNode)
        return v
    
    elif isinstance(s,Discard):
        (v,a) = flatten_exp(s.expr)
        return v

    elif isinstance(s,Return):
        (v,a) = flatten_exp(s.value)
        return v+[Return(a)]


def flatten_exp(e):
    global templabel
    if isinstance(e,AssName):
        return([],e)
    
    elif isinstance(e,Const):
        return([],e)
    
    elif isinstance(e,Name) or isinstance(e,FuncName):
        return([],e)
    
    elif isinstance(e,AddInt):
        (vl,al) = flatten_exp(e.left)
        (vr,ar) = flatten_exp(e.right)
        vl = vl + vr
        newName = label+str(templabel)
        templabel=templabel+1
        vl.append(Assign([AssName(newName,'OP_ASSIGN')],AddInt((al,ar))))
        return (vl,Name(newName))
    
    elif isinstance(e,UnarySub):
        (v,a) = flatten_exp(e.expr)
        newName = label+str(templabel)
        templabel=templabel+1
        v.append(Assign([AssName(newName,'OP_ASSIGN')],UnarySub(a)))
        return (v,Name(newName))
    
    elif isinstance(e,IfExp):
        (tv,ta) = flatten_exp(e.test)
        (thv,tha) = flatten_exp(e.then)
        (ev,ea) = flatten_exp(e.else_)
        newNameResult = label+str(templabel)
        templabel = templabel + 1
        thennode = Assign([AssName(newNameResult,'OP_ASSIGN')],tha)
        elsenode = Assign([AssName(newNameResult,'OP_ASSIGN')],ea)
        thv.append(thennode)
        ev.append(elsenode)
        ifnode = If([(ta,Stmt(thv))],Stmt(ev))
        #tv.extend(thv)
        #tv.extend(ev)
        tv.append(ifnode)
        return (tv,Name(newNameResult))
    
    elif isinstance(e,Subscript):
        print e
        (vE,aE) = flatten_exp(e.expr)
        (vS,aS) = flatten_exp(e.subs[0])
        vE.extend(vS)
        newName = label + str(templabel)
        templabel = templabel + 1
        newNode = Assign([AssName(newName,'OP_ASSIGN')],Subscript(aE,'OP_APPLY',[aS]))
        vE.append(newNode)
        return (vE,Name(newName))
    
    elif isinstance(e,ProjectTo):
        (v,a) = flatten_exp(e.arg)
        newName = label+str(templabel)
        templabel = templabel + 1
        newNode = Assign([AssName(newName,'OP_ASSIGN')],ProjectTo(e.typ,a))
        v.append(newNode)
        return (v,Name(newName))
    
    elif isinstance(e,InjectFrom):
        (v,a) = flatten_exp(e.arg)
        newName = label+str(templabel)
        templabel = templabel + 1
        newNode = Assign([AssName(newName,'OP_ASSIGN')],InjectFrom(e.typ,a))
        v.append(newNode)
        return (v,Name(newName))
    
    elif isinstance(e,GetTag):
        (v,a) = flatten_exp(e.arg)
        newName = label+str(templabel)
        templabel = templabel + 1
        newNode = Assign([AssName(newName,'OP_ASSIGN')],GetTag(a))
        v.append(newNode)
        return (v,Name(newName))
        
    elif isinstance(e,Let):
        #printe
        (v,a) = flatten_exp(e.rhs)
        newNode = Assign([AssName(e.var.name,'OP_ASSIGN')],a)
        v.append(newNode)
        
        (vB,aB) = flatten_exp(e.body)
        newName = label + str(templabel)
        templabel = templabel + 1
        newNode = Assign([AssName(newName,'OP_ASSIGN')],aB)
        v.extend(vB)
        v.append(newNode)
        return (v,Name(newName))
    
    elif isinstance(e,List):
        elements = []
        pre = []
        print e
        print e.nodes
        for exp in e.nodes:
            print exp
            (preP, result) = flatten_exp(exp)
            elements.append(result)
            pre.extend(preP)
        print "ELEMENTS"
        print elements
        newName = label + str(templabel)
        templabel = templabel + 1
        newNode = Assign([AssName(newName,'OP_ASSIGN')], List(elements))
        pre.append(newNode)
        return (pre,Name(newName))
    
    elif isinstance(e,Dict):
        dic = []
        pre = []
        for exp in e.items:
            (preK,key) = flatten_exp(exp[0])
            (preV,value) = flatten_exp(exp[1])
            pre.extend(preK)
            pre.extend(preV)
            dic.append((key,value))
            
        newName = label + str(templabel)
        templabel = templabel + 1
        newNode = Assign([AssName(newName,'OP_ASSIGN')], Dict(dic))
        pre.append(newNode)
        return (pre,Name(newName))
    
    elif isinstance(e,CallFunc):
        flat = []
        args = []
        for exp in e.args:
            (v,a) = flatten_exp(exp)
            flat.extend(v)
            args.append(a)
        print "CALL ARGS"
        print flat
        newName = label + str(templabel)
        templabel = templabel + 1
        newNode = Assign([AssName(newName,'OP_ASSIGN')], CallFunc(e.node,args))
        return (flat+[newNode],Name(newName))
    
    elif isinstance(e,Compare):
        (vL, aL) = flatten_exp(e.expr)
        (vR, aR) = flatten_exp(e.ops[0][1])
        newOps = (e.ops[0][0],aR)
        newName = label + str(templabel)
        templabel = templabel + 1
        newNode = Assign([AssName(newName,'OP_ASSIGN')], Compare(aL,newOps))
        vL.extend(vR)
        vL.append(newNode)
        return (vL,Name(newName))

    elif isinstance(e,CallDef):
        #flat = []
        args = []
        flat,name = flatten_exp(e.node)
        for exp in e.args:
            (v,a) = flatten_exp(exp)
            flat.extend(v)
            args.append(a)
        newName = label + str(templabel)
        templabel = templabel + 1
        newNode = Assign([AssName(newName,'OP_ASSIGN')], CallDef(name,args))
        return (flat+[newNode],Name(newName))

  

