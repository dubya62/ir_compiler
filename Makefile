

CODEFILES :=*.py
MAIN :=main

TESTFLAGS :=testcase3.c


$(MAIN): $(CODEFILES) memory-checking
	python $(MAIN).py $(TESTFLAGS)

memory-checking:
	rm -rf memory-checker/
	cp -r ~/Desktop/IR-Memory-Checker/ memory-checker
	cp memory-checker/memory_check.py .





