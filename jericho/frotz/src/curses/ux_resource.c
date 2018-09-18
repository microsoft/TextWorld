#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "ux_frotz.h"
#include "ux_blorb.h"

bb_map_t *blorb_map;


/*
 * ux_getresource
 *
 * Load a bb_result_t struct (encapsulated within myresource struct)
 * with information about a resource.  We need two other facts about the
 * chunk to do something intelligent later: a filepointer and type
 * (gotten from the bb_map_t struct).  I'll have to talk to Zarf about
 * possibly modifying the bb_result_t struct in the reference version of
 * the Blorb library.
 *
 */
int ux_getresource( int num, int ispic, int method, myresource * res)
{
    int st;
    // ulong usage;
    unsigned long usage;

    res->bbres.data.ptr = NULL;
    res->fp = NULL;

    if (!blorb_map) return bb_err_NotFound;

    if (ispic)
	usage = bb_ID_Pict;
    else
	usage = bb_ID_Snd;

    st = bb_load_resource(blorb_map, method, (bb_result_t *) res, usage, num);

    if (st == bb_err_None) {
	res->type = blorb_map->chunks[res->bbres.chunknum].type;
	if (method == bb_method_FilePos)
	    res->fp = blorb_fp;
    }
    return st;
}


/*
 * ux_freeresource
 *
 * Destroys a myresource struct and returns the memory to the heap.
 *
 */
int ux_freeresource(myresource *res)
{
    if (res == NULL)
	return 0;

    if (blorb_map != NULL)
	return bb_unload_chunk(blorb_map, res->bbres.chunknum);

    return 0;
}
