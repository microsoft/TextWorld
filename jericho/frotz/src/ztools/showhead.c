/*
 * showhead - part of infodump
 *
 * Header display routines.
 */

#include "tx.h"

#ifdef __STDC__
static void show_header_extension (void);
#else
static void show_header_extension ();
#endif

static const char *interpreter_flags1[] = {
    "Byte swapped data",
    "Display time",
    "Unknown (0x04)",
    "Tandy",
    "No status line",
    "Windows available",
    "Proportional fonts used",
    "Unknown (0x80)"
};

static const char *interpreter_flags2[] = {
    "Colours",
    "Pictures",
    "Bold font",
    "Emphasis",
    "Fixed space font",
    "Unknown (0x20)",
    "Unknown (0x40)",
    "Timed input"
};

static const char *game_flags1[] = {
    "Scripting",
    "Use fixed font",
    "Unknown (0x0004)",
    "Unknown (0x0008)",
    "Supports sound",
    "Unknown (0x0010)",
    "Unknown (0x0020)",
    "Unknown (0x0040)",
    "Unknown (0x0080)",
    "Unknown (0x0200)",
    "Unknown (0x0400)",
    "Unknown (0x0800)",
    "Unknown (0x1000)",
    "Unknown (0x2000)",
    "Unknown (0x4000)",
    "Unknown (0x8000)"
};

static const char *game_flags2[] = {
    "Scripting",
    "Use fixed font",
    "Screen refresh required",
    "Supports graphics",
    "Supports undo",
    "Supports mouse",
    "Supports colour",
    "Supports sound",
    "Supports menus",
    "Unknown (0x0200)",
    "Printer error",
    "Unknown (0x0800)",
    "Unknown (0x1000)",
    "Unknown (0x2000)",
    "Unknown (0x4000)",
    "Unknown (0x8000)"
};

/*
 * show_header
 *
 * Format the header which is a 64 byte area at the front of the story file.
 * The format of the header is described by the header structure.
 */

#ifdef __STDC__
void show_header (void)
#else
void show_header ()
#endif
{
    unsigned long address;
    int i, j, list;
    short inform = 0;

    if (header.serial[0] >= '0' && header.serial[0] <= '9' &&
		header.serial[1] >= '0' && header.serial[1] <= '9' &&
		header.serial[2] >= '0' && header.serial[2] <= '1' &&
		header.serial[3] >= '0' && header.serial[3] <= '9' &&
		header.serial[4] >= '0' && header.serial[4] <= '3' &&
		header.serial[5] >= '0' && header.serial[5] <= '9' &&
		header.serial[0] != '8') {
		inform = 5;

		if (header.name[4] >= '6')
			inform = header.name[4] - '0';
    }


    tx_printf ("\n    **** Story file header ****\n\n");

    /* Z-code version */

    tx_printf ("Z-code version:           %d\n", (int) header.version);

    /* Interpreter flags */

    tx_printf ("Interpreter flags:        ");
    tx_fix_margin (1);
    list = 0;
    for (i = 0; i < 8; i++) {
	if ((unsigned int) header.config & (1 << i)) {
	    tx_printf ("%s%s", (list++) ? ", " : "",
		       ((unsigned int) header.version < V4) ? interpreter_flags1[i] : interpreter_flags2[i]);
	} else {
	    if ((unsigned int) header.version < V4 && i == 1)
		tx_printf ("%sDisplay score/moves", (list++) ? ", " : "");
	}
    }
    if (list == 0)
	tx_printf ("None");
    tx_printf ("\n");
    tx_fix_margin (0);

    /* Release number */

    tx_printf ("Release number:           %d\n", (int) header.release);

    /* Size of resident memory */

    tx_printf ("Size of resident memory:  %04x\n", (unsigned int) header.resident_size);

    /* Start PC */

    if ((unsigned int) header.version != V6)
	tx_printf ("Start PC:                 %04x\n", (unsigned int) header.start_pc);
    else
	tx_printf ("Main routine address:     %05lx\n", (unsigned long)
		   (((unsigned long) header.start_pc * code_scaler) +
		    ((unsigned long) header.routines_offset * story_scaler)));

    /* Dictionary address */

    tx_printf ("Dictionary address:       %04x\n", (unsigned int) header.dictionary);

    /* Object table address */

    tx_printf ("Object table address:     %04x\n", (unsigned int) header.objects);

    /* Global variables address */

    tx_printf ("Global variables address: %04x\n", (unsigned int) header.globals);

    /* Size of dynamic memory */

    tx_printf ("Size of dynamic memory:   %04x\n", (unsigned int) header.dynamic_size);

    /* Game flags */

    tx_printf ("Game flags:               ");
    tx_fix_margin (1);
    list = 0;
    for (i = 0; i < 16; i++) {
	if ((unsigned int) header.flags & (1 << i)) {
	    tx_printf ("%s%s", (list++) ? ", " : "",
		       ((unsigned int) header.version < V4) ? game_flags1[i] : game_flags2[i]);
	}
    }
    if (list == 0)
	tx_printf ("None");
    tx_printf ("\n");
    tx_fix_margin (0);

    /* Serial number */

    tx_printf ("Serial number:            %c%c%c%c%c%c\n",
	    (char) header.serial[0], (char) header.serial[1],
	    (char) header.serial[2], (char) header.serial[3],
	    (char) header.serial[4], (char) header.serial[5]);

    /* Abbreviations address */

    if ((unsigned int) header.abbreviations)
	tx_printf ("Abbreviations address:    %04x\n", (unsigned int) header.abbreviations);

    /* File size and checksum */

    if ((unsigned int) header.file_size) {
	tx_printf ("File size:                %05lx\n", (unsigned long) file_size);
	tx_printf ("Checksum:                 %04x\n", (unsigned int) header.checksum);
    }

#if defined(FULL_HEADER)

    /* Interpreter */

    tx_printf ("Interpreter number:       %d ", header.interpreter_number);
    switch ((unsigned int) header.interpreter_number) {
	case 1 : tx_printf ("DEC-20"); break;
	case 2 : tx_printf ("Apple //e"); break;
	case 3 : tx_printf ("Macintosh"); break;
	case 4 : tx_printf ("Amiga"); break;
	case 5 : tx_printf ("Atari ST"); break;
	case 6 : tx_printf ("IBM/MS-DOS"); break;
	case 7 : tx_printf ("Commodore 128"); break;
	case 8 : tx_printf ("C64"); break;
	case 9 : tx_printf ("Apple //c"); break;
	case 10: tx_printf ("Apple //gs"); break;
	case 11: tx_printf ("Tandy Color Computer"); break;
	default: tx_printf ("Unknown");
    }
    tx_printf ("\n");

    /* Interpreter version */

    tx_printf ("Interpreter version:      ");
    if (isprint ((unsigned int) header.interpreter_version))
	tx_printf ("%c\n", (char) header.interpreter_version);
    else
	tx_printf ("%d\n", (int) header.interpreter_version);

    /* Screen dimensions */

    tx_printf ("Screen rows:              %d\n", (int) header.screen_rows);
    tx_printf ("Screen columns:           %d\n", (int) header.screen_columns);
    tx_printf ("Screen width:             %d\n", (int) header.screen_width);
    tx_printf ("Screen height:            %d\n", (int) header.screen_height);

    /* Font size */

    tx_printf ("Font width:               %d\n", (int) header.font_width);
    tx_printf ("Font height:              %d\n", (int) header.font_height);

#endif /* defined(FULL_HEADER) */

    /* V6 and V7 offsets */

    if ((unsigned int) header.routines_offset)
	tx_printf ("Routines offset:          %05lx\n", (unsigned long) header.routines_offset * story_scaler);
    if ((unsigned int) header.strings_offset)
	tx_printf ("Strings offset:           %05lx\n", (unsigned long) header.strings_offset * story_scaler);

#if defined(FULL_HEADER)

    /* Default colours */

    tx_printf ("Background color:         %d\n", (int) header.default_background);
    tx_printf ("Foreground color:         %d\n", (int) header.default_foreground);

#endif /* defined(FULL_HEADER) */

    /* Function keys address */

    if ((unsigned int) header.terminating_keys) {
	tx_printf ("Terminating keys address: %04x\n", (unsigned int) header.terminating_keys);
	address = (unsigned long) header.terminating_keys;
	tx_printf ("    Keys used: ");
	tx_fix_margin (1);
	list = 0;
	for (i = (unsigned int) read_data_byte (&address); i;
	     i = (unsigned int) read_data_byte (&address)) {
	    if (list)
		tx_printf (", ");
	    if (i == 0x81)
		tx_printf ("Up arrow"); /* Arrow keys */
	    else if (i == 0x82)
		tx_printf ("Down arrow");
	    else if (i == 0x83)
		tx_printf ("Left arrow");
	    else if (i == 0x84)
		tx_printf ("Right arrow");
	    else if (i >= 0x85 && i <= 0x90)
		tx_printf ("F%d", (int) (i - 0x84)); /* Function keys */
	    else if (i >= 0x91 && i <= 0x9a)
		tx_printf ("KP%d", (int) (i - 0x91)); /* Keypad keys */
	    else if (i == 0xfc)
		tx_printf ("Menu click");
	    else if (i == 0xfd)
		tx_printf ("Single mouse click");
	    else if (i == 0xfe)
		tx_printf ("Double mouse click");
	    else if (i == 0xff)
		tx_printf ("Any function key");
	    else
		tx_printf ("Unknown key (0x%02x)", (unsigned int) i);
	    list++;
	}
	tx_printf ("\n");
	tx_fix_margin (0);
    }

#if defined(FULL_HEADER)

    /* Line width */

    tx_printf ("Line width:               %d\n", (int) header.line_width);

    /* Specification number */

    if ((unsigned int) header.specification_hi)
	tx_printf ("Specification number:   %d.%d",
		   (unsigned int) header.specification_hi,
		   (unsigned int) header.specification_lo);

#endif /* defined(FULL_HEADER) */

    /* Alphabet address */

    if ((unsigned int) header.alphabet) {
	tx_printf ("Alphabet address:         %04x\n", (unsigned int) header.alphabet);
	tx_printf ("    ");
	tx_fix_margin (1);
	for (i = 0; i < 3; i++) {
	    tx_printf ("\"");
	    for (j = 0; j < 26; j++)
		tx_printf ("%c", (char) get_byte ((unsigned int) header.alphabet + (i * 26) + j));
	    tx_printf ("\"\n");
	}
	tx_fix_margin (0);
    }

    /* Mouse table address */

    if ((unsigned int) header.mouse_table)
	tx_printf ("Header extension address: %04x\n", (unsigned int) header.mouse_table);

#if defined(FULL_HEADER)

    /* Name */

    if ((unsigned int) header.name[0] || (unsigned int) header.name[1] || (unsigned int) header.name[2] || (unsigned int) header.name[3] ||
	(unsigned int) header.name[4] || (unsigned int) header.name[5] || (unsigned int) header.name[6] || (unsigned int) header.name[7]) {
	tx_printf ("Name:                     \"");
	for (i = 0; i < sizeof (header.name); i++)
	    tx_printf ("%c", (char) header.name[i]);
	tx_printf ("\"\n");
    }

#endif /* defined(FULL_HEADER) */
    
    /* Inform version -- overlaps name */
    if (inform >= 6) {
	tx_printf ("Inform Version:           ");
	for (i = 4; i < sizeof (header.name); i++)
	    tx_printf ("%c", (char) header.name[i]);
	tx_printf ("\n");
    }

    show_header_extension();

}/* show_header */

#ifdef __STDC__
static void show_header_extension (void)
#else
static void show_header_extension ()
#endif
{
    zword_t tlen;

    if ((unsigned int) header.mouse_table) {
	tlen = get_word(header.mouse_table); 
	tx_printf ("Header extension length:  %04x\n", tlen);
    }
    else
	return;

#if defined(FULL_HEADER)
    if (tlen > 0)
	tx_printf ("Mouse Y coordinate:       %04x\n", get_word(header.mouse_table + 2));
    if (tlen > 1)
	tx_printf ("Mouse X coordinate:       %04x\n", get_word(header.mouse_table + 4));
#endif /* defined(FULL_HEADER) */

    if (tlen > 2)
	tx_printf ("Unicode table address:    %04x\n", (unsigned long)get_word(header.mouse_table + 6));
}
