from compiler.ast import *
from x86Nodes import *
from explicateNodes import *
from explicate import *

outputlabel = 0

def convertMain(flatAST):
    return Function(None,'_main',[],None,0,None,Stmt(flatAST))

def generateOne(instr,assignmentVariable):
    
    vars = set([])
    
    if isinstance(instr,Add) or isinstance(instr, AddInt):
        if isinstance(instr.left,Name) and isinstance(instr.right,Name):
            tmp1 = Var(instr.left.name)
            tmp2 = Var(instr.right.name)
            vars.add(tmp1)
            vars.add(tmp2)
            moveNode = MovL((tmp1,assignmentVariable))
            addNode = AddL((tmp2,assignmentVariable))
        #return [moveNode,addNode],vars
        #IR.extend([moveNode,addNode])
        
        elif isinstance(instr.left,Name):
            tmp1 = Var(instr.left.name)
            tmp2 = Con(instr.right.value)
            vars.add(tmp1)
            moveNode = MovL((tmp1,assignmentVariable))
            addNode = AddL((tmp2,assignmentVariable))
        #return [moveNode,addNode],vars
        #IR.extend([moveNode,addNode])
        
        elif isinstance(instr.right,Name):
            tmp1 = Con(instr.left.value)
            tmp2 = Var(instr.right.name)
            vars.add(tmp2)
            moveNode = MovL((tmp1,assignmentVariable))
            addNode = AddL((tmp2,assignmentVariable))
        
        #IR.extend([moveNode,addNode])
        
        else:
            tmp1 = Con(instr.left.value)
            tmp2 = Con(instr.right.value)
            moveNode = MovL((tmp1,assignmentVariable))
            addNode = AddL((tmp2,assignmentVariable))
        #IR.extend([moveNode,addNode])
        
        return [moveNode,addNode],vars


    elif isinstance(instr,UnarySub):
        if isinstance(instr.expr,Name):
            tmp = Var(instr.expr.name)
            vars.add(tmp)
        else:
            tmp = Con(tree.expr.expr.value)
        
        moveNode = MovL((tmp,assignmentVariable))
        negNode = NegL(assignmentVariable)
        
        return [moveNode,negNode],vars

    elif isinstance(instr,Const):
        moveNode = MovL((Con(tree.expr.value),assignmentVariable))
        return [moveNode],vars
    
    elif isinstance(instr,Name):
        moveNode = MovL((Var(instr.name),assignmentVariable))
        vars.add(Var(instr.name))
        return [moveNode],vars

    elif isinstance(instr,FuncName):
        moveNode = ((Var(instr.name),assignmentVariable))
        return [moveNode],vars
    
    
    elif isinstance(instr,CallFunc):
        #print instr
        if instr.node.name == 'input':
            funcNode = Call(instr.node.name+'_int')
            moveNode = MovL((Register("%eax"),assignmentVariable))
            return [funcNode,moveNode],vars
            '''
        elif instr.node.name == 'add' or instr.node.name=='equal' or instr.node.name == 'not_equal':
            args = instr.args
            #print args
            pushNode1 = Push(Var(args[1].name))
            pushNode2 = Push(Var(args[0].name))
            funcNode = Call(instr.node.name)
            moveNode = MovL((Register("%eax"),assignmentVariable))
            popStack = AddL((Con(8),Register("%esp")))
            vars.add(Var(args[0]))
            vars.add(Var(args[1]))
            return [pushNode1,pushNode2,funcNode,moveNode,popStack],vars
        elif instr.node.name == 'is_true':
            args = instr.args
            pushNode = Push(Var(args[0]))
            funcNode = Call(instr.node.name)
            moveNode = MovL((Register("%eax"),assignmentVariable))
            popStack = AddL((Con(4),Register("%esp")))
            vars.add(Var(args[0]))
            return [pushNode,funcNode,moveNode,popStack],vars
            '''
        else:
            toPop = len(instr.args)
            push=[]
            for arg in reversed(instr.args):
                if isinstance(arg,Name):
                    v = Var(arg.name)
                    push.append(Push(v))
                    vars.add(v)
                elif isinstance(arg,FuncName):
                    push.append(Push(arg))
                else:
                    push.append(Push(Con(arg.value)))

            callNode = Call(instr.node.name)
            moveNode = MovL((Register("%eax"),assignmentVariable))
            popNode = AddL((Con(toPop*4),Register("%esp")))
            return push+[callNode]+[moveNode]+[popNode],vars
                           
            

    
            '''
                elif isinstance(instr,GetTag):
                if isinstance(instr.arg,Name):
                pushNode = Push(Var(instr.arg.name))
                vars.add(Var(instr.arg.name))
                elif isinstance(instr.arg,Const):
                pushNode = Push(Con(instr.arg))
                
                tagNode = Call("tag")
                popStack = AddL((Con(4),Register("%esp")))
                moveNode = MovL((Register("%eax"),assignmentVariable))
                return [pushNode,tagNode,popStack,moveNode],vars
            '''

    elif isinstance(instr,GetTag):
        if isinstance(instr.arg,Name):
            var = Var(instr.arg.name)
            vars.add(Var(instr.arg.name))
        elif isinstance(instr.arg,Const):
            var = Con(instr.arg.value)

        tagNode = andL((Con(3),assignmentVariable))

        movNode = MovL((var,assignmentVariable))

        return ([movNode,tagNode],vars)

    elif isinstance(instr,ProjectTo): #untag
        type = instr.typ
        if isinstance(instr.arg,Name):
            var = Var(instr.arg.name)
            vars.add(Var(instr.arg.name))
        elif isinstance(instr.arg,Const):
            var = Con(instr.arg.value)
        
        if type == 'INT':
            shiftNode = sArl((Con(2),assignmentVariable))
        #tagNode = orL((Con(0),instr.arg))
        elif type == 'BOOL':
            shiftNode = sArl((Con(2),assignmentVariable))
        #    tagNode = orL((Con(1),instr.arg))
        elif type == 'BIG':
            movNode = MovL((Con(3),assignmentVariable))
            notNode = notL(assignmentVariable)
            andNode = andL((var,assignmentVariable))
            return ([movNode,notNode,andNode],vars)
        
        movNode = MovL((var,assignmentVariable))
        
        return ([movNode,shiftNode],vars)


    elif isinstance(instr,InjectFrom): #tag
        type = instr.typ
        #print type
        if isinstance(instr.arg,Name):
            var = Var(instr.arg.name)
            vars.add(Var(instr.arg.name))
        elif isinstance(instr.arg,Const):
            var = Con(instr.arg.value)
     

        if type == 'INT':
            shiftNode = sAll((Con(2),assignmentVariable))
            tagNode = orL((Con(0),assignmentVariable))
        elif type == 'BOOL':
            shiftNode = sAll((Con(2),assignmentVariable))
            tagNode = orL((Con(1),assignmentVariable))
        elif type == 'BIG':
            #shiftNode = sAll((Con(3),assignmentVariable))
            tagNode = orL((Con(3),assignmentVariable))
            movNode = MovL((var,assignmentVariable))
            return ([movNode,tagNode],vars)

        movNode = MovL((var,assignmentVariable))
                
        return ([movNode,shiftNode,tagNode],vars)
    
    elif isinstance(instr,Subscript):
        
        expr = instr.expr
        subs = instr.subs[0]
        pushCollection = Push(Var(expr.name))
        vars.add(Var(expr.name))
        #print subs
        
        if isinstance(subs,Name):
            ##print subs
            pushNode = Push(Var(subs.name))
            subNode = Call('get_subscript')
            popStack = AddL((Con(8),Register("%esp")))
            moveNode = MovL((Register("%eax"),assignmentVariable))
            vars.add(Var(subs.name))
            
        elif isinstance(subs,Const):
            ##print instr
            pushNode = Push(Con(subs))
            subNode = Call('get_subscript')
            popStack = AddL((Con(8),Register("%esp")))
            moveNode = MovL((Register("%eax"),assignmentVariable))
        
#return [pushCollection,pushNode,subNode,popStack,moveNode],vars
        return [pushNode,pushCollection,subNode,popStack,moveNode],vars

    elif isinstance(instr,Dict):
        createDictionary = []
        items = instr.items
        
        tagNode = orL((Con(3),assignmentVariable))
        movNode = MovL((Register("%eax"),assignmentVariable))
        
            
        createDictionary.extend([Call('create_dict'),movNode,tagNode])

        for (k,v) in items:
           
            if isinstance(v,Name):
                vars.add(Var(v.name))
                pushNodeV = Push(Var(v.name))
            else:
                #shiftNode = sAll((Con(2),assignmentVariable))
                #tagNode = orL((Con(0),assignmentVariable))
                pushNodeV = Push(Con(v.value))
            
            if isinstance(k,Name):
                vars.add(Var(k.name))
                pushNodeK = Push(Var(k.name))
            else:
                pushNodeK = Push(Con(k.value))
            
            pushNodeL = Push(assignmentVariable)
            callNode = Call('set_subscript')
            popStack = AddL((Con(12),Register("%esp")))
            #moveNode = MovL((Register("%eax"),assignmentVariable))
            createDictionary.extend([pushNodeV,pushNodeK,pushNodeL,callNode,popStack])
                                               
        return createDictionary,vars

    elif isinstance(instr,List):
        createList = []
        nodes = instr.nodes
        createList.extend([Push(Con(len(nodes))),
                           Call('inject_int'),
                           Push(Register("%eax"))])

        createList.extend([Call('create_list'),
                           Push(Register("%eax"))])
        
        createList.extend([Call('inject_big'),
                           MovL((Register("%eax"),assignmentVariable)),
                           AddL((Con(12),Register("%esp")))])
        
        
        for (i,n) in enumerate(nodes):
            createList.extend([Push(Con(i)),
                               Call('inject_int'),
                               AddL((Con(4),Register("%esp")))])
            if isinstance(n,Name):
                vars.add(Var(n.name))
                pushNodeV = Push(Var(n.name))
            else:
                pushNodeV = Push(Con(n.value))
            pushNodeK = Push(Register("%eax"))
            pushNodeL = Push(assignmentVariable)
            callNode = Call('set_subscript')
            popStack = AddL((Con(12),Register("%esp")))
            #moveNode = MovL((Register("%eax"),assignmentVariable))
            createList.extend([pushNodeV,pushNodeK,pushNodeL,callNode,popStack])
        
        return createList,vars



    elif isinstance(instr,Compare):
        ##print instr
        if instr.ops[0] == '==':
            if isinstance(instr.ops[1],Name) and isinstance(instr.expr,Name):
                compareNode = CmpL((Var(instr.expr.name),Var(instr.ops[1].name)))
                vars.add(Var(instr.expr.name))
                vars.add(Var(instr.ops[1].name))
            elif isinstance(instr.ops[1],Name):
                compareNode = CmpL((Con(instr.expr.value),Var(instr.ops[1].name)))
                vars.add(Var(instr.ops[1].name))
            elif isinstance(instr.expr,Name):
                compareNode = CmpL((Con(instr.ops[1].value),Var(instr.expr.name)))
                vars.add(Var(instr.expr.name))
            else:
                compareNode = CmpL((Con(instr.expr.name),Con(instr.ops[1])))
            setnode = SetNode(instr.ops[0],Register('%al'))
            movenode = MovZBL((Register('%al'),assignmentVariable))
            #movenode = MovZBL((Register('%al'),Register('%eax')))
            #movevalnode = MovL((Register("%eax"),assignmentVariable))

        elif instr.ops[0] == '!=':
            if isinstance(instr.ops[1],Name) and isinstance(instr.expr,Name):
                compareNode = CmpL((Var(instr.expr.name),Var(instr.ops[1].name)))
                vars.add(Var(instr.expr.name))
                vars.add(Var(instr.ops[1].name))
            elif isinstance(instr.ops[1],Name):
                compareNode = CmpL((Con(instr.expr.value),Var(instr.ops[1].name)))
                vars.add(Var(instr.ops[1].name))
            elif isinstance(instr.expr,Name):
                compareNode = CmpL((Con(instr.ops[1].value),Var(instr.expr.name)))
                vars.add(Var(instr.expr.name))
            else:
                compareNode = CmpL((Con(instr.expr.value),Con(instr.ops[1].value)))
            setnode = SetNode(instr.ops[0],Register('%al'))
            movenode = MovZBL((Register('%al'),assignmentVariable))
            #movenode = MovZBL((Register('%al'),Register('%eax')))
            #movevalnode = MovL((Register("%eax"),assignmentVariable))
        
        #return [compareNode,setnode,movenode,movevalnode],vars
        return [compareNode,setnode,movenode],vars

    elif isinstance(instr,CallDef):
        toPop = len(instr.args)
        push=[]
        for arg in reversed(instr.args):
            if isinstance(arg,Name):
                v = Var(arg.name)
                push.append(Push(v))
                vars.add(v)
            else:
                push.append(Con(arg.value))
        vars.add(Var(instr.node.name))
        callNode = CallStar(Var(instr.node.name))
        moveNode = MovL((Register("%eax"),assignmentVariable))
        popNode = AddL((Con(toPop*4),Register("%esp")))
        return push+[callNode]+[moveNode]+[popNode],vars

def generateAssign(tree):
    #if isinstance(tree,Subscript)
    ##print tree
    assignNode = tree.nodes[0]
    ##print assignNode
    if isinstance(assignNode,AssName):
        assignmentVariable = Var(assignNode.name)
        
        ##print assignmentVariable
        ##print tree.expr
        #print assignNode
        #print assignmentVariable
        #print tree.expr
        newIR,vars = generateOne(tree.expr,assignmentVariable)
    
        vars.add(assignmentVariable)
        return newIR,vars
    
    else:
        vars = set([])
        if isinstance(assignNode.subs[0],Name):
            vars.add(Var(assignNode.subs[0].name))
            pushNodeKey = Push(Var(assignNode.subs[0].name))
        else:
            pushNodeKey = Push(Con(assignNode.subs[0].value))
        if isinstance(tree.expr,Name):
            vars.add(Var(tree.expr.name))
            pushNodeValue = Push(Var(tree.expr.name))
        else:
            pushNodeValue = Push(Con(tree.expr.value))
        
        pushNodeBig = Push(Var(assignNode.expr))
        vars.add(Var(assignNode.expr))
        callNode = Call('set_subscript')
        popStack = AddL((Con(12),Register("%esp")))


        return [pushNodeValue,pushNodeKey,pushNodeBig,callNode,popStack],vars


def generatePrint(tree):
    vars = set([])
    if isinstance(tree.nodes[0],Name):
        pushNode = Push(Var(tree.nodes[0].name))
        vars.add(Var(tree.nodes[0].name))
    elif isinstance(tree.nodes[0],Const):
        pushNode = Push(Con(tree.nodes[0].value))
    
    printNode = Call("print_any")
    popStack = AddL((Con(4),Register("%esp")))
    return [pushNode,printNode,popStack],vars

def generateInstructions(function):
    #print "here"
    prologue = []
    loadParams = []
    epilogue = []
    vars = set([])
    #print "FUNCTION NAME"
    #print function.name
    if function.name != '_main':
        prologue = [Push(Register("%edi")),Push(Register("%esi")),Push(Register("%ebx")),
                    Push(Register("%edx"))]
        offset = 8
        #print function.argnames
        for arg in function.argnames:
            if isinstance(arg,Name):
                loadParams.append(MovL((Address(offset),Var(arg.name))))
                vars.add(Var(arg.name))
            else:
                loadParams.append(MovL((Address(offset),Var(arg))))
                vars.add(Var(arg))
            offset+=4
        
        epilogue = [Pop(Register("%edx")),Pop(Register("%ebx")),Pop(Register("%esi")),
                                Pop(Register("%edi"))]

    astList = function.code.nodes
    #print astList
    
    IR = prologue+loadParams

    #print astList
    for tree in astList:
        #print tree
        if isinstance(tree,Assign):
            newIR,v = generateAssign(tree)
            IR.extend(newIR)
            vars = vars | v
        
        
        elif isinstance(tree,Printnl):
            newIR,v = generatePrint(tree)
            IR.extend(newIR)
            vars = vars | v
        
        
        elif isinstance(tree,If):
            newIR,newVars = generateIf(tree)
            IR.extend(newIR)
            vars = newVars | vars

        elif isinstance(tree,Return):
            if isinstance(tree.value,Name):
                vars.add(Var(tree.value.name))
                moveNode = MovL((Var(tree.value.name),Register("%eax")))
            else:
                moveNode = Movl(Con((tree.value.value),Register("%eax")))
                    
                    #jumpBack = Jmp(Label("exit_"+function.name))

            
            IR.extend([moveNode])#,jumpBack])
    
    IR.extend(epilogue)

    return IR,vars

def generateIf(instr):
    
    vars = set([])
    s = []
    for x in instr.tests:
        if isinstance(x[0],Name):
            #do is true here instead
            compare = CmpL((Con(0),Var(x[0].name)))
            vars.add(Var(x[0].name))
        else:
            compare = CmpL((Con(0),Con(x[0].value)))
        IRif = []
        for n in x[1].nodes:
            if isinstance(n,Assign):
                newIR,v = generateAssign(n)
                IRif.extend(newIR)
                vars = vars | v
            elif isinstance(n,Printnl):
                newIR,v = generatePrint(n)
                IRif.extend(newIR)
                vars = vars | v
            
            else:
                newIR,newVars = generateIf(n)
                IRif.extend(newIR)
                vars = newVars | vars    
    s.append((compare,IRif))

    IR=[]
    for e in instr.else_.nodes:
        if isinstance(e,Assign):
            newIR,v = generateAssign(e)
            
            IR.extend(newIR)
            vars = vars | v
        elif isinstance(e,Printnl):
            newIR,v = generatePrint(e)
            IR.extend(newIR)
            vars = vars | v
        
        else:
            newIR,newVars = generateIf(e)
            IR.extend(newIR)
            vars = newVars | vars
    return ([If(s,IR)],vars)

'''
def outputCode(instructionList,stackSize,filename):
    preamble = ".globl main\nmain:\n\tpushl %ebp\n\tmovl %esp, %ebp\n\t"
    postemble = 'movl $0, %eax\n\tleave\n\tret\n'
    stackspace = "subl $" + str(stackSize*4)+",%esp\n\n\t"
    
    assemblyCode = preamble
    assemblyCode += stackspace
    code = outputHelper(instructionList,"")
    #print code
    assemblyCode += code
    assemblyCode += postemble
    targetfile = open(filename+".s", "w")
    targetfile.truncate()
    targetfile.write(assemblyCode)
    targetfile.close()
'''

def outputCode(functions,filename):
    assemblyCode=""
    for f in functions:
        #print len(f)
        name = f[0]
        #print name
        stackSize = f[2]
        preamble = ".globl "+ name+"\n"+name+":\n\tpushl %ebp\n\tmovl %esp, %ebp\n\t"
        stackspace = "subl $" + str(stackSize*4)+",%esp\n\n\t"
        if name=='main':
            postemble = 'movl $0, %eax\n\tleave\n\tret\n'
        else:
            postemble = 'leave\n\tret\n'


        assemblyCode += preamble
        assemblyCode += stackspace
        code = outputHelper(f[1],"")
        #print code
        assemblyCode += code
        assemblyCode += postemble

    targetfile = open(filename+".s", "w")
    targetfile.truncate()
    targetfile.write(assemblyCode)
    targetfile.close()

def outputHelper(instructionList,instrs):
    global outputlabel
    if len(instructionList) == 0:
        return instrs
    else:

        i = instructionList[0]
        #print i
        if isinstance(i,If):
            name = str(outputlabel)
            outputlabel+=1
            ifstmt = outputHelper([i.tests[0][0]],"")
            
            instrs += ifstmt
            thenstmt = outputHelper(i.tests[0][1],"")
            instrs += "je else_label_"+name+"\n\t"
            instrs += thenstmt
            elsestmt = outputHelper(i.else_,"")
            instrs += "jmp end_label_"+name+"\n\t"
            instrs += "else_label_"+name+":\n\t"
            instrs += elsestmt
            #print "ifstmt:", ifstmt
            #print "elsestmt:", elsestmt
            #print "thenstmt:", thenstmt
            instrs += "end_label_"+name+":\n\t"
            return outputHelper(instructionList[1:],instrs)
        

        elif i!=None:
            #print "here"
            #print instrs
            instrs = instrs + str(i) +"\n\t"
            return outputHelper(instructionList[1:],instrs)


'''
def outputHelper(instructionList,varmap):
    global outputlabel
    code = ""
    for i in instructionList:
        if isinstance(i,IfNode):
            name = str(outputlabel)
            outputlabel += 1
            ifstmt = outputHelper([i.tests[0][0]],varmap)
            
            code += ifstmt
            thenstmt = outputHelper(i.tests[0][1],varmap)
            code += "je else_label_"+name+"\n\t"
            code += thenstmt
            elsestmt = outputHelper(i.else_,varmap)
            code += "jmp end_label_"+name+"\n\t"
            code += "else_label_"+name+":\n\t"
            code += elsestmt
            #print "ifstmt:", ifstmt
            #print "elsestmt:", elsestmt
            #print "thenstmt:", thenstmt
            code += "end_label_"+name+":\n\t"
            
        elif i!=None:
            if isinstance(i,AddL):
                left = right = 0
                if isinstance(i.left,Var):
                    left = 1
                    i.left = Address(varmap[i.left])
                if isinstance(i.right,Var):
                    right = 1
                    i.right = Address(varmap[i.right])
                if isinstance(i.left,Con):
                    left = 1
                if isinstance(i.right,Con):
                    right = 1
                if left == 1 and right == 1:
                    code += str(MovL((i.left,Register("%edx")))) + "\n\t"
                    i.left = Register("%edx")
            elif isinstance(i,MovL):
                left = right = 0
                if isinstance(i.left,Var):
                    left = 1
                    i.left = Address(varmap[i.left])
                if isinstance(i.right,Var):
                    right = 1
                    i.right = Address(varmap[i.right])
                if isinstance(i.left,Con):
                    left = 1
                if isinstance(i.right,Con):
                    right = 1
                if left == 1 and right == 1:
                    code += str(MovL((i.left,Register("%edx")))) + "\n\t"
                    i.left = Register("%edx")
            elif isinstance(i,CmpL):
                left = right = 0
                if isinstance(i.left,Var):
                    left = 1
                    i.left = Address(varmap[i.left])
                if isinstance(i.right,Var):
                    right = 1
                    i.right = Address(varmap[i.right])
                if isinstance(i.left,Con):
                    left = 1
                if isinstance(i.right,Con):
                    right = 1
                if left == 1:
                    code += str(MovL((i.left,Register("%edx")))) + "\n\t"
                    i.left = Register("%edx")
                if right == 1:
                    code += str(MovL((i.right,Register("%ecx")))) + "\n\t"
                    i.right = Register("%ecx")
            elif isinstance(i,NegL):
                if isinstance(i.value,Var):
                    i.value = Address(varmap[i.value])
            elif isinstance(i,Push):
                if isinstance(i.argument,Var):
                    i.argument = Address(varmap[i.argument])
            elif isinstance(i,Call):
                if i.funcName == '$error':
                    i = '' 
            code +=(str(i))+'\n\t'
    return code
'''

def prettyPrint(IR,toString):
    if (len(IR)!=0):
        i = IR[0]
        #print i
        if isinstance(i,If):
            #print "IF"
            ifList = []
            for t in i.tests:
                #print "GUARD"
                guard = prettyPrint([t[0]],[])
                #print "then instructions"
                then = prettyPrint(t[1],[])
                ifList.extend(guard)
                ifList.extend(then)
            #print "else instructions"
            elses = prettyPrint(i.else_,[])
            ifList.extend(elses)
            
            return prettyPrint(IR[1:],toString+ifList)
        else:
            return prettyPrint(IR[1:],toString+[(str(i.liveBefore),str(i.liveAfter))])
    else:
        return toString

def prettyPrintInstr(IR,toString):
    if (len(IR)!=0):
        i = IR[0]
        if isinstance(i,If):
            #print "IF"
            ifList = []
            for t in i.tests:
                #print "GUARD"
                guard = ["If "] + prettyPrintInstr([t[0]],[])
                #print "then instructions"
                then = prettyPrintInstr(t[1],[])
                ifList.extend(guard)
                ifList.extend(then)
            #print "else instructions"
            elses = prettyPrintInstr(i.else_,[])
            ifList.extend(["else "] + elses)
            
            return prettyPrintInstr(IR[1:],toString+ifList)
        else:
            return prettyPrintInstr(IR[1:],toString+[str(i)])
    else:
        return toString


'''

    elif isinstance(tree.expr,Subscript):
    #call func to get subscript
    
    elif isinstance(tree.expr,GetTag):
    #call func tag
    
    elif isinstance(tree.expr,ProjectTo):
    #call correct project function
    
    elif isinstance(tree.expr,InjectFrom):
    #call correct inject function
'''

