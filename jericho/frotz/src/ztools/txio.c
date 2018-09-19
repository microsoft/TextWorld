/* txio.c
 *
 * I/O routines for Z code disassembler and story file dumper.
 *
 * Mark Howell 26 August 1992 howell_ma@movies.enet.dec.com
 *
 */

#include "tx.h"
#ifdef MAC_MPW
#include <CursorCtl.h>
#include <Signal.h>
#endif


zheader_t header;

int story_scaler;
int story_shift;
int code_scaler;
int code_shift;
int property_mask;
int property_size_mask;

zbyte_t *datap;

int option_inform = 0;

unsigned long file_size = 0;

static const char *v1_lookup_table[3] = {
    "abcdefghijklmnopqrstuvwxyz",
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    " 0123456789.,!?_#'\"/\\<-:()"
};

static const char *v3_lookup_table[3] = {
    "abcdefghijklmnopqrstuvwxyz",
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    " \n0123456789.,!?_#'\"/\\-:()"
};

static const char *euro_substitute[69] = {
    "ae", "oe", "ue", "Ae", "Oe", "Ue", "ss", ">>", "<<", "e",
    "i",  "y",  "E",  "I",  "a",  "e",  "i",  "o",  "u",  "y",
    "A",  "E",  "I",  "O",  "U",  "Y",  "a",  "e",  "i",  "o",
    "u",  "A",  "E",  "I",  "O",  "U",  "a",  "e",  "i",  "o",
    "u",  "A",  "E",  "I",  "O",  "U",  "a",  "A",  "o",  "O",
    "a",  "n",  "o",  "A",  "N",  "O",  "ae", "AE", "c",  "C",
    "th", "th", "Th", "Th", "L",  "oe", "OE", "!",  "?"
};

static const char *inform_euro_substitute[69] = {
    "ae", "oe", "ue", "AE", "OE", "UE", "ss", ">>", "<<", ":e",
    ":i",  ":y",  ":E",  ":I",  "'a",  "'e",  "'i",  "'o",  "'u",  "'y",
    "'A",  "'E",  "'I",  "'O",  "'U",  "'Y",  "`a",  "`e",  "`i",  "`o",
    "`u",  "`A",  "`E",  "`I",  "`O",  "`U",  "^a",  "^e",  "^i",  "^o",
    "^u",  "^A",  "^E",  "^I",  "^O",  "^U",  "oa",  "oA",  "\\o",  "\\O",
    "~a",  "~n",  "~o",  "~A",  "~N",  "~O",  "ae", "AE", "cc",  "cC",
    "th", "et", "Th", "Et", "LL",  "oe", "OE", "!!",  "??"
};

static int lookup_table_loaded = 0;
static char lookup_table[3][26];

#define TX_SCREEN_COLS 79

static char *tx_line = NULL;
static int tx_line_pos = 0;
static int tx_col = 1;
static int tx_margin = 0;
static int tx_do_margin = 1;
static int tx_screen_cols = TX_SCREEN_COLS;

typedef struct cache_entry {
    struct cache_entry *flink;
    unsigned int page_number;
    zbyte_t data[PAGE_SIZE];
} cache_entry_t;

#ifdef __STDC__
static cache_entry_t *update_cache (unsigned int);
static unsigned long get_story_size (void);
static void tx_write_char (int);
#else
static cache_entry_t *update_cache ();
static unsigned long get_story_size ();
static void tx_write_char ();
#endif

static FILE *gfp = NULL;

static cache_entry_t *cache = NULL;

static unsigned int current_data_page = 0;
static cache_entry_t *current_data_cachep = NULL;

static unsigned int data_size;

#ifdef __STDC__
void configure (int min_version, int max_version)
#else
void configure (min_version, max_version)
int min_version;
int max_version;
#endif
{
    zbyte_t buffer[PAGE_SIZE];
    int i;

#if !defined(lint)
    assert (sizeof (zheader_t) == 64);
    assert (sizeof (zheader_t) <= PAGE_SIZE);
#endif /* !defined(lint) */

    read_page (0, buffer);
    datap = buffer;

    (void) memset (&header, 0, sizeof (zheader_t));

    header.version = get_byte (H_VERSION);
    header.config = get_byte (H_CONFIG);
    header.release = get_word (H_RELEASE);
    header.resident_size = get_word (H_RESIDENT_SIZE);
    header.start_pc = get_word (H_START_PC);
    header.dictionary = get_word (H_DICTIONARY);
    header.objects = get_word (H_OBJECTS);
    header.globals = get_word (H_GLOBALS);
    header.dynamic_size = get_word (H_DYNAMIC_SIZE);
    header.flags = get_word (H_FLAGS);
    for (i = 0; i < sizeof (header.serial); i++)
	header.serial[i] = get_byte (H_SERIAL + i);
    header.abbreviations = get_word (H_ABBREVIATIONS);
    header.file_size = get_word (H_FILE_SIZE);
    header.checksum = get_word (H_CHECKSUM);
    header.interpreter_number = get_byte (H_INTERPRETER_NUMBER);
    header.interpreter_version = get_byte (H_INTERPRETER_VERSION);
    header.screen_rows = get_byte (H_SCREEN_ROWS);
    header.screen_columns = get_byte (H_SCREEN_COLUMNS);
    header.screen_width = get_word (H_SCREEN_WIDTH);
    header.screen_height = get_word (H_SCREEN_HEIGHT);
    if (header.version != V6) {
	header.font_width = get_word (H_FONT_WIDTH);
	header.font_height = get_byte (H_FONT_HEIGHT);
    } else {
	header.font_width = get_word (H_FONT_HEIGHT);
	header.font_height = get_byte (H_FONT_WIDTH);
    }
    header.routines_offset = get_word (H_ROUTINES_OFFSET);
    header.strings_offset = get_word (H_STRINGS_OFFSET);
    header.default_background = get_byte (H_DEFAULT_BACKGROUND);
    header.default_foreground = get_byte (H_DEFAULT_FOREGROUND);
    header.terminating_keys = get_word (H_TERMINATING_KEYS);
    header.line_width = get_word (H_LINE_WIDTH);
    header.specification_hi = get_byte (H_SPECIFICATION_HI);
    header.specification_lo = get_byte (H_SPECIFICATION_LO);
    header.alphabet = get_word (H_ALPHABET);
    header.mouse_table = get_word (H_MOUSE_TABLE);
    for (i = 0; i < sizeof (header.name); i++)
	header.name[i] = get_byte (H_NAME + i);

    if ((unsigned int) header.version < (unsigned int) min_version ||
	(unsigned int) header.version > (unsigned int) max_version ||
	(unsigned int) header.config & CONFIG_BYTE_SWAPPED) {
	(void) fprintf (stderr, "\nFatal: wrong game or version\n");
	exit (EXIT_FAILURE);
    }

    if ((unsigned int) header.version < V4) {
	story_scaler = 2;
	story_shift = 1;
	code_scaler = 2;
	code_shift = 1;
	property_mask = P3_MAX_PROPERTIES - 1;
	property_size_mask = 0xe0;
    } else if ((unsigned int) header.version < V6) {
	story_scaler = 4;
	story_shift = 2;
	code_scaler = 4;
	code_shift = 2;
	property_mask = P4_MAX_PROPERTIES - 1;
	property_size_mask = 0x3f;
    } else if ((unsigned int) header.version < V8) {
	story_scaler = 8;
	story_shift = 3;
	code_scaler = 4;
	code_shift = 2;
	property_mask = P4_MAX_PROPERTIES - 1;
	property_size_mask = 0x3f;
    } else {
	story_scaler = 8;
	story_shift = 3;
	code_scaler = 8;
	code_shift = 3;
	property_mask = P4_MAX_PROPERTIES - 1;
	property_size_mask = 0x3f;
    }

    /* Calculate the file size */

    if ((unsigned int) header.file_size == 0)
	file_size = (unsigned long) get_story_size ();
    else if ((unsigned int) header.version <= V3)
	file_size = (unsigned long) header.file_size * 2;
    else if ((unsigned int) header.version <= V5)
	file_size = (unsigned long) header.file_size * 4;
    else
	file_size = (unsigned long) header.file_size * 8;

}/* configure */

#ifdef __STDC__
void open_story (const char *storyname)
#else
void open_story (storyname)
const char *storyname;
#endif
{

    gfp = fopen (storyname, "rb");
    if (gfp == NULL) {
	(void) fprintf (stderr, "\nFatal: game file not found\n");
	exit (EXIT_FAILURE);
    }

}/* open_story */

#ifdef __STDC__
void close_story (void)
#else
void close_story ()
#endif
{

    if (gfp != NULL)
	(void) fclose (gfp);

}/* close_story */

#ifdef __STDC__
void read_page (unsigned int page, void *buffer)
#else
void read_page (page, buffer)
unsigned int page;
zbyte_t *buffer;
#endif
{
    unsigned int bytes_to_read;

    if (file_size == 0)
	bytes_to_read = 64;
    else if (page != (unsigned int) (file_size / PAGE_SIZE))
	bytes_to_read = PAGE_SIZE;
    else
	bytes_to_read = (unsigned int) (file_size & PAGE_MASK);

    fseek (gfp, (long) page * PAGE_SIZE, SEEK_SET);
    if (fread (buffer, bytes_to_read, 1, gfp) != 1) {
	(void) fprintf (stderr, "\nFatal: game file read error\n");
	exit (EXIT_FAILURE);
    }

}/* read_page */

#ifdef __STDC__
void load_cache (void)
#else
void load_cache ()
#endif
{
    unsigned long file_size;
    unsigned int i, file_pages, data_pages;
    cache_entry_t *cachep;

    /* Must have at least one cache page for memory calculation */

    cachep = (cache_entry_t *) malloc (sizeof (cache_entry_t));
    if (cachep == NULL) {
	(void) fprintf (stderr, "\nFatal: insufficient memory\n");
	exit (EXIT_FAILURE);
    }
    cachep->flink = cache;
    cachep->page_number = 0;
    cache = cachep;

    /* Calculate dynamic cache pages required */

    data_pages = ((unsigned int) header.resident_size + PAGE_MASK) >> PAGE_SHIFT;
    data_size = data_pages * PAGE_SIZE;
    file_size = (unsigned long) header.file_size * story_scaler;
    file_pages = (unsigned int) ((file_size + PAGE_MASK) >> PAGE_SHIFT);

    /* Allocate static data area and initialise it */

    datap = (zbyte_t *) malloc ((size_t) data_size);
    if (datap == NULL) {
	(void) fprintf (stderr, "\nFatal: insufficient memory\n");
	exit (EXIT_FAILURE);
    }
    for (i = 0; i < data_pages; i++)
	read_page (i, &datap[i * PAGE_SIZE]);

    /* Allocate cache pages and initialise them */

    for (i = data_pages; cachep != NULL && i < file_pages && i < data_pages + MAX_CACHE; i++) {
	cachep = (cache_entry_t *) malloc (sizeof (cache_entry_t));
	if (cachep != NULL) {
	    cachep->flink = cache;
	    cachep->page_number = i;
	    read_page (cachep->page_number, cachep->data);
	    cache = cachep;
        }
    }

}/* load_cache */

#ifdef __STDC__
zword_t read_data_word (unsigned long *addr)
#else
zword_t read_data_word (addr)
unsigned long *addr;
#endif
{
    unsigned int w;

    w = (unsigned int) read_data_byte (addr) << 8;
    w |= (unsigned int) read_data_byte (addr);

    return (w);

}/* read_data_word */

#ifdef __STDC__
zbyte_t read_data_byte (unsigned long *addr)
#else
zbyte_t read_data_byte (addr)
unsigned long *addr;
#endif
{
    unsigned int page_number, page_offset;
    zbyte_t value;

    if (*addr < (unsigned long) data_size)
        value = datap[*addr];
    else {
        page_number = (int) (*addr >> PAGE_SHIFT);
        page_offset = (int) *addr & PAGE_MASK;
        if (page_number != current_data_page) {
            current_data_cachep = update_cache (page_number);
        current_data_page = page_number;
	}
        value = current_data_cachep->data[page_offset];
    }
    (*addr)++;

    return (value);

}/* read_data_byte */

#ifdef __STDC__
int decode_text (unsigned long *address)
#else
int decode_text (address)
unsigned long *address;
#endif
{
    int i, j, char_count, synonym_flag, synonym = 0, ascii_flag, ascii = 0;
    int data, code, shift_state, shift_lock;
    unsigned long addr;

    /*
     * Load correct character translation table for this game.
     */

    if (lookup_table_loaded == 0) {
        for (i = 0; i < 3; i++) {
            for (j = 0; j < 26; j++) {
                if ((unsigned int) header.alphabet) {
		    lookup_table[i][j] = (char) get_byte ((unsigned int) header.alphabet + (i * 26) + j);
                } else {
		    if ((unsigned int) header.version == V1)
                        lookup_table[i][j] = v1_lookup_table[i][j];
                    else
                        lookup_table[i][j] = v3_lookup_table[i][j];
                }   
                if (option_inform && lookup_table[i][j] == '\"')
                    lookup_table[i][j] = '~';
            }
        }
        lookup_table_loaded = 1;
    }

    /* Set state variables */

    shift_state = 0;
    shift_lock = 0;
    char_count = 0;
    ascii_flag = 0;
    synonym_flag = 0;

    do {

        /*
         * Read one 16 bit word. Each word contains three 5 bit codes. If the
         * high bit is set then this is the last word in the string.
         */
        data = read_data_word (address);

        for (i = 10; i >= 0; i -= 5) {

            /* Get code, high bits first */

            code = (data >> i) & 0x1f;

            /* Synonym codes */

            if (synonym_flag) {

                synonym_flag = 0;
		synonym = (synonym - 1) * 64;
                addr = (unsigned long) get_word ((unsigned int) header.abbreviations + synonym + (code * 2)) * 2;
                char_count += decode_text (&addr);
                shift_state = shift_lock;

            /* ASCII codes */

            } else if (ascii_flag) {

                /*
		 * If this is the first part ASCII code then remember it.
                 * Because the codes are only 5 bits you need two codes to make
                 * one eight bit ASCII character. The first code contains the
                 * top 3 bits. The second code contains the bottom 5 bits.
                 */

                if (ascii_flag++ == 1)

                    ascii = code << 5;

		/*
                 * If this is the second part ASCII code then assemble the
                 * character from the two codes and output it.
                 */

                else {

                    ascii_flag = 0;
                    tx_printf ("%c", (char) (ascii | code));
                    char_count++;

                }

            /* Character codes */

            } else if (code > 5) {

                code -= 6;

                /*
		 * If this is character 0 in the punctuation set then the next two
                 * codes make an ASCII character.
                 */

                if (shift_state == 2 && code == 0)

                    ascii_flag = 1;

                /*
                 * If this is character 1 in the punctuation set then this
		 * is a new line.
                 */

		else if (shift_state == 2 && code == 1 && (unsigned int) header.version > V1)

                    tx_printf ("%c", (option_inform) ? '^' : '\n');

                /*
                 * This is a normal character so select it from the character
                 * table appropriate for the current shift state.
		 */

                else {

                    tx_printf ("%c", (char) lookup_table[shift_state][code]);
                    char_count++;

                }

                shift_state = shift_lock;

            /* Special codes 0 to 5 */

            } else {

                /*
                 * Space: 0
                 *
                 * Output a space character.
                 *
		 */

                if (code == 0) {

                    tx_printf (" ");
                    char_count++;

                } else {

                    /*
		     * The use of the synonym and shift codes is the only difference between
                     * the different versions.
                     */

		    if ((unsigned int) header.version < V3) {

                        /*
                         * Newline or synonym: 1
                         *
                         * Output a newline character or set synonym flag.
			 *
                         */

                        if (code == 1) {

                            if ((unsigned int) header.version == V1) {
                                tx_printf ("%c", (option_inform) ? '^' : '\n');
                                char_count++;
                            } else {
                                synonym_flag = 1;
				synonym = code;
                            }

                        /*
                         * Shift keys: 2, 3, 4 or 5
                         *
                         * Shift keys 2 & 3 only shift the next character and can be used regardless of
                         * the state of the shift lock. Shift keys 4 & 5 lock the shift until reset.
                         *
                         * The following code implements the the shift code state transitions:
			 *
                         *               +-------------+-------------+-------------+-------------+
                         *               |       Shift   State       |        Lock   State       |
                         * +-------------+-------------+-------------+-------------+-------------+
                         * | Code        |      2      |       3     |      4      |      5      |
                         * +-------------+-------------+-------------+-------------+-------------+
                         * | lowercase   | uppercase   | punctuation | uppercase   | punctuation |
                         * | uppercase   | punctuation | lowercase   | punctuation | lowercase   |
                         * | punctuation | lowercase   | uppercase   | lowercase   | uppercase   |
                         * +-------------+-------------+-------------+-------------+-------------+
			 *
                         */

                        } else {
                            if (code < 4)
                                shift_state = (shift_lock + code + 2) % 3;
                            else
                                shift_lock = shift_state = (shift_lock + code) % 3;
                        }

		    } else {

                        /*
                         * Synonym table: 1, 2 or 3
                         *
                         * Selects which of three synonym tables the synonym
                         * code following in the next code is to use.
                         *
                         */

			if (code < 4) {

                            synonym_flag = 1;
                            synonym = code;
                        /*
                         * Shift key: 4 or 5
                         *
                         * Selects the shift state for the next character,
                         * either uppercase (4) or punctuation (5). The shift
			 * state automatically gets reset back to lowercase for
                         * V3+ games after the next character is output.
                         *
                         */

                        } else {
                            shift_state = code - 3;
                            shift_lock = 0;

			}
                    }
                }
            }
        }
    } while ((data & 0x8000) == 0);

    return (char_count);

}/* decode_text */

#ifdef __STDC__
static cache_entry_t *update_cache (unsigned int page_number)
#else
static cache_entry_t *update_cache (page_number)
unsigned int page_number;
#endif
{
    cache_entry_t *cachep, *lastp;

    for (lastp = cache, cachep = cache;
         cachep->flink != NULL &&
         cachep->page_number &&
         cachep->page_number != page_number;
         lastp = cachep, cachep = cachep->flink)
        ;
    if (cachep->page_number != page_number) {
        if (cachep->flink == NULL && cachep->page_number) {
            if (current_data_page == (unsigned int) cachep->page_number)
                current_data_page = 0;
	}
        cachep->page_number = page_number;
        read_page (page_number, cachep->data);
    }
    if (lastp != cache) {
        lastp->flink = cachep->flink;
        cachep->flink = cache;
        cache = cachep;
    }

    return (cachep);

}/* update_cache */

/*
 * get_story_size
 *
 * Calculate the size of the game file. Only used for very old games that do not
 * have the game file size in the header.
 *
 */

#ifdef __STDC__
static unsigned long get_story_size (void)
#else
static unsigned long get_story_size ()
#endif
{
    unsigned long file_length;

    /* Read whole file to calculate file size */

    rewind (gfp);
    for (file_length = 0; fgetc (gfp) != EOF; file_length++)
	;
    rewind (gfp);

    return (file_length);

}/* get_story_size */

/*VARARGS*/
#ifdef __STDC__
void tx_printf (const char *format, ...)
#else
void tx_printf (va_alist)
va_dcl
#endif
{
    va_list ap;
    int count, i;
    char buffer[TX_SCREEN_COLS + 1];

#ifdef MAC_MPW
    static short cursor_initialized = 0;
#endif

#ifdef __STDC__
    va_start (ap, format);
#else
    const char *format;
    va_start (ap);
    format = va_arg (ap, const char *);
#endif

#ifdef MAC_MPW
    if (!cursor_initialized) {
    	InitCursorCtl((acurHandle)NULL);
	Show_Cursor(WATCH_CURSOR);
	cursor_initialized = 1;
	signal(SIGINT, SIG_DFL);
    }
    if (strchr(format, '\n'))
    	SpinCursor(1);
#endif

    if (tx_screen_cols != 0) {
	if (tx_line == NULL) {
	    tx_line = (char *) malloc ((size_t) tx_screen_cols);
	    if (tx_line == NULL) {
		(void) fprintf (stderr, "\nFatal: insufficient memory\n");
		exit (EXIT_FAILURE);
	    }
	}
	/* On some systems vsprintf does not return the text length */
	(void) vsprintf (buffer, format, ap);
	count = strlen (buffer);
	if (count > TX_SCREEN_COLS) {
	    (void) fprintf (stderr, "\nFatal: buffer space overflow\n");
	    exit (EXIT_FAILURE);
	}
	for (i = 0; i < count; i++)
	    tx_write_char ((unsigned char) buffer[i]);
    } else
	(void) vprintf (format, ap);

    va_end (ap);

}/* tx_printf */

#ifdef __STDC__
static void write_high_zscii(int c)
#else
static void write_high_zscii(c)
int c;
#endif
{
    static zword_t unicode_table[256];
    static int unicode_table_loaded;
    int unicode_table_addr;
    int length, i;
    
    if (!unicode_table_loaded) {
    	if (header.mouse_table && (get_word(header.mouse_table) > 2)) {
	    unicode_table_addr = get_word(header.mouse_table + 6);
	    if (unicode_table_addr) {
	    	length = get_byte(unicode_table_addr);
	   	for (i = 0; i < unicode_table_addr; i++)
	    	    unicode_table[i + 155] = get_word(unicode_table_addr + 1 + i*2);
	    }
	}
	unicode_table_loaded = 1;
    }
  
    if ((c <= 0xdf) && !unicode_table[c]) {
    	if (option_inform)
	    tx_printf("@%s", inform_euro_substitute[c - 0x9b]);
	else
	    tx_printf (euro_substitute[c - 0x9b]);
    }
    else /* no non-inform version of these.  */
    	tx_printf("@{%x}", unicode_table[c]);
}

#ifdef __STDC__
static void tx_write_char (int c)
#else
static void tx_write_char (c)
int c;
#endif
{
    int i;
    char *cp;

    /* In V6 games a tab is a paragraph indent gap and a vertical tab is
       an inter-sentence gap. Both can be set to a space for readability */

    if (c == '\v' || c == '\t')
	c = ' ';

    /* European characters should be substituted by their replacements. */

    if (c >= 0x9b && c <= 0xfb) {
	write_high_zscii(c);
	return;
    }

    if (tx_col == tx_screen_cols + 1 || c == '\n') {
	tx_do_margin = 1;
	tx_line[tx_line_pos++] = '\0';
	cp = strrchr (tx_line, ' ');
	if (c == ' ' || c == '\n' || cp == NULL) {
	    (void) printf ("%s\n", tx_line);
	    tx_line_pos = 0;
	    tx_col = 1;
	    return;
	} else {
	    *cp++ = '\0';
	    (void) printf ("%s\n", tx_line);
	    tx_line_pos = 0;
	    tx_col = 1;
	    tx_printf ("%s", cp);
        }
    }

    if (tx_do_margin) {
        tx_do_margin = 0;
        for (i = 1; i < tx_margin; i++)
	    tx_write_char (' ');
    }

    tx_line[tx_line_pos++] = (char) c;
    tx_col++;

}/* tx_write_char */

#ifdef __STDC__
void tx_fix_margin (int flag)
#else
void tx_fix_margin (flag)
int flag;
#endif
{

    tx_margin = (flag) ? tx_col : 0;

}/* tx_fix_margin */

#ifdef __STDC__
void tx_set_width (int width)
#else
void tx_set_width (width)
int width;
#endif
{

    if (width > tx_screen_cols) {
	if (tx_line != NULL) {
	    tx_line[tx_line_pos++] = '\0';
	    (void) printf ("%s", tx_line);
	}
	tx_line_pos = 0;
	free (tx_line);
	tx_line = NULL;
    }
    tx_screen_cols = width;

}/* tx_set_width */


