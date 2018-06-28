Git is an interpreter for the Glulx virtual machine. Its homepage is here:

http://ifarchive.org/indexes/if-archiveXprogrammingXglulxXinterpretersXgit.html

Git's main goal in life is to be fast. It's about five times faster than Glulxe,
and about twice as fast as Frotz (using the same Inform source compiled for the
Z-machine). It also tries to be reasonably careful with memory: it's possible to
trade speed off against memory by changing the sizes of Git's internal buffers.

I wrote Git because I want people to be able to write huge games or try out
complicated algorithms without worrying about how fast their games are going to
run. I want to play City of Secrets on a Palm without having to wait ten seconds
between each prompt.

Have fun, and let me know what you think!

  Iain Merrick (Original author)
  iain@diden.net

  David Kinder (Current maintainer)
  davidk@davidkinder.co.uk

--------------------------------------------------------------------------------

* Building and installing Git

This is just source code, not a usable application. You'll have to do a bit of
work before you can start playing games with it. If you're not confident about
compiling stuff yourself, you probably want to wait until somebody uploads a
compiled version of Git for your own platform.

Git needs to be linked with a Glk library in order to run. This can be easy or
hard, depending on what kind of computer you're using and whether you want Git
to be able to display graphics and play sounds. To find a suitable Glk library,
look here:

http://eblong.com/zarf/glk/
http://ifarchive.org/indexes/if-archiveXprogrammingXglkXimplementations.html

Exactly how you build and link everything depends on what platform you're on and
which Glk library you're using. The supplied Makefile should work on any Unix
machine (including Macs with OS X), but you'll probably want to tweak it to
account for your particular setup. If you're not using Unix, I'm afraid you'll
have to play it by ear. If the Glk library you chose comes with instructions,
that's probably a good place to start.

On Unix, git_unix.c contains the startup code required by the Glk library.
git_mac.c and git_windows.c contain startup code for MacGlk and WinGlk
respectively, but I can't guarantee that they're fully up-to-date.

It should be possible to build Git with any C compiler, but it works best with
GCC, because that has a non-standard extension that Git can use for a big speed
boost. GCC 2.95 actually generates faster code than later versions, so if you
have a choice, use the former. (On OS X, this means compiling with 'gcc2'.)

--------------------------------------------------------------------------------

* Configuring Git

There are several configuration options you can use when compiling Git. Have a
look at config.h and see which ones look applicable to your platform. The
Makefile includes settings to configure Git for maximum speed on Mac OS X; the
best settings for other Unix platforms should be similar.

The most important setting is USE_DIRECT_THREADING, which makes the interpreter
engine use GCC's labels-as-values extension, but this only works with GCC 2.95.

--------------------------------------------------------------------------------

* Porting to a new platform

To do a new port, you first need to find a suitable Glk library, or write a new
one. Then you need to write the startup code. Start with a copy of git_unix.c,
git_mac.c or git_windows.c and modify it appropriately.

The startup code needs to implement the following functions:

  void glk_main()                 // Standard Glk entrypoint
  void fatalError(const char* s)  // Display error message and quit

In glk_main(), you need to locate the game file somehow. Then you have two
options. You can open the game as a Glk stream and pass it to this function:

  extern void gitWithStream (strid_t stream,
                             git_uint32 cacheSize,
                             git_uint32 undoSize);

Or you can load the game yourself, and just pass Git a pointer to your buffer:

  extern void git (const git_uint8 * game,
                   git_uint32 gameSize,
                   git_uint32 cacheSize,
                   git_uint32 undoSize);

If the operating system provides some way of memory-mapping files (such as
Unix's mmap() system call), you should do that and call git(), because it will
allow the game to start up much more quickly. If you can't do memory-mapping,
you should just open the game as a file stream and call gitWithStream(). Note
that some Glk libraries, such as xglk, aren't compatible with memory-mapped
files.

"cacheSize" and "undoSize" tell Git what size to use for its two main internal
buffers. Both sizes are in bytes. You may want to make these values
user-configurable, or you may just want to pick values that make sense for your
platform and use those. (My Unix version currently uses fixed values, but I'm
going to add some optional command-line parameters to override these defaults.)

"cacheSize" is the size of the buffer used to store Glulx code that Git has
recompiled into its internal format. Git will run faster with a larger buffer,
but using a huge buffer is just a waste of memory; 256KB is plenty.

"undoSize" is the maximum amount of memory used to remember previous moves. The
larger you make it, the more levels of undo will be available. The amount of
memory required to remember one undo position varies from a few KB up to tens of
KB. 256KB is usually enough to store dozens of moves.

--------------------------------------------------------------------------------

* Known problems

GCC 3 has bigger problems than I thought. On PowerPC, the direct threading
option results in much slower code; and on x86, terp.c crashes GCC itself if
direct threading is used. GCC 4 seems to work, given some very limited testing,
but still results in slow code. Therefore, I recommend that you use GCC 2.95 if
possible. If you only have GCC 3, don't define USE_DIRECT_THREADING.

Some Glk libraries, such as xglk, can't deal with memory-mapped files. You can
tell that this is happening if Git can open .ulx files, but complains that .blb
files are invalid. The solution is to use gitWithStream() rather than git() in
your startup file, and make sure you're giving it a file stream rather than a
memory stream. If you're using the git_unix.c startup file, just make sure
USE_MMAP isn't defined.

1-byte and 2-byte local variables are not implemented. This means git can't
play games created with old versions of the Superglus system. As these small
local variables now deprecated, it is unlikely that this will be fixed.

In the search opcodes, direct keys don't work unless they're exactly 4 bytes
long.

--------------------------------------------------------------------------------

* Copyright information

Note: previous versions of Git used an informal freeware license, but I've
decided it's worth formalising. As of version 1.2.3, I've switched to the
MIT license.

Copyright (c) 2003 Iain Merrick

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

--------------------------------------------------------------------------------

* Credits

Andrew Plotkin invented Glulx, so obviously Git wouldn't exist without him. I
also reused some code from his Glulxe interpreter (glkop.c and search.c), which
saved me a lot of time and let me concentrate on the more interesting stuff.

Many thanks are due to John Cater, who not only persuaded me to use source
control, but let me use his own CVS server. John also provided lots of useful
advice and encouragement, as did Sean Barrett.

Thanks also to Joe Mason, Adam Thornton, Simon Baldwin and Joonas Pihlaja who
were among the first to try it out and complain that it wasn't working. Joonas
also gets special brownie points for trying out more bizarre boundary cases than
I realised existed in the first place.

Tor Andersson was apparently the first person to use setmemsize, since he also
explained why it didn't work and contributed a fix. Thanks, Tor!

David Kinder has done a stellar job of maintaining the code recently. Thanks
also to Eliuk Blau for tracking down bugs in the memory management opcodes.

--------------------------------------------------------------------------------

* Version History

1.3.5 2016-11-19  Fixed a bug when the streamnum opcode is called with the
                  smallest possible negative number.

1.3.4 2015-06-13  Performance improvements from Peter De Wachter, which give
                  approximately a 15% speed increase.

1.3.3 2014-03-15  Added acceleration functions 8 through 13, which work
                  correctly when the Inform 6 compiler setting NUM_ATTR_BYTES
                  is changed, contributed by Andrew Plotkin.

1.3.2 2013-03-26  A further fix to glkop.c, following the similar fix added to
                  Glulxe 0.5.1.
                  Increased the default undo buffer size in all ports to 2Mb.

1.3.1 2012-11-09  Further fixes to glkop.c, following similar fixes added to
                  Glulxe 0.5.0.

1.3.0 2011-12-16  Fixed a bug in glkop.c dispatching, to do with arrays
                  of opaque objects, following a similar fix in Glulxe.
                  Fixed a problem with the memory heap not being sorted
                  correctly on restore, contributed by Brady Garvin.

1.2.9 2011-08-28  Fixed a bug in glkop.c dispatching, to do with optional
                  array arguments, following a similar fix in Glulxe.
                  Glk array and string operations are now checked for memory
                  overflows (though not for ROM writing), following a similar
                  fix in Glulxe.

1.2.8 2010-08-25  Fixed a problem with 'undo' when compiled as 64 bit,
                  contributed by Ben Cressey.
                  Fixed a sign problem for the @fceil opcode, following a
                  similar fix in Glulxe.

1.2.7 2010-08-20  Floating point opcode support (VM spec 3.1.2).
                  Restart does not now discard undo information, so that a
                  restart can be undone.

1.2.6 2010-02-09  Imported fix for retained Glk array handling from Glulxe.

1.2.5 2009-11-21  Fixes for problems shown by Andrew Plotkin's glulxercise test
                  cases, from David Kinder.

1.2.4 2009-04-02  More David Kinder! Accelerated opcode support (VM spec 3.1.1).

1.2.3 2009-02-22  David Kinder and Eliuk Blau fixed some memory management bugs.
                  Added a regression test (thanks to Emily Short for assistance)
                  Switched to MIT-style license (see above).

1.2.2 2009-01-21  malloc & mfree contributed by the most excellent David Kinder.

1.2.1 2008-09-14  Support for 64-bit machines, contributed by Alexander Beels.
                  Fix for crashing bug in RESTORE, contributed by David Kinder.
                  Non-Unicode display bug fix, contributed by Jeremy Bernstein.

1.2   2008-01-06  Minor version increment for VM spec 3.1.
                  Implemented mzero and mcopy, but not malloc and mfree (yet).

1.1.3 2006-10-04  Fixed a bug in the cache logic that broke the game Floatpoint.
                  Added some other caching tweaks and put in a few more asserts.

1.1.2 2006-08-22  streamnum in filter I/O mode no longer prints a garbage char.
                  Merged in David Kinder's updated Windows startup code.
                  
1.1.1 2006-08-17  Wow, over a year since the last update.
                  Rolled in Tor Andersson's fix for setmemsize.

1.1   2004-12-22  Minor version increment because we now implement VM spec 3.0.
                  Implemented new Unicode opcodes and string types.

1.0.6 2004-12-10  Random number generator now handles random(0) correctly.
                  Code cache now tracks the number of function calls properly.
                  Fixed a bug that could hang the terp when the cache filled up.

1.0.5 2004-05-31  Random number generator is now initialised properly.
                  Some source files had Mac line-endings, now fixed.
                  Version number is now set in the Makefile, not in git.h.
                  Merged David Kinder's Windows Git code into main distribution.

1.0.4 2004-03-13  Fixed a silly bug in direct threading mode that broke stkroll.
                  Memory access bounds checking has been tightened up slightly.
                  aload and astore now work correctly with negative offsets.
                  Rewrote the shift opcodes a bit more defensively.
                  Implemented the "verify" opcode.
                  Code in RAM is no longer cached by default.
                  Adding some special opcodes to control the code cache.
                  Bad instructions are now caught in the terp, not the compiler.
                  Now passes all of Joonas' indirect string decoding tests.
                  
1.0.3 2004-01-22  No longer hangs when using streamnum in the "filter" I/O mode.
                  setstringtbl opcode now works correctly.

1.0.2 2003-10-25  Stupid bug in 1.0.1 -- gitWithStream() was broken and wasn't
                  able to load Blorb files. Now it's *really* fixed.

1.0.1 2003-10-23  Fixed a bug where strings were printed as "[string]"
                  Fixed a bug in tailcall
                  Implemented setmemsize
                  Implemented protect
                  Moved git_init_dispatch() call out of startup code, into git.c
                  Added divide-by-zero check
                  Compiler now stops when it finds a 'quit' or 'restart'
                  Added gitWithStream() as a workaround for xglk

1.0   2003-10-18  First public release

