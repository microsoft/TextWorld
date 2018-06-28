/* macglk_startup.c: Sample Mac-specific startup code.
	Designed by Andrew Plotkin <erkyrath@eblong.com>
	http://www.eblong.com/zarf/glk/index.html
	
	This is an extremely simple piece of startup code; it doesn't
	do anything.
*/

#include "glk.h"
#include "macglk_startup.h"
#include "git.h"
#include <stdlib.h>
#include <stdio.h>
#include <assert.h>

static strid_t mac_gamefile;

Boolean macglk_startup_code(macglk_startup_t *data)
{
  OSType mac_gamefile_types[] = { 'UlxG', 'IFRS' };

  data->startup_model  = macglk_model_ChooseOrBuiltIn;
  data->app_creator    = 'MGit' /* 'niTf' */;
  data->gamefile_types = mac_gamefile_types;
  data->num_gamefile_types = sizeof(mac_gamefile_types) / sizeof(*mac_gamefile_types);
  data->savefile_type  = 'IFZS' /* 'IFZS' */;
  data->datafile_type  = 'UlxD' /* 'ZipD' */;
  data->gamefile       = &mac_gamefile;
/*  data->when_selected  = mac_whenselected;
  data->when_builtin   = mac_whenbuiltin;*/
	return TRUE;
}

#define CACHE_SIZE (256 * 1024L)
#define UNDO_SIZE (2 * 1024 * 1024L)

void glk_main ()
{
    strid_t file = mac_gamefile;
    size_t size, remaining;
    git_uint8 * data;
    git_uint8 * ptr;

    glk_stream_set_position (file, 0, seekmode_End);
    size = glk_stream_get_position (file);
    glk_stream_set_position (file, 0, seekmode_Start);

    data = malloc (size);

    ptr = data;
    remaining = size;
    while (remaining > 0)
    {
		size_t n = glk_get_buffer_stream (file, (char *) ptr, remaining);
		if (n == 0)
		{
			printf ("Can't read file.");
			exit(1);
		}
		remaining -= n;
        ptr += n;
    }
	glk_stream_close (file, NULL);

    git (data, size, CACHE_SIZE, UNDO_SIZE);
}

void __msl_assertion_failed (const char * cond, const char * file, const char * func, int line)
{
    fprintf (stderr, "*** fatal error: assertion failed in function \"%s\" (%s:%d) ***\n", func, file, line);
    fprintf (stderr, "*** assert(%s) ***\n", cond);
    exit (1);
}

void fatalError (const char * s)
{
    fprintf (stderr, "*** fatal error: %s ***\n", s);
    exit (1);
}
