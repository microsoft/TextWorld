/*
 * dumb-init.c - Dumb interface, initialization
 *
 * This file is part of Frotz.
 *
 * Frotz is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * Frotz is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
 * Or visit http://www.fsf.org/
 */

#include <libgen.h>
#include "dumb_frotz.h"
#include "dumb_blorb.h"

f_setup_t f_setup;

static char *my_strdup(char *);
static void print_version(void);

#define INFORMATION "\
An interpreter for all Infocom and other Z-Machine games.\n\
\n\
Syntax: dfrotz [options] story-file\n\
  -a   watch attribute setting    \t -P   alter piracy opcode\n\
  -A   watch attribute testing    \t -R <path> restricted read/write\n\
  -h # screen height              \t -s # random number seed value\n\
  -i   ignore fatal errors        \t -S # transcript width\n\
  -I # interpreter number         \t -t   set Tandy bit\n\
  -o   watch object movement      \t -u # slots for multiple undo\n\
  -O   watch object locating      \t -v   show version information\n\
  -L <file> load this save file   \t -w # screen width\n\
  -m   turn off MORE prompts      \t -x   expand abbreviations g/x/z\n\
  -p   plain ASCII output only\n"

/* A unix-like getopt, but with the names changed to avoid any problems.  */
static int zoptind = 1;
static int zoptopt = 0;
static char *zoptarg = NULL;
static int zgetopt (int argc, char *argv[], const char *options)
{
    static int pos = 1;
    const char *p;
    if (zoptind >= argc || argv[zoptind][0] != '-' || argv[zoptind][1] == 0)
	return EOF;
    zoptopt = argv[zoptind][pos++];
    zoptarg = NULL;
    if (argv[zoptind][pos] == 0)
	{ pos = 1; zoptind++; }
    p = strchr (options, zoptopt);
    if (zoptopt == ':' || p == NULL) {
	fputs ("illegal option -- ", stderr);
	goto error;
    } else if (p[1] == ':') {
	if (zoptind >= argc) {
	    fputs ("option requires an argument -- ", stderr);
	    goto error;
	} else {
	    zoptarg = argv[zoptind];
	    if (pos != 1)
		zoptarg += pos;
	    pos = 1; zoptind++;
	}
    }
    return zoptopt;
error:
    fputc (zoptopt, stderr);
    fputc ('\n', stderr);
    return '?';
}/* zgetopt */

static int user_screen_width = 128;
static int user_screen_height = 1000;
static int user_interpreter_number = -1;
static int user_random_seed = -1;
static int user_tandy_bit = 0;
static char *graphics_filename = NULL;
static bool plain_ascii = FALSE;

void set_random_seed(int seed) {
  user_random_seed = seed;
}

void os_process_arguments(int argc, char *argv[])
{
    int c;
    char *p = NULL;

    do_more_prompts = TRUE;
    /* Parse the options */
    do {
	c = zgetopt(argc, argv, "-aAh:iI:L:moOpPs:r:R:S:tu:vw:xZ:");
	switch(c) {
	  case 'a': f_setup.attribute_assignment = 1; break;
	  case 'A': f_setup.attribute_testing = 1; break;
	case 'h': user_screen_height = atoi(zoptarg); break;
	  case 'i': f_setup.ignore_errors = 1; break;
	  case 'I': f_setup.interpreter_number = atoi(zoptarg); break;
	case 'L': f_setup.restore_mode = 1;
		  f_setup.tmp_save_name = my_strdup(zoptarg);
		  break;
	  case 'm': do_more_prompts = FALSE; break;
	  case 'o': f_setup.object_movement = 1; break;
	  case 'O': f_setup.object_locating = 1; break;
	  case 'P': f_setup.piracy = 1; break;
	case 'p': plain_ascii = 1; break;
	case 'r': dumb_handle_setting(zoptarg, FALSE, TRUE); break;
	case 'R': f_setup.restricted_path = strndup(zoptarg, PATH_MAX); break;
	case 's': user_random_seed = atoi(zoptarg); break;
	  case 'S': f_setup.script_cols = atoi(zoptarg); break;
	case 't': user_tandy_bit = 1; break;
	  case 'u': f_setup.undo_slots = atoi(zoptarg); break;
	case 'v': print_version(); exit(2); break;
	case 'w': user_screen_width = atoi(zoptarg); break;
	  case 'x': f_setup.expand_abbreviations = 1; break;
	  case 'Z': f_setup.err_report_mode = atoi(zoptarg);
		if ((f_setup.err_report_mode < ERR_REPORT_NEVER) ||
		(f_setup.err_report_mode > ERR_REPORT_FATAL))
			f_setup.err_report_mode = ERR_DEFAULT_REPORT_MODE;
		break;
	}
    } while (c != EOF);

    if (((argc - zoptind) != 1) && ((argc - zoptind) != 2)) {
	printf("FROTZ V%s\tDumb interface.\n", VERSION);
	puts(INFORMATION);
	printf("\t-Z # error checking mode (default = %d)\n"
	    "\t     %d = don't report errors   %d = report first error\n"
	    "\t     %d = report all errors     %d = exit after any error\n\n",
	    ERR_DEFAULT_REPORT_MODE, ERR_REPORT_NEVER,
	    ERR_REPORT_ONCE, ERR_REPORT_ALWAYS, ERR_REPORT_FATAL);
	printf("While running, enter \"\\help\" to list the runtime escape sequences\n\n");
	exit(1);
    }

    /* Create nice default file names */

    f_setup.story_file = my_strdup(argv[zoptind++]);
    if (zoptind < argc)
	graphics_filename = my_strdup(argv[zoptind++]);

    f_setup.story_name = my_strdup(basename(f_setup.story_file));

    /* Now strip off the extension */
    p = strrchr(f_setup.story_name, '.');
    *p = '\0';	/* extension removed */


    if (!f_setup.restore_mode) {
      f_setup.save_name = malloc(strlen(f_setup.story_name) * sizeof(char) + 5);
      strncpy(f_setup.save_name, f_setup.story_name, strlen(f_setup.story_name));
      strncat(f_setup.save_name, EXT_SAVE, strlen(EXT_SAVE));
    } else { /* Set our auto load save as the name save */
      f_setup.save_name = malloc(strlen(f_setup.tmp_save_name) * sizeof(char) + 5);
      strncpy(f_setup.save_name, f_setup.tmp_save_name, strlen(f_setup.tmp_save_name));
      free(f_setup.tmp_save_name);
    }

    f_setup.script_name = malloc(strlen(f_setup.story_name) * sizeof(char) + 5);
    strncpy(f_setup.script_name, f_setup.story_name, strlen(f_setup.story_name));
    strncat(f_setup.script_name, EXT_SCRIPT, strlen(EXT_SCRIPT));

    f_setup.command_name = malloc((strlen(f_setup.story_name) + strlen(EXT_COMMAND)) * sizeof(char) + 1);
    strncpy(f_setup.command_name, f_setup.story_name, strlen(f_setup.story_name) + 1);
    strncat(f_setup.command_name, EXT_COMMAND, strlen(EXT_COMMAND));
}

void load_story(char *s)
{
    char *p = NULL;
    f_setup.story_file = my_strdup(s);
    f_setup.story_name = my_strdup(basename(f_setup.story_file));

    /* Now strip off the extension */
    p = strrchr(f_setup.story_name, '.');
    *p = '\0';	/* extension removed */

    if (!f_setup.restore_mode) {
      f_setup.save_name = malloc(strlen(f_setup.story_name) * sizeof(char) + 500);
      strncpy(f_setup.save_name, f_setup.story_name, strlen(f_setup.story_name));
      strncat(f_setup.save_name, EXT_SAVE, strlen(EXT_SAVE));
    } else { /* Set our auto load save as the name save */
      f_setup.save_name = malloc(strlen(f_setup.tmp_save_name) * sizeof(char) + 500);
      strncpy(f_setup.save_name, f_setup.tmp_save_name, strlen(f_setup.tmp_save_name));
      free(f_setup.tmp_save_name);
    }

    f_setup.script_name = malloc(strlen(f_setup.story_name) * sizeof(char) + 500);
    strncpy(f_setup.script_name, f_setup.story_name, strlen(f_setup.story_name));
    strncat(f_setup.script_name, EXT_SCRIPT, strlen(EXT_SCRIPT));

    f_setup.command_name = malloc((strlen(f_setup.story_name) + strlen(EXT_COMMAND)) * sizeof(char) + 500);
    strncpy(f_setup.command_name, f_setup.story_name, strlen(f_setup.story_name) + 1);
    strncat(f_setup.command_name, EXT_COMMAND, strlen(EXT_COMMAND));
}

void os_init_screen(void)
{
    if (h_version == V3 && user_tandy_bit)
	h_config |= CONFIG_TANDY;

    if (h_version >= V5 && f_setup.undo_slots == 0)
	h_flags &= ~UNDO_FLAG;

    h_screen_rows = user_screen_height;
    h_screen_cols = user_screen_width;

    if (user_interpreter_number > 0)
	h_interpreter_number = user_interpreter_number;
    else {
	/* Use ms-dos for v6 (because that's what most people have the
	* graphics files for), but don't use it for v5 (or Beyond Zork
	* will try to use funky characters).  */
	h_interpreter_number = h_version == 6 ? INTERP_MSDOS : INTERP_DEC_20;
    }
    h_interpreter_version = 'F';

    dumb_init_input();
    dumb_init_output();
    dumb_init_pictures(graphics_filename);
}

int os_random_seed (void)
{
    if (user_random_seed == -1)
	/* Use the epoch as seed value */
	return (time(0) & 0x7fff);
    else return user_random_seed;
}

void os_restart_game (int UNUSED (stage)) {}

void os_fatal (const char *s, ...)
{
    fprintf(stderr, "\nFatal error: %s\n", s);
    exit(1);
}

FILE *os_load_story(void)
{
    FILE *fp;

    switch (dumb_blorb_init(f_setup.story_file)) {
	case bb_err_NoBlorb:
//	  printf("No blorb file found.\n\n");
	  break;
	case bb_err_Format:
	  printf("Blorb file loaded, but unable to build map.\n\n");
	  break;
	case bb_err_NotFound:
	  printf("Blorb file loaded, but lacks executable chunk.\n\n");
	  break;
	case bb_err_None:
//	  printf("No blorb errors.\n\n");
	  break;
    }

    fp = fopen(f_setup.story_file, "rb");

    /* Is this a Blorb file containing Zcode? */
    if (f_setup.exec_in_blorb)
	 fseek(fp, blorb_res.data.startpos, SEEK_SET);

    return fp;
}

/*
 * Seek into a storyfile, either a standalone file or the
 * ZCODE chunk of a blorb file (dumb does not support blorb
 * so this is just a wrapper for fseek)
 */
int os_storyfile_seek(FILE * fp, long offset, int whence)
{
    return fseek(fp, offset, whence);
}

/*
 * Tell the position in a storyfile, either a standalone file
 * or the ZCODE chunk of a blorb file (dumb does not support
 * blorb so this is just a wrapper for fseek)
 */
int os_storyfile_tell(FILE * fp)
{
    return ftell(fp);
}

void os_init_setup(void)
{
	f_setup.attribute_assignment = 0;
	f_setup.attribute_testing = 0;
	f_setup.context_lines = 0;
	f_setup.object_locating = 0;
	f_setup.object_movement = 0;
	f_setup.left_margin = 0;
	f_setup.right_margin = 0;
	f_setup.ignore_errors = 0;
	f_setup.piracy = 0;
	f_setup.undo_slots = MAX_UNDO_SLOTS;
	f_setup.expand_abbreviations = 0;
	f_setup.script_cols = 80;
	f_setup.sound = 1;
	f_setup.err_report_mode = ERR_DEFAULT_REPORT_MODE;
	f_setup.restore_mode = 0;

}

char *my_strdup(char *src)
{
	char *str;
	char *p;
	int len = 0;

	while (src[len])
		len++;
	str = malloc(len + 1);
	p = str;
	while (*src)
        *p++ = *src++;
	*p = '\0';
	return str;
}


static void print_version(void)
{
    printf("FROTZ V%s\t", VERSION);
    printf("Dumb interface.\n");
    printf("Git commit:\t%s\n", GIT_HASH);
    printf("Git tag:\t%s\n", GIT_TAG);
    printf("Git branch:\t%s\n", GIT_BRANCH);
    printf("  Frotz was originally written by Stefan Jokisch.\n");
    printf("  It complies with standard 1.0 of Graham Nelson's specification.\n");
    printf("  It was ported to Unix by Galen Hazelwood.\n");
    printf("  The core and dumb port are currently maintained by David Griffith.\n");
    printf("  See https://github.com/DavidGriffith/frotz for Frotz's homepage.\n\n");
    return;
}

