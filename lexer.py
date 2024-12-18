
from debug import *
from token import *

class Lexer:

    def __init__(self, filename:str):
        self.filename = filename

        self.file_data = self.open_file(self.filename)

        self.tokens = self.tokenize(self.file_data)
        for token in self.tokens:
            token.filename = self.filename

        # combine postfix and prefix operators while there are still spaces
        i = 0
        n = len(self.tokens)
        while i < n:
            if self.tokens[i].token in ["+", "-"]:
                if i + 1 < n and self.tokens[i].token == self.tokens[i+1].token:
                    self.tokens[i].token += self.tokens[i+1].token
                    del self.tokens[i+1]
                    n -= 1
            i += 1


    def open_file(self, filename:str) -> str:
        dbg(f"Opening file {filename}...")
        try:
            f = open(filename, 'r')
        except:
            panic(f"Unable to open file ({filename})")

        dbg(f"File read successfully!")
        return f.read()


    def tokenize(self, file_data:str) -> list[Token]:
        i = 0
        n = len(file_data)

        breakChars = {"~", "!", "#", "%", "^", "&", "*", "(", ")", "-", "+", "=", "{", "}", "[", "]", "|", '\\', "'", '"', ';', ":", "/", "?", ".", ",", "<", ">", '\n', '\t', ' '}

        result = []
        line_number = 1

        current_token = ""
        while i < n:

            if file_data[i] in breakChars:
                if file_data[i] == "\n":
                    line_number += 1

                if len(current_token) > 0:
                    result.append(Token(current_token, line_number, ""))

                result.append(Token(file_data[i], line_number, ""))

                current_token = ""

            else:
                current_token += file_data[i]

            i += 1

        return result





