
from debug import *
from token import *

import standard_types

class Converter:
    def __init__(self, tokens:list[Token]) -> list[Token]:
        self.tokens = tokens

        self.current_label = 0

        # convert else if(){} into else { if(){} }
        self.tokens = self.convert_else_ifs(self.tokens)

        # convert breaks into jumps to the end of loops
        self.tokens = self.convert_breaks(self.tokens)

        # convert while loops to if statements and jumps
        self.tokens = self.convert_while_loops(self.tokens)

        # convert for loops to if statements and jumps
        self.tokens = self.convert_for_loops(self.tokens)


    def convert_else_ifs(self, tokens:list[Token]) -> list[Token]:
        i = 0
        n = len(tokens)
        while i < n:
            if tokens[i] == "else":
                if i + 1 < n:
                    if tokens[i+1] == "if":
                        tokens.insert(i+1, Token("{", tokens[i].line_number, tokens[i].filename))
                        i += 2
                        n += 1
                        braces = []
                        while i < n:
                            if tokens[i] == "{":
                                braces.append("{")
                            elif tokens[i] == "}":
                                if len(braces) == 0:
                                    fatal_error(tokens[i], "Mismatched }...")
                                braces.pop()
                                if len(braces) == 0:
                                    if i + 1 < n and tokens[i+1] == "else":
                                        i += 1
                                        continue
                                    tokens.insert(i, Token("}", tokens[i].line_number, tokens[i].filename))
                                    n += 1
                                    break
                            i += 1

            i += 1

        return tokens


    def convert_breaks(self, tokens:list[Token]) -> list[Token]:
        i = 0
        n = len(tokens)

        brace_levels = []
        jump_labels = []
        jump_back_labels = []
        statement_increments = []
        statement_names = []
        open_braces = 0

        while i < n:
            if tokens[i] in ["for", "while", "switch"]:
                statement_names.append(tokens[i].token)
                increment = []
                if tokens[i] == "for":
                    j = i
                    opened = []
                    condition = 0
                    while j < n:
                        if tokens[j] == "(":
                            opened.append("(")
                        elif tokens[j] == ")":
                            if len(opened) == 0:
                                fatal_error(tokens[j], "Unmatched )...")
                            opened.pop()
                            if len(opened) == 0:
                                break
                        elif tokens[j] == ";":
                            if len(opened) == 1:
                                condition += 1
                                j += 1
                                continue

                        if condition == 2:
                            increment.append(tokens[j])
                        j += 1
                print(f"increment: {increment}")
                statement_increments.append(increment)
                brace_levels.append(open_braces)
                jump_labels.append(self.current_label)
                self.current_label += 1
                jump_back_labels.append(self.current_label)
                tokens.insert(i, Token("@" + str(self.current_label), tokens[i].line_number, tokens[i].filename))
                i += 1
                tokens.insert(i, Token(":", tokens[i].line_number, tokens[i].filename))
                i += 1
                n += 2
                self.current_label += 1
            elif tokens[i] == "{":
                open_braces += 1
            elif tokens[i] == "}":
                open_braces -= 1

                print("+++++++++++")
                print(tokens)
                print(brace_levels)
                print(open_braces)
                if len(brace_levels) > 0 and brace_levels[-1] == open_braces:
                    brace_levels.pop()
                    i += 1
                    tokens.insert(i, Token("@" + str(jump_labels[-1]), tokens[i].line_number, tokens[i].filename))
                    i += 1
                    n += 1
                    tokens.insert(i, Token(":", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    n += 1
                    self.current_label += 1
                    jump_labels.pop()
                    jump_back_labels.pop()
                    statement_increments.pop()
                    statement_names.pop()
                    continue
            elif tokens[i] == "continue":
                if len(jump_back_labels) == 0:
                    fatal_error(tokens[i], "Cannot break outside of loop...")
                the_label = 1
                for j in range(-1, -len(statement_names)-1, -1):
                    if statement_names[j] in ["for", "while"]:
                        the_label = j
                        break
                if the_label == 1:
                    fatal_error(tokens[i], "ERROR: Cannot use continue in switch-case.");

                tokens[i].token = "@" + str(jump_back_labels[the_label])
                tokens.insert(i, Token("goto", tokens[i].line_number, tokens[i].filename))
                for tok in statement_increments[-1]:
                    tokens.insert(i, tok)
                    i += 1
                    n += 1
                if len(statement_increments[-1]) > 0:
                    tokens.insert(i, Token(";", tokens[i].line_number, tokens[i].filename))
                    i += 1
                    n += 1
                n += 1
            elif tokens[i] == "break":
                if len(jump_labels) == 0:
                    fatal_error(tokens[i], "Cannot break outside of loop...")
                del tokens[i]
                n -= 1
                tokens.insert(i, Token("goto", tokens[i].line_number, tokens[i].filename))
                n += 1
                i += 1
                tokens.insert(i, Token("@" + str(jump_labels[-1]), tokens[i].line_number, tokens[i].filename))
                n += 1
                i += 1
                continue

            i += 1

        return tokens


    def convert_while_loops(self, tokens:list[Token]) -> list[Token]:
        """
        while (i < 10){
        }
        =>
        @x:
        if (i < 10){
            
            goto @x;
        }

        """

        i = 0
        n = len(tokens)
        while i < n:
            if tokens[i] == "while":
                tokens[i].token = "if"
                tokens.insert(i, Token("@" + str(self.current_label), tokens[i].line_number, tokens[i].line_number))
                i += 1
                n += 1
                tokens.insert(i, Token(":", tokens[i].line_number, tokens[i].filename))
                i += 1
                n += 1
                starting_index = i

                braces = []
                while i < n:
                    if tokens[i] == "{":
                        braces.append("{")
                    elif tokens[i] == "}":
                        if len(braces) == 0:
                            fatal_error(tokens[i], "Mismatched }...")
                        braces.pop()
                        if len(braces) == 0:
                            break;
                    i += 1

                tokens.insert(i, Token("goto", tokens[i].line_number, tokens[i].filename))
                i += 1
                n += 1
                tokens.insert(i, Token("@" + str(self.current_label), tokens[i].line_number, tokens[i].filename))
                i += 1
                n += 1
                tokens.insert(i, Token(";", tokens[i].line_number, tokens[i].filename))
                i += 1
                n += 1
                
                self.current_label += 1
                i = starting_index
            i += 1

        return tokens

    
    def convert_for_loops(self, tokens:list[Token]) -> list[Token]:
        """
        for ($TYPE i=0; i<10; i++){
            "hello";
        }
        =>
        $TYPE i=0;
        @x:
        if (i < 10){
            "hello";
            i++;
            goto @x;
        }
        """
        i = 0
        n = len(tokens)

        while i < n:
            if tokens[i] == "for":
                original_jump = None
                if i > 1:
                    if tokens[i-1] == ":":
                        original_jump = tokens[i-2]
                        del tokens[i-1]
                        i -= 1
                        n -= 1
                        del tokens[i-1]
                        i -= 1
                        n -= 1


                tokens[i].token = "if"

                if i + 1 >= n:
                    fatal_error(tokens[i], "Expected ( after for...")
                if not (tokens[i+1] == "("):
                    fatal_error(tokens[i+1], "Expected ( after for...")
                first_start = i + 2
                first_end = i + 2
                while first_end < n:
                    if tokens[first_end] == ";":
                        break
                    first_end += 1

                first = tokens[first_start:first_end+1]
                tokens = tokens[:first_start] + tokens[first_end+1:]
                n = len(tokens)

                for x in first:
                    tokens.insert(i, x)
                    i += 1
                    n += 1
                if original_jump is None:
                    tokens.insert(i, Token("@" + str(self.current_label), tokens[i].line_number, tokens[i].filename))
                else:
                    tokens.insert(i, original_jump)
                i += 1
                n += 1
                tokens.insert(i, Token(":", tokens[i].line_number, tokens[i].filename))
                i += 1
                n += 1



                last_start = i + 1
                while last_start < n:
                    if tokens[last_start] == ";":
                        del tokens[last_start]
                        n -= 1
                        break
                    last_start += 1
                last_end = last_start
                while last_end < n:
                    if tokens[last_end] == ")":
                        break
                    last_end += 1
                last = tokens[last_start:last_end]
                tokens = tokens[:last_start] + tokens[last_end:]
                n = len(tokens)
                last_end = last_start

                if len(last) > 0:
                    last.append(Token(";", last[0].line_number, last[0].filename))

                # put the last stuff just before the ending }
                braces = []
                while last_end < n:
                    if tokens[last_end] == "{":
                        braces.append("{")
                    elif tokens[last_end] == "}":
                        if len(braces) == 0:
                            fatal_error(tokens[last_end], "Mismatched }...")
                        braces.pop()
                        if len(braces) == 0:
                            for x in last:
                                tokens.insert(last_end, x)
                                last_end += 1
                                n += 1
                            tokens.insert(last_end, Token("goto", tokens[last_end].line_number, tokens[last_end].filename))
                            last_end += 1
                            n += 1
                            tokens.insert(last_end, Token("@" + str(self.current_label), tokens[last_end].line_number, tokens[last_end].filename))
                            last_end += 1
                            n += 1
                            self.current_label += 1
                            tokens.insert(last_end, Token(";", tokens[last_end].line_number, tokens[last_end].filename))
                            last_end += 1
                            n += 1
                            break
                                        
                    last_end += 1

            

            i += 1

        return tokens
        


