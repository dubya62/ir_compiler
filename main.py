
import sys

from debug import *
import standard

import cli_parser
import lexer
import normalizer
import preprocessor
import simplifier
import converter
import operator_converter
import type_checker

import memory_check


class Main:
    def __init__(self):
        pass

    def parse_args(self):
        # parse cli args
        dbg("##############################")
        dbg("Parsing Command Line Arguments")
        cli_args = cli_parser.CliArgs(sys.argv)
        return cli_args


    def start(self, args:str=None) -> int:
        dbg("Starting the IR compiler...")

        if args is None:
            cli_args = self.parse_args()
        else:
            cli_args = cli_parser.CliArgs(args)
        
        # perform lexing
        dbg("##############################")
        dbg("Performing Lexical Analysis...")
        the_lexer = lexer.Lexer(cli_args.input_files[0])
        tokens = the_lexer.tokens

        dbg("Lexical Anaylsis Finished!")
        dbg("Resulting Tokens:")
        dbg(tokens)

        # basic normalization
        dbg("##############################")
        dbg("Performing Basic Normalization...")
        the_normalizer = normalizer.Normalizer(tokens)
        tokens = the_normalizer.tokens

        dbg("Basic Normalization Finished!")
        dbg("Resulting Tokens:")
        dbg(tokens)

        # compiler directives
        dbg("##############################")
        dbg("Handling Compiler Directives...")
        the_preprocessor = preprocessor.Preprocessor(tokens, cli_args.include_dirs, cli_args.input_files[0])
        tokens = the_preprocessor.tokens

        dbg("Finished Handling Compiler Directives!")
        dbg("Resulting Tokens:")
        dbg(tokens)

        # simplification
        dbg("##############################")
        dbg("Performing Variable Simplification...")
        the_simplifier = simplifier.Simplifier(tokens)
        tokens = the_simplifier.tokens
        variable_names = the_simplifier.definitions
        final_varnum = the_simplifier.varnum

        dbg("Finished Performing Variable Simplification!")
        dbg("Resulting Tokens:")
        dbg(tokens)

        # conversion 
        dbg("##############################")
        dbg("Performing Conversion...")
        the_converter = converter.Converter(tokens)
        tokens = the_converter.tokens

        dbg("Finished Performing Conversion!")
        dbg("Resulting Tokens:")
        dbg(tokens)

        # operator
        dbg("##############################")
        dbg("Performing Operator Conversion...")
        the_operator = operator_converter.Operator(tokens, final_varnum, variable_names)
        tokens = the_operator.tokens
        the_types = the_operator.token_types

        dbg("Finished Performing Operator Conversion!")
        dbg("Resulting Tokens:")
        dbg(tokens)

        dbg("")

        dbg("##############################")
        dbg("Performing Type Checking")
        type_checker.TypeChecker(tokens)

        print_errors()
        dbg("##############################")
        dbg("Performing Memory Checking...")

        for x in tokens:
            if issubclass(type(x), standard.Function):
                print(f"Checking function ({x.name})")
                memory_check.check_memory([y.token for y in x.tokens])
                print("\tFunction is Safe")
            else:
                print(f"Skipping ({x})")

        return tokens, the_types


if __name__ == '__main__':
    main = Main()
    main.start()

        
