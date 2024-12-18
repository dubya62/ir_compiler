

CODEFILES :=*.py
MAIN :=main

TESTFLAGS :=testing.c


$(MAIN): $(CODEFILES)
	python $(MAIN).py $(TESTFLAGS)




