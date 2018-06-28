// Header for compiler.c
// $Id: compiler.h,v 1.11 2004/02/02 00:13:46 iain Exp $

#ifndef GIT_COMPILER_H
#define GIT_COMPILER_H

// -------------------------------------------------------------
// Types

typedef enum
{
#define LABEL(foo) label_ ## foo,
#include "labels.inc"
    MAX_LABEL
}
Label;

#ifdef USE_DIRECT_THREADING
typedef void* Opcode; // Generated opcode: pointer to a label in exec().
#else
typedef Label Opcode;
#endif

typedef git_uint32* Block; // Generated code block: array of labels.

// -------------------------------------------------------------
// Settings

extern int gPeephole; // Peephole optimisation of generated code?
extern int gDebug;    // Insert debug statements into generated code?
extern int gCacheRAM; // Keep RAM-based code in the JIT cache?

// -------------------------------------------------------------
// Compiling code

extern const char* gLabelNames[];

extern void initCompiler (size_t cacheSize);
extern void shutdownCompiler ();

extern void emitData (git_uint32);
extern void emitFinalCode (Label);
extern void emitConstBranch (Label op, git_uint32 address);

extern void abortCompilation ();

extern git_uint32 undoEmit();
extern void nextInstructionIsReferenced ();

extern Block peekAtEmittedStuff (int numOpcodes);

// -------------------------------------------------------------
// Accessing compiled code

extern void pruneCodeCache (git_uint32 start, git_uint32 size);
extern void resetCodeCache ();
extern void compressCodeCache ();

extern Block compile (git_uint32 pc);

typedef struct HashNode HashNode;

struct HashNode
{
    git_uint32 address;      // Glulx address for this entry.
    git_sint16 codeOffset;   // Offset in 4-byte words from this hash node to the compiled code.
    git_sint16 headerOffset; // Offset in 4-byte words from this hash node to the block header.
    union {
        int pad;             // This pad assures that PatchNode and HashNode are the same size.
        HashNode * next;     // Next node in the same hash table slot.
    } u;
};

typedef struct BlockHeader
{
    git_uint16 numHashNodes; // Number of lookup-able addresses in this block.
    git_uint16 compiledSize; // Total size of this block, in 4-byte words.
    git_uint32 glulxSize;    // Size of the glulx code this block represents, in bytes.
    git_uint32 runCounter;   // Total number of times this block was retrieved from the cache
}                            // (used to determine which blocks stay in the cache)
BlockHeader;

// This is the header for the block currently being executed --
// that is, the one containing the return value of the last call
// to getCode().
extern BlockHeader * gBlockHeader;

// Hash table for code lookup -- inlined for speed

extern HashNode ** gHashTable; // Hash table of glulx address -> code.
extern git_uint32 gHashSize;   // Number of slots in the hash table.

GIT_INLINE Block getCode (git_uint32 pc)
{
    HashNode * n = gHashTable [pc & (gHashSize-1)];
    while (n)
    {
        if (n->address == pc)
        {
            gBlockHeader = (BlockHeader*) ((git_uint32*)n + n->headerOffset);
            gBlockHeader->runCounter++;
            return (git_uint32*)n + n->codeOffset;
        }
        n = n->u.next;
    }
    return compile (pc);
}

#endif // GIT_COMPILER_H
