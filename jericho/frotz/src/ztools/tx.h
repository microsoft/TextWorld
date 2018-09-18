/* tx.h
 *
 * Common I/O support routines for multiple Infocom story file utilities.
 *
 * Mark Howell 26 August 1992 howell_ma@movies.enet.dec.com
 *
 */

#include <assert.h>
#ifdef __STDC__
#include <stdarg.h>
#else
#include <varargs.h>
#endif
#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <string.h>

#ifndef TRUE
#define TRUE 1
#endif

#ifndef FALSE
#define FALSE 0
#endif

#ifndef EXIT_SUCCESS
#define EXIT_SUCCESS 0
#endif

#ifndef EXIT_FAILURE
#define EXIT_FAILURE 1
#endif

#ifndef __STDC__
/* 7/3 -- strrchr is defined in section B3 on page 249 of K&R2. */
/* memmove is defined on page 250 of K&R2.  This used to be an  */
/* ifdef unix, but that doesn't work on UNIX with ANSI C        */
#define strchr(a, b) index (a, b)
#define memmove(a, b, c) bcopy (b, a, c)

#define const
#define void int

#else

#ifndef HAS_STRTOUL
#define HAS_STRTOUL
#endif

#endif /* __STDC__ */

/* Z types */

typedef unsigned char zbyte_t;  /* unsigned 1 byte quantity */
typedef unsigned short zword_t; /* unsigned 2 byte quantity */

/* Data file header format */

typedef struct zheader {
    zbyte_t version;
    zbyte_t config;
    zword_t release;
    zword_t resident_size;
    zword_t start_pc;
    zword_t dictionary;
    zword_t objects;
    zword_t globals;
    zword_t dynamic_size;
    zword_t flags;
    zbyte_t serial[6];
    zword_t abbreviations;
    zword_t file_size;
    zword_t checksum;
    zbyte_t interpreter_number;
    zbyte_t interpreter_version;
    zbyte_t screen_rows;
    zbyte_t screen_columns;
    zword_t screen_width;
    zword_t screen_height;
    zbyte_t font_width;
    zbyte_t font_height;
    zword_t routines_offset;
    zword_t strings_offset;
    zbyte_t default_background;
    zbyte_t default_foreground;
    zword_t terminating_keys;
    zword_t line_width;
    zbyte_t specification_hi;
    zbyte_t specification_lo;
    zword_t alphabet;
    zword_t mouse_table;
    zbyte_t name[8];
} zheader_t;

#define H_VERSION 0
#define H_CONFIG 1

#define CONFIG_BYTE_SWAPPED 0x01 /* Game data is byte swapped          - V3  */
#define CONFIG_COLOUR       0x01 /* Interpreter supports colour        - V5+ */
#define CONFIG_TIME         0x02 /* Status line displays time          - V3  */
#define CONFIG_PICTURES	    0x02 /* Interpreter supports pictures      - V6  */
#define CONFIG_BOLDFACE     0x04 /* Interpreter supports bold text     - V4+ */
#define CONFIG_TANDY        0x08 /* Tandy licensed game                - V3  */
#define CONFIG_EMPHASIS     0x08 /* Interpreter supports text emphasis - V4+ */
#define CONFIG_NOSTATUSLINE 0x10 /* Interpreter has no status line     - V3  */
#define CONFIG_FIXED_FONT   0x10 /* Interpreter supports fixed font    - V4+ */
#define CONFIG_WINDOWS      0x20 /* Interpreter supports split screen  - V3  */
#define CONFIG_PROPORTIONAL 0x40 /* Interpreter uses proportional font - V3  */
#define CONFIG_TIMEDINPUT   0x80 /* Interpreter supports timed input   - V4+ */

#define H_RELEASE 2
#define H_RESIDENT_SIZE 4
#define H_START_PC 6
#define H_DICTIONARY 8
#define H_OBJECTS 10
#define H_GLOBALS 12
#define H_DYNAMIC_SIZE 14
#define H_FLAGS 16

#define SCRIPTING_FLAG 0x0001
#define FIXED_FONT_FLAG 0x0002
#define REFRESH_FLAG 0x0004
#define GRAPHICS_FLAG 0x0008
#define OLD_SOUND_FLAG 0x0010 /* V3 */
#define UNDO_AVAILABLE_FLAG 0x0010 /* V5 */
#define MOUSE_FLAG 0x0020
#define COLOUR_FLAG 0x0040
#define NEW_SOUND_FLAG 0x0080
#define MENU_FLAG 0x0100

#define H_SERIAL 18
#define H_ABBREVIATIONS 24
#define H_FILE_SIZE 26
#define H_CHECKSUM 28
#define H_INTERPRETER_NUMBER 30

#define INTERP_GENERIC 0
#define INTERP_DEC_20 1
#define INTERP_APPLE_IIE 2
#define INTERP_MACINTOSH 3
#define INTERP_AMIGA 4
#define INTERP_ATARI_ST 5
#define INTERP_MSDOS 6
#define INTERP_CBM_128 7
#define INTERP_CBM_64 8
#define INTERP_APPLE_IIC 9
#define INTERP_APPLE_IIGS 10
#define INTERP_TANDY 11

#define H_INTERPRETER_VERSION 31
#define H_SCREEN_ROWS 32
#define H_SCREEN_COLUMNS 33
#define H_SCREEN_WIDTH 34
#define H_SCREEN_HEIGHT 36
#define H_FONT_WIDTH 38 /* this is the font height in V6 */
#define H_FONT_HEIGHT 39 /* this is the font width in V6 */
#define H_ROUTINES_OFFSET 40
#define H_STRINGS_OFFSET 42
#define H_DEFAULT_BACKGROUND 44
#define H_DEFAULT_FOREGROUND 45
#define H_TERMINATING_KEYS 46
#define H_LINE_WIDTH 48
#define H_SPECIFICATION_HI 50
#define H_SPECIFICATION_LO 51
#define H_ALPHABET 52
#define H_MOUSE_TABLE 54
#define H_NAME 56

#define V1 1

#define V2 2

/* Version 3 object format */

#define V3 3

typedef struct zobjectv3 {
    zword_t attributes[2];
    zbyte_t parent;
    zbyte_t next;
    zbyte_t child;
    zword_t property_offset;
} zobjectv3_t;

#define O3_ATTRIBUTES 0
#define O3_PARENT 4
#define O3_NEXT 5
#define O3_CHILD 6
#define O3_PROPERTY_OFFSET 7

#define O3_SIZE 9

#define PARENT3(offset) (offset + O3_PARENT)
#define NEXT3(offset) (offset + O3_NEXT)
#define CHILD3(offset) (offset + O3_CHILD)

#define P3_MAX_PROPERTIES 0x20

/* Version 4 object format */

#define V4 4

typedef struct zobjectv4 {
    zword_t attributes[3];
    zword_t parent;
    zword_t next;
    zword_t child;
    zword_t property_offset;
} zobjectv4_t;

#define O4_ATTRIBUTES 0
#define O4_PARENT 6
#define O4_NEXT 8
#define O4_CHILD 10
#define O4_PROPERTY_OFFSET 12

#define O4_SIZE 14

#define PARENT4(offset) (offset + O4_PARENT)
#define NEXT4(offset) (offset + O4_NEXT)
#define CHILD4(offset) (offset + O4_CHILD)

#define P4_MAX_PROPERTIES 0x40

#define V5 5

#define V6 6

#define V7 7

#define V8 8

/* Local defines */

#define PAGE_SIZE 512
#define PAGE_MASK 511
#define PAGE_SHIFT 9

#define NIL 0
#define ANYTHING 1
#define VAR 2
#define NUMBER 3
#define LOW_ADDR 4
#define ROUTINE 5
#define OBJECT 6
#define STATIC 7
#define LABEL 8
#define PCHAR 9
#define VATTR 10
#define PATTR 11
#define INDIRECT 12
#define PROPNUM 13
#define ATTRNUM 14

#define NONE 0
#define TEXT 1
#define STORE 2
#define BRANCH 3
#define BOTH 4

#define PLAIN 0
#define CALL 1
#define RETURN 2
#define ILLEGAL 3

#define TWO_OPERAND 0
#define ONE_OPERAND 1
#define ZERO_OPERAND 2
#define VARIABLE_OPERAND 3
#define EXTENDED_OPERAND 4

#define WORD_IMMED 0
#define BYTE_IMMED 1
#define VARIABLE 2
#define NO_OPERAND 3

#define END_OF_CODE 1
#define END_OF_ROUTINE 2
#define END_OF_INSTRUCTION 3
#define BAD_ENTRY 4
#define BAD_OPCODE 5

#define ROMAN 0
#define REVERSE 1
#define BOLDFACE 2
#define EMPHASIS 4
#define FIXED_FONT 8

/* Grammar related defines */

enum parser_types {
	infocom_fixed,
	infocom_variable,
	infocom6_grammar,
	inform5_grammar,
	inform_gv1,
	inform_gv2,
	inform_gv2a
};

#define VERB_NUM(index, parser_type) (((parser_type) >= inform_gv2a)?(index):((unsigned int)(255-(index))))

#define PREP 		0x08
#define DESC 		0x20	/* infocom V1-5 only -- actually an adjective. */
#define NOUN 		0x80
#define VERB 		0x40	/* infocom V1-5 only */
#define DIR  		0x10 	/* infocom V1-5 only */
#define VERB_INFORM	0x01
#define VERB_V6		0x01
#define PLURAL		0x04 	/* inform only */
#define SPECIAL		0x04 	/* infocom V1-5 only */
#define META		0x02 	/* infocom V1-5 only */
#define DATA_FIRST	0x03 	/* infocom V1-5 only */
#define DIR_FIRST	0x03  	/* infocom V1-5 only */
#define ADJ_FIRST	0x02  	/* infocom V1-5 only */
#define VERB_FIRST	0x01  	/* infocom V1-5 only */
#define PREP_FIRST	0x00  	/* infocom V1-5 only */
#define ENDIT 0x0F

/* txd-specific defines? */

#define MAX_CACHE 10

typedef struct decode_t {
    unsigned int  first_pass;   /* Code pass flag                   */
    unsigned long pc;           /* Current PC                       */
    unsigned long initial_pc;   /* Initial PC                       */
    unsigned long high_pc;      /* Highest PC in current subroutine */
    unsigned long low_address;  /* Lowest subroutine address        */
    unsigned long high_address; /* Highest code address             */
} decode_t;

typedef struct opcode_t {
    int opcode;  /* Current opcode  */
    int class;   /* Class of opcode */
    int par[4];  /* Types of parameters */
    int extra;   /* Branch/store/text */
    int type;    /* Opcode type */
} opcode_t;

typedef struct cref_item_s {
    struct cref_item_s *next;
    struct cref_item_s *child;
    unsigned long address;
    int number;
} cref_item_t;

/* Data access macros */

#define get_byte(offset) ((zbyte_t) datap[offset])
#define get_word(offset) ((zword_t) (((unsigned short) datap[offset] << 8) + (unsigned short) datap[offset + 1]))
#define set_byte(offset,value) datap[offset] = (zbyte_t) (value)
#define set_word(offset,value) datap[offset] = (zbyte_t) ((unsigned short) (value) >> 8), datap[offset + 1] = (zbyte_t) ((unsigned short) (value) & 0xff)

/* External data */

extern zheader_t header;

extern int story_scaler;
extern int story_shift;
extern int code_scaler;
extern int code_shift;
extern int property_mask;
extern int property_size_mask;

extern zbyte_t *datap;

extern option_inform;

extern unsigned long file_size;

#ifdef __STDC__
int decode_text (unsigned long *);
void close_story (void);
void configure (int, int);
void load_cache (void);
void open_story (const char *);
void read_page (unsigned int, void *);
zbyte_t read_data_byte (unsigned long *);
zword_t read_data_word (unsigned long *);
void tx_printf (const char *, ...);
void tx_fix_margin (int);
void tx_set_width (int);
#else
int decode_text ();
void close_story ();
void configure ();
void load_cache ();
void open_story ();
void read_page ();
zbyte_t read_data_byte ();
zword_t read_data_word ();
void tx_printf ();
void tx_fix_margin ();
void tx_set_width ();
#endif

/* Inform version codes */
#define INFORM_5		500
#define INFORM_6		600
#define INFORM_610		610

/* Grammar prototypes */
#ifdef __STDC__
void configure_parse_tables
    (unsigned int *, unsigned int *, unsigned int *, unsigned int *, unsigned int *,
     unsigned long *, unsigned long *, unsigned long *, unsigned long *,
     unsigned long *, unsigned long *);
void show_verb_grammar
    (unsigned long, unsigned int, int, int, int, unsigned long, unsigned long);
void show_syntax_of_action(int action,
			unsigned long verb_table_base,
			unsigned int verb_count,
			unsigned int parser_type,
			unsigned int prep_type,
			unsigned long attr_names_base,
			unsigned long prep_table_base);
			
void show_syntax_of_parsing_routine(unsigned long parsing_routine,
				    unsigned long verb_table_base,
				    unsigned int verb_count,
				    unsigned int parser_type,
				    unsigned int prep_type,
				    unsigned long prep_table_base,
				    unsigned long attr_names_base);
				    
int is_gv2_parsing_routine(unsigned long parsing_routine,
				    unsigned long verb_table_base,
				    unsigned int verb_count);
#else
void configure_parse_tables ();
void show_verb_grammar ();
void show_syntax_of_action();
void show_syntax_of_parsing_routine();
int is_gv2_parsing_routine();
#endif

#ifndef SEEK_SET
#define SEEK_SET 0
#endif
