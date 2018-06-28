// $Id: compiler.c,v 1.27 2004/12/10 00:37:00 iain Exp $

#include "git.h"
#include <assert.h>
#include <stdlib.h>
#include <setjmp.h>
#include <string.h>

// -------------------------------------------------------------
// Constants

enum
{
    LONGJMP_NO_ERROR = 0,
    LONGJMP_CACHE_FULL = 1,
    LONGJMP_BAD_OPCODE = 2
};

// -------------------------------------------------------------
// Globals

int gPeephole = 1;
int gDebug = 0;
int gCacheRAM = 0;

BlockHeader * gBlockHeader;

const char * gLabelNames [] = {
#define LABEL(label) #label,
#include "labels.inc"
    NULL
};

HashNode ** gHashTable; // Hash table of glulx address -> code.
git_uint32 gHashSize;   // Number of slots in the hash table.

// -------------------------------------------------------------
// Types.

typedef struct PatchNode
{
    git_uint32 address;       // The glulx address of this instruction.
    git_sint16 codeOffset;    // Offset from the block header to the compiled code for this instruction.
    git_sint16 branchOffset;  // If non-zero, offset to a branch opcode followed by a glulx address.
    union {
        int isReferenced;     // Set to TRUE if this can be the destination of a jump.
        HashNode* pad;        // This pad assures that PatchNode and HashNode are the same size.
    } u;
}
PatchNode;

// -------------------------------------------------------------
// Static variables.

static git_uint32 * sBuffer;   // The buffer where everything is stored.
static git_uint32 sBufferSize; // Size of the buffer, in 4-byte words.

static Block       sCodeStart; // Start of code cache.
static Block       sCodeTop;   // Next free space in code cache.
static PatchNode*  sTempStart; // Start of temporary storage.
static PatchNode*  sTempEnd;   // End of temporary storage.

static jmp_buf sJumpBuf; // setjmp buffer, used to abort compilation when the buffer is full.

// This is the patch node for the opcode currently being compiled.
// The 'address' and 'code' fields will be filled in. The other
// fields can be updated during compilation as necessary.
static PatchNode * sPatch;

static int sNextInstructionIsReferenced;
static git_uint32 sLastAddr;

// -------------------------------------------------------------
// Functions

void initCompiler (size_t size)
{
    static BlockHeader dummyHeader;
    gBlockHeader = &dummyHeader;

    // Make sure various assumptions we're making are correct.

    assert (sizeof(HashNode) <= sizeof(PatchNode));

    // Allocate the buffer. As far as possible, we're going to 
    // use this buffer for everything compiler-related, and
    // avoid further dynamic allocation.

    sBuffer = malloc (size);
    if (sBuffer == NULL)
        fatalError ("Couldn't allocate code cache");
    
    memset (sBuffer, 0, size);
    sBufferSize = size / 4;

    // Pick a reasonable size for the hash table. This should be
    // a power of two, and take up about a tenth of the buffer.
    // (If the buffer is itself a power of two in size, the hash
    // table will take up a sixteenth of it, which is fine.)

    gHashSize = 1;
    while (gHashSize < (sBufferSize / 20))
        gHashSize *= 2;

    // The hash table is stored at the beginning of the buffer,
    // and the rest is used for code and temporary storage.

    gHashTable = (HashNode**) sBuffer;

    sCodeStart = sCodeTop = (Block) (gHashTable + gHashSize);
    sTempStart = sTempEnd = (PatchNode*) (sBuffer + sBufferSize);
}

void shutdownCompiler ()
{
    free (sBuffer);

    sBuffer = NULL;
    sCodeStart = sCodeTop = NULL;
    sTempStart = sTempEnd = NULL;
    
    gHashTable = NULL;
    gBlockHeader = NULL;
}

static void abortIfBufferFull ()
{
    // Make sure we have at least two words free,
    // because we'll need them to store a jumpabs
    // instruction at the very end of the buffer.

    if ((void*) (sCodeTop + 2) >= (void*) sTempStart)
        longjmp (sJumpBuf, LONGJMP_CACHE_FULL);
}

void abortCompilation ()
{
    longjmp (sJumpBuf, LONGJMP_BAD_OPCODE);
}

void nextInstructionIsReferenced ()
{
    sNextInstructionIsReferenced = 1;
}

Block compile (git_uint32 pc)
{
    git_uint32 endOfBlock;
    int i, numNodes;

    // Make sure we have enough room for, at a minimum:
    // - the block header
    // - one patch node
    // - one jumpabs instruction (two words).

    int spaceNeeded = (sizeof(BlockHeader) + sizeof(PatchNode) + 8) / 4;
    if ((void*) (sCodeTop + spaceNeeded) >= (void*) sTempStart)
    {
        compressCodeCache();
    }

    // Emit the header for this block.

    gBlockHeader = (BlockHeader*) sCodeTop;
    sCodeTop = (git_uint32*) (gBlockHeader + 1);

    sLastAddr = 0;
    sNextInstructionIsReferenced = 1;
    resetPeepholeOptimiser();

    sPatch = NULL;

    i = setjmp (sJumpBuf);    
    if (i == LONGJMP_NO_ERROR)
    {
        git_uint32 patchSize = 0;
        git_uint32 codeSize = 0;

        int done = 0;

        while (!done)
        {
        	// If we don't have room for more code, abort.
			if ((void*) (sCodeTop + 2) >= (void*) (sTempStart - 1))
			{
				longjmp (sJumpBuf, LONGJMP_CACHE_FULL);
			}
		
            // Create a temporary patch node for this instruction.
            --sTempStart;
            sPatch = sTempStart;
            sPatch->address = pc;
            sPatch->codeOffset = sCodeTop - (git_uint32*)gBlockHeader;
            sPatch->branchOffset = 0;
            sPatch->u.isReferenced = sNextInstructionIsReferenced;

            sNextInstructionIsReferenced = 0;

            // Make sure we haven't generated over 32K of code.

            patchSize += sizeof(PatchNode) / 4;
            codeSize = sCodeTop - (git_uint32*)gBlockHeader;

            if (codeSize + patchSize > 32000)
            {
                // We've generated almost 32K words of code, which will
                // start to cause problems for the 16-bit offsets we use
                // in the hash nodes, so let's just stop here.
                longjmp (sJumpBuf, LONGJMP_CACHE_FULL);
            }

            // Parse the next instruction.

            parseInstruction (&pc, &done);

            if (pc < sLastAddr)
                done = 0;
        }
    }
    else    
    {
        // Compilation was aborted, but we should have a
        // patch node and at least two words of space free.
        
        assert (sPatch != NULL);
        sPatch->branchOffset = 0; // Make sure the patch isn't treated as a branch.
        
        sCodeTop = ((git_uint32*)gBlockHeader) + sPatch->codeOffset;

        if (i == LONGJMP_CACHE_FULL)
        {
            // The buffer is full. We'll replace the partially-compiled
            // instruction with a jumpabs, forcing another cache lookup
            // when the terp hits this point in the code.
    
            *sCodeTop++ = (git_uint32) labelToOpcode (label_recompile);
            *sCodeTop++ = sPatch->address;
			
            // Make sure this node doesn't get put into the hash table.
            sPatch->u.isReferenced = 0;
        }
        else if (i == LONGJMP_BAD_OPCODE)
        {
            // We found a badly-formed instruction. We'll replace the
            // partially-compiled instruction with a label that raises
            // an error if the terp hits this code location.
            
            *sCodeTop++ = (git_uint32) labelToOpcode (label_error_bad_opcode);
            *sCodeTop++ = sPatch->address;
        }
        else
        {
            fatalError ("unknown error in compile (BUG)");
        }
    }
    
    assert ((void*) sCodeTop <= (void*) sTempStart);

    // We now know where the block ends.
    
    endOfBlock = pc;

    // Fix up the constant branches.

    numNodes = sTempEnd - sTempStart;
    for (i = 0 ; i < numNodes ; ++i)
    {
        git_uint32* constBranch;
            
        git_uint32 dest;
        git_uint32 lower = 0;
        git_uint32 upper = numNodes;
        
        PatchNode * p = sTempStart + i;
        if (p->branchOffset == 0)
            continue;
       
        constBranch = ((git_uint32*)gBlockHeader) + p->branchOffset;
        dest = constBranch [1];
        while (upper > lower)
        {
            git_uint32 guess = (lower + upper) / 2;
            PatchNode * p2 = sTempStart + guess;
            if (p2->address == dest)
            {
                git_uint32 * op = constBranch;
                git_uint32 * by = constBranch + 1;

                // Change the 'const' branch to a 'by' branch.
                *op = *op - label_jump_const + label_jump_by;

                // Turn the address into a relative offset.
                *by = ((git_uint32*)gBlockHeader + p2->codeOffset) - (constBranch + 2);

                // And we're done.
                break;
            }
            else if (p2->address > dest)
                lower = guess + 1;
            else
                upper = guess;
        }

        // Whether we found the branch destination or not,
        // turn the label into a real opcode.
        *constBranch = (git_uint32) labelToOpcode (*constBranch);
    }

    // Convert all the referenced addresses into hash table nodes,
    // as long as they're not in RAM.

    numNodes = 0;
    for ( ; sTempStart < sTempEnd ; ++sTempStart)
    {
        // 'pc' holds the address of *end* of the instruction,
        // so we'll use that to determine whether it overlaps
        // the start of RAM.
        
        int isInRAM = (pc > gRamStart);
        
        // Set the PC to the start of the instruction, since
        // that's equal to the end of the previous instruction.
        
        pc = sTempStart->address;
        
        if (isInRAM && !gCacheRAM)
            continue;

        // If we're not skipping this instruction, and it's
        // referenced somewhere, attach it to the hash table.
                
        if (sTempStart->u.isReferenced)
        {
            HashNode * node = (HashNode*) sCodeTop;
            sCodeTop = (git_uint32*) (node + 1);

            node->address = sTempStart->address;
            node->headerOffset = (git_uint32*)gBlockHeader - (git_uint32*)node;
            node->codeOffset = node->headerOffset + sTempStart->codeOffset;

            node->u.next = gHashTable [node->address & (gHashSize-1)];
            gHashTable [node->address & (gHashSize-1)] = node;

            ++numNodes;
        }
    }

    // Write the block header.

    assert (sCodeTop - (git_uint32*) gBlockHeader < 32767);

    gBlockHeader->numHashNodes = numNodes;
    gBlockHeader->compiledSize = sCodeTop - (git_uint32*) gBlockHeader;
    gBlockHeader->glulxSize = endOfBlock - pc;
    gBlockHeader->runCounter = 0;
    
    assert(gBlockHeader->compiledSize > 0);

    // And we're done.
    return (git_uint32*) (gBlockHeader + 1);
}

#define END_OF_BLOCK(header) ((void*) (((git_uint32*)header) + header->compiledSize))

static git_uint32 findCutoffPoint ()
{
    BlockHeader * start = (BlockHeader*) sCodeStart;
    BlockHeader * top = (BlockHeader*) sCodeTop;
    BlockHeader * h;

    git_uint32 blockCount = 0;
    git_uint32 runCount = 0;

    for (h = start ; h < top ; h = END_OF_BLOCK(h))
    {
        if (h->glulxSize > 0)
        {
            ++blockCount;
        }
    }

    for (h = start ; h < top ; h = END_OF_BLOCK(h))
    {
        if (h->glulxSize > 0)
        {
            runCount += (h->runCounter + blockCount + 1) / blockCount;
        }
    }

    return runCount / 2;
}

static void compressWithCutoff (git_uint32 cutoff)
{
    BlockHeader * start = (BlockHeader*) sCodeStart;
    BlockHeader * top = (BlockHeader*) sCodeTop;
    BlockHeader * h = start;

    git_uint32 saveCount = 0;
    git_uint32 deleteCount = 0;

    sCodeTop = sCodeStart;

    while (h < top)
    {
        BlockHeader * next = END_OF_BLOCK(h);
        if (h->runCounter >= cutoff && h->glulxSize > 0)
        {
        	git_uint32 size = h->compiledSize;
        	
            // Lower the run count of the saved blocks so that they'll
            // stick around in the short term, but eventually fall out
            // of the cache if they're not used much in the future.
            h->runCounter /= 2;
 
            memmove (sCodeTop, h, size * sizeof(git_uint32));
            sCodeTop += size;
            ++saveCount;
        }
        else
        {
            ++deleteCount;
        }
        h = next;
    }
}

static void rebuildHashTable ()
{
    BlockHeader * start = (BlockHeader*) sCodeStart;
    BlockHeader * top = (BlockHeader*) sCodeTop;
    BlockHeader * h;

    memset (gHashTable, 0, gHashSize * sizeof(HashNode*));

    for (h = start ; h < top ; h = END_OF_BLOCK(h))
    {
        if (h->glulxSize > 0)
        {
            HashNode * node = END_OF_BLOCK(h);
            git_uint32 i;
            for (i = 0 ; i < h->numHashNodes ; ++i) 
            {
                --node;
                node->u.next = gHashTable [node->address & (gHashSize-1)];
                gHashTable [node->address & (gHashSize-1)] = node;
            }    
        }
    }
}

static void removeHashNode (HashNode* deadNode)
{
    HashNode* n = gHashTable [deadNode->address & (gHashSize-1)];
    assert (deadNode != NULL);
    
    if (n == NULL)
    {
        // This hash bucket is empty! We have nothing to do.
    }
    else if (n == deadNode)
    {
        // The node to be removed is the first one in its bucket.        
        gHashTable [deadNode->address & (gHashSize-1)] = NULL;
    }
    else
    {
        // The node to be removed is somewhere in the middle
        // of the bucket. Step along the linked list until
        // we find it.
                
        while (n->u.next != deadNode)
            n = n->u.next;
        
        // Unlink it from the linked list.        
        n->u.next = deadNode->u.next;
    }
}

void pruneCodeCache (git_uint32 address, git_uint32 size)
{
    BlockHeader * start = (BlockHeader*) sCodeStart;
    BlockHeader * top = (BlockHeader*) sCodeTop;
    BlockHeader * h;

    // Step through the cache, looking for blocks that overlap the
    // specified range. If we find any, remove their nodes from the
    // hash table, and set glulxSize to 0 so that they're dropped
    // the next time we clean up the cache.
    
    for (h = start ; h < top ; h = END_OF_BLOCK(h))
    {
        // The start address of the block is in its final hash node.
        
        HashNode * node = END_OF_BLOCK(h);
        git_uint32 glulxAddr = node[-1].address;
        
        if (glulxAddr < (address + size) && (glulxAddr + h->glulxSize) > address)
        {
            // This block overlaps the range of code that has to be pruned.
            
            git_uint32 i;
            for (i = 0 ; i < h->numHashNodes ; ++i) 
            {
                --node;
                removeHashNode (node);
            }
    
            h->glulxSize = 0;
        }
    }
}

void compressCodeCache ()
{
    git_uint32 n;
    git_uint32 spaceUsed, spaceFree;
    
    n = findCutoffPoint();
    compressWithCutoff (n);
    rebuildHashTable ();

    spaceUsed = sCodeTop - sCodeStart;
    spaceFree = sBufferSize - spaceUsed - gHashSize;

//    {
//        char buffer [100];
//        sprintf (buffer, "[Cache cleanup: %d bytes used, %d free]\n",
//            spaceUsed * 4, spaceFree * 4);
//        glk_put_string (buffer);
//    }

    // If that didn't free up at least a quarter of the cache,
    // clear it out entirely.

    if (spaceFree * 3 < spaceUsed)
        resetCodeCache();
}

void resetCodeCache ()
{
//    glk_put_string ("[resetting cache]\n");

    memset (sBuffer, 0, sBufferSize * 4);
    sCodeStart = sCodeTop = (Block) (gHashTable + gHashSize);
    sTempStart = sTempEnd = (PatchNode*) (sBuffer + sBufferSize);
}

Block peekAtEmittedStuff (int numOpcodes)
{
    return sCodeTop - numOpcodes;
}

void emitConstBranch (Label op, git_uint32 address)
{
    sPatch->branchOffset = sCodeTop - (git_uint32*)gBlockHeader;
    emitData (op);
    emitData (address);

    if (sLastAddr < address)
        sLastAddr = address;
}

void emitData (git_uint32 val)
{
    abortIfBufferFull ();
    *sCodeTop++ = val;
}

extern void emitFinalCode (Label op)
{
    abortIfBufferFull ();
    *sCodeTop++ = (git_uint32) labelToOpcode (op);
}

extern git_uint32 undoEmit ()
{
    return *--sCodeTop;
}
