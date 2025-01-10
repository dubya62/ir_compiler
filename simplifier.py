
from token import *
from debug import *

import types


class Simplifier:
    def __init__(self, tokens:list[Token]):
        self.tokens = tokens

        self.structures = []
        self.unions = []
        self.enums = []

        self.typedefs = []

        self.varnum = 1

        # convert type tokens
        self.tokens, _ = self.convert_type_tokens(self.tokens, 0, len(self.tokens))
        
        # handle typedefs
        self.tokens = self.handle_typedefs(self.tokens)

        # create extra scopes
        self.tokens = self.create_extra_scopes(self.tokens)

        # generalize variables
        self.definitions = {}
        self.tokens = self.generalize_variables(self.tokens)

        # fix function scoping
        self.tokens = self.fix_extra_scopes(self.tokens)

    
    def convert_type_tokens(self, tokens:list[Token], starting_index, ending_index) -> list[Token]:
        # convert all types to Type Tokens
        dbg("Converting Type Tokens...")
        i = starting_index
        n = len(tokens)
        if ending_index < n:
            n = ending_index
        starting_n = n

        builtin_types = set(["short", "long", "int", "float", "double", "void", "signed", "unsigned", "const", "char"])

        dbg(f"Converting types of: {tokens[i:n]}")


        while i < n:
            if tokens[i].token in ["struct", "union"]:
                # if a struct or union, handle everything inside first

                # make sure this is a definition
                if not (i + 1 < n and tokens[i+1] == "{") and not (i + 2 < n and tokens[i+2] == "{"):
                    # this is a usage
                    # TODO: make this consume * and & like normal
                    new_builtin_types = builtin_types
                    new_builtin_types.add(tokens[i].token)
                    new_builtin_types.add(tokens[i+1].token)
                    n_difference = self.replace_type(tokens, i, new_builtin_types)
                    n += n_difference
                    i += 1
                    continue
                    

                return_index = i
                brace_stack = []
                new_starting_index = i + 1
                new_ending_index = n

                if i + 1 < n and tokens[i+1].token in ["{", ";"]:
                    if tokens[i] == "struct":
                        self.structures.append(tokens[i+1].token)
                    else:
                        self.unions.append(tokens[i+1].token)

                while i < n:
                    if tokens[i] == "{":
                        break;
                    i += 1
                while i < n:
                    if tokens[i] == "{":
                        brace_stack.append("{")
                    elif tokens[i] == "}":
                        if len(brace_stack) == 0:
                            fatal_error(tokens[i], "Mismatched }...")
                        brace_stack.pop()
                        if len(brace_stack) == 0:
                            new_ending_index = i + 1
                            break;
                    i += 1

                # everything inside is now converted. Now create a new token for this struct

                tokens, n_difference = self.convert_type_tokens(tokens, new_starting_index, new_ending_index)
                n += n_difference
                i = return_index

                # we now have everything inside the struct taken care of
                # create a $STRUCT or $UNION token
                the_types = []
                going = False
                while i < n:
                    if tokens[i] == "{":
                        going = True
                    elif tokens[i] == "}":
                        if going:
                            the_types.append(tokens[i])
                            del tokens[i]
                            n -= 1
                        break

                    if going:
                        the_types.append(tokens[i])
                        del tokens[i]
                        n -= 1
                        continue
                    i += 1

                print(the_types)
                i = return_index

                if tokens[i] == "union":
                    new_union = types.Union(the_types, tokens[i].line_number, tokens[i].filename)
                    tokens[i] = new_union
                elif tokens[i] == "struct":
                    new_struct = types.Structure(the_types, tokens[i].line_number, tokens[i].filename)
                    tokens[i] = new_struct

            elif tokens[i].token in builtin_types:
                n_difference = self.replace_type(tokens, i, builtin_types)
                n += n_difference
            elif tokens[i].token == "enum":
                if not (i + 1 < n and tokens[i+1] == "{") and not (i + 2 < n and tokens[i+2] == "{"):
                    i += 1
                    continue
                # convert this token to an enum token
                starting_index = i
                braces = []
                the_type = []
                while i < n:
                    if tokens[i] == "{":
                        braces.append("{")
                    elif tokens[i] == "}":
                        if len(braces) == 0:
                            fatal_error(tokens[i], "Mismatched }...")
                        braces.pop()
                        if len(braces) == 0:
                            the_type.append(tokens[i])
                            del tokens[i]
                            n -= 1
                            break

                    if len(braces) > 0:
                        the_type.append(tokens[i])
                        del tokens[i]
                        n -= 1
                    else:
                        i += 1

                i = starting_index
                new_enum = types.Enum(the_type, tokens[i].line_number, tokens[i].filename)
                tokens[i] = new_enum

            
            i += 1

        dbg("Finished Converting Type Tokens!")

        return tokens, n - starting_n
    

    def replace_type(self, tokens:list[Token], i:int, builtin_types:set):
        the_line_number = tokens[i].line_number
        the_filename = tokens[i].filename
        # eat up the tokens to get the correct type
        current_type = []
        return_index = i
        n = len(tokens)
        starting_len = n

        type_tokens = set(["*", "&"])

        while i < n:
            if tokens[i].token not in builtin_types and tokens[i].token not in type_tokens:
                if tokens[i].token in ["=", "{", ";", "(", ",", ")"]:
                    break;
                i += 1
                continue
            current_type.append(tokens[i])
            del tokens[i]
            n -= 1
        i = return_index
        tokens.insert(i, types.Type(current_type, the_line_number, the_filename))
        n += 1
        return n - starting_len

    
    def handle_typedefs(self, tokens:list[Token]) -> list[Token]:
        dbg("Handling typedefs...")
        i = 0
        n = len(tokens)

        builtin_types = set(["short", "long", "int", "float", "double", "void", "signed", "unsigned", "const", "char"])

        scopes = [{}]

        while i < n:
            if tokens[i] == "typedef":
                # save the type for later
                if i + 2 >= n:
                    fatal_error(tokens[i], "Expected type declaration after typedef...")
                starting = i

                while i < n:
                    if tokens[i] == ";":
                        break;
                    i += 1

                second = tokens[i-1]
                first = tokens[starting+1:i-1]

                for j in range(len(first)):
                    if first[j].token == "$STRUCT":
                        first[j].token = "struct"
                    if first[j].token == "$UNION":
                        first[j].token = "union"

                print(f"typedef {first}, {second}")
                tokens = tokens[:starting] + tokens[i+1:]
                n = len(tokens)

                # check if this is a redefinition of a type
                if second.token in builtin_types:
                    fatal_error(second, f"Redefinition of builtin type {second}...")
                for j in range(len(scopes)-1, -1, -1):
                    if second.token in scopes[j]:
                        fatal_error(second, f"Redefinition of type {second}...")

                scopes[-1][second.token] = first

            elif tokens[i] == "{":
                scopes.append({})
            elif tokens[i] == "}":
                if len(scopes) == 0:
                    fatal_error(tokens[i], "Mismatched }...")
                scopes.pop()
            else:
                for j in range(len(scopes)-1, -1, -1):
                    if tokens[i].token in scopes[j]:
                        key = tokens[i].token
                        del tokens[i]
                        for x in scopes[j][key]:
                            tokens.insert(i, x)
                            i += 1

            i += 1

        self.typedefs = scopes[0]

        dbg("Finished Handling typedefs...")

        return tokens


    def create_extra_scopes(self, tokens:list[Token]) -> list[Token]:
        brace_stack = []
        
        i = 0
        n = len(tokens)
        while i < n:
            if tokens[i] == "for":
                tokens.insert(i, Token("{", tokens[i].line_number, tokens[i].filename))
                i += 1
                starting = i
                brace_stack = []
                while i < n:
                    if tokens[i] == "{":
                        brace_stack.append("{")
                    elif tokens[i] == "}":
                        if len(brace_stack) == 0:
                            fatal_error(tokens[i], "Mismatched }...")
                        brace_stack.pop()
                        if len(brace_stack) == 0:
                            tokens.insert(i, Token("}", tokens[i].line_number, tokens[i].filename))
                            break
                    i += 1
                i = starting

            i += 1

        tokens = self.create_extra_function_scopes(tokens)

        return tokens


    def create_extra_function_scopes(self, tokens:list[Token]) -> list[Token]:
        # look for a type, varname, (...), {
        # put another { before the (
        i = 0
        n = len(tokens)

        while i < n:
            if tokens[i].token in ["struct", "$STRUCT", "union", "$UNION", "$TYPE"]:
                done = False
                starting_index = i 
                starting = 0
                while i < n:
                    if tokens[i] in [";", ":", "="]:
                        done = True
                        break
                    if tokens[i] == "(":
                        the_parenthesis = i
                        break

                    i += 1
                if tokens[i-1] in ["if", "switch", "while", "for"]:
                    break
                if done:
                    i += 1
                    continue
                while i < n:
                    if tokens[i] == ")":
                        break
                    i += 1
                if i + 1 >= n:
                    fatal_error(tokens[i], "Expected ; or { after function declaration")
                if tokens[i+1] == "{":
                    # this is a function definition
                    tokens.insert(the_parenthesis, Token("#FIXFUNC", tokens[the_parenthesis].line_number, tokens[the_parenthesis].filename))
                    i += 1
                    n += 1
                    tokens.insert(the_parenthesis+1, Token("{", tokens[the_parenthesis].line_number, tokens[the_parenthesis].filename))
                    i += 1
                    n += 1
                    braces_stack = []
                    while i < n:
                        if tokens[i] == "{":
                            braces_stack.append("{")
                        elif tokens[i] == "}":
                            if len(braces_stack) == 0:
                                fatal_error(tokens[i], "Mismatched }...")
                            braces_stack.pop()
                            if len(braces_stack) == 0:
                                tokens.insert(i, Token("}", tokens[i].line_number, tokens[i].filename))
                                i += 1
                                n += 1
                                break;
                        i += 1
                    i = starting_index + 3
                        
            i += 1

        return tokens

    def generalize_variables(self, tokens:list[Token]) -> list[Token]:
        dbg("Generalizing variables...")
        i = 0
        n = len(tokens)

        builtins = set(["++", "--", "*", "+", "-", "(", ")", ".", "[", "]", "{", "}", "<", ">", ",", "/", "=", "|", "%", "#", "!", "~", "^", "&", ";", ":", "?", "return", "break", "void", "if", "else", "for", "while", "switch", "case", "short", "long", "const", "unsigned", "struct", "signed", "sizeof", "continue", "auto", "register", "static", "$STRUCT", "$UNION", "$ENUM", "$TYPE", "#FIXFUNC", "goto"])

        scopes = [{}]

        varnum = 0

        while i < n:
            if tokens[i] == "{":
                scopes.append({})
            elif tokens[i] == "}":
                if len(scopes) == 0:
                    fatal_error(tokens[i], "Mismatched }...")
                scopes.pop()
            elif tokens[i].token not in builtins:
                # make sure it is not a string, char, or float literal
                if len(tokens[i].token) > 0:
                    if tokens[i].token[0] in ['"', "'"]:
                        i += 1
                        continue
                    try:
                        float(tokens[i].token)
                        i += 1
                        continue
                    except:
                        pass
                

                found = False
                for j in range(len(scopes)-1, -1, -1):
                    if tokens[i].token in scopes[j]:
                        # TODO: throw an redefinition error if the token before was a type
                        tokens[i].token = scopes[j][tokens[i].token]
                        found = True
                        break
                if not found:
                    # TODO: throw an undefined error if the token before was not a type
                    self.definitions["#" + str(varnum)] = tokens[i].token
                    scopes[-1][tokens[i].token] = "#" + str(varnum)
                    tokens[i].token = scopes[-1][tokens[i].token]
                    varnum += 1
            i += 1

        dbg("Finished generalizing variables!")
        self.varnum = varnum

        return tokens
        
    
    def fix_extra_scopes(self, tokens:list[Token]) -> list[Token]:
        dbg("Removing extra function scopes...")
        i = 0
        n = len(tokens)

        dbg(tokens)

        while i < n:
            if tokens[i].token == "#FIXFUNC":
                starting_index = i
                del tokens[i]
                n -= 1
                if i < n:
                    del tokens[i]
                    n -= 1

                braces = ["{"]

                while i < n:
                    if tokens[i] == "{":
                        braces.append("{")
                    elif tokens[i] == "}":
                        if len(braces) == 0:
                            fatal_error(tokens[i], "Mismatched }...")
                        braces.pop()
                        if len(braces) == 0:
                            del tokens[i]
                            n -= 1
                            break

                    i += 1
                i = starting_index
            i += 1

        dbg("Finished removing extra function scopes...")
        return tokens





