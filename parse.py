from compiler.ast import Module,Stmt,Printnl, Assign, AssName, Const, Name, Add, UnarySub, CallFunc, Discard

reserved = { #our small set of keywords for P0
    'print' : 'PRINT'
#'input' : 'INPUT' #this probably shouldn't be a reserved word, only if it is followed by parens
}

tokens = [
          'NAME','INT',
          'PLUS','MINUS','EQUALS',
          'LPAREN','RPAREN','INPUT'
          ] + list(reserved.values())

# Tokens


t_PLUS    = r'\+'
t_MINUS   = r'-'
t_EQUALS  = r'='
t_LPAREN  = r'\('
t_RPAREN  = r'\)'

def t_BACKSLASH(t):
    r'\\'


def t_INPUT(t):
    r'input[ \t]*\([ \t\v\r\n]*\)'
    t.value = 'input'
    return t

def t_NAME(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value,'NAME')    # Check for reserved words
    #print "name: " + str(t.lexer.lineno)
    #print t
    return t

def t_INT(t):
    r'\d+'
    try:
        t.value = int(t.value)
    except ValueError:
        print("Integer value too large %d", t.value)
        t.value = 0
    return t

def t_COMMENT(t): #am I handling comments correctly?
    r'\#.*'

# Ignored characters
t_ignore = " \t\v\r"

def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")

def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

# Build the lexer
import ply.lex as lex
lex.lex()

# Parsing rules

precedence = (
    ('nonassoc','PRINT'),
    ('left','PLUS','MINUS'),
    ('right','UMINUS'),
    )


#Program and Module

def p_program(t):
    '''program : 
        | module'''
    if(len(t)==1):
        t[0] = Module(None,Stmt([]))
    else:
        t[0] = Module(None, t[1])

def p_module(t):
    '''module : statement 
        | statement module'''
    if(len(t)>2):
        list = t[2].nodes
        t[0] = Stmt([t[1]] + t[2].nodes)
    else:
        t[0] = Stmt([t[1]])

#STATEMENTS

def p_print_statement(t):
    'statement : PRINT expression'
    t[0] = Printnl([t[2]], None)

def p_statement_assign(t):
    '''statement : NAME EQUALS expression 
        | INPUT EQUALS expression '''
    t[0] = Assign([AssName(t[1],'OP_ASSIGN')],t[3])

def p_statement_expr(t):
    'statement : expression'
    t[0] = Discard(t[1])


#EXPRESSIONS

def p_plus_expression(t):
    'expression : expression MINUS INT'
    t[0] = Add((t[1],t[3]))

def p_int_expression(t):
    'expression : INT'
    t[0] = Const(t[1])

def p_expression_uminus(t):
    'expression : MINUS expression %prec UMINUS'
    t[0] = UnarySub(t[2])

def p_name_expression(t):
    'expression : NAME'
    t[0] = Name(t[1])

def p_input_expression(t):
    'expression : INPUT'
    t[0] = CallFunc(Name(t[1]),[])

#def p_name_expression(t):
#   'expression : INPUT'
#   t[0] = Name(t[1])

def p_expression_group(t):
    'expression : LPAREN expression RPAREN'
    t[0] = t[2]

def p_error(t):
    print("Syntax error at '%s'" % t.value)


import ply.yacc as yacc
yacc.yacc()
