
from debug import *
from token import *


class Type(Token):
    def __init__(self, types:list[Token], line_number:int, filename:str):
        Token.__init__(self, "$TYPE", line_number, filename)
        self.types = types

class Structure(Type):
    def __init__(self, types:list[Token], line_number:int, filename:str):
        Type.__init__(self, types, line_number, filename)
        self.token = "$STRUCT"

class Union(Type):
    def __init__(self, types:list[Token], line_number:int, filename:str):
        Type.__init__(self, types, line_number, filename)
        self.token = "$UNION"

class Enum(Type):
    def __init__(self, types:list[Token], line_number:int, filename:str):
        Type.__init__(self, types, line_number, filename)
        self.token = "$ENUM"

class Function:
    def __init__(self):
        pass
