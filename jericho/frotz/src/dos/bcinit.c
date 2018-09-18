/*
 * file "BCinit.c"
 *
 * Borland C front end, initialisation
 *
 */

#include <conio.h>
#include <dos.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "frotz.h"
#include "bcfrotz.h"
#include "bcblorb.h"

f_setup_t f_setup;

static char information[] =
"An interpreter for all Infocom and other Z-Machine games.\n"
"Complies with standard 1.0 of Graham Nelson's specification.\n"
"\n"
"Syntax: frotz [options] story-file\n"
"  -a   watch attribute setting    \t -o   watch object movement\n"
"  -A   watch attribute testing    \t -O   watch object locating\n"
"  -b # background colour          \t -p   alter piracy opcode\n"
"  -B # reverse background colour  \t -r # right margin\n"
"  -c # context lines              \t -R <path> restricted read/write\n"
"  -d # display mode (see below)   \t -s # random number seed value\n"
"  -e # emphasis colour [mode 1]   \t -S # transscript width\n"
"  -f # foreground colour          \t -t   set Tandy bit\n"
"  -F # reverse foreground colour  \t -T   bold typing [modes 2+4+5]\n"
"  -g # font [mode 5] (see below)  \t -u # slots for multiple undo\n"
"  -h # screen height              \t -w # screen width\n"
"  -i   ignore runtime errors      \t -x   expand abbreviations g/x/z\n"
"  -l # left margin                \t -Z # error checking (see below)"
"\n"
"Fonts are 0 (fixed), 1 (sans serif), 2 (comic), 3 (times), 4 (serif).\n"
"Display modes are 0 (mono), 1 (text), 2 (CGA), 3 (MCGA), 4 (EGA), 5 (Amiga)."
"\n\n"
"Error checking is 0 (none), 1 (report first error (default)),\n"
"  2 (report all errors), 3 (exit after any error).";

/* in bcinit.c only.  What is its significance? */
extern unsigned cdecl _heaplen = 0x800 + 4 * BUFSIZ;
extern unsigned cdecl _stklen = 0x800;

extern const char *optarg;
extern int optind;

int cdecl getopt (int, char *[], const char *);

static const char *progname = NULL;

extern char script_name[];
extern char command_name[];
extern char save_name[];
extern char auxilary_name[];

int display = -1;

int user_background = -1;
int user_foreground = -1;
int user_emphasis = -1;
int user_bold_typing = -1;
int user_reverse_bg = -1;
int user_reverse_fg = -1;
int user_screen_height = -1;
int user_screen_width = -1;
int user_tandy_bit = -1;
int user_random_seed = -1;
int user_font = 1;


/* Blorb-related things */
char *blorb_name;
char *blorb_file;
bool use_blorb;
bool exec_in_blorb;

static byte old_video_mode = 0;

static void interrupt (*oldvect) () = NULL;



/*
 * os_init_setup
 *
 * Set or reset various configuration variables.
 *
 */
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

}/* os_init_setup */


/*
 * dectoi
 *
 * Convert a string containing a decimal number to integer. The string may
 * be NULL, but it must not be empty.
 *
 */
int dectoi (const char *s)
{
    int n = 0;

    if (s != NULL)

	do {

	    n = 10 * n + (*s & 15);

	} while (*++s > ' ');

    return n;

}/* dectoi */


/*
 * hextoi
 *
 * Convert a string containing a hex number to integer. The string may be
 * NULL, but it must not be empty.
 *
 */
int hextoi (const char *s)
{
    int n = 0;

    if (s != NULL)

	do {

	    n = 16 * n + (*s & 15);

	    if (*s > '9')
		n += 9;

	} while (*++s > ' ');

    return n;

}/* hextoi */


/*
 * basename
 *
 * A generic and spartan bit of code to extract the filename from a path.
 * This one is so trivial that it's okay to steal.
 */
char *basename(const char *path)
{
    const char *s;
    const char *p;
    p = s = path;

    while (*s) {
        if (*s++ == '\\') {
            p = s;
        }
    }
    return (char *) p;
} /* basename */


/*
 * cleanup
 *
 * Shut down the IO interface: free memory, close files, restore
 * interrupt pointers and return to the previous video mode.
 *
 */
static void cleanup (void)
{

#ifdef SOUND_SUPPORT
    dos_reset_sound ();
#endif
    reset_pictures ();

    asm mov ah,0
    asm mov al,old_video_mode
    asm int 0x10

    setvect (0x1b, oldvect);

}/* cleanup */


/*
 * fast_exit
 *
 * Handler routine to be called when the crtl-break key is pressed.
 *
 */
static void interrupt fast_exit ()
{

    cleanup (); exit (EXIT_FAILURE);

}/* fast_exit */


/*
 * os_fatal
 *
 * Display error message and exit program.
 *
 */

void os_fatal (const char *s, ...)
{

    if (h_interpreter_number)
	os_reset_screen ();

    /* Display error message */

    fputs ("\nFatal error: ", stderr);
    fputs (s, stderr);
    fputs ("\n", stderr);

    /* Abort program */

    exit (EXIT_FAILURE);

}/* os_fatal */


/*
 * parse_options
 *
 * Parse program options and set global flags accordingly.
 *
 */
static void parse_options (int argc, char **argv)
{
    int c;

    do {

	int num = 0;

	c = getopt (argc, argv, "aAb:B:c:d:e:f:F:g:h:il:oOpr:R:s:S:tTu:w:xZ:");

	if (optarg != NULL)
	    num = dectoi (optarg);

	if (c == 'a')
	    f_setup.attribute_assignment = 1;
	if (c == 'A')
	    f_setup.attribute_testing = 1;
	if (c == 'b')
	    user_background = num;
	if (c == 'B')
	    user_reverse_bg = num;
	if (c == 'c')
	    f_setup.context_lines = num;
	if (c == 'd') {
	    display = optarg[0] | 32;
	    if ((display < '0' || display > '5')
		&& (display < 'a' || display > 'e')) {
		display = -1;
	    }
	}
	if (c == 'e')
	    user_emphasis = num;
	if (c == 'T')
	    user_bold_typing = 1;
	if (c == 'f')
	    user_foreground = num;
	if (c == 'F')
	    user_reverse_fg = num;
	if (c == 'g') {
	    if (num >= 0 && num <= 4)
		user_font = num;
	}
	if (c == 'h')
	    user_screen_height = num;
	if (c == 'i')
	    f_setup.ignore_errors = 1;
	if (c == 'l')
	    f_setup.left_margin = num;
	if (c == 'o')
	    f_setup.object_movement = 1;
	if (c == 'O')
	    f_setup.object_locating = 1;
	if (c == 'p')
	    f_setup.piracy = 1;
	if (c == 'r')
	    f_setup.right_margin = num;
	if (c == 'R')
	    f_setup.restricted_path = strdup(optarg);
	if (c == 's')
	    user_random_seed = num;
	if (c == 'S')
	    f_setup.script_cols = num;
	if (c == 't')
	    user_tandy_bit = 1;
	if (c == 'u')
	    f_setup.undo_slots = num;
	if (c == 'w')
	    user_screen_width = num;
	if (c == 'x')
	    f_setup.expand_abbreviations = 1;
	if (c == 'Z') {
	    if (num >= ERR_REPORT_NEVER && num <= ERR_REPORT_FATAL)
		f_setup.err_report_mode = num;
	}
	if (c == '?')
	    optind = argc;
    } while (c != EOF && c != '?');

}/* parse_options */


/*
 * os_process_arguments
 *
 * Handle command line switches. Some variables may be set to activate
 * special features of Frotz:
 *
 *     option_attribute_assignment
 *     option_attribute_testing
 *     option_context_lines
 *     option_object_locating
 *     option_object_movement
 *     option_left_margin
 *     option_right_margin
 *     option_ignore_errors
 *     option_piracy
 *     option_undo_slots
 *     option_expand_abbreviations
 *     option_script_cols
 *
 * The global pointer "story_name" is set to the story file name.
 *
 */
void os_process_arguments (int argc, char *argv[])
{
    const char *p;
    int i;
    char stripped_story_name[10];

    /* Parse command line options */

    parse_options (argc, argv);

    if (optind != argc - 1) {
	printf ("FROTZ V%s\tMSDOS / PCDOS Edition\n", VERSION);
	puts (information);
	exit (EXIT_FAILURE);
    }

    /* Set the story file name */

    f_setup.story_file = strdup(argv[optind]);

    /* Strip path and extension off the story file name */

    p = strdup(f_setup.story_file);

    for (i = 0; f_setup.story_file[i] != 0; i++)
	if (f_setup.story_file[i] == '\\' || f_setup.story_file[i] == '/'
	    || f_setup.story_file[i] == ':')
	    p = f_setup.story_file + i + 1;

    for (i = 0; p[i] != 0 && p[i] != '.'; i++)
	stripped_story_name[i] = p[i];
    stripped_story_name[i] = 0;
    f_setup.story_name = strdup(stripped_story_name);

    /* Create nice default file names */

    f_setup.script_name = strdup(f_setup.story_name);
    f_setup.command_name = strdup(f_setup.story_name);
    f_setup.save_name = strdup(f_setup.story_name);
    f_setup.aux_name = strdup(f_setup.story_name);

    strcat (f_setup.script_name, ".scr");
    strcat (f_setup.command_name, ".rec");
    strcat (f_setup.save_name, ".sav");
    strcat (f_setup.aux_name, ".aux");

    /* Save the executable file name */

    progname = argv[0];

    blorb_file = strdup(f_setup.story_name);
    strcat(blorb_file, ".blb");

    switch (dos_init_blorb()) {
	case bb_err_Format:
	    printf("Blorb file loaded, but unable to build map.\n\n");
	    break;
	default:
	    break;
/* No problem.  Don't say anything. */
/*	    printf("Blorb error code %i\n\n"); */
    }
}/* os_process_arguments */


/*
 * standard_palette
 *
 * Set palette registers to EGA default values and call VGA BIOS to
 * use DAC registers #0 to #63.
 *
 */
static void standard_palette (void)
{

    static byte palette[] = {
	0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x14, 0x07,
	0x38, 0x39, 0x3a, 0x3b, 0x3c, 0x3d, 0x3e, 0x3f,
	0x00 /* last one is the overscan register */
    };

    if (display == _AMIGA_) {
	asm mov ax,0x1002
	asm lea dx,palette
	asm push ds
	asm pop es
	asm int 0x10
	asm mov ax,0x1013
	asm mov bx,0x0001
	asm int 0x10
    }

}/* standard_palette */


/*
 * special_palette
 *
 * Set palette register #i to value i and call VGA BIOS to use DAC
 * registers #64 to #127.
 *
 */
static void special_palette (void)
{

    static byte palette[] = {
	0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
	0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f,
	0x00 /* last one is the overscan register */
    };

    if (display == _AMIGA_) {
	asm mov ax,0x1002
	asm mov dx,offset palette
	asm push ds
	asm pop es
	asm int 0x10
	asm mov ax,0x1013
	asm mov bx,0x0101
	asm int 0x10
    }

}/* special_palette */


/*
 * os_init_screen
 *
 * Initialise the IO interface. Prepare the screen and other devices
 * (mouse, sound board). Set various OS depending story file header
 * entries:
 *
 *     h_config (aka flags 1)
 *     h_flags (aka flags 2)
 *     h_screen_cols (aka screen width in characters)
 *     h_screen_rows (aka screen height in lines)
 *     h_screen_width
 *     h_screen_height
 *     h_font_height (defaults to 1)
 *     h_font_width (defaults to 1)
 *     h_default_foreground
 *     h_default_background
 *     h_interpreter_number
 *     h_interpreter_version
 *     h_user_name (optional; not used by any game)
 *
 * Finally, set reserve_mem to the amount of memory (in bytes) that
 * should not be used for multiple undo and reserved for later use.
 *
 */
void os_init_screen (void)
{
    static byte zcolour[] = {
	BLACK_COLOUR,
	BLUE_COLOUR,
	GREEN_COLOUR,
	CYAN_COLOUR,
	RED_COLOUR,
	MAGENTA_COLOUR,
	BROWN + 16,
	LIGHTGRAY + 16,
	GREY_COLOUR,
	LIGHTBLUE + 16,
	LIGHTGREEN + 16,
	LIGHTCYAN + 16,
	LIGHTRED + 16,
	LIGHTMAGENTA + 16,
	YELLOW_COLOUR,
	WHITE_COLOUR
    };

    static struct {	/* information on modes 0 to 5 */
	byte vmode;
	word width;
	word height;
	byte font_width;
	byte font_height;
	byte fg;
	byte bg;
    } info[] = {
	{ 0x07,  80,  25,  1,  1, LIGHTGRAY + 16, BLACK_COLOUR }, /* MONO  */
	{ 0x03,  80,  25,  1,  1, LIGHTGRAY + 16, BLUE_COLOUR  }, /* TEXT  */
	{ 0x06, 640, 200,  8,  8, WHITE_COLOUR,   BLACK_COLOUR }, /* CGA   */
	{ 0x13, 320, 200,  5,  8, WHITE_COLOUR,   GREY_COLOUR  }, /* MCGA  */
	{ 0x0e, 640, 200,  8,  8, WHITE_COLOUR,   BLUE_COLOUR  }, /* EGA   */
	{ 0x12, 640, 400,  8, 16, WHITE_COLOUR,   BLACK_COLOUR }  /* AMIGA */
    };

    static struct {	/* information on modes A to E */
	word vesamode;
	word width;
	word height;
    } subinfo[] = {
	{ 0x001,  40, 25 },
	{ 0x109, 132, 25 },
	{ 0x10b, 132, 50 },
	{ 0x108,  80, 60 },
	{ 0x10c, 132, 60 }
    };

    int subdisplay;

    /* Get the current video mode. This video mode will be selected
       when the program terminates. It's also useful to auto-detect
       monochrome boards. */

    asm mov ah,15
    asm int 0x10
    asm mov old_video_mode,al

    /* If the display mode has not already been set by the user then see
       if this is a monochrome board. If so, set the display mode to 0.
       Otherwise check the graphics flag of the story. Select a graphic
       mode if it is set or if this is a V6 game. Select text mode if it
       is not. */

    if (display == -1)

	if (old_video_mode == 7)
	    display = '0';
	else if (h_version == V6 || (h_flags & GRAPHICS_FLAG))
	    display = '5';
	else
	    display = '1';

    /* Activate the desired display mode. All VESA text modes are very
       similar to the standard text mode; in fact, only here we need to
       know which VESA mode is used. */

    if (display >= '0' && display <= '5') {
	subdisplay = -1;
	display -= '0';
	_AL = info[display].vmode;
	_AH = 0;
    } else if (display == 'a') {
	subdisplay = 0;
	display = 1;
	_AL = 0x01;
	_AH = 0;
    } else if (display >= 'b' && display <= 'e') {
	subdisplay = display - 'a';
	display = 1;
	_BX = subinfo[subdisplay].vesamode;
	_AX = 0x4f02;
    }

    geninterrupt (0x10);

    /* Make various preparations */

    if (display <= _TEXT_) {

	/* Enable bright background colours */

	asm mov ax,0x1003
	asm mov bl,0
	asm int 0x10

	/* Turn off hardware cursor */

	asm mov ah,1
	asm mov cx,0xffff
	asm int 0x10

    } else {

	load_fonts ();

	if (display == _AMIGA_) {

	     scaler = 2;

	     /* Use resolution 640 x 400 instead of 640 x 480. BIOS doesn't
		help us here since this is not a standard resolution. */

	     outportb (0x03c2, 0x63);

	     outport (0x03d4, 0x0e11);
	     outport (0x03d4, 0xbf06);
	     outport (0x03d4, 0x1f07);
	     outport (0x03d4, 0x9c10);
	     outport (0x03d4, 0x8f12);
	     outport (0x03d4, 0x9615);
	     outport (0x03d4, 0xb916);

	 }

    }

#if !defined(__SMALL__) && !defined (__TINY__) && !defined (__MEDIUM__)

    /* Set the amount of memory to reserve for later use. It takes
       some memory to open command, script and game files. If Frotz
       is compiled in a small memory model then memory for opening
       files is allocated on the "near heap" while other allocations
       are made on the "far heap", i.e. we need not reserve memory
       in this case. */

    reserve_mem = 4 * BUFSIZ;

#endif

    /* Amiga emulation under V6 needs special preparation. */

    if (display == _AMIGA_ && h_version == V6) {

	user_reverse_fg = -1;
	user_reverse_bg = -1;
	zcolour[LIGHTGRAY] = LIGHTGREY_COLOUR;
	zcolour[DARKGRAY] = DARKGREY_COLOUR;

	special_palette ();

    }

    /* Set various bits in the configuration byte. These bits tell
       the game which features are supported by the interpreter. */

    if (h_version == V3 && user_tandy_bit != -1)
	h_config |= CONFIG_TANDY;
    if (h_version == V3)
	h_config |= CONFIG_SPLITSCREEN;
    if (h_version == V3 && (display == _MCGA_ || (display == _AMIGA_ && user_font != 0)))
	h_config |= CONFIG_PROPORTIONAL;
    if (h_version >= V4 && display != _MCGA_ && (user_bold_typing != -1 || display <= _TEXT_))
	h_config |= CONFIG_BOLDFACE;
    if (h_version >= V4)
	h_config |= CONFIG_EMPHASIS | CONFIG_FIXED | CONFIG_TIMEDINPUT;
    if (h_version >= V5 && display != _MONO_ && display != _CGA_)
	h_config |= CONFIG_COLOUR;
    if (h_version >= V5 && display >= _CGA_ && init_pictures ())
	h_config |= CONFIG_PICTURES;

    /* Handle various game flags. These flags are set if the game wants
       to use certain features. The flags must be cleared if the feature
       is not available. */

    if (h_flags & GRAPHICS_FLAG)
	if (display <= _TEXT_)
	    h_flags &= ~GRAPHICS_FLAG;
    if (h_version == V3 && (h_flags & OLD_SOUND_FLAG))
#ifdef SOUND_SUPPORT
	if (!dos_init_sound ())
#endif
	    h_flags &= ~OLD_SOUND_FLAG;
    if (h_flags & SOUND_FLAG)
#ifdef SOUND_SUPPORT
	if (!dos_init_sound ())
#endif
	    h_flags &= ~SOUND_FLAG;
    if (h_version >= V5 && (h_flags & UNDO_FLAG))
	if (!f_setup.undo_slots)
	    h_flags &= ~UNDO_FLAG;
    if (h_flags & MOUSE_FLAG)
	if (subdisplay != -1 || !detect_mouse ())
	    h_flags &= ~MOUSE_FLAG;
    if (h_flags & COLOUR_FLAG)
	if (display == _MONO_ || display == _CGA_)
	    h_flags &= ~COLOUR_FLAG;
    h_flags &= ~MENU_FLAG;

    /* Set the screen dimensions, font size and default colour */

    h_screen_width = info[display].width;
    h_screen_height = info[display].height;
    h_font_height = info[display].font_height;
    h_font_width = info[display].font_width;
    h_default_foreground = info[display].fg;
    h_default_background = info[display].bg;

    if (subdisplay != -1) {
	h_screen_width = subinfo[subdisplay].width;
	h_screen_height = subinfo[subdisplay].height;
    }

    if (user_screen_width != -1)
	h_screen_width = user_screen_width;
    if (user_screen_height != -1)
	h_screen_height = user_screen_height;

    h_screen_cols = h_screen_width / h_font_width;
    h_screen_rows = h_screen_height / h_font_height;

    if (user_foreground != -1)
	h_default_foreground = zcolour[user_foreground];
    if (user_background != -1)
	h_default_background = zcolour[user_background];

    /* Set the interpreter number (a constant telling the game which
       operating system it runs on) and the interpreter version. The
       interpreter number has effect on V6 games and "Beyond Zork". */

    h_interpreter_number = INTERP_MSDOS;
    h_interpreter_version = 'F';

    if (display == _AMIGA_)
	h_interpreter_number = INTERP_AMIGA;

     /* Install the fast_exit routine to handle the ctrl-break key */

    oldvect = getvect (0x1b); setvect (0x1b, fast_exit);

}/* os_init_screen */


/*
 * os_reset_screen
 *
 * Reset the screen before the program stops.
 *
 */
void os_reset_screen (void)
{

    os_set_font (TEXT_FONT);
    os_set_text_style (0);
    os_display_string ((zchar *) "[Hit any key to exit.]");
    os_read_key (0, TRUE);

    cleanup ();

}/* os_reset_screen */


/*
 * os_restart_game
 *
 * This routine allows the interface to interfere with the process of
 * restarting a game at various stages:
 *
 *     RESTART_BEGIN - restart has just begun
 *     RESTART_WPROP_SET - window properties have been initialised
 *     RESTART_END - restart is complete
 *
 */
void os_restart_game (int stage)
{
    int x, y;

    if (story_id == BEYOND_ZORK)

	if (stage == RESTART_BEGIN)

	    if ((display == _MCGA_ || display == _AMIGA_) && os_picture_data (1, &x, &y)) {

		special_palette ();

		asm mov ax,0x1010
		asm mov bx,64
		asm mov dh,0
		asm mov ch,0
		asm mov cl,0
		asm int 0x10
		asm mov ax,0x1010
		asm mov bx,79
		asm mov dh,0xff
		asm mov ch,0xff
		asm mov cl,0xff
		asm int 0x10

		os_draw_picture (1, 1, 1);
		os_read_key (0, FALSE);

		standard_palette ();

	    }

}/* os_restart_game */


/*
 * os_random_seed
 *
 * Return an appropriate random seed value in the range from 0 to
 * 32767, possibly by using the current system time.
 *
 */
int os_random_seed (void)
{
    if (user_random_seed == -1) {

	/* Use the time of day as seed value */

	asm mov ah,0
	asm int 0x1a

	return _DX & 0x7fff;

    } else return user_random_seed;

}/* os_random_seed */


/*
 * os_path_open
 *
 * Open a file in the current directory.  If this fails then
 * search the directories in the ZCODE_PATH environment variable,
 * if it is defined, otherwise search INFOCOM_PATH.
 *
 */
FILE *os_path_open (const char *name, const char *mode)
{
    FILE *fp;
    char buf[MAX_FILE_NAME + 1];
    char *p, *bp, lastch;

    if ((fp = fopen (name, mode)) != NULL)
        return fp;
    if ((p = getenv ("ZCODE_PATH")) == NULL)
        p = getenv ("INFOCOM_PATH");
    if (p != NULL) {
	while (*p) {
	    bp = buf;
	    while (*p && *p != OS_PATHSEP)
		lastch = *bp++ = *p++;
	    if (lastch != '\\' && lastch != '/')
		*bp++ = '\\';
	    strcpy (bp, name);
	    if ((fp = fopen (buf, mode)) != NULL)
		return fp;
	    if (*p)
		p++;
	}
    }
    return NULL;
}/* os_path_open */


/*
 * os_load_story
 *
 * This is different from os_path_open() because we need to see if the
 * story file is actually a chunk inside a blorb file.  Right now we're
 * looking only at the exact path we're given on the command line.
 *
 * Open a file in the current directory.  If this fails, then search the
 * directories in the ZCODE_PATH environmental variable.  If that's not
 * defined, search INFOCOM_PATH.
 *
 */
FILE *os_load_story(void)
{
    FILE *fp;

    /* Did we build a valid blorb map? */
    if (exec_in_blorb) {
        fp = fopen(blorb_file, "rb");
        fseek(fp, blorb_res.data.startpos, SEEK_SET);
    } else {
        fp = fopen(f_setup.story_file, "rb");
    }
    return fp;
}


int dos_init_blorb(void)
{
    FILE *blorbfile;

    /* If the filename given on the command line is the same as our
     * computed blorb filename, then we will assume the executable
     * is contained in the blorb file.
     */

    if (strncmp((char *)basename(f_setup.story_file),
     (char *)basename(blorb_file), 55) == 0) {
	if ((blorbfile = fopen(blorb_file, "rb")) == NULL)
	    return bb_err_Read;
/* Under DOS, bb_create_map() returns bb_err_Format */
	blorb_err = bb_create_map(blorbfile, &blorb_map);

	if (blorb_err != bb_err_None) {
	    return blorb_err;
	}

    /* Now we need to locate the EXEC chunk within the blorb file
     * and present it to the rest of the program as a file stream.
     */

	blorb_err = bb_load_chunk_by_type(blorb_map, bb_method_FilePos,
			&blorb_res, bb_ID_ZCOD, 0);

	if (blorb_err == bb_err_None) {
	    exec_in_blorb = 1;
	    use_blorb = 1;
	}
    }
    return 0;
}


/*
 * Seek into a storyfile, either a standalone file or the
 * ZCODE chunk of a blorb file
 */
int os_storyfile_seek(FILE * fp, long offset, int whence)
{
    int retval;
    /* Is this a Blorb file containing Zcode? */
    if (exec_in_blorb) {
	switch (whence) {
	    case SEEK_END:
		retval = fseek(fp, blorb_res.data.startpos + blorb_res.length + offset, SEEK_SET);
		break;
	    case SEEK_CUR:
		retval = fseek(fp, offset, SEEK_CUR);
		break;
	    case SEEK_SET:
	    default:
		retval = fseek(fp, blorb_res.data.startpos + offset, SEEK_SET);
		break;
	}
	return retval;
    }
    return fseek(fp, offset, whence);
}


/*
 * Tell the position in a storyfile, either a standalone file
 * or the ZCODE chunk of a blorb file
 */
int os_storyfile_tell(FILE * fp)
{
    /* Is this a Blorb file containing Zcode? */
    if (exec_in_blorb)
       return ftell(fp) - blorb_res.data.startpos;

    return ftell(fp);
}
