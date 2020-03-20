# Minimal makefile to call the Makefile found in the source folder.
#

# Put it first so that "make" without argument is like "make help".
help:
	$(MAKE) -C source/ help

.PHONY: help Makefile

# Catch-all target: route all targets to the Makefile in the source folder.
%: Makefile
	$(MAKE) -C source/ $@