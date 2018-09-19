/* fastmem.c - Memory related functions (fast version without virtual memory)
 *	Copyright (c) 1995-1997 Stefan Jokisch
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
 */

/*
 * New undo mechanism added by Jim Dunleavy <jim.dunleavy@erha.ie>
 */

#include <stdio.h>
#include <string.h>
#include "frotz.h"

#ifdef MSDOS_16BIT

#include <alloc.h>

#define malloc(size)	farmalloc (size)
#define realloc(size,p)	farrealloc (size,p)
#define free(size)	farfree (size)
#define memcpy(d,s,n)	_fmemcpy (d,s,n)

#else

#include <stdlib.h>

#ifndef SEEK_SET
#define SEEK_SET 0
#define SEEK_CUR 1
#define SEEK_END 2
#endif

#define far

#endif

extern void seed_random (int);
extern void restart_screen (void);
extern void refresh_text_style (void);
extern void call (zword, int, zword *, int);
extern void split_window (zword);
extern void script_open (void);
extern void script_close (void);

extern FILE *os_load_story (void);
extern int os_storyfile_seek (FILE * fp, long offset, int whence);
extern int os_storyfile_tell (FILE * fp);

extern zword save_quetzal (FILE *, FILE *);
extern zword restore_quetzal (FILE *, FILE *);

extern void erase_window (zword);

extern void (*op0_opcodes[]) (void);
extern void (*op1_opcodes[]) (void);
extern void (*op2_opcodes[]) (void);
extern void (*var_opcodes[]) (void);

/* char save_name[MAX_FILE_NAME + 1] = DEFAULT_SAVE_NAME; */
char auxilary_name[MAX_FILE_NAME + 1] = DEFAULT_AUXILARY_NAME;

zbyte far *zmp = NULL;
zbyte far *pcp = NULL;

FILE *story_fp = NULL;

/*
 * Data for the undo mechanism.
 * This undo mechanism is based on the scheme used in Evin Robertson's
 * Nitfol interpreter.
 * Undo blocks are stored as differences between states.
 */

typedef struct undo_struct undo_t;
struct undo_struct {
    undo_t *next;
    undo_t *prev;
    long pc;
    long diff_size;
    zword frame_count;
    zword stack_size;
    zword frame_offset;
    /* undo diff and stack data follow */
};

static undo_t *first_undo = NULL, *last_undo = NULL, *curr_undo = NULL;
zbyte *undo_mem = NULL, *prev_zmp, *undo_diff;

static int undo_count = 0;


/*
 * get_header_extension
 *
 * Read a value from the header extension (former mouse table).
 *
 */
zword get_header_extension (int entry)
{
    zword addr;
    zword val;

    if (h_extension_table == 0 || entry > hx_table_size)
	return 0;

    addr = h_extension_table + 2 * entry;
    LOW_WORD (addr, val);

    return val;

}/* get_header_extension */


/*
 * set_header_extension
 *
 * Set an entry in the header extension (former mouse table).
 *
 */
void set_header_extension (int entry, zword val)
{
    zword addr;

    if (h_extension_table == 0 || entry > hx_table_size)
	return;

    addr = h_extension_table + 2 * entry;
    SET_WORD (addr, val);

}/* set_header_extension */


/*
 * restart_header
 *
 * Set all header fields which hold information about the interpreter.
 *
 */
void restart_header (void)
{
    zword screen_x_size;
    zword screen_y_size;
    zbyte font_x_size;
    zbyte font_y_size;

    int i;

    SET_BYTE (H_CONFIG, h_config);
    SET_WORD (H_FLAGS, h_flags);

    if (h_version >= V4) {
	SET_BYTE (H_INTERPRETER_NUMBER, h_interpreter_number);
	SET_BYTE (H_INTERPRETER_VERSION, h_interpreter_version);
	SET_BYTE (H_SCREEN_ROWS, h_screen_rows);
	SET_BYTE (H_SCREEN_COLS, h_screen_cols);
    }

    /* It's less trouble to use font size 1x1 for V5 games, especially
       because of a bug in the unreleased German version of "Zork 1" */

    if (h_version != V6) {
	screen_x_size = (zword) h_screen_cols;
	screen_y_size = (zword) h_screen_rows;
	font_x_size = 1;
	font_y_size = 1;
    } else {
	screen_x_size = h_screen_width;
	screen_y_size = h_screen_height;
	font_x_size = h_font_width;
	font_y_size = h_font_height;
    }

    if (h_version >= V5) {
	SET_WORD (H_SCREEN_WIDTH, screen_x_size);
	SET_WORD (H_SCREEN_HEIGHT, screen_y_size);
	SET_BYTE (H_FONT_HEIGHT, font_y_size);
	SET_BYTE (H_FONT_WIDTH, font_x_size);
	SET_BYTE (H_DEFAULT_BACKGROUND, h_default_background);
	SET_BYTE (H_DEFAULT_FOREGROUND, h_default_foreground);
    }

    if (h_version == V6)
	for (i = 0; i < 8; i++)
	    storeb ((zword) (H_USER_NAME + i), h_user_name[i]);

    SET_BYTE (H_STANDARD_HIGH, h_standard_high);
    SET_BYTE (H_STANDARD_LOW, h_standard_low);

}/* restart_header */


/*
 * init_memory
 *
 * Allocate memory and load the story file.
 *
 * Data collected from http://www.russotto.net/zplet/ivl.html
 *
 */
void init_memory (void)
{
    long size;
    zword addr;
    unsigned n;
    int i, j;

    static struct {
	enum story story_id;
	zword release;
	zbyte serial[6];
    } records[] = {
	{	   ZORK1,   2, "AS000C" },
	{	   ZORK1,   5, ""       },
	{	   ZORK1,  15, "UG3AU5" },
	{	   ZORK1,  23, "820428" },
	{	   ZORK1,  25, "820515" },
	{	   ZORK1,  26, "820803" },
	{	   ZORK1,  28, "821013" },
	{	   ZORK1,  30, "830330" },
	{	   ZORK1,  75, "830929" },
	{	   ZORK1,  76, "840509" },
	{	   ZORK1,  88, "840726" },
	{	   ZORK1,  52, "871125" },
	{	  ZORK1G,   3, "880113" },
	{	   ZORK2,   7, "UG3AU5" },
	{	   ZORK2,  15, "820308" },
	{	   ZORK2,  17, "820427" },
	{	   ZORK2,  18, "820512" },
	{	   ZORK2,  18, "820517" },
	{	   ZORK2,  19, "820721" },
	{	   ZORK2,  22, "830331" },
	{	   ZORK2,  23, "830411" },
	{	   ZORK2,  48, "840904" },
	{	   ZORK3,  10, "820818" },
	{	   ZORK3,  12, "821025" },
	{	   ZORK3,  15, "830331" },
	{	   ZORK3,  15, "840518" },
	{	   ZORK3,  16, "830410" },
	{	   ZORK3,  17, "840727" },
	{	MINIZORK,  34, "871124" },
	{	SAMPLER1,  26, "840731" },
	{	SAMPLER1,  53, "850407" },
	{	SAMPLER1,  55, "850823" },
	{	SAMPLER2,  97, "870601" },
	{      ENCHANTER,  10, "830810" },
	{      ENCHANTER,  15, "831107" },
	{      ENCHANTER,  16, "831118" },
	{      ENCHANTER,  24, "851118" },
	{      ENCHANTER,  29, "860820" },
	{	SORCERER,   4, "840131" },
	{	SORCERER,   6, "840508" },
	{	SORCERER,  13, "851021" },
	{	SORCERER,  15, "851108" },
	{	SORCERER,  18, "860904" },
	{	SORCERER,  67, "0"      },
	{	SORCERER,  63, "850916" },
	{	SORCERER,  87, "860904" },
	{   SPELLBREAKER,  63, "850916" },
	{   SPELLBREAKER,  87, "860904" },
	{     PLANETFALL,  20, "830708" },
	{     PLANETFALL,  26, "831014" },
	{     PLANETFALL,  29, "840118" },
	{     PLANETFALL,  37, "851003" },
	{     PLANETFALL,  10, "880531" },
	{    STATIONFALL, 107, "870430" },
	{	BALLYHOO,  97, "851218" },
	{    BORDER_ZONE,   9, "871008" },
	{	    AMFV,  77, "850814" },
	{	    AMFV,  79, "851122" },
	{	    HHGG,  47, "840914" },
	{	    HHGG,  56, "841221" },
	{	    HHGG,  58, "851002" },
	{	    HHGG,  59, "851108" },
	{	    HHGG,  31, "871119" },
	{	    LGOP,   0, "BLOWN!" },
	{	    LGOP,  50, "860711" },
	{	    LGOP,  59, "860730" },
	{	    LGOP,  59, "861114" },
	{	    LGOP, 118, "860325" },
	{	    LGOP,   4, "880405" },
	{	 SUSPECT,  14, "841005" },
	{       SHERLOCK,  21, "871214" },
	{       SHERLOCK,  26, "880127" },
	{    BEYOND_ZORK,  47, "870915" },
	{    BEYOND_ZORK,  49, "870917" },
	{    BEYOND_ZORK,  51, "870923" },
	{    BEYOND_ZORK,  57, "871221" },
	{      ZORK_ZERO, 296, "881019" },
	{      ZORK_ZERO, 366, "890323" },
	{      ZORK_ZERO, 383, "890602" },
	{      ZORK_ZERO, 393, "890714" },
	{         SHOGUN, 292, "890314" },
	{         SHOGUN, 295, "890321" },
	{         SHOGUN, 311, "890510" },
	{         SHOGUN, 322, "890706" },
	{         ARTHUR,  54, "890606" },
	{         ARTHUR,  63, "890622" },
	{         ARTHUR,  74, "890714" },
	{        JOURNEY,  26, "890316" },
	{        JOURNEY,  30, "890322" },
	{        JOURNEY,  77, "890616" },
	{        JOURNEY,  83, "890706" },
	{ LURKING_HORROR, 203, "870506" },
	{ LURKING_HORROR, 219, "870912" },
	{ LURKING_HORROR, 221, "870918" },
	{        UNKNOWN,   0, "------" }
    };

    /* Open story file */

    if ((story_fp = os_load_story()) == NULL)
        os_fatal ("Cannot open story file");

    /* Allocate memory for story header */

    if ((zmp = (zbyte far *) malloc (64)) == NULL)
	os_fatal ("Out of memory");

    /* Load header into memory */

    if (fread (zmp, 1, 64, story_fp) != 64)
	os_fatal ("Story file read error");

    /* Copy header fields to global variables */

    LOW_BYTE (H_VERSION, h_version);

    if (h_version < V1 || h_version > V8)
	os_fatal ("Unknown Z-code version");

    LOW_BYTE (H_CONFIG, h_config);

    if (h_version == V3 && (h_config & CONFIG_BYTE_SWAPPED))
	os_fatal ("Byte swapped story file");

    LOW_WORD (H_RELEASE, h_release);
    LOW_WORD (H_RESIDENT_SIZE, h_resident_size);
    LOW_WORD (H_START_PC, h_start_pc);
    LOW_WORD (H_DICTIONARY, h_dictionary);
    LOW_WORD (H_OBJECTS, h_objects);
    LOW_WORD (H_GLOBALS, h_globals);
    LOW_WORD (H_DYNAMIC_SIZE, h_dynamic_size);
    LOW_WORD (H_FLAGS, h_flags);

    for (i = 0, addr = H_SERIAL; i < 6; i++, addr++)
	LOW_BYTE (addr, h_serial[i]);

    /* Auto-detect buggy story files that need special fixes */

    story_id = UNKNOWN;

    for (i = 0; records[i].story_id != UNKNOWN; i++) {

	if (h_release == records[i].release) {

	    for (j = 0; j < 6; j++)
		if (h_serial[j] != records[i].serial[j])
		    goto no_match;

	    story_id = records[i].story_id;

	}

    no_match: ; /* null statement */

    }

    LOW_WORD (H_ABBREVIATIONS, h_abbreviations);
    LOW_WORD (H_FILE_SIZE, h_file_size);

    /* Calculate story file size in bytes */

    if (h_file_size != 0) {

	story_size = (long) 2 * h_file_size;

	if (h_version >= V4)
	    story_size *= 2;
	if (h_version >= V6)
	    story_size *= 2;

    } else {		/* some old games lack the file size entry */
	os_storyfile_seek (story_fp, 0, SEEK_END);
	story_size = os_storyfile_tell (story_fp);
	os_storyfile_seek (story_fp, 64, SEEK_SET);
    }

    LOW_WORD (H_CHECKSUM, h_checksum);
    LOW_WORD (H_ALPHABET, h_alphabet);
    LOW_WORD (H_FUNCTIONS_OFFSET, h_functions_offset);
    LOW_WORD (H_STRINGS_OFFSET, h_strings_offset);
    LOW_WORD (H_TERMINATING_KEYS, h_terminating_keys);
    LOW_WORD (H_EXTENSION_TABLE, h_extension_table);

    /* Zork Zero Macintosh doesn't have the graphics flag set */

    if (story_id == ZORK_ZERO && h_release == 296)
	h_flags |= GRAPHICS_FLAG;

    /* Adjust opcode tables */

    if (h_version <= V4) {
	op0_opcodes[0x09] = z_pop;
	op1_opcodes[0x0f] = z_not;
    } else {
	op0_opcodes[0x09] = z_catch;
	op1_opcodes[0x0f] = z_call_n;
    }

    /* Allocate memory for story data */

    if ((zmp = (zbyte far *) realloc (zmp, story_size)) == NULL)
	os_fatal ("Out of memory");

    /* Load story file in chunks of 32KB */

    n = 0x8000;

    for (size = 64; size < story_size; size += n) {

	if (story_size - size < 0x8000)
	    n = (unsigned) (story_size - size);

	SET_PC (size);

	if (fread (pcp, 1, n, story_fp) != n)
	    os_fatal ("Story file read error");

    }

    /* Read header extension table */

    hx_table_size = get_header_extension (HX_TABLE_SIZE);
    hx_unicode_table = get_header_extension (HX_UNICODE_TABLE);

}/* init_memory */


/*
 * init_undo
 *
 * Allocate memory for multiple undo. It is important not to occupy
 * all the memory available, since the IO interface may need memory
 * during the game, e.g. for loading sounds or pictures.
 *
 */
void init_undo (void)
{
    void far *reserved;

    reserved = NULL;	/* makes compilers shut up */

    if (reserve_mem != 0) {
	if ((reserved = malloc (reserve_mem)) == NULL)
	    return;
    }

    /* Allocate h_dynamic_size bytes for previous dynamic zmp state
       + 1.5 h_dynamic_size for Quetzal diff + 2. */
    undo_mem = malloc ((h_dynamic_size * 5) / 2 + 2);
    if (undo_mem != NULL) {
	prev_zmp = undo_mem;
	undo_diff = undo_mem + h_dynamic_size;
	memcpy (prev_zmp, zmp, h_dynamic_size);
    } else
	f_setup.undo_slots = 0;

    if (reserve_mem != 0)
	free (reserved);

}/* init_undo */


/*
 * free_undo
 *
 * Free count undo blocks from the beginning of the undo list.
 *
 */
static void free_undo (int count)
{
    undo_t *p;

    if (count > undo_count)
	count = undo_count;
    while (count--) {
	p = first_undo;
	if (curr_undo == first_undo)
	    curr_undo = curr_undo->next;
	first_undo = first_undo->next;
	free (p);
	undo_count--;
    }
    if (first_undo)
	first_undo->prev = NULL;
    else
	last_undo = NULL;
}/* free_undo */


/*
 * reset_memory
 *
 * Close the story file and deallocate memory.
 *
 */
void reset_memory (void)
{
    if (story_fp != NULL)
	fclose (story_fp);
    story_fp = NULL;

    if (undo_mem) {
	free_undo (undo_count);
	free (undo_mem);
    }

    undo_mem = NULL;
    undo_count = 0;

    if (zmp)
	free (zmp);
    zmp = NULL;
}/* reset_memory */


/*
 * storeb
 *
 * Write a byte value to the dynamic Z-machine memory.
 *
 */
void storeb (zword addr, zbyte value)
{
    if (addr >= h_dynamic_size)
	runtime_error (ERR_STORE_RANGE);

    if (addr == H_FLAGS + 1) {	/* flags register is modified */

	h_flags &= ~(SCRIPTING_FLAG | FIXED_FONT_FLAG);
	h_flags |= value & (SCRIPTING_FLAG | FIXED_FONT_FLAG);

	if (value & SCRIPTING_FLAG) {
	    if (!ostream_script)
		script_open ();
	} else {
	    if (ostream_script)
		script_close ();
	}

	refresh_text_style ();

    }

    SET_BYTE (addr, value);

}/* storeb */


/*
 * storew
 *
 * Write a word value to the dynamic Z-machine memory.
 *
 */
void storew (zword addr, zword value)
{
    storeb ((zword) (addr + 0), hi (value));
    storeb ((zword) (addr + 1), lo (value));

}/* storew */


/*
 * z_restart, re-load dynamic area, clear the stack and set the PC.
 *
 * 	no zargs used
 *
 */
void z_restart (void)
{
    static bool first_restart = TRUE;

    flush_buffer ();

    os_restart_game (RESTART_BEGIN);

    seed_random (0);

    if (!first_restart) {

	os_storyfile_seek (story_fp, 0, SEEK_SET);

	if (fread (zmp, 1, h_dynamic_size, story_fp) != h_dynamic_size)
	    os_fatal ("Story file read error");

    } else first_restart = FALSE;

    restart_header ();
    restart_screen ();

    sp = fp = stack + STACK_SIZE;
    frame_count = 0;

    if (h_version != V6) {

	long pc = (long) h_start_pc;
	SET_PC (pc);

    } else call (h_start_pc, 0, NULL, 0);

    os_restart_game (RESTART_END);

}/* z_restart */


/*
 * get_default_name
 *
 * Read a default file name from the memory of the Z-machine and
 * copy it to a string.
 *
 */
static void get_default_name (char *default_name, zword addr)
{
    if (addr != 0) {

	zbyte len;
	int i;

	LOW_BYTE (addr, len);
	addr++;

	for (i = 0; i < len; i++) {

	    zbyte c;

	    LOW_BYTE (addr, c);
	    addr++;

	    if (c >= 'A' && c <= 'Z')
		c += 'a' - 'A';

	    default_name[i] = c;

	}

	default_name[i] = 0;

	if (strchr (default_name, '.') == NULL)
	    strcpy (default_name + i, ".AUX");

    } else strcpy (default_name, f_setup.aux_name);

}/* get_default_name */


/*
 * z_restore, restore [a part of] a Z-machine state from disk
 *
 *	zargs[0] = address of area to restore (optional)
 *	zargs[1] = number of bytes to restore
 *	zargs[2] = address of suggested file name
 *
 */
void z_restore (void)
{
    char new_name[MAX_FILE_NAME + 1];
    char default_name[MAX_FILE_NAME + 1];
    FILE *gfp = NULL;

    zword success = 0;

    if (zargc != 0) {

	/* Get the file name */

	get_default_name (default_name, (zargc >= 3) ? zargs[2] : 0);

	if (os_read_file_name (new_name, default_name, FILE_LOAD_AUX) == 0)
	    goto finished;

	strcpy (f_setup.aux_name, default_name);

	/* Open auxilary file */

	if ((gfp = fopen (new_name, "rb")) == NULL)
	    goto finished;

	/* Load auxilary file */

	success = fread (zmp + zargs[0], 1, zargs[1], gfp);

	/* Close auxilary file */

	fclose (gfp);

    } else {

//	long pc;
//	zword release;
//	zword addr;
//	int i;

	/* Get the file name */

	if (os_read_file_name (new_name, f_setup.save_name, FILE_RESTORE) == 0)
	    goto finished;

	strcpy (f_setup.save_name, new_name);

	/* Open game file */

	if ((gfp = fopen (new_name, "rb")) == NULL)
	    goto finished;

	success = restore_quetzal (gfp, story_fp);

	if ((short) success >= 0) {

	    /* Close game file */

	    fclose (gfp);

	    if ((short) success > 0) {
		zbyte old_screen_rows;
		zbyte old_screen_cols;

		/* In V3, reset the upper window. */
		if (h_version == V3)
		    split_window (0);

		LOW_BYTE (H_SCREEN_ROWS, old_screen_rows);
		LOW_BYTE (H_SCREEN_COLS, old_screen_cols);

		/* Reload cached header fields. */
		restart_header ();

		/*
		 * Since QUETZAL files may be saved on many different machines,
		 * the screen sizes may vary a lot. Erasing the status window
		 * seems to cover up most of the resulting badness.
		 */
		if (h_version > V3 && h_version != V6
		    && (h_screen_rows != old_screen_rows
		    || h_screen_cols != old_screen_cols))
		    erase_window (1);
	    }
	} else
	    os_fatal ("Error reading save file");
    }

finished:

    if (gfp == NULL && f_setup.restore_mode)
	os_fatal ("Error reading save file");

    if (h_version <= V3)
	branch (success);
    else
	store (success);

}/* z_restore */


/*
 * mem_diff
 *
 * Set diff to a Quetzal-like difference between a and b,
 * copying a to b as we go.  It is assumed that diff points to a
 * buffer which is large enough to hold the diff.
 * mem_size is the number of bytes to compare.
 * Returns the number of bytes copied to diff.
 *
 */
static long mem_diff (zbyte *a, zbyte *b, zword mem_size, zbyte *diff)
{
    unsigned size = mem_size;
    zbyte *p = diff;
    unsigned j;
    zbyte c;

    for (;;) {
	for (j = 0; size > 0 && (c = *a++ ^ *b++) == 0; j++)
	    size--;
	if (size == 0) break;
	size--;
	if (j > 0x8000) {
	    *p++ = 0;
	    *p++ = 0xff;
	    *p++ = 0xff;
	    j -= 0x8000;
	}
	if (j > 0) {
	    *p++ = 0;
	    j--;
	    if (j <= 0x7f) {
		*p++ = j;
	    } else {
		*p++ = (j & 0x7f) | 0x80;
		*p++ = (j & 0x7f80) >> 7;
	    }
	}
	*p++ = c;
	*(b - 1) ^= c;
    }
    return p - diff;
}/* mem_diff */


/*
 * mem_undiff
 *
 * Applies a quetzal-like diff to dest
 *
 */
static void mem_undiff (zbyte *diff, long diff_length, zbyte *dest)
{
    zbyte c;

    while (diff_length) {
	c = *diff++;
	diff_length--;
	if (c == 0) {
	    unsigned runlen;

	    if (!diff_length)
		return;  /* Incomplete run */
	    runlen = *diff++;
	    diff_length--;
	    if (runlen & 0x80) {
		if (!diff_length)
		    return; /* Incomplete extended run */
		c = *diff++;
		diff_length--;
		runlen = (runlen & 0x7f) | (((unsigned) c) << 7);
	    }

	    dest += runlen + 1;
	} else {
	    *dest++ ^= c;
	}
    }
}/* mem_undiff */


/*
 * restore_undo
 *
 * This function does the dirty work for z_restore_undo.
 *
 */
int restore_undo (void)
{
    long pc = curr_undo->pc;

    if (f_setup.undo_slots == 0)	/* undo feature unavailable */

	return -1;

    if (curr_undo == NULL)		/* no saved game state */

	return 0;

    /* undo possible */

    memcpy (zmp, prev_zmp, h_dynamic_size);
    SET_PC (pc);
    sp = stack + STACK_SIZE - curr_undo->stack_size;
    fp = stack + curr_undo->frame_offset;
    frame_count = curr_undo->frame_count;
    mem_undiff ((zbyte *) (curr_undo + 1), curr_undo->diff_size, prev_zmp);
    memcpy (sp, (zbyte *)(curr_undo + 1) + curr_undo->diff_size,
	    curr_undo->stack_size * sizeof (*sp));

    curr_undo = curr_undo->prev;

    restart_header ();

    return 2;

}/* restore_undo */


/*
 * z_restore_undo, restore a Z-machine state from memory.
 *
 *	no zargs used
 *
 */
void z_restore_undo (void)
{
    store ((zword) restore_undo ());

}/* z_restore_undo */


/*
 * z_save, save [a part of] the Z-machine state to disk.
 *
 *	zargs[0] = address of memory area to save (optional)
 *	zargs[1] = number of bytes to save
 *	zargs[2] = address of suggested file name
 *
 */
void z_save (void)
{
    char new_name[MAX_FILE_NAME + 1];
    char default_name[MAX_FILE_NAME + 1];
    FILE *gfp;

    zword success = 0;

    if (zargc != 0) {

	/* Get the file name */

	get_default_name (default_name, (zargc >= 3) ? zargs[2] : 0);

	if (os_read_file_name (new_name, default_name, FILE_SAVE_AUX) == 0)
	    goto finished;

	strcpy (f_setup.aux_name, default_name);

	/* Open auxilary file */

	if ((gfp = fopen (new_name, "wb")) == NULL)
	    goto finished;

	/* Write auxilary file */

	success = fwrite (zmp + zargs[0], zargs[1], 1, gfp);

	/* Close auxilary file */

	fclose (gfp);

    } else {

//	long pc;
//	zword addr;
//	zword nsp, nfp;
//	int skip;
//	int i;

	/* Get the file name */

	if (os_read_file_name (new_name, f_setup.save_name, FILE_SAVE) == 0)
	    goto finished;

	strcpy (f_setup.save_name, new_name);

	/* Open game file */

	if ((gfp = fopen (new_name, "wb")) == NULL)
	    goto finished;

	success = save_quetzal (gfp, story_fp);

	/* Close game file and check for errors */

	if (fclose (gfp) == EOF || ferror (story_fp)) {
	    print_string ("Error writing save file\n");
	    goto finished;
	}

	/* Success */

	success = 1;
    }

finished:

    if (h_version <= V3)
	branch (success);
    else
	store (success);

}/* z_save */


/*
 * save_undo
 *
 * This function does the dirty work for z_save_undo.
 *
 */
int save_undo (void)
{
    long diff_size;
    zword stack_size;
    undo_t *p;
    long pc;

    if (f_setup.undo_slots == 0)	/* undo feature unavailable */
	return -1;

    /* save undo possible */

    while (last_undo != curr_undo) {
	p = last_undo;
	last_undo = last_undo->prev;
	free (p);
	undo_count--;
    }
    if (last_undo)
	last_undo->next = NULL;
    else
	first_undo = NULL;

    if (undo_count == f_setup.undo_slots)
	free_undo (1);

    diff_size = mem_diff (zmp, prev_zmp, h_dynamic_size, undo_diff);
    stack_size = stack + STACK_SIZE - sp;
    do {
	p = malloc (sizeof (undo_t) + diff_size + stack_size * sizeof (*sp));
	if (p == NULL)
	    free_undo (1);
    } while (!p && undo_count);
    if (p == NULL)
	return -1;
    pc = p->pc;
    GET_PC (pc);	/* Turbo C doesn't like seeing p->pc here */
    p->pc = pc;
    p->frame_count = frame_count;
    p->diff_size = diff_size;
    p->stack_size = stack_size;
    p->frame_offset = fp - stack;
    memcpy (p + 1, undo_diff, diff_size);
    memcpy ((zbyte *)(p + 1) + diff_size, sp, stack_size * sizeof (*sp));

    if (!first_undo) {
	p->prev = NULL;
	first_undo = p;
    } else {
	last_undo->next = p;
	p->prev = last_undo;
    }
    p->next = NULL;
    curr_undo = last_undo = p;
    undo_count++;
    return 1;

}/* save_undo */


/*
 * z_save_undo, save the current Z-machine state for a future undo.
 *
 *	no zargs used
 *
 */
void z_save_undo (void)
{
    store ((zword) save_undo ());

}/* z_save_undo */


/*
 * z_verify, check the story file integrity.
 *
 *	no zargs used
 *
 */
void z_verify (void)
{
    zword checksum = 0;
    long i;

    /* Sum all bytes in story file except header bytes */

    os_storyfile_seek (story_fp, 64, SEEK_SET);

    for (i = 64; i < story_size; i++)
	checksum += fgetc (story_fp);

    /* Branch if the checksums are equal */

    branch (checksum == h_checksum);

}/* z_verify */
