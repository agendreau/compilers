
# -----------------------------------------------------------------------------
# calc.py
#
# A simple calculator with variables -- all in one file.
# -----------------------------------------------------------------------------

reserved = {
    'print' : 'PRINT',
    'input' : 'INPUT'
}

#there should be no need to tokenize the lex comment, correct?

tokens = [
          'NAME','INT',
          'PLUS','MINUS','EQUALS',
          'LPAREN','RPAREN',
          ] + list(reserved.values())

# Tokens


t_PLUS    = r'\+'
t_MINUS   = r'-'
t_EQUALS  = r'='
t_LPAREN  = r'\('
t_RPAREN  = r'\)'

def t_COMMENT(t):
    r'\#.*\n'
    t.lexer.lineno += t.value.count("\n")
#return t

def t_NAME(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value,'NAME')    # Check for reserved words
    return t

def t_INT(t):
    r'\d+'
    try:
        t.value = int(t.value)
    except ValueError:
        print("Integer value too large %d", t.value)
        t.value = 0
    return t

# Ignored characters
t_ignore = " \t"

def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")

def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

# Build the lexer
import ply.lex as lex
lex.lex()


# Test it out
data = '''#this is a comment
    
        1+2 #this is a comment
        x=3
        
        print x
        input(      )'''

# Give the lexer some input
lex.input(data)

# Tokenize
while True:
    tok = lex.token()
    if not tok: break      # No more input
    print tok
