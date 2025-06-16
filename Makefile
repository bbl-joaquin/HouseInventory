# Makefile

# Define the Python interpreter path (usually python3 or python, depending on your system)
PYTHON = python3

# Define the target for running the main script
run:
	$(PYTHON) -m barcode_lib.main
	
# Define the target for running tests
test:
	$(PYTHON) -m unittest discover test/

.PHONY: run test
