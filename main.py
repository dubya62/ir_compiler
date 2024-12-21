
import sys

from debug import *

import cli_parser
import lexer
import normalizer
import preprocessor


class Main:
    def __init__(self):
        pass


    def start(self) -> int:
        dbg("Starting the TCABIR compiler...")

        # parse cli args
        dbg("##############################")
        dbg("Parsing Command Line Arguments")
        cli_args = cli_parser.CliArgs(sys.argv)
        
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

        """
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
        the_operator = operator.Operator(tokens, final_varnum, variable_names)
        tokens = the_operator.tokens

        dbg("Finished Performing Operator Conversion!")
        dbg("Resulting Tokens:")
        dbg(tokens)
        """


        dbg("")
        print_errors()

        return 0


if __name__ == '__main__':
    main = Main()
    main.start()

        
