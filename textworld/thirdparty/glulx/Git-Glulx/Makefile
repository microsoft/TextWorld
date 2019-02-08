# Unix makefile for Git (shamelessly ripped off from Glulxe's makefile)

# -----------------------------------------------------------------
# Step 1: pick a Glk library.

# Note: when using xglk, do NOT define USE_MMAP in step 2, below.

GLK = cheapglk
#GLK = glkterm
#GLK = xglk

GLKINCLUDEDIR = ../$(GLK)
GLKLIBDIR = ../$(GLK)
GLKMAKEFILE = Make.$(GLK)

# -----------------------------------------------------------------
# Step 2: pick a C compiler.

# Generic C compiler
CC = cc -O2
OPTIONS = 

# Best settings for GCC 2.95. This generates faster code than
# GCC 3, so you should use this setup if possible.
#CC = gcc -Wall -O3
#OPTIONS = -DUSE_DIRECT_THREADING -DUSE_MMAP -DUSE_INLINE

# Best settings for GCC 3. The optimiser in this version of GCC
# is somewhat broken, so we can't use USE_DIRECT_THREADING.
#CC = gcc -Wall -O3
#OPTIONS = -DUSE_MMAP -DUSE_INLINE

# Mac OS X (PowerPC) settings.
#CC = gcc2 -Wall -O3 -no-cpp-precomp
#OPTIONS = -DUSE_DIRECT_THREADING -DUSE_BIG_ENDIAN_UNALIGNED -DUSE_MMAP -DUSE_INLINE

# -----------------------------------------------------------------
# Step 3: decide where you want to install the compiled executable.

INSTALLDIR = /usr/local/bin

# -----------------------------------------------------------------
# You shouldn't have to change anything from here on down.

MAJOR = 1
MINOR = 3
PATCH = 5

-include $(GLKINCLUDEDIR)/$(GLKMAKEFILE)

EXENAME := git-glulx-ml

CFLAGS = $(OPTIONS) -I$(GLKINCLUDEDIR)

LIBS = -L$(GLKLIBDIR) $(GLKLIB) $(LINKLIBS) -lm

HEADERS = version.h git.h config.h compiler.h \
	memory.h opcodes.h labels.inc

SOURCE = compiler.c gestalt.c git.c git_mac.c git_unix.c \
	git_windows.c glkop.c heap.c memory.c opcodes.c \
	operands.c peephole.c savefile.c saveundo.c \
	search.c terp.c accel.c

OBJS = git.o memory.o compiler.o opcodes.o operands.o \
	peephole.o terp.o glkop.o search.o git_unix.o \
	savefile.o saveundo.o gestalt.o heap.o accel.o

TESTS = test/test.sh \
	test/Alabaster.gblorb test/Alabaster.walk test/Alabaster.golden

all: $(EXENAME)

$(EXENAME): $(OBJS)
	$(CC) $(OPTIONS) -o $@ $(OBJS) $(LIBS)

install: git
	cp $(EXENAME) $(INSTALLDIR)/$(EXENAME)

clean:
	rm -f *~ *.o $(EXENAME) test/*.tmp

$(OBJS): $(HEADERS)

version.h: Makefile
	echo "// Automatically generated file -- do not edit!" > version.h
	echo "#define GIT_MAJOR" $(MAJOR) >> version.h
	echo "#define GIT_MINOR" $(MINOR) >> version.h
	echo "#define GIT_PATCH" $(PATCH) >> version.h

DISTZIP = git-$(MAJOR)$(MINOR)$(PATCH).zip

DISTDIR = git-$(MAJOR).$(MINOR).$(PATCH)

DISTFILES = README.txt Makefile Makefile.win win $(HEADERS) $(SOURCE)

dist: $(DISTFILES)
	rm -rf $(DISTDIR)
	mkdir $(DISTDIR)
	cp -r $(DISTFILES) $(DISTDIR)
	mkdir $(DISTDIR)/test
	cp $(TESTS) $(DISTDIR)/test
	find $(DISTDIR) -name "CVS" | xargs rm -rf
	rm -f $(DISTZIP)
	zip -r $(DISTZIP) $(DISTDIR)

test: git
	sh test/test.sh
