DYLD := DYLD_LIBRARY_PATH=/opt/homebrew/lib

test:
	$(DYLD) python3 -m pytest -v

run:
	$(DYLD) python3 cli.py $(ARGS)
