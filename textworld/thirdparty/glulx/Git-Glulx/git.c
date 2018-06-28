// $Id: git.c,v 1.21 2004/12/22 12:40:07 iain Exp $

#include "git.h"
#include <gi_blorb.h>
#include <stdlib.h>
#include <stdio.h>

// The four-char code 'FORM' as a big-endian value.
// This is the magic number at the start of Blorb files.
#define FORM 0x464f524d

static void gitMain (const git_uint8 * game, git_uint32 gameSize, git_uint32 cacheSize, git_uint32 undoSize)
{
    git_uint32 version;
    enum IOMode ioMode = IO_NULL;
    
    init_accel ();

    // Initialise the Glk dispatch layer.
    git_init_dispatch();

    // Set various globals.    
    gPeephole = 1;
    gDebug = 0;
    
    // Load the gamefile into memory
    // and initialise undo records.
    initMemory (game, gameSize);
    initUndo (undoSize);
    
    // Check that we're compatible with the
    // glulx spec version that the game uses.
    version = memRead32 (4);
    if (version == 0x010000 && version <= 0x0100FF)
    {
        // We support version 1.0.0 even though it's
        // officially obsolete. The only significant
        // difference is the lack of I/O modes. In 1.0,
        // all output goes directly to the Glk library.
        ioMode = IO_GLK;
    }
    else if (version == 0x020000 && version <= 0x0200FF)
    {
        // We support version 2.0, which most people currently use.
    }
    else if (version >= 0x030000 && version <= 0x0300FF)
    {
        // We support version 3.0, which adds Unicode functionality.
    }
    else if (version >= 0x030100 && version <= 0x0301FF)
    {
        // We support version 3.1, which adds some memory-management opcodes.
    }
    else
    {
        fatalError ("Can't run this game, because it uses a newer version "
            "of the gamefile format than Git understands. You should check "
            "whether a newer version of Git is available.");
    }
    
    // Call the top-level function.
    startProgram (cacheSize, ioMode);
    
    // Shut everything down cleanly.
    shutdownUndo();
    shutdownMemory();
}

static giblorb_result_t handleBlorb (strid_t stream)
{
    giblorb_err_t err;
    giblorb_result_t blorbres;
    giblorb_map_t *map;

    err = giblorb_set_resource_map (stream);
    switch (err)
    {
        case giblorb_err_None:
            break;
            
        case giblorb_err_CompileTime:
            fatalError ("Can't read the Blorb file because something is compiled wrong in the Blorb library.");
        case giblorb_err_Alloc:
            fatalError ("Can't read the Blorb file because there isn't enough memory available.");
        case giblorb_err_Read:
            fatalError ("Can't read data from the Blorb file.");
        case giblorb_err_Format:
            fatalError ("Can't read the Blorb file because it seems to be corrupted.");
        default:
            fatalError ("Can't read the Blorb file because an unknown error occurred.");
    }
    
    map = giblorb_get_resource_map();
    if (map == NULL)
        fatalError ("Can't find the Blorb file's resource map.");
        
    err = giblorb_load_resource(map, giblorb_method_FilePos, &blorbres, giblorb_ID_Exec, 0);
    if (err)
        fatalError ("This Blorb file does not contain an executable Glulx chunk.");

    if (blorbres.chunktype != giblorb_make_id('G', 'L', 'U', 'L'))
        fatalError ("This Blorb file contains an executable chunk, but it is not a Glulx file.");

    return blorbres;
}

void gitWithStream (strid_t str, git_uint32 cacheSize, git_uint32 undoSize)
{
    char * game;
    git_uint32 gamePos;
    git_uint32 gameSize;
    
    git_uint32 remaining;
    char * ptr;
    
    char buffer [4];
    
    glk_stream_set_position (str, 0, seekmode_Start);
    if (4 != glk_get_buffer_stream (str, buffer, 4))
        fatalError ("can't read from game file stream");
    
    if (readtag (buffer) == FORM)
    {
        giblorb_result_t result = handleBlorb (str);
        gamePos = result.data.startpos;
        gameSize = result.length;
    }
    else
    {
        gamePos = 0;
        glk_stream_set_position (str, 0, seekmode_End);
        gameSize = glk_stream_get_position (str);        
    }
    
    game = malloc (gameSize);
    if (game == NULL)
        fatalError ("failed to allocate memory to store game file");
    
    glk_stream_set_position (str, gamePos, seekmode_Start);
    
    remaining = gameSize;
    ptr = game;    
    while (remaining > 0)
    {
        git_uint32 n = glk_get_buffer_stream (str, ptr, remaining);
        if (n == 0)
            fatalError ("failed to read entire game file");
        remaining -= n;
        ptr += n;
    }
    
    gitMain ((git_uint8 *) game, gameSize, cacheSize, undoSize);
    free (game);
}

void git (const git_uint8 * game, git_uint32 gameSize, git_uint32 cacheSize, git_uint32 undoSize)
{
    // If this is a blorb file, register it
    // with glk and find the gamefile chunk.

    if (read32 (game) == FORM)
    {
        strid_t stream;
        giblorb_result_t result;
        
        stream = glk_stream_open_memory ((char *) game, gameSize, filemode_Read, 0);
        if (stream == NULL)
            fatalError ("Can't open the Blorb file as a Glk memory stream.");
            
        result = handleBlorb (stream);
        game += result.data.startpos;
        gameSize = result.length;
    }
    
    gitMain (game, gameSize, cacheSize, undoSize);
}
