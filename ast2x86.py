from compiler.ast import *

def generateX86(astlist,filename,varmap):
    preamble = ".globl main\nmain:\n\tpushl %ebp\n\tmovl %esp, %ebp\n\t"
    postemble = 'movl $0, %eax\n\tleave\n\tret\n'
    stackspace = "subl $" + str(len(varmap)*4)+",%esp\n\n\t"

    assemblyCode = preamble
    assemblyCode += stackspace

    for tree in astlist:
        if isinstance(tree,Assign):
            if isinstance(tree.expr,CallFunc):
                destination = str(varmap[tree.nodes[0].name])
                assemblyCode += "call input\n\tmovl %eax, "+destination+"(%ebp)\n\n\t"
            elif isinstance(tree.expr,Const):
                destination = str(varmap[tree.nodes[0].name])
                value = str(tree.expr.value)
                assemblyCode += "movl $"+value+", "+destination+"(%ebp)\n\n\t"
            elif isinstance(tree.expr,Name):
                destination = str(varmap[tree.nodes[0].name])
                source = str(varmap[tree.expr.name])
                assemblyCode += "movl "+source+"(%ebp), %eax\n\t"
                assemblyCode += "movl %eax, "+destination+"(%ebp)\n\n\t"
                #print destination
                #print source
                #print "movl "+source+"(%ebp), "+destination+"(%ebp)\n\t"
                #assemblyCode += "movl "+source+"(%ebp), "+destination+"(%ebp)\n\t"
                    
            elif isinstance(tree.expr,UnarySub):
                if isinstance(tree.expr.expr,Name):
                    source = str(varmap[tree.expr.expr.name])
                    assemblyCode += "movl "+source+"(%ebp), %eax\n\t"
                    destination = str(varmap[tree.nodes[0].name])
                    assemblyCode += "movl %eax, "+destination+"(%ebp)\n\t"
                    assemblyCode += "negl "+destination+"(%ebp)\n\n\t"
                elif isinstance(tree.expr.expr,Const):
                    value = str(tree.expr.expr.value)
                    destination = str(varmap[tree.nodes[0].name])
                    assemblyCode += "movl $"+value+", "+destination+"(%ebp)\n\t"
                    assemblyCode += "negl "+destination+"(%ebp)\n\n\t"
            elif isinstance(tree.expr,Add):
                destination = str(varmap[tree.nodes[0].name])
                if isinstance(tree.expr.left,Name):
                    source = str(varmap[tree.expr.left.name])
                    assemblyCode += "movl "+source+"(%ebp), %eax\n\t"
                    assemblyCode += "movl %eax, "+destination+"(%ebp)\n\t"
                elif isinstance(tree.expr.left,Const):
                    value = str(tree.expr.left.value)
                    assemblyCode += "movl $"+value+", "+destination+"(%ebp)\n\t"
                if isinstance(tree.expr.right,Name):
                    source = str(varmap[tree.expr.right.name])
                    assemblyCode += "movl "+source+"(%ebp), %eax\n\t"
                    assemblyCode += "addl %eax, "+destination+"(%ebp)\n\n\t"
                elif isinstance(tree.expr.right,Const):
                    value = str(tree.expr.right.value)
                    assemblyCode += "addl $"+value+", "+destination+"(%ebp)\n\n\t"

        elif isinstance(tree,Printnl):
            if isinstance(tree.nodes[0],Name):
                #print "here"
                #print tree.nodes
                source = str(varmap[tree.nodes[0].name])
                assemblyCode += "pushl "+source+"(%ebp)\n\tcall print_int_nl\n\taddl $4, %esp\n\n\t"
            elif isinstance(tree.nodes[0],Const):
                value = str(tree.nodes[0].value)
                assemblyCode += "pushl $"+value+"\n\tcall print_int_nl\n\taddl $4, %esp\n\n\t"

    assemblyCode += postemble

    targetfile = open(filename+".s", "w")
    targetfile.truncate()
    targetfile.write(assemblyCode)
    targetfile.close()
