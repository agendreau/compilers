from compiler.ast import *

class GetTag(Node):
    def __init__(self, arg):
        self.arg = arg
    def __repr__(self):
        return "GetTag(%s)" % (repr(self.arg))

class InjectFrom(Node):
    def __init__(self, typ, arg):
        self.typ = typ
        self.arg = arg
        
    def __repr__(self):
        return "InjectFrom(%s, %s)" % (repr(self.typ), repr(self.arg))
        
class ProjectTo(Node):
    def __init__(self, typ, arg):
        self.typ = typ
        self.arg = arg
    
    def __repr__(self):
        return "ProjectTo(%s, %s)" % (repr(self.typ), repr(self.arg))
        
class Let(Node):
    def __init__(self, var, rhs, body):
        self.var = var
        self.rhs = rhs
        self.body = body
        
    def __repr__(self):
        return "Let(%s, %s, %s)" % (repr(self.var), repr(self.rhs), repr(self.body))
        
class AddInt(Node):
    def __init__(self, leftright):
        self.left = leftright[0]
        self.right = leftright[1]
    
    def __repr__(self):
        return "AddInt(%s, %s)" % (repr(self.left), repr(self.right))
