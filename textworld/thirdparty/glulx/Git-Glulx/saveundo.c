// $Id: saveundo.c,v 1.15 2003/10/20 16:05:06 iain Exp $

#include "git.h"
#include <stdlib.h>
#include <string.h>
#include <assert.h>

typedef const git_uint8 * MemoryPage;
typedef MemoryPage * MemoryMap;

typedef struct UndoRecord UndoRecord;

struct UndoRecord
{
    git_uint32   endMem;
    MemoryMap    memoryMap;
    git_sint32   stackSize;
    git_sint32 * stack;
    glui32       heapSize;
    glui32     * heap;
    UndoRecord * prev;
    UndoRecord * next;
};

static UndoRecord * gUndo = NULL;
static git_uint32 gUndoSize = 0;
static git_uint32 gMaxUndoSize = 256 * 1024;

static void reserveSpace (git_uint32);
static void deleteRecord (UndoRecord * u);

void initUndo (git_uint32 size)
{
    gMaxUndoSize = size;
    gUndoSize = 0;
    gUndo = NULL;
}

int saveUndo (git_sint32 * base, git_sint32 * sp)
{
    git_uint32 undoSize = sizeof(UndoRecord);
    git_uint32 mapSize = sizeof(MemoryPage*) * (gEndMem - gRamStart) / 256;
    git_uint32 stackSize = sizeof(git_sint32) * (sp - base);
    git_uint32 totalSize = undoSize + mapSize + stackSize;

    git_uint32 addr = gRamStart; // Address in glulx memory.
    git_uint32 slot = 0;         // Slot in our memory map.
    
    UndoRecord * undo = malloc (undoSize);
    if (undo == NULL)
        fatalError ("Couldn't allocate undo record");
        
    undo->endMem = gEndMem;
    undo->memoryMap = malloc (mapSize);
    undo->stackSize = stackSize;
    undo->stack = malloc (stackSize);
    undo->prev = NULL;
    undo->next = NULL;

    if (undo->memoryMap == NULL || undo->stack == NULL)
        fatalError ("Couldn't allocate memory for undo");

    // Save the stack.
    memcpy (undo->stack, base, undo->stackSize);

    // Are we diffing against the previous undo record,
    // or against the initial gamefile state?
    if (gUndo == NULL)
    {
        // We're diffing against the gamefile.        
        for ( ; addr < gExtStart ; addr += 256, ++slot)
        {
            if (memcmp (gInitMem + addr, gMem + addr, 256) != 0)
            {
                // We need to save this page.
                git_uint8 * page = malloc(256);
                if (page == NULL)
                    fatalError ("Couldn't allocate memory for undo");
                    
                memcpy (page, gMem + addr, 256);
                undo->memoryMap[slot] = page;
                totalSize += 256;
            }
            else
            {
                // We don't need to save this page.
                // Just make it point into ROM.
                undo->memoryMap[slot] = gInitMem + addr;
            }
        }

        // If the memory map has been extended, save the exended area
        for (addr = gExtStart ; addr < gEndMem ; addr += 256, ++slot)
        {
            git_uint8 * page = malloc(256);
            if (page == NULL)
                fatalError ("Couldn't allocate memory for undo");
                
            memcpy (page, gMem + addr, 256);
            undo->memoryMap[slot] = page;
            totalSize += 256;
        }
    }
    else
    {
        // We're diffing against the most recent undo record.
        git_uint32 endMem = (gUndo->endMem < gEndMem) ? gUndo->endMem : gEndMem;
        for ( ; addr < endMem ; addr += 256, ++slot)
        {
            if (memcmp (gUndo->memoryMap [slot], gMem + addr, 256) != 0)
            {
                // We need to save this page.
                git_uint8 * page = malloc(256);
                memcpy (page, gMem + addr, 256);
                undo->memoryMap[slot] = page;
                totalSize += 256;
            }
            else
            {
                // We don't need to save this page. Just copy
                // the pointer from the previous undo record.
                undo->memoryMap[slot] = gUndo->memoryMap[slot];
            }
        }

        // If the memory map has been extended, save the exended area
        for (addr = endMem ; addr < gEndMem ; addr += 256, ++slot)
        {
            git_uint8 * page = malloc(256);
            if (page == NULL)
                fatalError ("Couldn't allocate memory for undo");
                
            memcpy (page, gMem + addr, 256);
            undo->memoryMap[slot] = page;
            totalSize += 256;
        }
    }

    // Save the heap.
    if (heap_get_summary (&(undo->heapSize), &(undo->heap)))
        fatalError ("Couldn't get heap summary");
    totalSize += undo->heapSize * 4;

    // Link this record into the undo list.
    
    undo->prev = gUndo;
    if (gUndo)
        gUndo->next = undo;
    
    gUndo = undo;
    gUndoSize += totalSize;

    // Delete old records until we have enough free space.
    reserveSpace (0);

    // And we're done.
    return 0;
}

int restoreUndo (git_sint32* base, git_uint32 protectPos, git_uint32 protectSize)
{
    if (gUndo == NULL)
    {
        // Nothing to undo!
        return 1;
    }
    else
    {
        UndoRecord * undo = gUndo;

        git_uint32 addr = gRamStart;     // Address in glulx memory.
        MemoryMap map = undo->memoryMap; // Glulx memory map.

        // Restore the size of the memory map
        heap_clear ();
        resizeMemory (undo->endMem, 1);

        // Restore the stack.
        memcpy (base, undo->stack, undo->stackSize);
        gStackPointer = base + (undo->stackSize / sizeof(git_sint32));

        // Restore the contents of RAM.

        if (protectSize > 0 && protectPos < gEndMem)
        {
            for ( ; addr < (protectPos & ~0xff) ; addr += 256, ++map)
                memcpy (gMem + addr, *map, 256);
            
            memcpy (gMem + addr, *map, protectPos & 0xff);
            protectSize += protectPos & 0xff;
            
            while (protectSize > 256)
                addr += 256, ++map, protectSize -= 256;

            if (addr < gEndMem)
            {
                memcpy (gMem + addr + protectSize,
                        *map + protectSize,
                        256 - protectSize);
            }
            addr += 256, ++map;
        }

        for ( ; addr < gEndMem ; addr += 256, ++map)
            memcpy (gMem + addr, *map, 256);

        // Restore the heap.
        if (heap_apply_summary (undo->heapSize, undo->heap))
            fatalError ("Couldn't apply heap summary");

        // Delete the undo record.

        gUndo = undo->prev;
        deleteRecord (undo);

        if (gUndo)
            gUndo->next = NULL;
        else
            assert (gUndoSize == 0);

        // And we're done.
        return 0;
    }
}

void resetUndo ()
{
    reserveSpace (gMaxUndoSize);
    assert (gUndo == NULL);
    assert (gUndoSize == 0);
}

void shutdownUndo ()
{
    resetUndo();
}

static void reserveSpace (git_uint32 n)
{
    UndoRecord * u = gUndo;
    if (u == NULL)
        return;

    // Find the oldest undo record.

    while (u->prev)
        u = u->prev;

    // Delete records until we've freed up the required amount of space.

    while (gUndoSize + n > gMaxUndoSize)
    {
        if (u->next)
        {
            assert (u->next->prev == u);
            u = u->next;

            deleteRecord (u->prev);
            u->prev = NULL;
        }
        else
        {
            assert (u == gUndo);
            if (n > 0)
            {
                gUndo = NULL;

                deleteRecord (u);
                assert (gUndoSize == 0);
            }
            break;
        }
    }
}

static void deleteRecord (UndoRecord * u)
{
    git_uint32 addr = gRamStart; // Address in glulx memory.
    git_uint32 slot = 0;         // Slot in our memory map.

    // Zero out all the slots which are duplicates
    // of pages held in older undo records.

    if (u->prev)
    {
        // We're diffing against the previous undo record.
        while (addr < u->endMem && addr < u->prev->endMem)
        {
            if (u->memoryMap [slot] == u->prev->memoryMap [slot])
                u->memoryMap [slot] = NULL;
            addr += 256, ++slot;
        }
    }
    else
    {
        // We're diffing against the gamefile.
        while (addr < u->endMem && addr < gExtStart)
        {
            if (u->memoryMap [slot] == (gInitMem + addr))
                u->memoryMap [slot] = NULL;
            addr += 256, ++slot;
        }
    }

    // Zero out all the slots which are duplicates
    // of newer undo records.

    if (u->next)
    {
        addr = gRamStart;
        slot = 0;

        while (addr < u->endMem && addr < u->next->endMem)
        {
            if (u->memoryMap [slot] == u->next->memoryMap [slot])
                u->memoryMap [slot] = NULL;
            addr += 256, ++slot;
        }
    }

    // Free all the slots which are owned by this record only.

    addr = gRamStart;
    slot = 0;
    while (addr < u->endMem)
    {
        if (u->memoryMap [slot])
        {
            free ((void*) u->memoryMap [slot]);
            gUndoSize -= 256;
        }
        addr += 256, ++slot;
    }

    // Free the memory map itself.
    free ((void*) u->memoryMap);
    gUndoSize -= sizeof(MemoryPage*) * (u->endMem - gRamStart) / 256;

    // Free the stack.
    free (u->stack);
    gUndoSize -= u->stackSize;

    // Free the heap.
    free (u->heap);
    gUndoSize -= u->heapSize * 4;

    // Finally, free the record.
    free (u);
    gUndoSize -= sizeof(UndoRecord);
}
