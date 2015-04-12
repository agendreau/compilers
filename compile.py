import compiler
#from parse import *
import sys
#from flattenNJ import *
import flattenNJ
#from ast2x86 import *
import x86IR
from registerAllocation import *
from colorSpill import *
#from explicateNJ import *
#from explicateNodes import *
from typecheck import *
from explicate import * 
from uniquify import *
from heapify import *
from closure import *
import heapify1
# python compile.py example1.py
# $gcc -m32 *.c example1.s -o test.exe -lm
# ./text.exe
# cat test.in | -l test.exe



if __name__ == '__main__':
    startAST = compiler.parseFile(sys.argv[1])
    
    debug = 1
    
    
    registerTest = 0
    
    runCode = 0
    
    flat = []
    if (debug):
        
        print "STARTAST:"
        print startAST , "\n"
        varMap={}
        uniqueAST = uniquify(startAST,varMap)
        
        print "STARTAST:"
        print uniqueAST , "\n"
        
        explicateAST = explicate(uniqueAST)
        
        
        print "EXPLICATE_AST:"
        print explicateAST
        print 
        for x in explicateAST.node.nodes:
            print x
            print varNames(x)
        
        #freevars = free_vars(explicateAST)
        #print freevars
        #print "VARS"
        #vars = varNames(explicateAST)
        #print vars
        
        heapifiedAST,heaplist = heapify1.heapify(explicateAST,set([]))
        print "HEAP list"
        print heaplist
        print "heapified ast"
        print heapifiedAST
        
        
        closure,defs = create_closure(heapifiedAST)
        
        #toHeap = free_vars(explicateAST)
        #print toHeap
        
        print "CLOSURES"
    
        for n in closure.node.nodes:
            print n
        
        print
        print "DEFS"
        for d in defs:
            print d.name
            print d.argnames
            for c in d.code:
                '''
                if isinstance(c,Return):
                    print "TEST"
                    print c.value.test
                    print "THEN"
                    print c.value.then
                    print "ELSE"
                    if isinstance(c.value.else_,If):
                        print c.value.else_.test
                        print
                        print c.value.else_.then
                        print
                        print c.value.else_.else_
                    else:
                        print c.value.else_
                else:
                '''
                print c
    
        print
        
        flatMain = flattenNJ.flatten(closure)
        print "flat main no list"
        print flatMain
        print "FLAT MAIN:"
        for f in flatMain:
            print f

        
        
        print
#print defs[0]
        funcs = []
        for d in defs:
            funcs.append(flattenNJ.flatten(d))
        #funcs = flattenNJ.flatten(defs[0]) # hack to test one
        print "FLAT FUNCS"
#        print funcs
#print funcs
        for f in funcs:
            print f.name
            print f.argnames
            for c in f.code:
                if isinstance(c,If):
                    print "TEST"
                    print c.tests[0][0]
                    print "THEN"
                    for s in c.tests[0][1]:
                        print s
                    print "ELSE"
                    for e in c.else_:
                        if isinstance(e,If):
                            print "elif test"
                            print e.tests[0][0]
                            print "elif then"
                            for st in e.tests[0][1]:
                                print st
                            print "elif else"
                            for sts in e.else_:
                                print sts
                        else:
                            print e
                else:
                    print c
    #exit(-1)
        '''
        for f in funcs.code:
            print f
        '''
        print
        print "MAIN"
        create_main = convertMain(flatMain)
        print create_main
        print
        
        IR,vars = x86IR.generateInstructions(create_main)
        print IR
        instrs = x86IR.prettyPrintInstr(IR,[])
        #print instrs
        for i in instrs:
            print i
        print
        exit(-1)
        #print funcs
        funcList = [('main',IR,vars)]
        for f in funcs:
            func1,vars1 = x86IR.generateInstructions(f)
            funcList.append((f.name,func1,vars1))
        print
        print "function defs"
        for f in funcList:
            instrsFunc = x86IR.prettyPrintInstr(f[1],[])
            for i in instrsFunc:
                print i
            print

        #funcList = [('main',IR,vars),(funcs.name,func1,vars1)]
        funcsOutput = []
        for n in funcList:
            vars = n[2]
            name = n[0]
            IR = n[1]
            instrLive = []
            liveAfter = set([])
            print
            liveness = livenessAnalysis(IR,instrLive,liveAfter)
            #print liveness
            print len(IR)
            print total(IR)
            print len(liveness)
            instrs = x86IR.prettyPrint(IR,[])
            
            for index,i in enumerate(instrs):
                print str(index) + " " + str(i)


            print
            for (i,v) in enumerate(prettyPrintInstr(liveness,[])):
                print str(i) + " " + str(v)
            print
            print
            
            iGraph = interferenceGraph(liveness,vars)
            #print iGraph
            for (k,v) in iGraph.iteritems():
                print "key: " + str(k)
                print "values: " + str(v)
            
            coloring = graphColor(iGraph)
            print coloring
            
            spill = toSpill(coloring)
            
            print "STACK SIZE"
            print len(spill)
            tmp = Var("#tmp")
            vars.add(tmp)
            print spill
            print coloring
            print vars
            #print liveness
            good,IR,newVars,check = allocateRegisters(spill,liveness,vars,coloring,[],[],True)
            print good
            funcsOutput.append((name,good,len(spill)))
            print
            
            
        
        filename = ""
        prev = sys.argv[1].split('.')[0]
        for k in sys.argv[1].split('.')[1:]:
            filename += prev
            prev = "."+k
        print len(funcsOutput)
        outputCode(funcsOutput,filename)

        


    
    if(registerTest):
        
        
        IR,vars = x86IR.generateInstructions(flatast)
        '''
        print vars
        print "IR"
        #instrs = x86IR.prettyPrint(IR,[])
        #print instrs
        i=0
        
        i=0
        for n in IR:
            if isinstance(n,If):
                print "IF"
                for t in n.tests:
                    print str(i) + " Guard " + str(t[0])
                    i = i+1
                    print "tests"
                    for line in t[1]:
                        print str(i) + " " + str(line)
                        i += 1
                print "elses"
                for e in n.else_:
                    print str(i) + " " + str(e)
                    i += 1
                print 
            else:
                print str(i) + " " + str(n)
                i +=1
        
        #liveVars = [set([])]
        check = False
        #while not check:
        for i in range(1,3):
            instrLive = []
            liveAfter = set([])
            print
            liveness = livenessAnalysis(IR,instrLive,liveAfter)
            #print liveness
            print len(IR)
            print total(IR)
            print len(liveness)
            instrs = x86IR.prettyPrint(IR,[])
            
            for index,i in enumerate(instrs):
                print str(index) + " " + str(i)
            
                #for (i,v) in enumerate(liveness):
                #print str(i) + " " + str(v.liveBefore) + " " + str(v.liveAfter)
            
            print 
            for (i,v) in enumerate(prettyPrintInstr(liveness,[])):
                print str(i) + " " + str(v)
            print
            print 

            iGraph = interferenceGraph(liveness,vars)
            #print iGraph
            for (k,v) in iGraph.iteritems():
                print "key: " + str(k)
                print "values: " + str(v)
            
            coloring = graphColor(iGraph)
            print coloring

            spill = toSpill(coloring)

            print "STACK SIZE"
            print len(spill)
            tmp = Var("#tmp")
            vars.add(tmp)

            good,IR,newVars,check = allocateRegisters(spill,liveness,vars,coloring,[],[],True)
            
            
            print
            
                #for g in good:
                #print g
            
            for b in IR:
                print b

            print check

        filename = ""
        prev = sys.argv[1].split('.')[0]
        for k in sys.argv[1].split('.')[1:]:
            filename += prev
            prev = "."+k

        outputCode(good,len(spill),filename)
        '''
#OUTPUT CODE
    if(runCode):
        
        varMap={}
        uniqueAST = uniquify(startAST,varMap)
     
        
        explicateAST = explicate(uniqueAST)
        
        heapifiedAST,heaplist = heapify1.heapify(explicateAST,set([]))
        
        
        
        closure,defs = create_closure(heapifiedAST)

        flatMain = flattenNJ.flatten(closure)

        funcs = []
        for d in defs:
            funcs.append(flattenNJ.flatten(d))

        create_main = convertMain(flatMain)

        
        IR,vars = x86IR.generateInstructions(create_main)

        funcList = [('main',IR,vars)]
        for f in funcs:
            func1,vars1 = x86IR.generateInstructions(f)
            funcList.append((f.name,func1,vars1))


        check = False
        newFuncList = funcList
        funcsOutput = []
        while not check:
            check = True
            
            funcList = newFuncList
            newFuncList = []
            for n in funcList:
                vars = n[2]
                name = n[0]
                IR = n[1]
                instrLive = []
                liveAfter = set([])
                liveness = livenessAnalysis(IR,instrLive,liveAfter)
                iGraph = interferenceGraph(liveness,vars)
                coloring = graphColor(iGraph)
                spill = toSpill(coloring)
                tmp = Var("#tmp")
                vars.add(tmp)

                good,IR,newVars,check_func = allocateRegisters(spill,liveness,vars,coloring,[],[],True)
                if check_func:
                    funcsOutput.append((name,good,len(spill)))
                else:
                    check = False
                    newFuncList.append((name,IR,vars))

        filename = ""
        prev = sys.argv[1].split('.')[0]
        for k in sys.argv[1].split('.')[1:]:
            filename += prev
            prev = "."+k

        outputCode(funcsOutput,filename)
    
    '''
        for i in liveness:
            if isinstance(i,If):
                tests = i.tests
                else_ = i.else_
                for e in else_:
                    print e.liveBefore
                    print e.liveAfter
                for test in tests:
                    print test[0].liveBefore
                    print test[0].liveAfter
                    for t in test[0]:
                        print t.liveBefore
                        print t.liveAfter
                print
            else:
                print i.liveBefore
                print i.liveAfter
                print
    '''
    '''
    
        counter = -4
        varmap = {}
        for v in vars:
            varmap[v] = counter
            counter -= 4

        print varmap
        done = False
        totalIter = 0
        tmp = 0
        
        filename = ""
        prev = sys.argv[1].split('.')[0]
        for k in sys.argv[1].split('.')[1:]:
        	filename += prev
        	prev = "."+k
    	
        outputCode(IR,len(vars),filename,varmap) # change these values
    '''
    #OUTPUT CODE
    '''
    IR,vars = generateInstructions(flat)

    counter = -4
    varmap = {}
    for v in vars:
        varmap[v] = counter
        counter -= 4


    done = False
    totalIter = 0
    tmp = 0
        
    filename = ""
    prev = sys.argv[1].split('.')[0]
    for k in sys.argv[1].split('.')[1:]:
        filename += prev
        prev = "."+k

    outputCode(IR,len(vars),filename,varmap)
    '''




