from compiler.ast import *
from x86Nodes import *
from x86IR import *
from collections import defaultdict
import heapq
from explicateNodes import *

REMOVED = '<removed-task>'


class updatePriorityQueue:
    def __init__(self):
        self.pq = []
        self.entry_finder = {}
        #self.counter = itertools.count()

    def add_task(self,task, count, priority=0): #use count to mark spill variables?
        #Add a new task or update the priority of an existing task'
        if task in self.entry_finder:
            self.remove_task(task)
        #count = next(counter)
        #print isinstance(task,Var)
        entry = [priority, count, task]
        self.entry_finder[task] = entry
        heapq.heappush(self.pq, entry)

    def remove_task(self,task):
        #'Mark an existing task as REMOVED.  Raise KeyError if not found.'
        entry = self.entry_finder.pop(task)
        entry[-1] = Var(REMOVED)

    def pop_task(self):
        #'Remove and return the lowest priority task. Raise KeyError if empty.'
        while self.pq:
            priority, count, task = heapq.heappop(self.pq)
            if task != Var(REMOVED):
                del self.entry_finder[task]
                return task
        raise KeyError('pop from an empty priority queue')


def livenessAnalysis(oldList,liveSet,liveAfter):
    if len(oldList)==0:
        return liveSet
    else:
        i = oldList[-1]
        #print "new instruction"
        #print i
        if isinstance(i,AddL) or isinstance(i,orL) or isinstance(i,andL) or isinstance(i,CmpL):
            if isinstance(i.left,Var) and isinstance(i.right,Var):
                i.liveBefore = (liveAfter|set([i.left,i.right]))
            elif isinstance(i.left,Var):
                i.liveBefore = liveAfter | set([i.left])
            elif isinstance(i.right,Var):
                i.liveBefore = liveAfter | set([i.right])
            else:
                i.liveBefore = liveAfter
            i.liveAfter = liveAfter
            return livenessAnalysis(oldList[:-1],[i]+liveSet,i.liveBefore)

        elif isinstance(i,MovL) or isinstance(i,MovZBL) or isinstance(i,sArl) or isinstance(i,sAll):
            if isinstance(i.left,Var):
                i.liveBefore= (liveAfter-set([i.right]))|set([i.left])
                
            else:
                i.liveBefore = (liveAfter-set([i.right]))
            i.liveAfter = liveAfter
            return livenessAnalysis(oldList[:-1],[i]+liveSet,i.liveBefore)

        elif isinstance(i,NegL) or isinstance(i,notL):
            i.liveBefore = liveAfter
            i.liveAfter = liveAfter
            return livenessAnalysis(oldList[:-1],[i]+liveSet,i.liveBefore)
            
        elif isinstance(i,Push) or isinstance(i,CallStar):
            i.liveAfter = liveAfter
            if isinstance(i,Push) and isinstance(i.argument,Var):
                i.liveBefore = (liveAfter)|set([i.argument])
            elif isinstance(i,CallStar) and isinstance(i.funcName,Var):
                i.liveBefore = (liveAfter)|set([i.funcName])
            else:
                i.liveBefore = (liveAfter)

            return livenessAnalysis(oldList[:-1],[i]+liveSet,i.liveBefore)

        elif isinstance(i,Call) or isinstance(i,Jmp) or isinstance(i,Label) or isinstance(i,Pop):
            i.liveBefore = liveAfter
            i.liveAfter = liveAfter
            return livenessAnalysis(oldList[:-1],[i]+liveSet,i.liveBefore)
            
        elif isinstance(i,SetNode):
            i.liveAfter = liveAfter
            if isinstance(i.argument,Var):
                i.liveBefore = liveAfter | set([i.argument])
            else:
                i.liveBefore = liveAfter

            return livenessAnalysis(oldList[:-1],[i]+liveSet,i.liveBefore)

        elif isinstance(i,If):
            tests = i.tests
            else_ = i.else_
            '''
            print "LIVE AFTER"
            print liveAfter
            print "LIVE SET"
            print liveSet
            '''
            #for e in else_:
            livenessElse = livenessAnalysis(else_,[],liveAfter)
            #print livenessElse
            preElseLive = livenessElse[0].liveBefore
            #print livenessElse
            #preElseLive = livenessElse[0]
            #liveSet = livenessElse[:-1] + liveSet
            liveIf = []
            preIfsLive = set([])
            for t in tests:
                #print "if live after"
                #print liveAfter
                livenessIfs = livenessAnalysis(t[1],[],liveAfter)
                #printlivenessIfs
                guard = t[0]
                guard.liveBefore = liveAfter
                guard.liveAfter = livenessIfs[0].liveBefore
                newStmt = (guard,livenessIfs)
                #print guard
                #printnewStmt
                preIfsLive = preIfsLive | livenessIfs[0].liveBefore | set([guard.right])
                liveIf = [newStmt]+liveIf
                #printliveIf
                #liveSet[0] = liveSet[0]|liveAfter #hack
                #liveSet = livenessIfs[:-1] + liveSet

            #liveBefore = preElseLive | preIfsLive
            liveIf[0][0].liveBefore = preIfsLive | preElseLive
            newIf = If(liveIf,livenessElse)
            
#print


            return livenessAnalysis(oldList[:-1],[newIf]+liveSet,liveIf[0][0].liveBefore)
                
        else:
            return "Error in computing live point"

def total(instructionList): #count line for if statements
    t = 0
    for i in instructionList:
        if isinstance(i,If):
            for n in i.tests:
                t += 1 + len(n[1])
            t += len(i.else_)
        
        else:
            t += 1
    return t

def interferenceGraph(instructionList,variables):
    #totalVariables = 10 #hack for working example
    #totalVariables = [Var('w'),Var('x'),Var('y'),Var('z'),Var('$tmp0'),Var('$tmp1'),Var('$tmp2')]
    interference = {k: set([]) for k in variables}
    interference[Register("%eax")] = set([Register("%al")])
    interference[Register("%ecx")] = set([Register("%cl")])
    interference[Register("%edx")] = set([])
    interference[Register("%al")] = set([Register("eax")])
    interference[Register("%cl")] = set([Register("ecx")])
    return interferencePoint(instructionList,interference,variables)


def interferencePoint(instructionList,interference,vars):
    #print i
    edges = set([])
    #print edges
    if len(instructionList) == 0:
        return interference
    else:
        i = instructionList[0]
        #printi
        #print i.liveAfter
        if isinstance(i,MovL):
            s = i.left
            t = i.right
            
            if isinstance(s,Var) and isinstance(t,Var):
                
                for v in i.liveAfter:
                    if v!=t and v!=s:
                        interference[t].add(v)
                        interference[v].add(t)
                        #edges.add((t,v))
            else:
                for v in i.liveAfter:
                    if v!=t:
                        print i
                        interference[v].add(t)
                        interference[t].add(v)

        elif isinstance(i,AddL) and isinstance(i.right,Var) or \
            isinstance(i,MovZBL) and isinstance(i.right,Var) or \
            isinstance(i,sAll) and isinstance(i.right,Var) or \
            isinstance(i,sArl) and isinstance(i.right,Var) or \
            isinstance(i,orL) and isinstance(i.right,Var) or \
            isinstance(i,andL) and isinstance(i.right,Var):
            t = i.right
            for v in i.liveAfter:
                if v!=t:
                    interference[v].add(t)
                    interference[t].add(v)
        
        elif (isinstance(i,NegL) or isinstance(i,notL)) and isinstance(i.value,Var):
            t = i.value
            for v in i.liveAfter:
                if v!=t:
                    interference[v].add(t)
                    interference[t].add(v)

        elif isinstance(i,SetNode) and isinstance(i.argument,Var):
            t = i.argument
            for v in i.liveAfter:
                if v!=t:
                    interference[v].add(t)
                    interference[t].add(v)


        elif isinstance(i,Call) or isinstance(i,CallStar):
            for v in i.liveAfter:
                interference[v].add(Register("%eax"))
                interference[v].add(Register("%al"))
                interference[Register("%eax")].add(v)
                interference[Register("%al")].add(v)
                interference[v].add(Register("%ecx"))
                interference[v].add(Register("%cl"))
                interference[Register("%ecx")].add(v)
                interference[Register("%cl")].add(v)
                interference[v].add(Register("%edx"))

        elif isinstance(i,CmpL):
            l = i.left
            r = i.right
            for v in i.liveAfter:
                interference[v].add(Register("%eax"))
                interference[v].add(Register("%al"))
                interference[Register("%eax")].add(v)
                interference[Register("%al")].add(v)
                interference[v].add(Register("%ecx"))
                interference[v].add(Register("%cl"))
                interference[Register("%ecx")].add(v)
                interference[Register("%cl")].add(v)
                '''
                interference[r].add(v)
                interference[v].add(r)
                '''
            if isinstance(r,Var):
                interference[r].add(Register("%eax"))
                interference[r].add(Register("%al"))
                interference[Register("%eax")].add(r)
                interference[Register("%al")].add(r)
                interference[r].add(Register("%ecx"))
                interference[r].add(Register("%cl"))
                interference[Register("%ecx")].add(r)
                interference[Register("%cl")].add(r)

            #elif isinstance

        elif isinstance(i,If):
            #print "HERE"
            tests = i.tests
            else_ = i.else_
            
            interIf = {k: set([]) for k in vars}
            interIf[Register("%eax")] = set([Register("%al")])
            interIf[Register("%ecx")] = set([Register("%cl")])
            interIf[Register("%edx")] = set([])
            interIf[Register("%al")] = set([Register("eax")])
            interIf[Register("%cl")] = set([Register("ecx")])
            
            newInstr = []
            for t in tests:
                newInstr.append(t[0])
                newInstr.extend(t[1])
            
            newInstr.extend(else_)
            

            ifGraph = interferencePoint(newInstr,interIf,vars)
            #print ifGraph
            for (k,v) in ifGraph.iteritems():
                #print "key: " + str(k)
                #print "value: " + str(v)
                #print isinstance(v,set)
                interference[k] = interference[k] | v
            

        #else:
            # print "Error in constructing interference graph"
            # return

        return interferencePoint(instructionList[1:],interference,vars)


def graphColor(interferenceGraph):
    vertices = set(interferenceGraph.keys())
    
    vertices.remove(Register("%eax"))
    vertices.remove(Register("%ecx"))
    vertices.remove(Register("%edx"))
    vertices.remove(Register("%al"))
    vertices.remove(Register("%cl"))
    
    #adjust node saturation, use heapq, make sure higher priority, return negative of the number
    coloring = defaultdict(int)
    coloring[Register("%eax")]=1
    coloring[Register("%ebx")]=2
    coloring[Register("%ecx")]=3
    coloring[Register("%edx")]=4
    coloring[Register("%esi")]=5
    coloring[Register("%edi")]=6
    #print coloring[Register("%eax")]
    
    
    sat,color_neighbors,count,countTmp = saturation(vertices,interferenceGraph,coloring)
    #print
    while len(vertices) > 0:
        toColor = sat.pop_task()
        varC = toColor
        color_n = color_neighbors[varC]
        #print varC
        if len(color_n)>0:
            color = findColor(color_n)
        else:
            color = 1
        coloring[varC]=color
        #print varC
        vertices.remove(varC)
        adj = interferenceGraph[varC]
        for n in adj:
            if n in vertices:
                heapq.heappush(color_neighbors[n],color)
                newSat = len(color_neighbors[n])
                if n.name[0]=="#":
                    sat.add_task(n,count,-newSat)
                    countTmp = countTmp-1
                else:
                    sat.add_task(n,count,-newSat)
                    count = count+1
        
        
        #sat = saturation(vertices,interferenceGraph,coloring)

    return coloring

def findColor(colors): #this is fine
    total = len(colors)
    if total==1:
        if heapq.heappop(colors) > 1:
            return 1
        else:
            return 2
    else:
        lo = heapq.heappop(colors)
        for c in range(total-1):
            hi = heapq.heappop(colors)
            if hi-lo > 1:
                return lo+1
            else:
                lo = hi
        return lo+1


def saturation(vertices,interferenceGraph,coloring):
    count = 1;
    countTmp = -1
    initSat = updatePriorityQueue()
    initColors = {}
    for v in vertices:
        adj = interferenceGraph[v]
        sat = 0
        colors = []
        for n in adj:
            #   print coloring[n]
            if coloring[n]>0:
                sat = sat+1
                heapq.heappush(colors,coloring[n])
    
        initColors[v] = colors
    #print "sat" +str(sat)
    #   print colors
    #print v
    
    #print v
        print v
        if v.name[0] == "#":
            initSat.add_task(v,-sat,countTmp)
            countTmp = countTmp-1
        else:
            initSat.add_task(v,-sat,count)
            count = count+1
#print initSat
#print initSat

    return initSat,initColors,count,countTmp

def toSpill(coloring):
    list = {}
    stackLocal = -4
    for k in coloring.iterkeys():
        if coloring[k]>6:
            list[k]=stackLocal
            stackLocal = stackLocal-4
    return list

def allocateRegisters(toSpill,instructionList,variables,coloring,good,bad,check):

    colorMap = {}
    colorMap[1] = Register("%eax")
    colorMap[2] = Register("%ebx")
    colorMap[3] = Register("%ecx")
    colorMap[4] = Register("%edx")
    colorMap[5] = Register("%esi")
    colorMap[6] = Register("%edi")
    #check = True
    #toSpillVar = toSpill.keys()
    #good = []
    #bad = []
    tmp = Var("#tmp")
    

    if len(instructionList) == 0:
        return (good,bad,variables,check)

    else:
        i = instructionList[0]
        print i
        if isinstance(i,AddL):
            regl = i.left
            regr = i.right
            localR = toSpill.has_key(regr)
            if isinstance(regr,Register):
                good.append(i)
                bad.append(i)
                return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)
            elif isinstance(regl,Con):
                if localR:
                    goodNode = AddL((regl,Address(toSpill[regr])))
                else:
                    #print regr
                    goodNode = AddL((regl,Register(colorMap[coloring[regr]])))
                good.append(goodNode)
                bad.append(i)
                return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)
                
            else:
                localL = toSpill.has_key(regl)
            
                if localL and localR:
                    check = False
                    badNodeMove = MovL((regl,tmp))
                    badNodeAdd = AddL((tmp,regr))
                    bad.extend([badNodeMove,badNodeAdd])
                    good.append(i)
                    return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)
                    #return (i,[badNodeMove,badNodeAdd])
                    #totalTmp+=1
                    #newVars.add(tmp)
                    #print "BAD VAR"
                    #print i
                else:
                    if localL:
                        goodNode = AddL((Address(toSpill[regl]),Register(colorMap[coloring[regr]])))
                
                    elif localR:
                        goodNode = AddL((Register(colorMap[coloring[regl]]),Address(toSpill[regr])))
                   
                    else:
                        goodNode = AddL((Register(colorMap[coloring[regl]]),Register(colorMap[coloring[regr]])))
                    good.append(goodNode)
                    bad.append(i)
                    return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)

        elif isinstance(i,andL):
            regl = i.left
            regr = i.right
            localR = toSpill.has_key(regr)
            if isinstance(regr,Register):
                good.append(i)
                bad.append(i)
                return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)
            elif isinstance(regl,Con):
                if localR:
                    goodNode = andL((regl,Address(toSpill[regr])))
                else:
                    #print regr
                    goodNode = andL((regl,Register(colorMap[coloring[regr]])))
                good.append(goodNode)
                bad.append(i)
                return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)

            else:
                localL = toSpill.has_key(regl)
            
                if localL and localR:
                    check = False
                    badNodeMove = MovL((regl,tmp))
                    badNodeAdd = andL((tmp,regr))
                    bad.extend([badNodeMove,badNodeAdd])
                    good.append(i)
                    return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)
                #totalTmp+=1
                #newVars.add(tmp)
                #print "BAD VAR"
                #print i
                else:
                    if localL:
                        goodNode = andL((Address(toSpill[regl]),Register(colorMap[coloring[regr]])))
                    
                    elif localR:
                        goodNode = andL((Register(colorMap[coloring[regl]]),Address(toSpill[regr])))
                    
                    else:
                        goodNode = andL((Register(colorMap[coloring[regl]]),Register(colorMap[coloring[regr]])))
                    
                    good.append(goodNode)
                    bad.append(i)
                    
                    return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)
                        
        elif isinstance(i,orL):
            regl = i.left
            regr = i.right
            localR = toSpill.has_key(regr)
            if isinstance(regr,Register):
                good.append(i)
                bad.append(i)
                return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)
            elif isinstance(regl,Con):
                if localR:
                    goodNode = orL((regl,Address(toSpill[regr])))
                else:
                    #print regr
                    goodNode = orL((regl,Register(colorMap[coloring[regr]])))
                good.append(goodNode)
                bad.append(i)
                return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)
            else:
                localL = toSpill.has_key(regl)
                if localL and localR:
                    check = False
                    badNodeMove = MovL((regl,tmp))
                    badNodeAdd = orL((tmp,regr))
                    bad.extend([badNodeMove,badNodeAdd])
                    good.append(i)
                    return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)
                #totalTmp+=1
                #newVars.add(tmp)
                #print "BAD VAR"
                #print i
                else:
                    if localL:
                        goodNode = orL((Address(toSpill[regl]),Register(colorMap[coloring[regr]])))
                    elif localR:
                        goodNode = orL((Register(colorMap[coloring[regl]]),Address(toSpill[regr])))
                    else:
                        goodNode = orL((Register(colorMap[coloring[regl]]),Register(colorMap[coloring[regr]])))
                    good.append(goodNode)
                    bad.append(i)
    
                    return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)

        elif isinstance(i,MovZBL):
            regl = i.left
            regr = i.right
            localR = toSpill.has_key(regr)
            if isinstance(regr,Register):
                good.append(i)
                bad.append(i)
                return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)
            elif isinstance(regl,Con) or isinstance(regl,Register):
                if localR:
                    check = False
                    badNodeMove = MovL((regr,tmp))
                    badNodeAdd = MovZBL((regl,tmp)) #cause liveness issues?
                    bad.extend([badNodeMove,badNodeAdd])
                    good.append(i)
                    return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)
               
                else:
                    #print regr
                    goodNode = MovZBL((regl,Register(colorMap[coloring[regr]])))
                    good.append(goodNode)
                    bad.append(i)
                    return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)
            

        elif isinstance(i,MovL):
            #print i
            regl = i.left
            regr = i.right
            localR = toSpill.has_key(regr)
            if isinstance(regl,Con) or isinstance(regl,Address):
                if localR:
                    goodNode = MovL((regl,Address(toSpill[regr])))
                else:
                    goodNode = MovL((regl,Register(colorMap[coloring[regr]])))
                good.append(goodNode)
                bad.append(i)
                return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)
        
            else:
                localL = toSpill.has_key(regl)
                if localL and localR:
                    check = False
                    badNodeMove = MovL((regl,tmp))
                    badNodeAdd = MovL((tmp,regr))
                    good.append(i)
                    bad.extend([badNodeMove,badNodeAdd])
                    return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)
                else:
                    if localL:
                        goodNode = MovL((Address(toSpill[regl]),Register(colorMap[coloring[regr]])))
                        good.append(goodNode)
                        bad.append(i)
                        return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)
                                      
                    elif localR:
                        goodNode = MovL((Register(colorMap[coloring[regl]]),Address(toSpill[regr])))
                        good.append(goodNode)
                        bad.append(i)
                        return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)
                    
                    else:
                        goodNode = MovL((Register(colorMap[coloring[regl]]),Register(colorMap[coloring[regr]])))
                        if goodNode.left != goodNode.right:
                            good.append(goodNode)
                            bad.append(i)
                            return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)
                        else:
                            bad.append(i)
                            return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)
                   
                                       
        elif isinstance(i,NegL):
            value = i.value
            goodNode = i
            if isinstance(value,Var):
                local = toSpill.has_key(value)
                if local:
                    goodNode = NegL(Address(toSpill[value]))
                else:
                    goodNode = NegL(Register(colorMap[coloring[value]]))
            good.append(goodNode)
            bad.append(i)
            return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)
        elif isinstance(i,notL):
            value = i.value
            goodNode = i
            if isinstance(value,Var):
                local = toSpill.has_key(value)
                if local:
                    goodNode = notL(Address(toSpill[value]))
                else:
                    goodNode = notL(Register(colorMap[coloring[value]]))
            good.append(goodNode)
            bad.append(i)
            return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)



        elif isinstance(i,Call) or isinstance(i,SetNode) or isinstance(i,Jmp) or isinstance(i,Label) or isinstance(i,Pop):
            good.append(i)
            bad.append(i)
            return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)

        elif isinstance(i,CallStar):
            bad.append(i)
            local = toSpill.has_key(i.funcName)
            if local:
                goodNode = CallStar(Address(toSpill[i.funcName]))
            else:
                goodNode = CallStar(Register(colorMap[coloring[i.funcName]]))
            good.append(goodNode)
            return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)

        elif isinstance(i,sAll):
            local = toSpill.has_key(i.right)
            if local:
                goodNode = sAll((i.left,Address(toSpill[i.right])))
            else:
                goodNode = sAll((i.left,Register(colorMap[coloring[i.right]])))
            good.append(goodNode)
            bad.append(i)
            return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)

        elif isinstance(i,sArl):
            local = toSpill.has_key(i.right)
            if local:
                goodNode = sArl((i.left,Address(toSpill[i.right])))
            else:
                goodNode = sArl((i.left,Register(colorMap[coloring[i.right]])))
            good.append(goodNode)
            bad.append(i)
            return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)

        elif isinstance(i,Push):
            #print "found push"
            #print i
            value = i.argument
            goodNode = i
            if isinstance(value,Var):
                local = toSpill.has_key(value)
                if local:
                    goodNode = Push(Address(toSpill[value]))
                else:
                    goodNode = Push(Register(colorMap[coloring[value]]))
            good.append(goodNode)
            bad.append(i)
            return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)

        elif isinstance(i,CmpL):
            regl = i.left
            regr = i.right
            localR = toSpill.has_key(regr)
            if isinstance(regr,Register):
                good.append(i)
                bad.append(i)
                return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)
            elif isinstance(regl,Con):
                if localR:
                    goodNode = CmpL((regl,Address(toSpill[regr])))
                else:
                    #print regr
                    goodNode = CmpL((regl,Register(colorMap[coloring[regr]])))
                good.append(goodNode)
                bad.append(i)
                return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)
            
            elif isinstance(regr,Con):
                goodNode = CmpL((Register(colorMap[coloring[regl]]),regr))
                good.append(goodNode)
                bad.append(i)
                return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)

            else:
                localL = toSpill.has_key(regl)
                
                if localL and localR:
                    check = False
                    badNodeMove = MovL((regl,tmp))
                    badNodeAdd = CmpL((tmp,regr))
                    bad.extend([badNodeMove,badNodeAdd])
                    good.append(goodNode)
                    return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)
                #totalTmp+=1
                #newVars.add(tmp)
                #print "BAD VAR"
                #print i
                else:
                    if localL:
                        goodNode = CmpL((Address(toSpill[regl]),Register(colorMap[coloring[regr]])))
                    
                    elif localR:
                        goodNode = CmpL((Register(colorMap[coloring[regl]]),Address(toSpill[regr])))
                    
                    else:
                        goodNode = CmpL((Register(colorMap[coloring[regl]]),Register(colorMap[coloring[regr]])))
                    good.append(goodNode)
                    bad.append(i)
    
                    return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)

        elif isinstance(i,If):
            tests = i.tests
            else_ = i.else_
            goodElse,badElse,newVars,elsecheck = allocateRegisters(toSpill,else_,variables,coloring,[],[],check) #not true, but check
            goodIf = []
            badIf = []
            ifcheck = True
            for t in tests:
                goodI,badI,newVars,check = allocateRegisters(toSpill,[t[0]]+t[1],variables,coloring,[],[],check)
                goodIf.append((goodI[0],goodI[1:]))
                badIf.append((badI[0],badI[1:]))
                if not check:
                    ifcheck = False
            goodNode = If(goodIf,goodElse)
            badNode = If(badIf,badElse)
            good.append(goodNode)
            bad.append(badNode)
      
            newCheck = elsecheck and ifcheck
            #print newCheck
            if not newCheck:
                check = False
        
            return allocateRegisters(toSpill,instructionList[1:],variables,coloring,good,bad,check)





#generate everything, then check if anything is violated
#map of colors to registers
#for each instruction check if it will cause memory to memory operation
#otherwise allocate stack slot and color -1
#if it does generate tmp intstruction and rerun

'''
    def interferencePoint(instr,liveAfter,interference):
    programPoint = 1
    for i in instructionList:
    liveAfter = livenessSet[programPoint]
    if isinstance(i,MovL):
    s = i.left
    t = i.right
    
    if isinstance(s,Var) and isinstance(t,Var):
    
    for v in liveAfter:
    if v!=t and v!=s:
    interference[v].add(t)
    interference[t].add(v)
    
    else:
    for v in liveAfter:
    if v!=t:
    interference[v].add(t)
    interference[t].add(v)
    
    
    elif isinstance(i,AddL) and isinstance(i.right,Var):
    t = i.right
    for v in liveAfter:
    if v!=t:
    interference[v].add(t)
    interference[t].add(v)
    
    elif isinstance(i,NegL) and isinstance(i.value,Var):
    t = i.value
    for v in liveAfter:
    if v!=t:
    interference[v].add(t)
    interference[t].add(v)
    
    elif isinstance(i,Call):
    for v in liveAfter:
    interference[v].add(Register("%eax"))
    interference[v].add(Register("%ecx"))
    interference[v].add(Register("%edx"))
    
    
    interference[Register("%eax")].add(v)
    interference[Register("%ecx")].add(v)
    interference[Register("%edx")].add(v)
    
    programPoint=programPoint+1
    #print interference
    return interference
    
    for i in instructionList:
    if isinstance(i,If):
    print "here"
    tests = i.tests
    pairG = []
    pairB = []
    elseG = []
    elseB = []
    
    else_ = i.else_
    for t in tests:
    instG = []
    instB = []
    for stmt in t[1]:
    print stmt
    if isinstance(stmt,If):
    
    newinstr = [stmt]
    (goodI,badI,newVarsIf,check) = allocateRegisters(toSpill,newinstr,variables,coloring)
    done = check
    newVars = newVars | newVarsIf
    good.extend(goodI)
    bad.extend(badI)
    else:
    
    (goodI,badI) = allocateInstruction(toSpill,stmt,variables,coloring,colorMap)
    if len(badI)>1:
    check = False
    instG.append(goodI)
    instB.extend(badI)
    if isinstance(t[0].left,Var) and isinstance(t[0].right,Var):
    pairG.append((CmpL((colorMap[coloring[t[0].left]],
    colorMap[coloring[t[0].right]])),instG))
    elif isinstance(t[0].right,Var):
    pairG.append((CmpL((t[0].left,colorMap[coloring[t[0].right]])),instG))
    elif isinstance(t[0].left,Var):
    pairG.append((CmpL((colorMap[coloring[t[0].left]],t[0].left)),instG))
    else:
    pairG.append((CmpL((t[0].left,t[1].right)),instG))
    pairB.append((t[0],instB))
    for e in else_:
    (goodI,badI) = allocateInstruction(toSpill,stmt,variables,coloring,colorMap)
    if len(badI)>1:
    check = False
    elseG.append(goodI)
    elseB.extend(badI)
    
    good.append(IfNode(pairG,elseG))
    bad.append(IfNode(pairB,elseB))
    
    else:
    (goodI,badI) = allocateInstruction(toSpill,i,variables,coloring,colorMap)
    
    if len(badI)>1:
    check = False
    
    good.append(goodI)
    bad.extend(badI)
    
    return good,bad,newVars,check
'''


