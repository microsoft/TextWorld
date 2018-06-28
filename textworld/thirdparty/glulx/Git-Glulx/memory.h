// $Id: memory.h,v 1.7 2004/01/25 21:04:19 iain Exp $
// Functions and macros for accessing game memory.

#ifndef GIT_MEMORY_H
#define GIT_MEMORY_H

#include "config.h"

// --------------------------------------------------------------
// Macros for reading and writing big-endian data.

#ifdef USE_BIG_ENDIAN_UNALIGNED
// We're on a big-endian platform which can handle unaligned
// accesses, such as the PowerPC. This means we can read and
// write multi-byte values in glulx memory directly, without
// having to pack and unpack each byte.

#define read32(ptr)    (*((git_uint32*)(ptr)))
#define read16(ptr)    (*((git_uint16*)(ptr)))
#define write32(ptr,v) (read32(ptr)=(git_uint32)(v))
#define write16(ptr,v) (read16(ptr)=(git_uint16)(v))

#else
// We're on a little-endian platform, such as the x86, or a
// big-endian platform that doesn't like unaligned accesses,
// such as the 68K. This means we have to read and write the
// slow and tedious way.

#define read32(ptr)    \
  ( (git_uint32)(((git_uint8 *)(ptr))[0] << 24) \
  | (git_uint32)(((git_uint8 *)(ptr))[1] << 16) \
  | (git_uint32)(((git_uint8 *)(ptr))[2] << 8)  \
  | (git_uint32)(((git_uint8 *)(ptr))[3]))
#define read16(ptr)    \
  ( (git_uint16)(((git_uint8 *)(ptr))[0] << 8)  \
  | (git_uint16)(((git_uint8 *)(ptr))[1]))

#define write32(ptr, v)   \
  (((ptr)[0] = (git_uint8)(((git_uint32)(v)) >> 24)), \
   ((ptr)[1] = (git_uint8)(((git_uint32)(v)) >> 16)), \
   ((ptr)[2] = (git_uint8)(((git_uint32)(v)) >> 8)),  \
   ((ptr)[3] = (git_uint8)(((git_uint32)(v)))))
#define write16(ptr, v)   \
  (((ptr)[0] = (git_uint8)(((git_uint32)(v)) >> 8)),  \
   ((ptr)[1] = (git_uint8)(((git_uint32)(v)))))

#endif // USE_BIG_ENDIAN_UNALIGNED

GIT_INLINE git_uint32 readtag (const char *ptr) {
	return read32((const git_uint8 *)ptr);
}

// Accessing single bytes is easy on any platform.

#define read8(ptr)     (*((git_uint8*)(ptr)))
#define write8(ptr, v) (read8(ptr)=(git_uint8)(v))

// --------------------------------------------------------------
// Globals

extern git_uint32 gRamStart; // The start of RAM.
extern git_uint32 gExtStart; // The start of extended memory (initialised to zero).
extern git_uint32 gEndMem;   // The current end of memory.
extern git_uint32 gOriginalEndMem; // The value of EndMem when the game was first loaded.

// This is the entire gamefile, as read-only memory. It contains
// both the ROM, which is constant for the entire run of the program,
// and the original RAM, which is useful for checking what's changed
// when saving to disk or remembering a position for UNDO.
extern const git_uint8 * gInitMem;

// This is the current contents of memory. This buffer includes
// both the ROM and the current contents of RAM.
extern git_uint8 * gMem;


// --------------------------------------------------------------
// Functions

// Initialise game memory. This sets up all the global variables
// declared above. Note that it does *not* copy the given memory
// image: it must be valid for the lifetime of the program.

extern void initMemory (const git_uint8 * game, git_uint32 gameSize);

// Verifies the gamefile based on its checksum. 0 on success, 1 on failure.

extern int verifyMemory ();

// Resizes the game's memory. Returns 0 on success, 1 on failure.

extern int resizeMemory (git_uint32 newSize, int isInternal);

// Resets memory to its initial state. Call this when the game restarts.

extern void resetMemory (git_uint32 protectPos, git_uint32 protectSize);

// Disposes of all the data structures allocated in initMemory().

extern void shutdownMemory ();

// Utility functions -- these just pass an appropriate
// string to fatalError().

extern git_noreturn void memReadError (git_uint32 address);
extern git_noreturn void memWriteError (git_uint32 address);

// Functions for reading and writing game memory.

GIT_INLINE git_uint32 memRead32 (git_uint32 address)
{
    if (address <= gEndMem - 4)
        return read32 (gMem + address);
    else
        return memReadError (address), 0;
}

GIT_INLINE git_uint32 memRead16 (git_uint32 address)
{
    if (address <= gEndMem - 2)
        return read16 (gMem + address);
    else
        return memReadError (address), 0;
}

GIT_INLINE git_uint32 memRead8 (git_uint32 address)
{
    if (address < gEndMem)
        return read8 (gMem + address);
    else
        return memReadError (address), 0;
}

GIT_INLINE void memWrite32 (git_uint32 address, git_uint32 val)
{
    if (address >= gRamStart && address <= (gEndMem - 4))
        write32 (gMem + address, val);
    else
        memWriteError (address);
}

GIT_INLINE void memWrite16 (git_uint32 address, git_uint32 val)
{
    if (address >= gRamStart && address <= (gEndMem - 2))
        write16 (gMem + address, val);
    else
        memWriteError (address);
}

GIT_INLINE void memWrite8 (git_uint32 address, git_uint32 val)
{
    if (address >= gRamStart && address < gEndMem)
        write8 (gMem + address, val);
    else
        memWriteError (address);
}

#endif // GIT_MEMORY_H
