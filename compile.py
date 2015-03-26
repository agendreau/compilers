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


# python compile.py example1.py
# $gcc -m32 *.c example1.s -o test.exe -lm
# ./text.exe
# cat test.in | -l test.exe



if __name__ == '__main__':
    startAST = compiler.parseFile(sys.argv[1])
    
    #explicator = explicateVisitor()
    
    #explicateAST = explicator.walk(startAST)
    
    explicateAST = explicate(startAST)
    

    
    debug = 0
    
    
    registerTest = 0
    
    flat = []
    if (debug):
        
        print "STARTAST:"
        print startAST , "\n"
        
        print "EXPLICATE_AST:"
        print explicateAST
        print 
        for x in explicateAST.node.nodes:
            print x
        
        print "\nTYPE CHECKER OUTPUT:"
        #tchecker = typecheckVisitor()
        #tchecker.walk(explicateAST)


        print "flattening"
        flatast = flattenNJ.flatten(explicateAST)
        #print flatast
        print "done flattening"
        print "FLAT AST"
        for n in flatast:
            print n
    



    

    
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

    explicateAST = explicate(startAST)

    flatast = flattenNJ.flatten(explicateAST)
    IR,vars = x86IR.generateInstructions(flatast)

    check = False
    while not check:
        instrLive = []

        liveAfter = set([])
            
        liveness = livenessAnalysis(IR,instrLive,liveAfter)
        iGraph = interferenceGraph(liveness,vars)
        
        
        coloring = graphColor(iGraph)

        spill = toSpill(coloring)
        tmp = Var("#tmp")
        vars.add(tmp)
        good,IR,vars,check = allocateRegisters(spill,liveness,vars,coloring,[],[],True)
#print check

    filename = ""
    prev = sys.argv[1].split('.')[0]
    for k in sys.argv[1].split('.')[1:]:
        filename += prev
        prev = "."+k

    outputCode(good,len(spill),filename)
    
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



