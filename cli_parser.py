
from debug import *

class CliArgs:
    def __init__(self, args:list[str]):

        self.input_files = []
        self.output_file = "a.out"
        self.include_dirs = []
        self.compile_to_object = False


        argc = len(args)
        dbg(f"Invocation: {args}")

        if argc < 2:
            panic("Fatal error: no input files\n")

        for i in args:
            if i == '-h':
                self.printHelpAndExit()

        continues = 0
        for i in range(1, argc):
            if continues:
                continues -= 1
                continue

            if args[i] == "-c":
                self.compile_to_object = True
                continue
            if i + 1 < argc:
                if args[i] == '-o':
                    self.output_file = args[i+1]
                    continues = 1
                    continue
                elif args[i] == '-I':
                    self.include_dirs.append(args[i+1])
                    continues = 1
                    continue
            if len(args[i]) > 2:
                if args[i][:2] == '-o':
                    self.output_file = args[i][2:]
                    continue
                elif args[i][:2] == '-I':
                    self.include_dirs.append(args[i][2:])
                    continue
            self.input_files.append(args[i])

        dbg("Cli Parser Output:")
        dbg(f"Input Files: {self.input_files}")
        dbg(f"Output File: {self.output_file}")
        dbg(f"Include Dirs: {self.include_dirs}")
        dbg(f"Compiling to Object: {self.compile_to_object}")

        if len(self.input_files) <= 0:
            panic("Fatal error: no input files")


    def printHelpAndExit(self):
        print("Compiler help:");
        print("\t./compiler [options] [input files]");
        print("\t-h                print help information");
        print("\t-o [filename]     ");
        print("\t-I [directory]    add include directory");
        print("\t-c                compile to object file");
        exit(0)





        
