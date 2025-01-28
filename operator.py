
from debug import *
from token import *

from types import *
import standard


class Operator:
    def __init__(self, tokens:list[Token], varnum:int, variable_names):
        self.tokens = tokens
        self.varnum = varnum
        self.variable_names = variable_names

        # combine multi-token operations
        self.tokens = self.combine_multi_token_operations(self.tokens)

        # break operations
        self.tokens = self.break_operations(self.tokens)

        # convert assignment operators
        # x += 3
        # =>
        # x = x + (3)
        self.tokens = self.convert_assignment_operators(self.tokens)

        # convert unary operators
        self.tokens = self.convert_unary_operators(self.tokens)

        # convert calls and accesses to use "call" and "access"
        self.tokens = self.convert_calls_and_accesses(self.tokens)

        # convert type casts to use "cast"
        self.tokens = self.convert_casts(self.tokens)

        # break up lines that have more than one operation on them
        self.tokens = self.break_multiple_operations(self.tokens)

        # Remove $TYPE, $STRUCT, $UNION, $ENUM, and $INFER variables
        self.token_types = ["NA"] * self.varnum
        self.tokens = self.remove_types(self.tokens)

        # convert unary + and -
        self.tokens = self.convert_unary_plus_and_minus(self.tokens)

        # parse structures, unions, enums, and typedefs into objects
        self.functions = []
        self.structures = []
        self.unions = []
        self.enums = []
        self.typedefs = []
        self.tokens = self.parse_structs_unions_enums_and_typedefs(self.tokens)

        # TODO: convert returns
        self.tokens = self.convert_returns(self.tokens)

        # remove un+ and un-
        self.tokens = self.remove_unary_operators(self.tokens)

        # remove ->
        self.remove_arrows()

        # remove <=, >=, and !=
        self.remove_or_equal()

        # make sure all if statements have an else clause
        self.create_else_clauses()

        # remove || 
        self.remove_logical_or()

        # remove &&
        self.remove_logical_and()

        # remove lognot
        self.remove_logical_not()

        # convert derefs to accesses

        """
        remaining tokens:
        $INFER, $TYPE, $ENUM, $STRUCTURE_DEFINITION, $UNION_DEFINITION, $TYPEDEF_DEFINITION
        bitnot, ref, %, ^, &, |, -, +, <, >, *, /, ==, ., call, access, >>, <<, =, ,, cast
        {, }, ;
        if, else
        goto, @x, #x, :
        <char, int, float, and string literals>
        """

        
    def combine_multi_token_operations(self, tokens:list[Token]) -> list[Token]:

        first_tokens = set(["+", "/", "*", "!", "=", "%", "^", "~", "-"])
        second_tokens = set(["<", ">", "&", "|"])

        i = 0
        n = len(tokens)
        while i < n:
            if tokens[i].token in first_tokens:
                if i + 1 < n and tokens[i+1] == "=":
                    tokens[i].token += tokens[i+1].token
                    del tokens[i+1]
                    n -= 1
                    i += 1
                    continue
                if tokens[i] == "-":
                    if i + 1 < n and tokens[i+1] == ">":
                        tokens[i].token += tokens[i+1].token
                        del tokens[i+1]
                        n -= 1
                        i += 1
                        continue
            elif tokens[i].token in second_tokens:
                if i + 1 < n:
                    if tokens[i+1] == "=":
                        tokens[i].token += tokens[i+1].token
                        del tokens[i+1]
                        n -= 1
                        i += 1
                        continue
                    if tokens[i+1].token == tokens[i].token:
                        if i + 2 < n and tokens[i+2] == "=":
                            tokens[i].token += tokens[i+1].token + tokens[i+2].token
                            del tokens[i+1]
                            del tokens[i+1]
                            n -= 2
                            i += 1
                            continue
                        else:
                            tokens[i].token += tokens[i+1].token
                            del tokens[i+1]
                            n -= 1
                            i += 1
                            continue
            i += 1


        return tokens


    def break_operations(self, tokens:list[Token]):
        dbg("Breaking operations from if statements")

        tokens = self.break_operations_from_ifs(tokens)

        tokens = self.break_operations_from_returns(tokens)

        tokens = self.convert_prefix_and_postfix(tokens)

        tokens = self.break_operations_from_function_calls(tokens)
        
        return tokens


    def break_operations_from_ifs(self, tokens:list[Token]) -> list[Token]:
        i = 0
        n = len(tokens)

        while i < n:
            if tokens[i] == "if":
                between = []
                parens = []
                starting_index = i
                while i < n:
                    if tokens[i] == "(":
                        break
                    i += 1
                while i < n:
                    if tokens[i] == "(":
                        parens.append("(")
                        i += 1
                        continue
                    elif tokens[i] == ")":
                        if len(parens) == 0:
                            fatal_error(tokens[i], "Mismatched )...")
                        parens.pop()
                        if len(parens) == 0:
                            break
                    between.append(tokens[i])
                    del tokens[i]
                    n -= 1
                tokens.insert(i, Token("#" + str(self.varnum), tokens[i].line_number, tokens[i].filename))
                i += 1
                n += 1
                tokens.insert(starting_index, Token("$INFER", tokens[i].line_number, tokens[i].filename))
                starting_index += 1
                i += 1
                n += 1
                tokens.insert(starting_index, Token("#" + str(self.varnum), tokens[starting_index].line_number, tokens[starting_index].filename))
                starting_index += 1
                i += 1
                n += 1
                tokens.insert(starting_index, Token("=", tokens[starting_index].line_number, tokens[starting_index].filename))
                starting_index += 1
                i += 1
                n += 1

                for x in between:
                    tokens.insert(starting_index, x)
                    starting_index += 1
                    i += 1
                    n += 1
                tokens.insert(starting_index, Token(";", tokens[starting_index].line_number, tokens[starting_index].filename))
                starting_index += 1
                i += 1
                n += 1

                self.varnum += 1
                
            i += 1

        return tokens


    def break_operations_from_returns(self, tokens:list[Token]) -> list[Token]:
        i = 0
        n = len(tokens)
        while i < n:
            if tokens[i] == "return":
                starting_index = i;
                after = []
                i += 1
                while i < n:
                    if tokens[i] == ";":
                        break
                    after.append(tokens[i])
                    del tokens[i]
                    n -= 1
                tokens.insert(i, Token("#" + str(self.varnum), tokens[i].line_number, tokens[i].filename))
                i += 1
                n += 1
                tokens.insert(starting_index, Token("$INFER", tokens[starting_index].line_number, tokens[starting_index].filename))
                i += 1
                n += 1
                starting_index += 1

                tokens.insert(starting_index, Token("#" + str(self.varnum), tokens[starting_index].line_number, tokens[starting_index].filename))
                i += 1
                n += 1
                starting_index += 1

                tokens.insert(starting_index, Token("=", tokens[starting_index].line_number, tokens[starting_index].filename))
                i += 1
                n += 1
                starting_index += 1

                for x in after:
                    tokens.insert(starting_index, x)
                    i += 1
                    n += 1
                    starting_index += 1
                tokens.insert(starting_index, Token(";", tokens[starting_index].line_number, tokens[starting_index].filename))
                i += 1
                n += 1
                starting_index += 1

                self.varnum += 1

            i += 1

        return tokens

    
    def convert_prefix_and_postfix(self, tokens:list[Token]) -> list[Token]:
        dbg("Converting prefix and postfix operators...")
        i = 0
        n = len(tokens)

        operators = set(["~", "!", "%", "^", "&", "|", "-", "+", "<", ">", "/", "*", "+=", "/=", "*=", "<=", ">=", "!=", "==", "%=", "^=", "&=", "|=", "~=", "-=", "->", "&&", "||", "&&=", "||=", ".", "(", "[", ">>", "<<", "<<=", ">>=", "=", ";", "++", "--"])
        
        while i < n:
            if tokens[i].token in ["++", "--"]:
                if tokens[i] == "++":
                    new_operator = "+="
                else:
                    new_operator = "-="
                # figure out if this is prefix or postfix
                is_prefix = 0
                if i > 0 and (tokens[i-1].token in ["}", "{", ";", "("] or tokens[i-1].token in operators):
                    is_prefix = 1

                inside = []

                del tokens[i]
                n -= 1

                if is_prefix:
                    parens = []
                    j = i
                    # higher:
                    # function call ()
                    # array subscript []
                    # .
                    # ->
                    # TODO: finish this
                    while j < n:
                        if tokens[j].token in ["(", "["]:
                            parens.append(tokens[j].token)
                        elif tokens[j] == ")":
                            if len(parens) == 0:
                                fatal_error(tokens[j], "Mismatched )...")

                            if len(parens) == 0:
                                break
                        elif tokens[j] == "]":
                            if len(parens) == 0:
                                fatal_error(tokens[j], "Mismatched ]...")

                            if len(parens) == 0:
                                break
                        elif tokens[j].token in ["(", "[", ".", "->"]:
                            inside.append(tokens[j])
                            j += 1
                            continue

                        inside.append(tokens[j])
                        if len(parens) == 0:
                            if not (j+1 < n and tokens[j+1].token in ["(", "[", ".", "->"]):
                                break

                        j += 1
                    # move to the line before
                    j = i
                    while j >= 0:
                        if tokens[j].token in ["{", ";", "}"]:
                            break
                        j -= 1
                    j += 1


                    for x in inside:
                        tokens.insert(j, x)
                        j += 1; n += 1
                    tokens.insert(j, Token(new_operator, tokens[j].line_number, tokens[j].filename))
                    j += 1; n += 1
                    tokens.insert(j, Token("1", tokens[j].line_number, tokens[j].filename))
                    j += 1; n += 1
                    tokens.insert(j, Token(";", tokens[j].line_number, tokens[j].filename))
                    j += 1; n += 1

                else:
                    j = i - 1
                    parens = []
                    while j >= 0:
                        if tokens[j] == ")":
                            parens.append(")")
                        elif tokens[j] == "(":
                            if len(parens) == 0:
                                fatal_error(tokens[j], "Mismatched (...")
                            parens.pop()
                            if len(parens) == 0:
                                break
                        inside.append(tokens[j])

                        if len(parens) == 0:
                            break

                        j -= 1

                    # move to the line after
                    j = i
                    while j < n:
                        if tokens[j] == ";":
                            j += 1
                            break
                        j += 1

                    for x in inside:
                        tokens.insert(j, x)
                        j += 1; n += 1
                    tokens.insert(j, Token(new_operator, tokens[j].line_number, tokens[j].filename))
                    j += 1; n += 1
                    tokens.insert(j, Token("1", tokens[j].line_number, tokens[j].filename))
                    j += 1; n += 1
                    tokens.insert(j, Token(";", tokens[j].line_number, tokens[j].filename))
                    j += 1; n += 1
                        

            

            i += 1

        dbg("Finished converting prefix and postfix operators...")
        return tokens

    def break_operations_from_function_calls(self, tokens:list[Token]) -> list[Token]:
        i = 0
        n = len(tokens)
        changes = 1
        while changes:
            changes = 0
            while i < n:
                if len(tokens[i].token) > 0 and tokens[i].token[0] == '#':
                    # this is a variable
                    starting_index = i
                    if i + 1 < n and tokens[i+1] == "(":
                        # this is a function call or definition
                        # make sure the thing before the var is not $TYPE or $STRUCT x, $ENUM x, $UNION x
                        if not (i > 0 and tokens[i-1] == "$TYPE" or i > 1 and tokens[i-2] in ["$STRUCT", "$ENUM", "$UNION", "struct", "union", "enum"]):
                            # this is a function call
                            while starting_index >= 0:
                                if tokens[starting_index].token in ["{", ";", "}"]:
                                    starting_index += 1
                                    break
                                starting_index -= 1
                            i += 1
                            braces = []
                            current = []
                            while i < n:
                                if tokens[i].token in ["(", "{"]:
                                    braces.append(tokens[i].token)
                                    if len(braces) == 1:
                                        i += 1
                                        continue
                                elif tokens[i] == "}":
                                    if len(braces) == 0:
                                        fatal_error(tokens[i], "Mismatched }...")
                                    braces.pop()
                                elif tokens[i] == ")":
                                    if len(braces) == 0:
                                        fatal_error(tokens[i], "Mismatched )...")
                                    braces.pop()
                                    if len(braces) == 0:
                                        # handle what was left
                                        if len(current) > 0:
                                            if len(current) == 1 and len(current[0].token) > 0 and current[0].token[0] == "#":
                                                # this should just be put back
                                                tokens.insert(i, current[0])
                                                current = []
                                                i += 2
                                                n += 1
                                                break

                                            changes += 1

                                            tokens.insert(i, Token("#" + str(self.varnum), tokens[i].line_number, tokens[i].filename))
                                            i += 2
                                            n += 1
                                            tokens.insert(starting_index, Token("$INFER", tokens[starting_index].line_number, tokens[starting_index].filename))
                                            starting_index += 1
                                            i += 1
                                            n += 1

                                            tokens.insert(starting_index, Token("#" + str(self.varnum), tokens[starting_index].line_number, tokens[starting_index].filename))
                                            starting_index += 1
                                            i += 1
                                            n += 1
                                            tokens.insert(starting_index, Token("=", tokens[starting_index].line_number, tokens[starting_index].filename))
                                            starting_index += 1
                                            i += 1
                                            n += 1

                                            for x in current:
                                                tokens.insert(starting_index, x)
                                                starting_index += 1
                                                i += 1
                                                n += 1
                                            tokens.insert(starting_index, Token(";", tokens[starting_index].line_number, tokens[starting_index].filename))
                                            starting_index += 1
                                            i += 1
                                            n += 1
                                            current = []

                                            self.varnum += 1

                                        break
                                elif tokens[i] == ",":
                                    if len(current) == 1 and len(current[0].token) > 0 and current[0].token[0] == "#":
                                        # this should just be put back
                                        tokens.insert(i, current[0])
                                        i += 2
                                        n += 1
                                        current = []
                                        continue

                                    changes += 1

                                    tokens.insert(i, Token("#" + str(self.varnum), tokens[i].line_number, tokens[i].filename))
                                    i += 2
                                    n += 1
                                    self.varnum += 1

                                    tokens.insert(starting_index, Token("#" + str(self.varnum), tokens[starting_index].line_number, tokens[starting_index].filename))
                                    starting_index += 1
                                    i += 1
                                    n += 1
                                    tokens.insert(starting_index, Token("=", tokens[starting_index].line_number, tokens[starting_index].filename))
                                    starting_index += 1
                                    i += 1
                                    n += 1

                                    for x in current:
                                        tokens.insert(starting_index, x)
                                        starting_index += 1
                                        i += 1
                                        n += 1
                                    tokens.insert(starting_index, Token(";", tokens[starting_index].line_number, tokens[starting_index].filename))
                                    starting_index += 1
                                    i += 1
                                    n += 1
                                    current = []
                                    continue
                                    
                                current.append(tokens[i])
                                del tokens[i] 
                                n -= 1


                i += 1;

        return tokens

    
    def convert_assignment_operators(self, tokens:list[Token]) -> list[Token]:
        i = 0
        n = len(tokens)

        assignment_operators = set(["+=", "/=", "*=", "%=", "^=", "&=", "|=", "~=", "-=", "&&=", "||=", "<<=", ">>="])

        while i < n:
            if tokens[i].token in assignment_operators:
                the_operator = tokens[i].token.strip("=")
                tokens[i].token = "="

                before = []
                j = i-1
                while j >= 0:
                    if tokens[j].token in [";", "{", "}"]:
                        break
                    before.append(tokens[j])
                    j -= 1
                j += 1

                i += 1
                for x in before:
                    tokens.insert(i, x)
                    i += 1
                    n += 1
                tokens.insert(i, Token(the_operator, tokens[i].line_number, tokens[i].filename))
                i += 1
                n += 1
                tokens.insert(i, Token("(", tokens[i].line_number, tokens[i].filename))
                i += 1
                n += 1

                j = i
                while j < n:
                    if tokens[j] == ";":
                        j += 1
                        break
                    j += 1
                j -= 1
                tokens.insert(j, Token(")", tokens[j].line_number, tokens[j].filename))
                n += 1
            
            i += 1


        return tokens

    def convert_unary_operators(self, tokens:list[Token]) -> list[Token]:
        unary_operators = {"~":"bitnot", "!":"lognot", "&":"ref", "*":"deref", "-":"un-", "+":"un+"}

        operators = set(["~", "!", "%", "^", "&", "|", "-", "+", "/", "<", ">", "*", "==", "->", "&&", "||", ".", "(", "[", ">>", "<<", "=", ";", "{", "}", "<=", ">=", "!="])

        i = 0
        n = len(tokens)
        while i < n:
            if tokens[i].token in unary_operators:
                if i == 0 or (i > 0 and tokens[i-1].token in operators):
                    # this is a unary operator
                    tokens.insert(i, Token("0", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    n += 1
                    tokens[i].token = unary_operators[tokens[i].token]
            
            i += 1

        return tokens


    def convert_calls_and_accesses(self, tokens:list[Token]) -> list[Token]:
        operators = set(["bitnot", "lognot", "deref", "ref", "un-", "un+", "%", "^", "&", "|", "-", "/", "+", "<", ">", "*", "==", "->", "&&", "||", ".", "(", "[", ">>", "<<", "=", "!=", "<=", ">="])
        # x[y] => x access (y)
        # x(y) => x call (y)
        # x() => x call(#NOTHING)
        i = 0
        n = len(tokens)
        while i < n:
            if len(tokens[i].token) > 0 and tokens[i].token[0] == '#':
                # this is a variable
                starting_index = i
                if i + 1 < n and tokens[i+1] == "(":
                    # this is a function call or definition
                    # make sure the thing before the var is not $TYPE or $STRUCT x, $ENUM x, $UNION x
                    if not (i > 0 and tokens[i-1] == "$TYPE" or i > 1 and tokens[i-2] in ["$STRUCT", "$ENUM", "$UNION"]):
                        # this is a function call
                        i += 1
                        tokens.insert(i, Token("call", tokens[i].line_number, tokens[i].filename))
                        i += 1
                        n += 1
                        i += 1
                        if i < n and tokens[i] == ")":
                            tokens.insert(i, Token("#NOTHING", tokens[i].line_number, tokens[i].filename))
                            i += 1
                            n += 1
            i += 1
        

        return tokens


    def convert_casts(self, tokens:list[Token]) -> list[Token]:
        i = 0
        n = len(tokens)

        while i < n:
            if tokens[i] == "$TYPE":
                if i > 0 and i + 1 < n and tokens[i-1] == "(" and tokens[i+1] == ")":
                    if i + 2 < n and tokens[i+2].token in ["{", ";"]:
                        i += 1
                        continue
                    del tokens[i-1]
                    del tokens[i]
                    tokens.insert(i, Token("cast", tokens[i].line_number, tokens[i].filename))
                    n -= 1

            i += 1

        return tokens


    def convert_unary_plus_and_minus(self, tokens:list[Token]) -> list[Token]:
        i = 0
        n = len(tokens)

        while i < n:
            if tokens[i] == "un-":
                tokens[i].token = "-"
            elif tokens[i] == "un+":
                tokens[i].token = "+"
            i += 1
        

        return tokens


    def remove_types(self, tokens:list[Token]) -> list[Token]:
        i = 0
        n = len(tokens)

        while i < n:
            if tokens[i] == "$TYPE":
                if i + 1 < n and len(tokens[i+1].token) > 0 and tokens[i+1].token[0] == "#":
                    varnum = tokens[i+1].token[1:]
                    try:
                        varnum = int(varnum)
                    except:
                        i += 1
                        continue
                    if varnum >= len(self.token_types):
                        fatal_error(tokens[i+1], "There is a serious problem with the compiler. Report this...")
                    self.token_types[varnum] = tokens[i].types
                    del tokens[i]
                    n -= 1
                    continue
            elif tokens[i] == "$STRUCT":
                pass
            elif tokens[i] == "$UNION":
                pass
            elif tokens[i] == "$INFER":
                pass

            i += 1

        print(f"Token types: {self.token_types}")

        return tokens


    def break_multiple_operations(self, tokens:list[Token]) -> list[Token]:
        dbg("Breaking lines that have multiple operations...")
        operators = set(["bitnot", "lognot", "deref", "ref", "cast", "%", "^", "&", "|", "-", "+", "/", "<", ">", "*", "==", "->", "&&", "||", ".", "call", "access", ">>", "<<", "=", "&&", "||", ",", "!=", "<=", ">=", "un+", "un-"])
        
        i = 0
        n = len(tokens)
        this_line = 0
        line_start = 0
        equals = 0
        while i < n:
            if tokens[i].token in [";", "{", "}"]:
                if this_line > 1 or equals > 1:
                    print(f"breaking ({this_line} ops): {tokens[line_start:i]}")
                    tokens = self.break_line(tokens, line_start, i)
                    i += len(tokens) - n
                    n = len(tokens)
                this_line = 0
                equals = 0
                line_start = i + 1
            elif tokens[i].token in operators:
                if tokens[i].token == "=":
                    equals += 1
                else:
                    this_line += 1
            
            i += 1
        
        dbg("Finished breaking lines that have multiple operations!")

        return tokens


    def break_line(self, tokens:list[Token], line_start:int, line_end:int) -> int:
        # break the given tokens using infix to postfix and convert them to include only 1 operation per line (not including =)

        precedences = {
                "call":1, 
                "access":2, 
                ".":3, 
                "->":4, 
                "un+":5,
                "un-":6,
                "lognot":7,
                "bitnot":8,
                "cast":9,
                "deref":10,
                "ref":11,
                "*":12, 
                "/":13, 
                "%":14, 
                "+":15, 
                "-":16, 
                "<<":17, 
                ">>":18, 
                "<":19, 
                "<=":20, 
                ">":21, 
                ">=":22,
                "==":23, 
                "!=":24, 
                "&":25, 
                "^":26, 
                "|":27, 
                "&&":28, 
                "||":29, 
                "=":30,
                ",":31, 
                }

        associativity = {
                "un++":1,
                "un--":1,
                "lognot":1,
                "bitnot":1,
                "cast":1,
                "deref":1,
                "ref":1,
                }

        the_line = tokens[line_start:line_end]
        prefix = []
        # convert from infix to postfix
        if len(the_line) > 0 and the_line[0].token == "$TYPE":
            prefix.append(the_line[0])
            del the_line[0]

        postfix = []
        op_stack = []
        for x in the_line:
            # if curr token is operand, put it in the postfix
            if x.token not in precedences and x.token not in ["(", ")"]:
                postfix.append(x)

            # if a (, push it to the stack
            elif x == "(":
                op_stack.append(x)
            # if a ), pop from the stack until (
            elif x == ")":
                while True:
                    if len(op_stack) == 0:
                        fatal_error(x, "Mismatched (...")
                    curr = op_stack.pop()
                    if curr == "(":
                        break
                    postfix.append(curr)
            else:
                if x.token not in precedences:
                    fatal_error(x, "Unrecognized operator...")
                if len(op_stack) == 0 or op_stack[-1] == "(" or precedences[x.token] < precedences[op_stack[-1].token]:
                    op_stack.append(x)
                else:
                    while len(op_stack) > 0 and op_stack[-1].token != "(":
                        if x.token in associativity and op_stack[-1].token in associativity:
                            break
                        if precedences[x.token] <= precedences[op_stack[-1].token]:
                            break
                        postfix.append(op_stack.pop())
                    op_stack.append(x)

        while len(op_stack) > 0:
            postfix.append(op_stack.pop())

        print(f"POSTFIX: {postfix}")

        # break the postfix expression into multiple lines
        result = []
        val_stack = []
        for x in postfix:
            # if a variable/number, push it onto the stack
            if x.token not in precedences:
                val_stack.append(x)
            else:
                if len(val_stack) < 2:
                    fatal_error(x, "Operator does not have enough inputs...")
                second = val_stack.pop()
                first = val_stack.pop()
                # op = x
                if x.token == "=":
                    for y in prefix:
                        result.append(y)
                else:
                    result.append(Token("$INFER", x.line_number, x.filename))
                    result.append(Token("#" + str(self.varnum), x.line_number, x.filename))
                    result.append(Token("=", x.line_number, x.filename))
                    val_stack.append(Token("#" + str(self.varnum), x.line_number, x.filename))

                    # TODO: infer the type of <first> <op> <second>
                    

                    self.varnum += 1

                result.append(first)
                result.append(x)
                result.append(second)
                result.append(Token(";", x.line_number, x.filename))


        print(f"RESULT: {result}")

        tokens = tokens[:line_start] + result + tokens[line_end+1:]

        return tokens


    def parse_structs_unions_enums_and_typedefs(self, tokens:list[Token]):
        i = 0
        n = len(tokens)

        # handle structs and unions
        while i < n:
            if tokens[i] == "$STRUCT" or tokens[i] == "$UNION":
                # get the name
                the_name = None
                if i + 1 < n and len(tokens[i+1].token) > 0 and tokens[i+1].token[0] == "#":
                    the_name = self.variable_names[tokens[i+1].token]
                    del tokens[i+1]
                    n -= 1

                # TODO: finish structs/unions
                member_names = []
                member_types = []

                if tokens[i] == "$STRUCT":
                    the_struct = standard.Structure(the_name, member_names, member_types)
                    self.structures.append(the_struct)
                else:
                    the_struct = standard.Union(the_name, member_names, member_types)
                    self.unions.append(the_struct)
                tokens[i] = the_struct
            elif tokens[i] == "$ENUM":
                the_name = None
                if i + 1 < n and len(tokens[i+1].token) > 0 and tokens[i+1].token[0] == "#":
                    the_name = self.variable_names[tokens[i+1].token]
                    del tokens[i+1]
                    n -= 1
                # TODO: finish enums
                member_names = []
                member_values = []

                the_enum = standard.Enum(the_name, member_names, member_values)
                self.enums.append(the_enum)
                tokens[i] = the_enum
            i += 1

        # get funcion definitions now
        i = 0
        n = len(tokens)
        while i < n:
            # variable followed by ( is a function
            if i + 1 < n and len(tokens[i].token) > 0:
                if tokens[i].token[0] == "#" and tokens[i+1] == "(":
                    starting_index = i
                    # this is a function def
                    the_name = self.variable_names[tokens[i].token]
                    return_type = standard.Type(self.token_types[int(tokens[i].token[1:])])

                    arg_types = []
                    arg_constraints = []
                    i += 1
                    parens = []

                    args = [[]]
                    while i < n:
                        if tokens[i] == "(":
                            parens.append("(")
                        elif tokens[i] == ")":
                            parens.pop()
                            if len(parens) == 0:
                                break
                        elif tokens[i] == ",":
                            args.append([])
                            pass
                        else:
                            args[-1].append(tokens[i])
                        i += 1

                    # if it ends in );, ignore this function
                    declaration = False

                    print(args)
                    if len(args) == 1 and len(args[0]) == 1 and args[0][0] == "$TYPE" and len(args[0][0].types) == 1 and args[0][0].types[0] == "void":
                        arg_types = [self.variable_types[x] for x in args]
                        # TODO: create function constraints
                        arg_constraints = []
                    else:
                        pass

                    
                    func_tokens = []
                    if i + 1 >= n or tokens[i+1] == ";":
                        declaration = True
                    elif tokens[i+1] == "{":
                        i += 2
                        braces = 1
                        while i < n:
                            if tokens[i] == "{":
                                braces += 1
                            elif tokens[i] == "}":
                                braces -= 1
                                if braces == 0:
                                    break
                            func_tokens.append(tokens[i])
                            del tokens[i]
                            n -= 1

                    while i > starting_index:
                        del tokens[starting_index]
                        i -= 1
                        n -= 1
                    the_function = standard.Function(the_name, return_type, arg_types, arg_constraints, func_tokens, declaration)
                    tokens[i] = the_function
                    self.functions.append(the_function)
            
            i += 1

        return tokens



    def convert_returns(self, tokens:list[Token]) -> list[Token]:
        # int foo(int x){return 3;}
        # y = foo(3);
        # =>
        # void foo(int* z, int x){*z = 3;}
        # foo(&y, 3);
        i = 0
        n = len(tokens)
        while i < n:
            i += 1

        return tokens


    def remove_unary_operators(self, tokens:list[Token]) -> list[Token]:
        i = 0
        n = len(tokens)
        while i < n:
            if tokens[i] == "un+":
                tokens[i].token = "+"
            elif tokens[i] == "un-":
                tokens[i].token = "-"
            i += 1
        return tokens


    def remove_arrows(self):
        for func in self.functions:
            tokens = func.tokens
            i = 0
            n = len(tokens)
            while i < n:
                if tokens[i] == "->":
                    tokens[i].token = ")"
                    i += 1
                    tokens.insert(i, Token(".", tokens[i].line_number, tokens[i].filename))
                    n += 1
                    parens = 0
                    return_index = i
                    while i > 0:
                        if tokens[i].token in ["=", "{", "}", ";"]:
                            i += 1
                            break
                        i -= 1
                    tokens.insert(i, Token("(", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    n += 1
                    tokens.insert(i, Token("0", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    n += 1
                    tokens.insert(i, Token("deref", tokens[i].line_number, tokens[i].filename))
                    n += 1
                    i = return_index + 3
                    continue
                i += 1
            func.tokens = self.break_multiple_operations(func.tokens)


    def remove_or_equal(self):
        for func in self.functions:
            tokens = func.tokens
            # remove <=, >=, and !=
            # x <= y 
            # 0 lognot (x > y)
            i = 0
            n = len(tokens)
            while i < n:
                replace = False
                if tokens[i] == "<=":
                    replace = True
                    operator = ">"
                elif tokens[i] == ">=":
                    replace = True
                    operator = "<"
                elif tokens[i] == "!=":
                    replace = True
                    operator = "=="

                if replace:
                    tokens[i].token = operator
                    starting_index = i
                    while i < n:
                        if tokens[i] == ";":
                            break
                        i += 1
                    tokens.insert(i, Token(")", tokens[i].line_number, tokens[i].filename))
                    n += 1
                    i = starting_index
                    while i > 0:
                        if tokens[i].token in ["=", "{", "}", ";"]:
                            i += 1
                            break
                        i -= 1
                    tokens.insert(i, Token("0", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    n += 1
                    tokens.insert(i, Token("lognot", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    n += 1
                    tokens.insert(i, Token("(", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    n += 1

                i += 1
            func.tokens = self.break_multiple_operations(func.tokens)


    def create_else_clauses(self):
        for func in self.functions:
            tokens = func.tokens
            i = 0
            n = len(tokens)
            while i < n:
                if tokens[i] == "if":
                    braces = 0
                    while i < n:
                        if tokens[i] == "{":
                            braces += 1
                        elif tokens[i] == "}":
                            braces -= 1
                            if braces == 0:
                                i += 1
                                break
                        i += 1
                    if i >= n or tokens[i].token != "else":
                        tokens.insert(i, Token("else", tokens[i].line_number, tokens[i].filename))
                        i += 1
                        n += 1
                        tokens.insert(i, Token("{", tokens[i].line_number, tokens[i].filename))
                        i += 1
                        n += 1
                        tokens.insert(i, Token("}", tokens[i].line_number, tokens[i].filename))
                        i += 1
                        n += 1
                
                i += 1
            func.tokens = self.break_multiple_operations(func.tokens)


    def remove_logical_or(self):

        # x || y
        # !(!(x)&&!(y))

        for func in self.functions:
            tokens = func.tokens
            i = 0
            n = len(tokens)
            while i < n:
                if tokens[i] == "||":
                    starting_index = i
                    tokens[i].token = "&&"
                    i += 1
                    tokens.insert(i, Token("0", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    n += 1
                    tokens.insert(i, Token("lognot", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    n += 1
                    tokens.insert(i, Token("(", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    n += 1
                    while i < n:
                        if tokens[i] == ";":
                            break
                        i += 1
                    pass
                    tokens.insert(i, Token(")", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    n += 1
                    tokens.insert(i, Token(")", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    n += 1

                    i = starting_index
                    tokens.insert(i, Token(")", tokens[i].line_number, tokens[i].filename))
                    n += 1
                    while i > 0:
                        if tokens[i].token in ["=", "{", "}", ";"]:
                            i += 1
                            break
                        i -= 1
                    tokens.insert(i, Token("0", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    n += 1
                    tokens.insert(i, Token("lognot", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    n += 1
                    tokens.insert(i, Token("(", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    n += 1
                    tokens.insert(i, Token("0", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    n += 1
                    tokens.insert(i, Token("lognot", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    n += 1
                    tokens.insert(i, Token("(", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    n += 1


                i += 1


            func.tokens = self.break_multiple_operations(func.tokens)


    def remove_logical_and(self):
        # a && b
        # =>
        # result = 0
        # if (a){
        #     if(b){
        #         result = 1
        #     }
        # }

        for func in self.functions:
            tokens = func.tokens
            
            i = 0
            n = len(tokens)
            while i < n:
                if tokens[i] == "&&":
                    before = []
                    j = i-2
                    while j >= 0:
                        if tokens[j].token in [";", "{", "}", "("]:
                            break
                        j -= 1
                    before = tokens[j+1:i-1]
                    tokens.insert(i-1, Token("0", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    tokens.insert(i-1, Token(";", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    tokens.insert(i-1, Token("if", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    tokens.insert(i-1, Token("(", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    tokens[i] = Token(")", tokens[i].line_number, tokens[i].filename)
                    i += 1
                    tokens.insert(i, Token("{", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    tokens.insert(i, Token("if", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    tokens.insert(i, Token("(", tokens[i].line_number, tokens[i].filename))
                    i += 2
                    tokens.insert(i, Token(")", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    tokens.insert(i, Token("{", tokens[i].line_number, tokens[i].filename))
                    i += 1

                    for the_token in before:
                        tokens.insert(i, Token(the_token.token, the_token.line_number, the_token.filename))
                        i += 1

                    tokens.insert(i, Token("1", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    tokens.insert(i, Token(";", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    tokens.insert(i, Token("}", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    tokens.insert(i, Token("else", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    tokens.insert(i, Token("{", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    tokens.insert(i, Token("}", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    tokens.insert(i, Token("}", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    tokens.insert(i, Token("else", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    tokens.insert(i, Token("{", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    tokens.insert(i, Token("}", tokens[i].line_number, tokens[i].filename))
                    if i + 1 < len(tokens):
                        if tokens[i+1] == ";":
                            del tokens[i+1]

                    n = len(tokens)

                i += 1

            func.tokens = tokens

    def remove_logical_not(self):
        for func in self.functions:
            tokens = func.tokens
            
            i = 0
            n = len(tokens)
            while i < n:
                if tokens[i] == "lognot":
                    j = i - 2
                    while j >= 0:
                        if tokens[j].token in [";", "{", "}", "("]:
                            break
                        j -= 1
                    before = tokens[j+1:i-1]

                    tokens[i-1] = Token("1", tokens[i].line_number, tokens[i].filename)

                    tokens[i] = Token(";", tokens[i].line_number, tokens[i].filename)
                    i += 1
                    tokens.insert(i, Token("if", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    tokens.insert(i, Token("(", tokens[i].line_number, tokens[i].filename))
                    i += 2
                    tokens.insert(i, Token(")", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    tokens.insert(i, Token("{", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    for the_token in before:
                        tokens.insert(i, Token(the_token.token, the_token.line_number, the_token.filename))
                        i += 1
                    tokens.insert(i, Token("0", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    tokens.insert(i, Token(";", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    tokens.insert(i, Token("}", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    tokens.insert(i, Token("else", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    tokens.insert(i, Token("{", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    tokens.insert(i, Token("}", tokens[i].line_number, tokens[i].filename))
                    if i + 1 < len(tokens) and tokens[i+1] == ";":
                        del tokens[i+1]

                    n = len(tokens)

                i += 1

            func.tokens = tokens
        




