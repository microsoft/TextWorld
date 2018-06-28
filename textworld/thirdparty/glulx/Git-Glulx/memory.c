// $Id: memory.c,v 1.11 2004/01/25 21:04:19 iain Exp $

#include "git.h"
#include <stdlib.h>
#include <string.h>

const git_uint8 * gInitMem;
git_uint8 * gMem;

git_uint32 gRamStart;
git_uint32 gExtStart;
git_uint32 gEndMem;
git_uint32 gOriginalEndMem;

void initMemory (const git_uint8 * gamefile, git_uint32 size)
{
	// Make sure we have at least enough
	// data for the standard glulx header.

	if (size < 36)
		fatalError("This file is too small to be a valid glulx gamefile");
	
	gInitMem = gamefile;

	// Check the magic number. From the spec:
	//     * Magic number: 47 6C 75 6C, which is to say ASCII 'Glul'.

	if (read32 (gInitMem + 0) != 0x476c756c)
		fatalError("This is not a glulx game file");

	// Load the correct values for ramstart, extstart and endmem.

	gRamStart = read32 (gInitMem + 8);
	gExtStart = read32 (gInitMem + 12);
	gOriginalEndMem = gEndMem = read32 (gInitMem + 16);

	// Make sure the values are sane.

    if (gRamStart < 36)
	    fatalError ("Bad header (RamStart is too low)");
        
    if (gRamStart > size)
	    fatalError ("Bad header (RamStart is bigger than the entire gamefile)");
        
    if (gExtStart > size)
	    fatalError ("Bad header (ExtStart is bigger than the entire gamefile)");
        
    if (gExtStart < gRamStart)
	    fatalError ("Bad header (ExtStart is lower than RamStart)");
        
    if (gEndMem < gExtStart)
	    fatalError ("Bad header (EndMem is lower than ExtStart)");
        
	if (gRamStart & 255)
	    fatalError ("Bad header (RamStart is not a multiple of 256)");

	if (gExtStart & 255)
	    fatalError ("Bad header (ExtStart is not a multiple of 256)");

	if (gEndMem & 255)
	    fatalError ("Bad header (EndMem is not a multiple of 256)");

	// Allocate the RAM. We'll duplicate the last few bytes of ROM
	// here so that reads which cross the ROM/RAM boundary don't fail.

	gMem = malloc (gEndMem);
        if (gMem == NULL)
	    fatalError ("Failed to allocate game RAM");

	// Copy the initial memory contents.
	memcpy (gMem, gInitMem, gExtStart);

	// Zero out the extended RAM.
	memset (gMem + gExtStart, 0, gEndMem - gExtStart);
}

int verifyMemory ()
{
    git_uint32 checksum = 0;

    git_uint32 n;
    for (n = 0 ; n < gExtStart ; n += 4)
        checksum += read32 (gInitMem + n);
    
    checksum -= read32 (gInitMem + 32);
    return (checksum == read32 (gInitMem + 32)) ? 0 : 1;
}

int resizeMemory (git_uint32 newSize, int isInternal)
{
    git_uint8* newMem;
    
    if (newSize == gEndMem)
        return 0; // Size is not changed.
    if (!isInternal && heap_is_active())
        fatalError ("Cannot resize Glulx memory space while heap is active.");
    if (newSize < gOriginalEndMem)
        fatalError ("Cannot resize Glulx memory space smaller than it started.");
    if (newSize & 0xFF)
        fatalError ("Can only resize Glulx memory space to a 256-byte boundary.");
    
    newMem = realloc(gMem, newSize);
    if (!newMem)
    {	
        return 1; // Failed to extend memory.
    }
    if (newSize > gEndMem)
        memset (newMem + gEndMem, 0, newSize - gEndMem);

    gMem = newMem;
    gEndMem = newSize;
    return 0;
}

void resetMemory (git_uint32 protectPos, git_uint32 protectSize)
{
    git_uint32 protectEnd = protectPos + protectSize;
    git_uint32 i;

    // Deactivate the heap (if it was active).
    heap_clear();

    gEndMem = gOriginalEndMem;
      
    // Copy the initial contents of RAM.
    for (i = gRamStart; i < gExtStart; ++i)
    {
        if (i >= protectEnd || i < protectPos)
            gMem [i] = gInitMem [i];
    }

    // Zero out the extended RAM.
    for (i = gExtStart; i < gEndMem; ++i)
    {
        if (i >= protectEnd || i < protectPos)
            gMem [i] = 0;
    }
}

void shutdownMemory ()
{
    // We didn't allocate the ROM, so we
    // only need to dispose of the RAM.
    
    free (gMem);
    
    // Zero out all our globals.
    
    gRamStart = gExtStart = gEndMem = gOriginalEndMem = 0;
    gInitMem = gMem = NULL;
}

void memReadError (git_uint32 address)
{
    fatalError ("Out-of-bounds memory access");
}

void memWriteError (git_uint32 address)
{
    fatalError ("Out-of-bounds memory access");
}
