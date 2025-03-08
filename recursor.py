"""
The purpose of this file is to remove recursion from the IR and inline all possible function calls

We still want to retain the original functions

"""

from debug import *
import standard


class Recursor:
    def __init__(self, tokens):
        self.tokens = tokens

        dbg("Running the Recursor...")

        changed = 1
        while changed:
            changed = 0
            changed |= self.remove_recursion()
            changed |= self.inline_functions()

    def remove_recursion(self):
        dbg("Removing recursion...")
        result = 0
        for tok in self.tokens:
            if issubclass(type(tok), standard.Function):
                # if this is a function, check to see if it calls itself
                dbg("Found function...")
                i = 0
                n = len(tok.tokens)
                this_function = tok.var_name
                while i < n:
                    if tok.tokens[i] == this_function:
                        dbg("Found call to self. Fixing...")
                        pass
                    i += 1
        return result

    def inline_functions(self):
        dbg("Inlining Functions...")
        result = 0
        for tok in self.tokens:
            if issubclass(type(tok), standard.Function):
                # if this is a function, look for other function calls that are defined
                pass
        return result

