
from token import *


class Type:
    def __init__(self, the_type:list[str]):
        self.type = the_type

    def __str__(self):
        return f"{self.type}"
    
    def __repr__(self):
        return self.__str__()


class Range:
    def __init__(self, min_val: int|float, max_val: int|float, step: int|float):
        self.min_val = min_val
        self.max_val = max_val
        self.step = step

    def __str__(self):
        return f"Range: {self.min_val}-{self.max_val} : {self.step}"

    def __repr__(self):
        return self.__str__()


class Constraint:
    def __init__(self, values:list[Range|int|str|float]):
        self.values = values

    def __str__(self):
        return f"Constraint: {self.values}"

    def __repr__(self):
        return self.__str__()


class Function(Token):
    def __init__(self, name:str, return_type:Type, arg_types:list[Type], arg_constraints:list[Constraint], tokens:list[str], declaration:bool):
        Token.__init__(self, "$FUNCTION_DEFINITION", 0, ".")
        self.name = name
        self.return_type = return_type
        self.arg_types = arg_types
        self.arg_constraints = arg_constraints
        self.tokens = tokens
        self.declaration = declaration

    def __str__(self):
        return f"Function{' Declaration' if self.declaration else ''} {self.name} -> {self.return_type}\narguments:\n{['\t' + self.arg_types[x].__str__() + self.arg_constraints[x].__str__() + '\n' for x in range(len(self.arg_types))]}\nTokens: {self.tokens}\n"

    def __repr__(self):
        return self.__str__()


class Structure(Token):
    def __init__(self, name:str, member_names:list[str], member_types:list[Type]):
        Token.__init__(self, "$STRUCTURE_DEFINITION", 0, ".")
        self.name = name
        self.member_names = member_names
        self.member_types = member_types

    def __repr__(self):
        return self.__str__()


class Union(Token):
    def __init__(self, name:str, member_names:list[str], member_types:list[Type]):
        Token.__init__(self, "$UNION_DEFINITION", 0, ".")
        self.name = name
        self.member_names = member_names
        self.member_types = member_types

    def __repr__(self):
        return self.__str__()


class Enum(Token):
    def __init__(self, name:str, member_names:list[str], member_values:list[int]):
        Token.__init__(self, "$ENUM_DEFINITION", 0, ".")
        self.name = name
        self.member_names = member_names
        self.member_values = member_values

    def __repr__(self):
        return self.__str__()


class Typedef(Token):
    def __init__(self, first:Type, second:Type):
        Token.__init__(self, "$TYPEDEF_DEFINITION", 0, ".")
        self.first = first
        self.second = second

    def __repr__(self):
        return self.__str__()


