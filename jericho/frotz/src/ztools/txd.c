/* txd.c V7/3
 *
 * Z code disassembler for Infocom game files
 *
 * Requires txio.c, getopt.c, showverb.c and tx.h.
 *
 * Works for all V1, V2, V3, V4, V5, V6, V7 and V8 games.
 *
 * Usage: txd story-file-name
 *
 * Mark Howell 25 August 1992 howell_ma@movies.enet.dec.com
 *
 * History:
 *    Merge separate disassemblers for each type into one program
 *    Fix logic error in low routine scan
 *    Force PC past start PC in middle routine scan
 *    Update opcodes
 *    Add pre-action and action verb names to routines
 *    Add print mode descriptions
 *    Wrap long lines of text
 *    Cleanup for 16 bit machines
 *    Change JGE and JLE to JG and JL
 *    Add support for V1 and V2 games
 *    Fix bug in printing of last string
 *    Add symbolic names for routines and labels
 *    Add verb syntax
 *    Improve verb formatting
 *    Add command line options
 *    Fix check for low address
 *    Add a switch to turn off grammar
 *    Add support for V6 games
 *    Make start of code for low scan the end of dictionary data
 *    Generate Inform style syntax as an option
 *    Add dump style and width option
 *    Fix lint warnings
 *    Fix inter-routine backward jumps
 *    Update operand names
 *    Add support for V7 and V8 games
 *    Limit cache size to MAX_CACHE pages
 *    Improve translation of constants to symbols
 *    Distinguish between pre-actions and Inform parsing routines
 *    Introduce indirect operands, eg. load [sp] sp
 *    Fix object 0 problem
 *    Add support for European characters (codes up to 223)
 *    Add support for Inform 6 (helped by Matthew T. Russotto)
 *    Add support for GV2 (MTR)
 *    Add support for Infocom V6 games
 *    Fix dependencies on sizeof(int) == 2 (mostly cosmetic) NOT DONE
 *    Add -S dump-strings at address option
 *    Remove GV2A support
 *    Add unicode disassembly support
 *    Add Inform and user symbol table support
 */

#include "tx.h"
#include "ztools.h"

#define MAX_PCS 100

#define ROUND_CODE(address) ((address + (code_scaler - 1)) & ~(code_scaler - 1))
#define ROUND_DATA(address) ((address + (story_scaler - 1)) & ~(story_scaler - 1))

#ifndef HAS_GETOPT
#ifdef __STDC__
extern int getopt (int, char *[], const char *);
#else
extern int getopt ();
#endif
#endif

#ifdef __STDC__
//static void process_story (const char *);
static void decode_program (void);
static int decode_routine (void);
static int decode_code (void);
static int decode_opcode (void);
static int decode_operands (const char *, int, int, int, int, int, int);
static int decode_parameters (int *);
static int decode_parameter (int, int);
static int decode_extra (void);
static void decode_strings (unsigned long);
static void scan_strings (unsigned long);
static int lookup_string (unsigned long);
static void lookup_verb (unsigned long);
static void setup_dictionary (void);
static int in_dictionary (unsigned long);
static void add_label (unsigned long);
static void add_routine (unsigned long);
static int lookup_label (unsigned long, int);
static int lookup_routine (unsigned long, int);
static void renumber_cref (cref_item_t *);
static void free_cref (cref_item_t *);
static int print_object_desc (unsigned int);
static void print_text (unsigned long *);
static void print_integer (unsigned int, int);
static void dump_data (unsigned long, unsigned long);
static void dump_opcode (unsigned long, int, int, int *, int);
static void dump_operand (unsigned long *, int, int, int *, int *);
static void print_variable (int);
#else
//static void process_story ();
static void decode_program ();
static int decode_routine ();
static int decode_code ();
static int decode_opcode ();
static int decode_operands ();
static int decode_parameters ();
static int decode_parameter ();
static int decode_extra ();
static void decode_strings ();
static void scan_strings ();
static int lookup_string ();
static void lookup_verb ();
static void setup_dictionary ();
static int in_dictionary ();
static void add_label ();
static void add_routine ();
static int lookup_label ();
static int lookup_routine ();
static void renumber_cref ();
static void free_cref ();
static int print_object_desc ();
static void print_text ();
static void print_integer ();
static void dump_data ();
static void dump_opcode ();
static void dump_operand ();
static void print_variable ();
#endif

static unsigned long pctable[MAX_PCS];
static int pcindex = 0;

static unsigned long start_data_pc, end_data_pc;

static decode_t decode;
static opcode_t opcode;

static cref_item_t *strings_base = NULL;
static cref_item_t *routines_base = NULL;
static cref_item_t *current_routine = NULL;

static int locals_count = 0;
static unsigned long start_of_routine = 0;

static unsigned int verb_count = 0;
static unsigned int action_count = 0;
static unsigned int parse_count = 0;
static unsigned int parser_type = 0;
static unsigned int prep_type = 0;
static unsigned long verb_table_base = 0;
static unsigned long verb_data_base = 0;
static unsigned long action_table_base = 0;
static unsigned long preact_table_base = 0;
static unsigned long prep_table_base = 0;
static unsigned long prep_table_end = 0;

static const int verb_sizes[4] = { 2, 4, 7, 7 };

static unsigned long dict_start = 0;
static unsigned long dict_end = 0;
static unsigned long word_size = 0;
static unsigned long word_count = 0;

static unsigned long code_base = 0;

static unsigned int obj_count = 0;
static unsigned long obj_table_base = 0, obj_table_end = 0, obj_data_base = 0, obj_data_end = 0;
static unsigned short inform_version = 0;
static unsigned long class_numbers_base = 0, class_numbers_end = 0;
static unsigned long property_names_base = 0, property_names_end = 0;
static unsigned long attr_names_base = 0, attr_names_end = 0;

#ifndef HAS_GETOPT
/* getopt linkages */

extern int optind;
extern const char *optarg;
#endif

static int option_labels = 1;
static int option_grammar = 1;
static int option_dump = 0;
static int option_width = 500;
static int option_symbols = 0;
static unsigned long string_location = 0;

/* #ifdef __STDC__ */
/* int main (int argc, char *argv []) */
/* #else */
/* int main (argc, argv) */
/* int argc; */
/* char *argv []; */
/* #endif */
/* { */
/*     int c, errflg = 0; */

/*     /\* Parse the options *\/ */

/*     while ((c = getopt (argc, argv, "abdghnsw:S:u:")) != EOF) { */
/*  switch (c) { */
/*      case 'a': */
/*      option_inform = 6; */
/*      break; */
/*      case 'd': */
/*      option_dump = 1; */
/*      break; */
/*      case 'g': */
/*      option_grammar = 0; */
/*      break; */
/*      case 'n': */
/*      option_labels = 0; */
/*      break; */
/*      case 'w': */
/*      option_width = atoi (optarg); */
/*      break; */
/*      case 'u': */
/*      init_symbols(optarg); */
/*      /\*FALLTHRU*\/ */
/*      case 's': */
/*      option_symbols = 1; */
/*      break; */
/*      case 'S': */
/* #ifdef HAS_STRTOUL */
/*          string_location = strtoul(optarg, (char **)NULL, 0); */
/* #else */
/*          string_location = atoi(optarg); */
/* #endif */
/*      break; */
/*      case 'h': */
/*      case '?': */
/*      default: */
/*      errflg++; */
/*  } */
/*     } */

/*     /\* Display usage if unknown flag or no story file *\/ */

/*     if (errflg || optind >= argc) { */
/*  (void) fprintf (stderr, "usage: %s [options...] story-file [story-file...]\n\n", argv[0]); */
/*  (void) fprintf (stderr, "TXD version 7/3 - disassemble Infocom story files. By Mark Howell\n"); */
/*  (void) fprintf (stderr, "Works with V1 to V8 Infocom games.\n\n"); */
/*  (void) fprintf (stderr, "\t-a   generate alternate syntax used by Inform\n"); */
/*  (void) fprintf (stderr, "\t-d   dump hex of opcodes and data\n"); */
/*  (void) fprintf (stderr, "\t-g   turn off grammar for action routines\n"); */
/*  (void) fprintf (stderr, "\t-n   use addresses instead of labels\n"); */
/*  (void) fprintf (stderr, "\t-w n display width (0 = no wrap)\n"); */
/*  (void) fprintf (stderr, "\t-s   Symbolic mode (Inform 6+ only)\n"); */
/*  (void) fprintf (stderr, "\t-u <file> Read user symbol table, implies -s for Inform games\n"); */
/*  (void) fprintf (stderr, "\t-S n Dump high strings only, starting at address n\n"); */
/*  exit (EXIT_FAILURE); */
/*     } */

/*     /\* Process any story files on the command line *\/ */

/*     for (; optind < argc; optind++) */
/*  process_story (argv[optind]); */

/*     exit (EXIT_SUCCESS); */

/*     return (0); */

/* }/\* main *\/ */

#ifdef __STDC__
void disassemble (const char *file_name)
#else
void disassemble (file_name)
const char *file_name;
#endif
{

    tx_set_width (option_width);

    open_story (file_name);

    configure (V1, V8);

    load_cache ();

    setup_dictionary ();

    if (option_grammar)
    configure_parse_tables (&verb_count, &action_count, &parse_count, &parser_type, &prep_type,
                &verb_table_base, &verb_data_base,
                &action_table_base, &preact_table_base,
                &prep_table_base, &prep_table_end);

    if (option_symbols && (parser_type >= inform_gv1)) {
    configure_object_tables (&obj_count, &obj_table_base, &obj_table_end,
                      &obj_data_base, &obj_data_end);
        configure_inform_tables(obj_data_end, &inform_version, &class_numbers_base, &class_numbers_end,
                        &property_names_base, &property_names_end, &attr_names_base, &attr_names_end);
    }

    if (header.version != V6 && header.version != V7) {
    decode.pc = code_base = dict_end;
    decode.initial_pc = (unsigned long) header.start_pc - 1;
    } else {
    decode.pc = code_base = (unsigned long) header.routines_offset * story_scaler;
    decode.initial_pc = decode.pc + (unsigned long) header.start_pc * code_scaler;
    }

    tx_printf ("Resident data ends at %lx, program starts at %lx, file ends at %lx\n",
           (unsigned long) header.resident_size, (unsigned long) decode.initial_pc, (unsigned long) file_size);
    tx_printf ("\nStarting analysis pass at address %lx\n", (unsigned long) decode.pc);

#if defined(TXD_DEBUG)
    decode.first_pass = 0;
    decode.low_address = decode.initial_pc;
    decode.high_address = file_size;
#if 0
    decode.low_address = atoi (getenv ("LOW_ADDRESS"));
    decode.high_address = atoi (getenv ("HIGH_ADDRESS"));
#endif
#else
    decode.first_pass = 1;
#endif
    if (string_location) {
    decode_strings (string_location);
    exit(0);
    }
    decode_program ();

    scan_strings (decode.pc);

#if !defined(TXD_DEBUG)
    tx_printf ("\nEnd of analysis pass, low address = %lx, high address = %lx\n",
           (unsigned long) decode.low_address, (unsigned long) decode.high_address);
    if (start_data_pc)
    tx_printf ("\n%ld bytes of data in code from %lx to %lx\n",
           (unsigned long) (end_data_pc - start_data_pc),
           (unsigned long) start_data_pc, (unsigned long) end_data_pc);
    if ((decode.low_address - code_base) >= story_scaler) {
    tx_printf ("\n%ld bytes of data before code from %lx to %lx\n",
           (unsigned long) (decode.low_address - code_base),
           (unsigned long) code_base, (unsigned long) decode.low_address);
    if (option_dump) {
        tx_printf ("\n[Start of data");
        if (option_labels == 0)
        tx_printf (" at %lx", (unsigned long) code_base);
        tx_printf ("]\n\n");
        dump_data (code_base, decode.low_address - 1);
        tx_printf ("\n[End of data");
        if (option_labels == 0)
        tx_printf (" at %lx", (unsigned long) (decode.low_address - 1));
        tx_printf ("]\n");
    }
    }

    if (option_labels)
    renumber_cref (routines_base);

    decode.first_pass = 0;
    decode_program ();

    decode_strings (decode.pc);
#endif

    close_story ();

}/* process_story */

/* decode_program - Decode Z code in two passes */

#ifdef __STDC__
static void decode_program (void)
#else
static void decode_program ()
#endif
{
    unsigned long pc, low_pc, high_pc, prev_low_pc, prev_high_pc;
    int i, flag, vars;

    if (decode.first_pass) {
    if (decode.pc < decode.initial_pc) {
        /* Scan for low routines */
        decode.pc = ROUND_CODE (decode.pc);
        for (pc = decode.pc, flag = 0; pc < decode.initial_pc && flag == 0; pc += code_scaler) {
        for (vars = (char) read_data_byte (&pc); vars < 0 || vars > 15; vars = (char) read_data_byte (&pc))
            pc = ROUND_CODE (pc);
        decode.pc = pc - 1;
        for (i = 0, flag = 1; i < 3 && flag; i++) {
            pcindex = 0;
            decode.pc = ROUND_CODE (decode.pc);
            if (decode_routine () != END_OF_ROUTINE || pcindex)
            flag = 0;
        }
        decode.pc = pc - 1;
        }
        if (flag && (unsigned int) header.version < V5) {
        pc = decode.pc;
        vars = (char) read_data_byte (&pc);
        low_pc = decode.pc;
        for (pc = pc + (vars * 2) - 1, flag = 0; pc >= low_pc && flag == 0; pc -= story_scaler) {
            decode.pc = pc;
            for (i = 0, flag = 1; i < 3 && flag; i++) {
            pcindex = 0;
            decode.pc = ROUND_CODE (decode.pc);
            if (decode_routine () != END_OF_ROUTINE || pcindex)
                flag = 0;
            }
            decode.pc = pc;
        }
        }
        if (flag == 0 || decode.pc > decode.initial_pc)
        decode.pc = decode.initial_pc;
    }
    /* Fill in middle routines */
    decode.low_address = decode.pc;
    decode.high_address = decode.pc;
    start_data_pc = 0;
    end_data_pc = 0;
    do {
        if (option_labels) {
        free_cref (routines_base);
        routines_base = NULL;
        }
        prev_low_pc = decode.low_address;
        prev_high_pc = decode.high_address;
        flag = 0;
        pcindex = 0;
        low_pc = decode.low_address;
        high_pc = decode.high_address;
        pc = decode.pc = decode.low_address;
        while (decode.pc <= high_pc || decode.pc <= decode.initial_pc) {
        if (start_data_pc == decode.pc)
            decode.pc = end_data_pc;
        if (decode_routine () != END_OF_ROUTINE) {
            if (start_data_pc == 0)
            start_data_pc = decode.pc;
            flag = 1;
            end_data_pc = 0;
            pcindex = 0;
            pc = ROUND_CODE (pc);
            do {
            pc += code_scaler;
            vars = (char) read_data_byte (&pc);
            pc--;
            } while (vars < 0 || vars > 15);
            decode.pc = pc;
        } else {
            if (pc < decode.initial_pc && decode.pc > decode.initial_pc) {
            pc = decode.pc = decode.initial_pc;
            decode.low_address = low_pc;
            decode.high_address = high_pc;
            } else {
            if (start_data_pc && end_data_pc == 0)
                end_data_pc = pc;
            pc = ROUND_CODE (decode.pc);
            if (flag == 0) {
                low_pc = decode.low_address;
                high_pc = decode.high_address;
            }
            }
        }
        }
        decode.low_address = low_pc;
        decode.high_address = high_pc;
    } while (low_pc < prev_low_pc || high_pc > prev_high_pc);
    /* Scan for high routines */
    pc = decode.pc;
    while (decode_routine () == END_OF_ROUTINE) {
        decode.high_address = pc;
        pc = decode.pc;
    }
    } else {
    tx_printf ("\n[Start of code");
    if (option_labels == 0)
        tx_printf (" at %lx", (unsigned long) decode.low_address);
    tx_printf ("]\n");
    for (decode.pc = decode.low_address;
         decode.pc <= decode.high_address; )
        (void) decode_routine ();
    tx_printf ("\n[End of code");
    if (option_labels == 0)
        tx_printf (" at %lx", (unsigned long) decode.pc);
    tx_printf ("]\n");
    }

}/* decode_program */

/* decode_routine - Decode a routine from start address to last instruction */

#ifdef __STDC__
static int decode_routine (void)
#else
static int decode_routine ()
#endif
{
    unsigned long old_pc, old_start;
    cref_item_t *cref_item;
    int vars, status, i, locals;

    if (decode.first_pass) {
    cref_item = NULL;
    if (option_labels)
        cref_item = current_routine;
    old_start = start_of_routine;
    locals = locals_count;
    old_pc = decode.pc;
    decode.pc = ROUND_CODE (decode.pc);
        vars = read_data_byte (&decode.pc);
        if (vars >= 0 && vars <= 15) {
            if (option_labels)
                add_routine (decode.pc - 1);
        locals_count = vars;
        if ((unsigned int) header.version < V5)
                for (; vars; vars--)
                    (void) read_data_word (&decode.pc);
        start_of_routine = decode.pc;
            if (decode_code () == END_OF_ROUTINE)
                return (END_OF_ROUTINE);
        if (option_labels)
                current_routine = cref_item;
            start_of_routine = old_start;
        locals_count = locals;
    }
        decode.pc = old_pc;
        if ((status = decode_code ()) != END_OF_ROUTINE) {
        decode.pc = old_pc;
    } else {
            pctable[pcindex++] = old_pc;
            if (pcindex == MAX_PCS) {
        (void) fprintf (stderr, "\nFatal: too many orphan code fragments\n");
                exit (EXIT_FAILURE);
            }
        }
    } else {
        if (decode.pc == start_data_pc) {
            if (option_dump) {
                tx_printf ("\n[Start of data");
                if (option_labels == 0)
            tx_printf (" at %lx", (unsigned long) start_data_pc);
                tx_printf ("]\n\n");
                dump_data (start_data_pc, end_data_pc - 1);
                tx_printf ("\n[End of data");
        if (option_labels == 0)
                    tx_printf (" at %lx", (unsigned long) (end_data_pc - 1));
                tx_printf ("]\n");
        }
        decode.pc = end_data_pc;
        }
        for (i = 0; i < pcindex && decode.pc != pctable[i]; i++)
            ;
        if (i == pcindex) {
            decode.pc = ROUND_CODE (decode.pc);
        start_of_routine = decode.pc;
            vars = read_data_byte (&decode.pc);
            if (option_labels) {
        tx_printf ("%soutine %c%04d, %d local",
                           (decode.pc - 1 == decode.initial_pc) ? "\nMain r" : "\nR",
                           (option_inform) ? 'r' : 'R',
               (int) lookup_routine (decode.pc - 1, 1),
                           (int) vars);
            } else {
        tx_printf ("%soutine %lx, %d local",
               (decode.pc - 1 == decode.initial_pc) ? "\nMain r" : "\nR",
                           (unsigned long) (decode.pc - 1),
                           (int) vars);
        }
        if (vars != 1)
                tx_printf ("s");
        if ((unsigned int) header.version < V5) {
                tx_printf (" (");
                tx_fix_margin (1);
                for (; vars; vars--) {
                    tx_printf ("%04x", (unsigned int) read_data_word (&decode.pc));
                    if (vars > 1)
                        tx_printf (", ");
                }
                tx_fix_margin (0);
                tx_printf (")");
        }
            tx_printf ("\n");
            lookup_verb (start_of_routine);
            tx_printf ("\n");
    } else
            tx_printf ("\norphan code fragment:\n\n");
        status = decode_code ();
    }

    return (status);

}/* decode_routine */

/* decode_code - grab opcode and determine the class */

#ifdef __STDC__
static int decode_code (void)
#else
static int decode_code ()
#endif
{
    int status;
    int label;

    decode.high_pc = decode.pc;
    do {
        if (decode.first_pass == 0) {
        if (option_labels) {
        label = lookup_label (decode.pc, 0);
                if (label != 0)
                    tx_printf ("%c%04d: ", (option_inform) ? 'l' : 'L', (int) label);
        else
                    tx_printf ("       ");
            } else
                tx_printf ("%5lx:  ", (unsigned long) decode.pc);
        }
        opcode.opcode = read_data_byte (&decode.pc);
    if ((unsigned int) header.version > V4 && opcode.opcode == 0xbe) {
            opcode.opcode = read_data_byte (&decode.pc);
            opcode.class = EXTENDED_OPERAND;
    } else if (opcode.opcode < 0x80)
        opcode.class = TWO_OPERAND;
        else
            if (opcode.opcode < 0xb0)
        opcode.class = ONE_OPERAND;
            else
                if (opcode.opcode < 0xc0)
            opcode.class = ZERO_OPERAND;
        else
            opcode.class = VARIABLE_OPERAND;
            
    status = decode_opcode ();
    } while (status == END_OF_INSTRUCTION);

    return (status);

}/* decode_code */

/* decode_opcode - Check and decode the opcode itself */

#define caseline(opc, text, par1, par2, par3, par4, extra, type) \
    case opc: return (decode_operands (text, par1, par2, par3, par4, extra, type))

#ifdef __STDC__
static int decode_opcode (void)
#else
static int decode_opcode ()
#endif
{
    int code;

    code = opcode.opcode;

    switch (opcode.class) {

    case EXTENDED_OPERAND:
        code &= 0x3f;
        switch (code) {
        caseline (0x00, "SAVE",            LOW_ADDR, NUMBER,   LOW_ADDR, NIL,      STORE,  PLAIN);
        caseline (0x01, "RESTORE",         LOW_ADDR, NUMBER,   LOW_ADDR, NIL,      STORE,  PLAIN);
        caseline (0x02, "LOG_SHIFT",       NUMBER,   NUMBER,   NIL,      NIL,      STORE,  PLAIN);
        caseline (0x03, "ART_SHIFT",       NUMBER,   NUMBER,   NIL,      NIL,      STORE,  PLAIN);
        caseline (0x04, "SET_FONT",        NUMBER,   NUMBER,   NIL,      NIL,      STORE,  PLAIN);
        caseline (0x05, "DRAW_PICTURE",    NUMBER,   NUMBER,   NUMBER,   NIL,      NONE,   PLAIN);
        caseline (0x06, "PICTURE_DATA",    NUMBER,   LOW_ADDR, NIL,      NIL,      BRANCH, PLAIN);
        caseline (0x07, "ERASE_PICTURE",   NUMBER,   NUMBER,   NUMBER,   NIL,      NONE,   PLAIN);
        caseline (0x08, "SET_MARGINS",     NUMBER,   NUMBER,   NUMBER,   NIL,      NONE,   PLAIN);
        caseline (0x09, "SAVE_UNDO",       NIL,      NIL,      NIL,      NIL,      STORE,  PLAIN);
        caseline (0x0A, "RESTORE_UNDO",    NIL,      NIL,      NIL,      NIL,      STORE,  PLAIN);

        caseline (0x10, "MOVE_WINDOW",     NUMBER,   NUMBER,   NUMBER,   NIL,      NONE,   PLAIN);
        caseline (0x11, "WINDOW_SIZE",     NUMBER,   NUMBER,   NUMBER,   NIL,      NONE,   PLAIN);
        caseline (0x12, "WINDOW_STYLE",    NUMBER,   NUMBER,   NUMBER,   NIL,      NONE,   PLAIN);
        caseline (0x13, "GET_WIND_PROP",   NUMBER,   NUMBER,   NIL,      NIL,      STORE,  PLAIN);
        caseline (0x14, "SCROLL_WINDOW",   NUMBER,   NUMBER,   NIL,      NIL,      NONE,   PLAIN);
        caseline (0x15, "POP_STACK",       NUMBER,   LOW_ADDR, NIL,      NIL,      NONE,   PLAIN);
        caseline (0x16, "READ_MOUSE",      LOW_ADDR, NIL,      NIL,      NIL,      NONE,   PLAIN);
        caseline (0x17, "MOUSE_WINDOW",    NUMBER,   NIL,      NIL,      NIL,      NONE,   PLAIN);
        caseline (0x18, "PUSH_STACK",      NUMBER,   LOW_ADDR, NIL,      NIL,      BRANCH, PLAIN);
        caseline (0x19, "PUT_WIND_PROP",   NUMBER,   NUMBER,   ANYTHING, NIL,      NONE,   PLAIN);
        caseline (0x1A, "PRINT_FORM",      LOW_ADDR, NIL,      NIL,      NIL,      NONE,   PLAIN);
        caseline (0x1B, "MAKE_MENU",       NUMBER,   LOW_ADDR, NIL,      NIL,      BRANCH, PLAIN);
        caseline (0x1C, "PICTURE_TABLE",   LOW_ADDR, NIL,      NIL,      NIL,      NONE,   PLAIN);

        default:
            return (decode_operands ("ILLEGAL", NIL, NIL, NIL, NIL, NONE, ILLEGAL));
        }

    case TWO_OPERAND:
        code &= 0x1f;

    case VARIABLE_OPERAND:
        code &= 0x3f;
        switch (code) {
        caseline (0x01, "JE",              ANYTHING, ANYTHING, ANYTHING, ANYTHING, BRANCH, PLAIN);
        caseline (0x02, "JL",              NUMBER,   NUMBER,   NIL,      NIL,      BRANCH, PLAIN);
        caseline (0x03, "JG",              NUMBER,   NUMBER,   NIL,      NIL,      BRANCH, PLAIN);
        caseline (0x04, "DEC_CHK",         VAR,      NUMBER,   NIL,      NIL,      BRANCH, PLAIN);
        caseline (0x05, "INC_CHK",         VAR,      NUMBER,   NIL,      NIL,      BRANCH, PLAIN);
        caseline (0x06, "JIN",             OBJECT,   OBJECT,   NIL,      NIL,      BRANCH, PLAIN);
        caseline (0x07, "TEST",            NUMBER,   NUMBER,   NIL,      NIL,      BRANCH, PLAIN);
        caseline (0x08, "OR",              NUMBER,   NUMBER,   NIL,      NIL,      STORE,  PLAIN);
        caseline (0x09, "AND",             NUMBER,   NUMBER,   NIL,      NIL,      STORE,  PLAIN);
        caseline (0x0A, "TEST_ATTR",       OBJECT,   ATTRNUM,  NIL,      NIL,      BRANCH, PLAIN);
        caseline (0x0B, "SET_ATTR",        OBJECT,   ATTRNUM,  NIL,      NIL,      NONE,   PLAIN);
        caseline (0x0C, "CLEAR_ATTR",      OBJECT,   ATTRNUM,  NIL,      NIL,      NONE,   PLAIN);
        caseline (0x0D, "STORE",           VAR,      ANYTHING, NIL,      NIL,      NONE,   PLAIN);
        caseline (0x0E, "INSERT_OBJ",      OBJECT,   OBJECT,   NIL,      NIL,      NONE,   PLAIN);
        caseline (0x0F, "LOADW",           LOW_ADDR, NUMBER,   NIL,      NIL,      STORE,  PLAIN);
        caseline (0x10, "LOADB",           LOW_ADDR, NUMBER,   NIL,      NIL,      STORE,  PLAIN);
        caseline (0x11, "GET_PROP",        OBJECT,   PROPNUM,  NIL,      NIL,      STORE,  PLAIN);
        caseline (0x12, "GET_PROP_ADDR",   OBJECT,   PROPNUM,  NIL,      NIL,      STORE,  PLAIN);
        caseline (0x13, "GET_NEXT_PROP",   OBJECT,   PROPNUM,  NIL,      NIL,      STORE,  PLAIN);
        caseline (0x14, "ADD",             LOW_ADDR, LOW_ADDR, NIL,      NIL,      STORE,  PLAIN);
        caseline (0x15, "SUB",             NUMBER,   NUMBER,   NIL,      NIL,      STORE,  PLAIN);
        caseline (0x16, "MUL",             NUMBER,   NUMBER,   NIL,      NIL,      STORE,  PLAIN);
        caseline (0x17, "DIV",             NUMBER,   NUMBER,   NIL,      NIL,      STORE,  PLAIN);
        caseline (0x18, "MOD",             NUMBER,   NUMBER,   NIL,      NIL,      STORE,  PLAIN);

        caseline (0x21, "STOREW",          LOW_ADDR, NUMBER,   ANYTHING, NIL,      NONE,   PLAIN);
        caseline (0x22, "STOREB",          LOW_ADDR, NUMBER,   ANYTHING, NIL,      NONE,   PLAIN);
        caseline (0x23, "PUT_PROP",        OBJECT,   NUMBER,   ANYTHING, NIL,      NONE,   PLAIN);

        caseline (0x25, "PRINT_CHAR",      PCHAR,    NIL,      NIL,      NIL,      NONE,   PLAIN);
        caseline (0x26, "PRINT_NUM",       NUMBER,   NIL,      NIL,      NIL,      NONE,   PLAIN);
        caseline (0x27, "RANDOM",          NUMBER,   NIL,      NIL,      NIL,      STORE,  PLAIN);
        caseline (0x28, "PUSH",            ANYTHING, NIL,      NIL,      NIL,      NONE,   PLAIN);

        caseline (0x2A, "SPLIT_WINDOW",    NUMBER,   NIL,      NIL,      NIL,      NONE,   PLAIN);
        caseline (0x2B, "SET_WINDOW",      NUMBER,   NIL,      NIL,      NIL,      NONE,   PLAIN);

        caseline (0x33, "OUTPUT_STREAM",   PATTR,    LOW_ADDR, NUMBER,   NIL,      NONE,   PLAIN);
        caseline (0x34, "INPUT_STREAM",    NUMBER,   NIL,      NIL,      NIL,      NONE,   PLAIN);
        caseline (0x35, "SOUND_EFFECT",    NUMBER,   NUMBER,   NUMBER,   ROUTINE,  NONE,   PLAIN);

        default:
            switch ((unsigned int) header.version) {
            case V1:
            case V2:
            case V3:
                switch (code) {
                caseline (0x20, "CALL",            ROUTINE,  ANYTHING, ANYTHING, ANYTHING, STORE,  CALL);

                caseline (0x24, "READ",            LOW_ADDR, LOW_ADDR, NIL,      NIL,      NONE,   PLAIN);

                caseline (0x29, "PULL",            VAR,      NIL,      NIL,      NIL,      NONE,   PLAIN);
                }
            case V4:
                switch (code) {
                caseline (0x19, "CALL_2S",         ROUTINE,  ANYTHING, NIL,      NIL,      STORE,  CALL);

                caseline (0x20, "CALL_VS",         ROUTINE,  ANYTHING, ANYTHING, ANYTHING, STORE,  CALL);

                caseline (0x24, "READ",            LOW_ADDR, LOW_ADDR, NUMBER,   ROUTINE,  NONE,   PLAIN);

                caseline (0x29, "PULL",            VAR,      NIL,      NIL,      NIL,      NONE,   PLAIN);

                caseline (0x2C, "CALL_VS2",        ROUTINE,  ANYTHING, ANYTHING, ANYTHING, STORE,  CALL);
                caseline (0x2D, "ERASE_WINDOW",    NUMBER,   NIL,      NIL,      NIL,      NONE,   PLAIN);
                caseline (0x2E, "ERASE_LINE",      NUMBER,   NIL,      NIL,      NIL,      NONE,   PLAIN);
                caseline (0x2F, "SET_CURSOR",      NUMBER,   NUMBER,   NIL,      NIL,      NONE,   PLAIN);

                caseline (0x31, "SET_TEXT_STYLE",  VATTR,    NIL,      NIL,      NIL,      NONE,   PLAIN);
                caseline (0x32, "BUFFER_MODE",     NUMBER,   NIL,      NIL,      NIL,      NONE,   PLAIN);

                caseline (0x36, "READ_CHAR",       NUMBER,   NUMBER,   ROUTINE,  NIL,      STORE,  PLAIN);
                caseline (0x37, "SCAN_TABLE",      ANYTHING, LOW_ADDR, NUMBER,   NUMBER,   BOTH,   PLAIN);
                }
            case V5:
            case V7:
            case V8:
                switch (code) {
                caseline (0x19, "CALL_2S",         ROUTINE,  ANYTHING, NIL,      NIL,      STORE,  CALL);
                caseline (0x1A, "CALL_2N",         ROUTINE,  ANYTHING, NIL,      NIL,      NONE,   CALL);
                caseline (0x1B, "SET_COLOUR",      NUMBER,   NUMBER,   NIL,      NIL,      NONE,   PLAIN);

                caseline (0x20, "CALL_VS",         ROUTINE,  ANYTHING, ANYTHING, ANYTHING, STORE,  CALL);

                caseline (0x24, "READ",            LOW_ADDR, LOW_ADDR, NUMBER,   ROUTINE,  STORE,  PLAIN);

                caseline (0x29, "PULL",            VAR,      NIL,      NIL,      NIL,      NONE,   PLAIN);

                caseline (0x2C, "CALL_VS2",        ROUTINE,  ANYTHING, ANYTHING, ANYTHING, STORE,  CALL);
                caseline (0x2D, "ERASE_WINDOW",    NUMBER,   NIL,      NIL,      NIL,      NONE,   PLAIN);
                caseline (0x2E, "ERASE_LINE",      NUMBER,   NIL,      NIL,      NIL,      NONE,   PLAIN);
                caseline (0x2F, "SET_CURSOR",      NUMBER,   NUMBER,   NIL,      NIL,      NONE,   PLAIN);

                caseline (0x31, "SET_TEXT_STYLE",  VATTR,    NIL,      NIL,      NIL,      NONE,   PLAIN);
                caseline (0x32, "BUFFER_MODE",     NUMBER,   NIL,      NIL,      NIL,      NONE,   PLAIN);

                caseline (0x36, "READ_CHAR",       NUMBER,   NUMBER,   ROUTINE,  NIL,      STORE,  PLAIN);
                caseline (0x37, "SCAN_TABLE",      ANYTHING, LOW_ADDR, NUMBER,   NUMBER,   BOTH,   PLAIN);

                caseline (0x39, "CALL_VN",         ROUTINE,  ANYTHING, ANYTHING, ANYTHING, NONE,   CALL);
                caseline (0x3A, "CALL_VN2",        ROUTINE,  ANYTHING, ANYTHING, ANYTHING, NONE,   CALL);
                caseline (0x3B, "TOKENISE",        LOW_ADDR, LOW_ADDR, LOW_ADDR, NUMBER,   NONE,   PLAIN);
                caseline (0x3C, "ENCODE_TEXT",     LOW_ADDR, NUMBER,   NUMBER,   LOW_ADDR, NONE,   PLAIN);
                caseline (0x3D, "COPY_TABLE",      LOW_ADDR, LOW_ADDR, NUMBER,   NIL,      NONE,   PLAIN);
                caseline (0x3E, "PRINT_TABLE",     LOW_ADDR, NUMBER,   NUMBER,   NUMBER,   NONE,   PLAIN);
                caseline (0x3F, "CHECK_ARG_COUNT", NUMBER,   NIL,      NIL,      NIL,      BRANCH, PLAIN);
                }
            case V6:
                switch (code) {
                caseline (0x19, "CALL_2S",         ROUTINE,  ANYTHING, NIL,      NIL,      STORE,  CALL);
                caseline (0x1A, "CALL_2N",         ROUTINE,  ANYTHING, NIL,      NIL,      NONE,   CALL);
                caseline (0x1B, "SET_COLOUR",      NUMBER,   NUMBER,   NIL,      NIL,      NONE,   PLAIN);
                caseline (0x1C, "THROW",           ANYTHING, NUMBER,   NIL,      NIL,      NONE,   PLAIN);

                caseline (0x20, "CALL_VS",         ROUTINE,  ANYTHING, ANYTHING, ANYTHING, STORE,  CALL);

                caseline (0x24, "READ",            LOW_ADDR, LOW_ADDR, NUMBER,   ROUTINE,  STORE,  PLAIN);

                caseline (0x29, "PULL",            LOW_ADDR, NIL,      NIL,      NIL,      STORE,  PLAIN);

                caseline (0x2C, "CALL_VS2",        ROUTINE,  ANYTHING, ANYTHING, ANYTHING, STORE,  CALL);
                caseline (0x2D, "ERASE_WINDOW",    NUMBER,   NIL,      NIL,      NIL,      NONE,   PLAIN);
                caseline (0x2E, "ERASE_LINE",      NUMBER,   NIL,      NIL,      NIL,      NONE,   PLAIN);
                caseline (0x2F, "SET_CURSOR",      NUMBER,   NUMBER,   NUMBER,   NIL,      NONE,   PLAIN);
                caseline (0x30, "GET_CURSOR",      LOW_ADDR, NIL,      NIL,      NIL,      NONE,   PLAIN);
                caseline (0x31, "SET_TEXT_STYLE",  VATTR,    NIL,      NIL,      NIL,      NONE,   PLAIN);
                caseline (0x32, "BUFFER_MODE",     NUMBER,   NIL,      NIL,      NIL,      NONE,   PLAIN);

                caseline (0x36, "READ_CHAR",       NUMBER,   NUMBER,   ROUTINE,  NIL,      STORE,  PLAIN);
                caseline (0x37, "SCAN_TABLE",      ANYTHING, LOW_ADDR, NUMBER,   NUMBER,   BOTH,   PLAIN);
                caseline (0x38, "NOT",             NUMBER,   NIL,      NIL,      NIL,      STORE,  PLAIN);
                caseline (0x39, "CALL_VN",         ROUTINE,  ANYTHING, ANYTHING, ANYTHING, NONE,   CALL);
                caseline (0x3A, "CALL_VN2",        ROUTINE,  ANYTHING, ANYTHING, ANYTHING, NONE,   CALL);
                caseline (0x3B, "TOKENISE",        LOW_ADDR, LOW_ADDR, LOW_ADDR, NUMBER,   NONE,   PLAIN);
                caseline (0x3C, "ENCODE_TEXT",     LOW_ADDR, NUMBER,   NUMBER,   LOW_ADDR, NONE,   PLAIN);
                caseline (0x3D, "COPY_TABLE",      LOW_ADDR, NUMBER,   LOW_ADDR, NIL,      NONE,   PLAIN);
                caseline (0x3E, "PRINT_TABLE",     LOW_ADDR, NUMBER,   NUMBER,   NUMBER,   NONE,   PLAIN);
                caseline (0x3F, "CHECK_ARG_COUNT", NUMBER,   NIL,      NIL,      NIL,      BRANCH, PLAIN);
                }
            }
            return (decode_operands ("ILLEGAL", NIL, NIL, NIL, NIL, NONE, ILLEGAL));
        }

    case ONE_OPERAND:
        code &= 0x0f;
        switch (code) {
        caseline (0x00, "JZ",               NUMBER,   NIL,      NIL,      NIL,      BRANCH, PLAIN);
        caseline (0x01, "GET_SIBLING",      OBJECT,   NIL,      NIL,      NIL,      BOTH,   PLAIN);
        caseline (0x02, "GET_CHILD",        OBJECT,   NIL,      NIL,      NIL,      BOTH,   PLAIN);
        caseline (0x03, "GET_PARENT",       OBJECT,   NIL,      NIL,      NIL,      STORE,  PLAIN);
        caseline (0x04, "GET_PROP_LEN",     LOW_ADDR, NIL,      NIL,      NIL,      STORE,  PLAIN);
        caseline (0x05, "INC",              VAR,      NIL,      NIL,      NIL,      NONE,   PLAIN);
        caseline (0x06, "DEC",              VAR,      NIL,      NIL,      NIL,      NONE,   PLAIN);
        caseline (0x07, "PRINT_ADDR",       LOW_ADDR, NIL,      NIL,      NIL,      NONE,   PLAIN);

        caseline (0x09, "REMOVE_OBJ",       OBJECT,   NIL,      NIL,      NIL,      NONE,   PLAIN);
        caseline (0x0A, "PRINT_OBJ",        OBJECT,   NIL,      NIL,      NIL,      NONE,   PLAIN);
        caseline (0x0B, "RET",              ANYTHING, NIL,      NIL,      NIL,      NONE,   RETURN);
        caseline (0x0C, "JUMP",             LABEL,    NIL,      NIL,      NIL,      NONE,   RETURN);
        caseline (0x0D, "PRINT_PADDR",      STATIC,   NIL,      NIL,      NIL,      NONE,   PLAIN);
        caseline (0x0E, "LOAD",             VAR,      NIL,      NIL,      NIL,      STORE,  PLAIN);

        default:
            switch ((unsigned int) header.version) {
            case V1:
            case V2:
            case V3:
                switch (code) {
                caseline (0x0F, "NOT",              NUMBER,   NIL,      NIL,      NIL,      STORE,  PLAIN);
                }
            case V4:
                switch (code) {
                caseline (0x08, "CALL_1S",          ROUTINE,  NIL,      NIL,      NIL,      STORE,  CALL);

                caseline (0x0F, "NOT",              NUMBER,   NIL,      NIL,      NIL,      STORE,  PLAIN);
                }
            case V5:
            case V6:
            case V7:
            case V8:
                switch (code) {
                caseline (0x08, "CALL_1S",          ROUTINE,  NIL,      NIL,      NIL,      STORE,  CALL);

                caseline (0x0F, "CALL_1N",          ROUTINE,  NIL,      NIL,      NIL,      NONE,   CALL);
                }
            }
            return (decode_operands ("ILLEGAL", NIL, NIL, NIL, NIL, NONE, ILLEGAL));
        }

    case ZERO_OPERAND:
        code &= 0x0f;
        switch (code) {
        caseline (0x00, "RTRUE",           NIL,      NIL,      NIL,      NIL,      NONE,   RETURN);
        caseline (0x01, "RFALSE",          NIL,      NIL,      NIL,      NIL,      NONE,   RETURN);
        caseline (0x02, "PRINT",           NIL,      NIL,      NIL,      NIL,      TEXT,   PLAIN);
        caseline (0x03, "PRINT_RET",       NIL,      NIL,      NIL,      NIL,      TEXT,   RETURN);
        caseline (0x04, "NOP",             NIL,      NIL,      NIL,      NIL,      NONE,   PLAIN);

        caseline (0x07, "RESTART",         NIL,      NIL,      NIL,      NIL,      NONE,   PLAIN);
        caseline (0x08, "RET_POPPED",      NIL,      NIL,      NIL,      NIL,      NONE,   RETURN);

        caseline (0x0A, "QUIT",            NIL,      NIL,      NIL,      NIL,      NONE,   RETURN);
        caseline (0x0B, "NEW_LINE",        NIL,      NIL,      NIL,      NIL,      NONE,   PLAIN);

        caseline (0x0D, "VERIFY",          NIL,      NIL,      NIL,      NIL,      BRANCH, PLAIN);

        default:
            switch ((unsigned int) header.version) {
            case V1:
            case V2:
            case V3:
                switch (code) {
                caseline (0x05, "SAVE",            NIL,      NIL,      NIL,      NIL,      BRANCH, PLAIN);
                caseline (0x06, "RESTORE",         NIL,      NIL,      NIL,      NIL,      BRANCH, PLAIN);

                caseline (0x09, "POP",             NIL,      NIL,      NIL,      NIL,      NONE,   PLAIN);

                caseline (0x0C, "SHOW_STATUS",     NIL,      NIL,      NIL,      NIL,      NONE,   PLAIN);
                }
            case V4:
                switch (code) {
                caseline (0x09, "POP",             NIL,      NIL,      NIL,      NIL,      NONE,   PLAIN);

                caseline (0x05, "SAVE",            NIL,      NIL,      NIL,      NIL,      STORE,  PLAIN);
                caseline (0x06, "RESTORE",         NIL,      NIL,      NIL,      NIL,      STORE,  PLAIN);
                }
            case V5:
            case V7:
            case V8:
                switch (code) {
                caseline (0x09, "CATCH",           NIL,      NIL,      NIL,      NIL,      STORE,  PLAIN);
                /* From a bug in Wishbringer V23 */
                caseline (0x0C, "SHOW_STATUS",     NIL,      NIL,      NIL,      NIL,      NONE,   PLAIN);
                }
            case V6:
                switch (code) {
                caseline (0x09, "CATCH",           NIL,      NIL,      NIL,      NIL,      STORE,  PLAIN);

                caseline (0x0F, "PIRACY",          NIL,      NIL,      NIL,      NIL,      BRANCH, PLAIN);
                }
            }
            return (decode_operands ("ILLEGAL", NIL, NIL, NIL, NIL, NONE, ILLEGAL));
        }

    default:
        (void) fprintf (stderr, "\nFatal: bad class (%d)\n", (int) opcode.class);
        exit (EXIT_FAILURE);
    }
    return (BAD_OPCODE);

}/* decode_opcode */

#undef caseline

/* decode_operands - Decode operands of opcode */

#ifdef __STDC__
static int decode_operands (const char *opcode_name, int par1, int par2, int par3, int par4, int extra, int type)
#else
static int decode_operands (opcode_name, par1, par2, par3, par4, extra, type)
const char *opcode_name;
int par1;
int par2;
int par3;
int par4;
int extra;
int type;
#endif
{
    size_t len;
    int i, opers, status;

    opcode.par[0] = par1;
    opcode.par[1] = par2;
    opcode.par[2] = par3;
    opcode.par[3] = par4;
    opcode.extra = extra;
    opcode.type = type;
 
    if (opcode.type == ILLEGAL)
    return (BAD_OPCODE);

    if (decode.first_pass) {
    status = decode_parameters (&opers);
    if (status)
        return (BAD_OPCODE);
    status = decode_extra ();
    } else {
    if (option_dump)
        dump_opcode (decode.pc, opcode.opcode, opcode.class, opcode.par, opcode.extra);
    if (option_inform) {
        len = strlen (opcode_name);
        for (i = 0; i < len; i++)
        tx_printf ("%c", tolower (opcode_name[i]));
    } else {
        tx_printf (opcode_name);
        len = strlen (opcode_name);
    }
    for (; len < 16; len++)
        tx_printf (" ");
    (void) decode_parameters (&opers);
    if (opers > 0 && opcode.extra != NONE)
        tx_printf (" ");
    status = decode_extra ();
    tx_printf ("\n");
    }
    if (decode.pc > decode.high_pc)
    decode.high_pc = decode.pc;

    return (status);

}/* decode_operands */

/* decode_parameters - Decode input parameters */

#ifdef __STDC__
static int decode_parameters (int *opers)
#else
static int decode_parameters (opers)
int *opers;
#endif
{
    int status, modes, addr_mode, maxopers;

    *opers = 0;

    switch (opcode.class) {

    case ONE_OPERAND:
        status = decode_parameter ((opcode.opcode >> 4) & 0x03, 0);
        if (status)
        return (status);
        *opers = 1;
        break;

    case TWO_OPERAND:
        status = decode_parameter ((opcode.opcode & 0x40) ? VARIABLE : BYTE_IMMED, 0);
        if (status)
        return (status);
        if (decode.first_pass == 0) {
        if (!option_inform && opcode.type == CALL)
            tx_printf (" (");
        else
            tx_printf ("%c", (option_inform) ? ' ' : ',');
        }
        status = decode_parameter ((opcode.opcode & 0x20) ? VARIABLE : BYTE_IMMED, 1);
        if (status)
        return (status);
        *opers = 2;
        if (!option_inform && decode.first_pass == 0 && opcode.type == CALL && *opers > 1)
        tx_printf (")");
        break;

    case VARIABLE_OPERAND:
    case EXTENDED_OPERAND:
        if ((opcode.opcode & 0x3f) == 0x2c ||
        (opcode.opcode & 0x3f) == 0x3a) {
        modes = read_data_word (&decode.pc);
        maxopers = 8;
        } else {
        modes = read_data_byte (&decode.pc);
        maxopers = 4;
        }
        for (addr_mode = 0, *opers = 0;
         (addr_mode != NO_OPERAND) && maxopers; maxopers--) {
        addr_mode = (modes >> ((maxopers - 1) * 2)) & 0x03;
        if (addr_mode != NO_OPERAND) {
            if (decode.first_pass == 0 && *opers) {
            if (!option_inform && opcode.type == CALL && *opers == 1)
                tx_printf (" (");
            else
                tx_printf ("%c", (option_inform) ? ' ' : ',');
            }
            status = decode_parameter (addr_mode, *opers);
            if (status)
            return (status);
            (*opers)++;
        }
        }
        if (!option_inform && decode.first_pass == 0 && opcode.type == CALL && *opers > 1)
        tx_printf (")");
        break;

    case ZERO_OPERAND:
        break;

    default:
        (void) fprintf (stderr, "\nFatal: bad class (%d)\n", (int) opcode.class);
        exit (EXIT_FAILURE);
    }

    return (0);

}/* decode_parameters */

/* decode_parameter - Decode one input parameter */

#ifdef __STDC__
static int decode_parameter (int addr_mode, int opers)
#else
static int decode_parameter (addr_mode, opers)
int addr_mode;
int opers;
#endif
{
    unsigned long addr;
    unsigned int value;
    int routine, vars, par, dictionary, string;

    par = (opers < 4) ? opcode.par[opers] : ANYTHING;

    switch (addr_mode) {

    case WORD_IMMED:
        value = (unsigned int) read_data_word (&decode.pc);
        break;

    case BYTE_IMMED:
        value = (unsigned int) read_data_byte (&decode.pc);
        break;

    case VARIABLE:
        value = (unsigned int) read_data_byte (&decode.pc);
        par = VAR;
        break;

    case NO_OPERAND:
        return (0);

    default:
        (void) fprintf (stderr, "\nFatal: bad addressing mode (%d)\n", (int) addr_mode);
        exit (EXIT_FAILURE);
    }

    /*
     * To make the code more readable, VAR type operands are not translated
     * as constants, eg. INC 5 is actually printed as INC L05. However, if
     * the VAR type operand _is_ a variable, the translation should look like
     * INC [L05], ie. increment the variable which is given by the contents
     * of local variable #5. Earlier versions of "txd" translated both cases
     * as INC L05. This bug was finally detected by Graham Nelson.
     */

    if (opers < 4 && opcode.par[opers] == VAR)
    par = (addr_mode == VARIABLE) ? INDIRECT : VAR;

    switch (par) {

    case NIL:
        if (decode.first_pass == 0) {
         fprintf(stderr, "\nWarning: Unexpected Parameter #%d near %05lx\n", opers, decode.pc);
         print_integer (value, addr_mode == BYTE_IMMED);
        }
        break;

    case ANYTHING:
        if (decode.first_pass == 0) {
        addr = (unsigned long) code_scaler * value + (unsigned long) story_scaler * header.strings_offset;
        string = lookup_string (addr);
        if (string)
            tx_printf ("%c%03d", (option_inform) ? 's' : 'S', string);
        addr = (unsigned long) value;
        dictionary = in_dictionary (addr);
        if (dictionary) {
            if (string)
            tx_printf (" %s ", (option_inform) ? "or" : "OR");
            tx_printf ("\"");
            (void) decode_text (&addr);
            tx_printf ("\"");
        }
        if (!dictionary && !string)
            print_integer (value, addr_mode == BYTE_IMMED);
        }
        break;

    case VAR:
        if (decode.first_pass == 0) {
        if (value == 0)
            tx_printf ("%s", (option_inform) ? "sp" : "(SP)+");
        else
            print_variable(value);
#ifdef DELETEME
            if (value < 16) {
            if (option_inform)
                tx_printf ("local%d", value - 1);
            else
                tx_printf ("L%02x", value - 1);
            } else
            tx_printf ("%c%02x", (option_inform) ? 'g' : 'G', value - 16);
#endif
        } else {
        if ((int) value > 0 && (int) value < 16 && (int) value > locals_count)
            return (1);
        }
        break;

    case NUMBER:
        if (decode.first_pass == 0)
        print_integer (value, addr_mode == BYTE_IMMED);
        break;

    case PROPNUM:
        if (decode.first_pass == 0)
        if (!print_property_name(property_names_base, value))
            print_integer (value, addr_mode == BYTE_IMMED);
        break;

    case ATTRNUM:
        if (decode.first_pass == 0)
        if (!print_attribute_name(attr_names_base, value))
            print_integer (value, addr_mode == BYTE_IMMED);
        break;

    case LOW_ADDR:
        if (decode.first_pass == 0) {
        addr = (unsigned long) value;
        dictionary = in_dictionary (addr);
        if (dictionary) {
            tx_printf ("\"");
            (void) decode_text (&addr);
            tx_printf ("\"");
        } else
            print_integer (value, addr_mode == BYTE_IMMED);
        }
        break;

    case ROUTINE:
        addr = (unsigned long) code_scaler * value + (unsigned long) header.routines_offset * story_scaler;
        if (decode.first_pass == 0) {
        if (option_labels)
            if (value != 0) {
            routine = lookup_routine (addr, 0);
            if (routine != 0)
                tx_printf ("%c%04d", (option_inform) ? 'r' : 'R', routine);
            else {
                (void) fprintf (stderr, "\nWarning: found call to nonexistent routine!\n");
                tx_printf ("%lx", addr);
            }
            } else
            print_integer (value, addr_mode == BYTE_IMMED);
        else
            tx_printf ("%lx", addr);
        } else {
        if (addr < decode.low_address &&
            addr >= code_base) {
            vars = read_data_byte (&addr);
            if (vars >= 0 && vars <= 15)
            decode.low_address = addr - 1;
        }
        if (addr > decode.high_address &&
            addr < file_size) {
            vars = read_data_byte (&addr);
            if (vars >= 0 && vars <= 15)
            decode.high_address = addr - 1;
        }
        }
        break;

    case OBJECT:
        if (decode.first_pass == 0) {
        if (value == 0 || print_object_desc (value) == 0)
            print_integer (value, addr_mode == BYTE_IMMED);
        }
        break;

    case STATIC:
        if (decode.first_pass == 0) {
        addr = (unsigned long) code_scaler * value + (unsigned long) story_scaler * header.strings_offset;
        string = lookup_string (addr);
        if (string != 0)
            tx_printf ("%c%03d", (option_inform) ? 's' : 'S', (int) string);
        else {
#ifndef TXD_DEBUG
            (void) fprintf (stderr, "\nWarning: printing of nonexistent string\n");
#endif
            tx_printf ("%lx", addr);
        }
        }
        break;

    case LABEL:
        addr = decode.pc + (short) value - 2;
        if (decode.first_pass && addr < decode.low_address)
        return (1);
        if (option_labels) {
        if (decode.first_pass)
            add_label (addr);
        else
            tx_printf ("%c%04d", (option_inform) ? 'l' : 'L', lookup_label (addr, 1));
        } else {
        if (decode.first_pass == 0)
            tx_printf ("%lx", addr);
        }
        if (addr > decode.high_pc)
        decode.high_pc = addr;
        break;

    case PCHAR:
        if (decode.first_pass == 0)
        if (isprint ((char) value))
            tx_printf ("\'%c\'", (char) value);
        else
            print_integer (value, addr_mode == BYTE_IMMED);
        break;

    case VATTR:
        if (decode.first_pass == 0) {
        if (value == ROMAN)
            tx_printf ("%s", (option_inform) ? "roman" : "ROMAN");
        else if (value == REVERSE)
            tx_printf ("%s", (option_inform) ? "reverse" : "REVERSE");
        else if (value == BOLDFACE)
            tx_printf ("%s", (option_inform) ? "boldface" : "BOLDFACE");
        else if (value == EMPHASIS)
            tx_printf ("%s", (option_inform) ? "emphasis" : "EMPHASIS");
        else if (value == FIXED_FONT)
            tx_printf ("%s", (option_inform) ? "fixed_font" : "FIXED_FONT");
        else
            print_integer (value, addr_mode == BYTE_IMMED);
        }
        break;

    case PATTR:
        if (decode.first_pass == 0) {
        if ((int) value == 1)
            tx_printf ("%s", (option_inform) ? "output_enable" : "OUTPUT_ENABLE");
        else if ((int) value == 2)
            tx_printf ("%s", (option_inform) ? "scripting_enable" : "SCRIPTING_ENABLE");
        else if ((int) value == 3)
            tx_printf ("%s", (option_inform) ? "redirect_enable" : "REDIRECT_ENABLE");
        else if ((int) value == 4)
            tx_printf ("%s", (option_inform) ? "record_enable" : "RECORD_ENABLE");
        else if ((int) value == -1)
            tx_printf ("%s", (option_inform) ? "output_disable" : "OUTPUT_DISABLE");
        else if ((int) value == -2)
            tx_printf ("%s", (option_inform) ? "scripting_disable" : "SCRIPTING_DISABLE");
        else if ((int) value == -3)
            tx_printf ("%s", (option_inform) ? "redirect_disable" : "REDIRECT_DISABLE");
        else if ((int) value == -4)
            tx_printf ("%s", (option_inform) ? "record_disable" : "RECORD_DISABLE");
        else
            print_integer (value, addr_mode == BYTE_IMMED);
        }
        break;

    case INDIRECT:
        if (decode.first_pass == 0) {
        if (value == 0)
            tx_printf ("[%s]", (option_inform) ? "sp" : "(SP)+");
        else {
            tx_printf("[");
            print_variable(value);
            tx_printf("]");
#ifdef DELETEME
            if (value < 16) {
            if (option_inform)
                tx_printf ("[local%d]", value - 1);
            else
                tx_printf ("[L%02x]", value - 1);
            } else
            tx_printf ("[%c%02x]", (option_inform) ? 'g' : 'G', value - 16);
#endif
        }
        }
        break;

    default:
        (void) fprintf (stderr, "\nFatal: bad operand type (%d)\n", (int) par);
        exit (EXIT_FAILURE);
    }

    return (0);

}/* decode_parameter */

/* decode_extra - Decode branches, stores and text */

#ifdef __STDC__
static int decode_extra (void)
#else
static int decode_extra ()
#endif
{
    unsigned long addr;
    zbyte_t firstbyte;

    if (opcode.extra == STORE || opcode.extra == BOTH) {
    addr = (zbyte_t) read_data_byte (&decode.pc);
    if (decode.first_pass == 0) {
        if (!option_inform || (option_inform >= 6))
        tx_printf ("-> ");
        if (addr == 0)
        tx_printf ("%s", (option_inform) ? "sp" : "-(SP)");
        else
        print_variable(addr);
#ifdef DELETEME
        if (addr < 16) {
            if (option_inform)
            tx_printf ("local%ld", (unsigned long) (addr - 1));
            else
            tx_printf ("L%02lx", (unsigned long) (addr - 1));
        } else
            tx_printf ("%c%02lx", (option_inform) ? 'g' : 'G', (unsigned long) (addr - 16));
#endif
        if (opcode.extra == BOTH)
        tx_printf (" ");
    } else {
        if (addr > 0 && addr < 16 && addr > (unsigned long) locals_count)
        return (BAD_OPCODE);
    }
    }

    if (opcode.extra == BRANCH || opcode.extra == BOTH) {
    addr = firstbyte = (zbyte_t) read_data_byte (&decode.pc);
    addr &= 0x7f;
    if (addr & 0x40)
        addr &= 0x3f;
    else {
        addr = (addr << 8) | (unsigned long) read_data_byte (&decode.pc);
        if (addr & 0x2000) {
        addr &= 0x1fff;
        addr |= ~0x1fff;
        }
    }
    if (decode.first_pass == 0) {
        if ((addr > 1) && !(firstbyte & 0x40) && (option_inform >= 6) && (option_labels)) {
        tx_printf("?"); /* Inform 6 long branch */
        }
        if (firstbyte & 0x80)
        tx_printf ("%s", (option_inform) ? "" : "[TRUE]");
        else
        tx_printf ("%s", (option_inform) ? "~" : "[FALSE]");
    }
    if (addr == 0) {
        if (decode.first_pass == 0)
        tx_printf ("%s", (option_inform) ? "rfalse" : " RFALSE");
    } else if (addr == 1) {
        if (decode.first_pass == 0)
        tx_printf ("%s", (option_inform) ? "rtrue" : " RTRUE");
    } else {
        addr = decode.pc + addr - 2;
        if (decode.first_pass && addr < start_of_routine)
        return (BAD_OPCODE);
        if (option_labels) {
        if (decode.first_pass)
            add_label (addr);
        else
            tx_printf ("%s%04d", (option_inform) ? "l" : " L", (int) lookup_label (addr, 1));
        } else {
        if (decode.first_pass == 0)
            tx_printf ("%s%lx", (option_inform) ? "" : " ", (unsigned long) addr);
        }
    if (addr > decode.high_pc)
        decode.high_pc = addr;
    }
    }

    if (opcode.extra == TEXT) {
    if (decode.first_pass) {
        while ((short) read_data_word (&decode.pc) >= 0)
        ;
    } else
        print_text (&decode.pc);
    }

    if (opcode.type == RETURN)
    if (decode.pc > decode.high_pc)
        return (END_OF_ROUTINE);

    return (END_OF_INSTRUCTION);

}/* decode_outputs */

/* decode_strings - Dump text after end of code */

#ifdef __STDC__
static void decode_strings (unsigned long pc)
#else
static void decode_strings (pc)
unsigned long pc;
#endif
{
    int count = 1;

    pc = ROUND_DATA (pc);
    tx_printf ("\n[Start of text");
    if (option_labels == 0)
    tx_printf (" at %lx", (unsigned long) pc);
    tx_printf ("]\n\n");
    while (pc < file_size) {
    if (option_labels)
        tx_printf ("%c%03d: ", (option_inform) ? 's' : 'S', (int) count++);
    else
        tx_printf ("%5lx: S%03d ", (unsigned long) pc, (int) count++);
    print_text (&pc);
    tx_printf ("\n");
    pc = ROUND_CODE (pc);
    }
    tx_printf ("\n[End of text");
    if (option_labels == 0)
    tx_printf (" at %lx", (unsigned long) pc);
    tx_printf ("]\n\n[End of file]\n");

}/* decode_strings */

/* scan_strings - build string address table */

#ifdef __STDC__
static void scan_strings (unsigned long pc)
#else
static void scan_strings (pc)
unsigned long pc;
#endif
{
    unsigned long old_pc;
    int count = 1;
    cref_item_t *cref_item;
    zword_t data;

    pc = ROUND_DATA (pc);
    old_pc = pc;
    while (pc < file_size) {
    cref_item = (cref_item_t *) malloc (sizeof (cref_item_t));
    if (cref_item == NULL) {
        (void) fprintf (stderr, "\nFatal: insufficient memory\n");
        exit (EXIT_FAILURE);
    }
    cref_item->address = pc;
    cref_item->number = count++;
    cref_item->next = strings_base;
    strings_base = cref_item;
    old_pc = pc;
    do
        data = (zword_t) read_data_word (&pc);
    while (pc < file_size && ((unsigned int) data & 0x8000) == 0);
    pc = ROUND_CODE (pc);
    if ((unsigned int) data & 0x8000)
        old_pc = pc;
    }
    file_size = old_pc;

}/* scan_strings */

/* lookup_string - lookup a string address */

#ifdef __STDC__
static int lookup_string (unsigned long addr)
#else
static int lookup_string (addr)
unsigned long addr;
#endif
{
    cref_item_t *cref_item;

    if (addr <= decode.high_address || addr >= file_size)
    return (0);

    for (cref_item = strings_base; cref_item != NULL; cref_item = cref_item->next)
    if (cref_item->address == addr)
        return (cref_item->number);

    return (0);

}/* lookup_string */

#ifdef __STDC__
static void lookup_verb (unsigned long addr)
#else
static void lookup_verb (addr)
unsigned long addr;
#endif
{
    unsigned long address, routine;
    unsigned int i, first;

    first = 1;
    address = action_table_base;
    for (i = 0; i < action_count; i++) {
    routine = (unsigned long) read_data_word (&address) * code_scaler + (unsigned long) story_scaler * header.routines_offset;
    if (routine == addr) {
        if (first) {
        tx_printf ("    Action routine for:\n");
        tx_printf ("        ");
        tx_fix_margin(1);
        first = 0;
        }
        show_syntax_of_action(i,
                  verb_table_base,
                  verb_count,
                  parser_type,
                  prep_type,
                  prep_table_base,
                  attr_names_base);
    }
    }
    tx_fix_margin(0);

    first = 1;
    address = preact_table_base;
    if (parser_type >= inform_gv2) {
    if (is_gv2_parsing_routine(addr, verb_table_base,
                   verb_count)) {
        tx_printf ("    Parsing routine for:\n");
        tx_printf ("        ");
        tx_fix_margin(1);
        first = 0;
       show_syntax_of_parsing_routine( addr,
                       verb_table_base,
                       verb_count,
                       parser_type,
                       prep_type,
                       prep_table_base,
                       attr_names_base);
    }
    }
    else if (parser_type >= inform5_grammar) {
    for (i = 0; i < parse_count; i++) {
        routine = (unsigned long) read_data_word (&address) * code_scaler + (unsigned long) story_scaler * header.routines_offset;
        if (routine == addr) {
            if (first) {
                tx_printf ("    Parsing routine for:\n");
                tx_printf ("        ");
                tx_fix_margin(1);
                first = 0;
            }
            show_syntax_of_parsing_routine(i,
                      verb_table_base,
                      verb_count,
                      parser_type,
                      prep_type,
                      prep_table_base,
                      attr_names_base);
        }
        }
    }
    else {
    for (i = 0; i < action_count; i++) {
        routine = (unsigned long) read_data_word (&address) * code_scaler + (unsigned long) story_scaler * header.routines_offset;
        if (routine == addr) {
            if (first) {
            tx_printf ("    Pre-action routine for:\n");
            tx_printf ("        ");
            tx_fix_margin(1);
            first = 0;
            }
            show_syntax_of_action(i,
                      verb_table_base,
                      verb_count,
                      parser_type,
                      prep_type,
                      prep_table_base,
                      attr_names_base);
        }
        }
    }
    tx_fix_margin(0);

}/* lookup_verb */

#ifdef __STC__
static void setup_dictionary (void)
#else
static void setup_dictionary ()
#endif
{

    dict_start = (unsigned long) header.dictionary;
    dict_start += (unsigned long) read_data_byte (&dict_start);
    word_size = (unsigned long) read_data_byte (&dict_start);
    word_count = (unsigned long) read_data_word (&dict_start);
    dict_end = dict_start + (word_count * word_size);

}/* setup_dictionary */

#ifdef __STDC__
static int in_dictionary (unsigned long word_address)
#else
static int in_dictionary (word_address)
unsigned long word_address;
#endif
{

    if (word_address < dict_start || word_address > dict_end)
    return (0);

    if ((word_address - dict_start) % word_size == 0)
    return (1);

    return (0);

}/* in_dictionary */

#ifdef __STDC__
static void add_label (unsigned long addr)
#else
static void add_label (addr)
unsigned long addr;
#endif
{
    cref_item_t *cref_item, **prev_item, *next_item;

    if (current_routine == NULL)
    return;

    prev_item = &current_routine->child;
    next_item = current_routine->child;
    while (next_item != NULL && next_item->address < addr) {
    prev_item = &(next_item->next);
    next_item = next_item->next;
    }

    if (next_item == NULL || next_item->address != addr) {
    cref_item = (cref_item_t *) malloc (sizeof (cref_item_t));
    if (cref_item == NULL) {
        (void) fprintf (stderr, "\nFatal: insufficient memory\n");
        exit (EXIT_FAILURE);
    }
    cref_item->next = next_item;
    *prev_item = cref_item;
    cref_item->child = NULL;
    cref_item->address = addr;
    cref_item->number = 0;
    }

}/* add_label */

#ifdef __STDC__
static void add_routine (unsigned long addr)
#else
static void add_routine (addr)
unsigned long addr;
#endif
{
    cref_item_t *cref_item, **prev_item, *next_item;

    prev_item = &routines_base;
    next_item = routines_base;
    while (next_item != NULL && next_item->address < addr) {
    prev_item = &(next_item->next);
    next_item = next_item->next;
    }

    if (next_item == NULL || next_item->address != addr) {
    cref_item = (cref_item_t *) malloc (sizeof (cref_item_t));
    if (cref_item == NULL) {
        (void) fprintf (stderr, "\nFatal: insufficient memory\n");
        exit (EXIT_FAILURE);
    }
    cref_item->next = next_item;
    *prev_item = cref_item;
    cref_item->child = NULL;
    cref_item->address = addr;
    cref_item->number = 0;
    } else
    cref_item = next_item;

    current_routine = cref_item;

}/* add_routine */

#ifdef __STDC__
static int lookup_label (unsigned long addr, int flag)
#else
static int lookup_label (addr, flag)
unsigned long addr;
int flag;
#endif
{
    cref_item_t *cref_item = current_routine->child;
    int label;

    while (cref_item != NULL && cref_item->address != addr)
    cref_item = cref_item->next;

    if (cref_item == NULL) {
    label = 0;
    if (flag) {
        (void) fprintf (stderr, "\nFatal: cannot find label!\n");
        exit (EXIT_FAILURE);
    }
    } else
    label = cref_item->number;

    return (label);

}/* lookup_label */

#ifdef __STDC__
static int lookup_routine (unsigned long addr, int flag)
#else
static int lookup_routine (addr, flag)
unsigned long addr;
int flag;
#endif
{
    cref_item_t *cref_item = routines_base;

    while (cref_item != NULL && cref_item->address != addr)
    cref_item = cref_item->next;

    if (cref_item == NULL) {
    if (flag) {
        (void) fprintf (stderr, "\nFatal: cannot find routine!\n");
        exit (EXIT_FAILURE);
    } else
        return (0);
    }

    if (flag)
    current_routine = cref_item;

    return (cref_item->number);

}/* lookup_routine */

#ifdef __STDC__
static void renumber_cref (cref_item_t *cref_item)
#else
static void renumber_cref (cref_item)
cref_item_t *cref_item;
#endif
{
    int number = 1;

    while (cref_item != NULL) {
    if (start_data_pc == 0 ||
        cref_item->address < start_data_pc ||
        cref_item->address >= end_data_pc)
        cref_item->number = number++;
    renumber_cref (cref_item->child);
    cref_item = cref_item->next;
    }

}/* renumber_cref */

#ifdef __STDC__
static void free_cref (cref_item_t *cref_item)
#else
static void free_cref (cref_item)
cref_item_t *cref_item;
#endif
{
    cref_item_t *t;

    while (cref_item != NULL) {
    free_cref (cref_item->child);
    t = cref_item->next;
    free (cref_item);
    cref_item = t;
    }

}/* free_cref */

#ifdef __STDC__
static int print_object_desc (unsigned int obj)
#else
static int print_object_desc (obj)
unsigned int obj;
#endif
{
    unsigned long address;

    address = (unsigned long) header.objects;
    if ((unsigned int) header.version < V4)
    address += ((P3_MAX_PROPERTIES - 1) * 2) + ((obj - 1) * O3_SIZE) + O3_PROPERTY_OFFSET;
    else
    address += ((P4_MAX_PROPERTIES - 1) * 2) + ((obj - 1) * O4_SIZE) + O4_PROPERTY_OFFSET;

    address = (unsigned long) read_data_word (&address);
    if ((unsigned int) read_data_byte (&address)) {
    tx_printf ("\"");
    (void) decode_text (&address);
    tx_printf ("\"");
    } else
    obj = 0;

    return (obj);

}/* print_object_desc */

#ifdef __STDC__
static void print_text (unsigned long *addr)
#else
static void print_text (addr)
unsigned long *addr;
#endif
{

    tx_printf ("\"");
    (void) decode_text (addr);
    tx_printf ("\"");

}/* print_text */

#ifdef __STDC___
static void print_integer (unsigned int value, int flag)
#else
static void print_integer (value, flag)
unsigned int value;
int flag;
#endif
{

    if (flag)
    tx_printf ("#%02x", value);
    else
    tx_printf ("#%04x", value);

}

#ifdef __STDC__
static void dump_data (unsigned long start_addr, unsigned long end_addr)
#else
static void dump_data (start_addr, end_addr)
unsigned long start_addr;
unsigned long end_addr;
#endif
{
    int i, c;
    unsigned long addr, save_addr, low_addr, high_addr;

    low_addr = start_addr & ~15;
    high_addr = (end_addr + 15) & ~15;

    for (addr = low_addr; addr < high_addr; ) {
    tx_printf ("%5lx: ", (unsigned long) addr);
    save_addr = addr;
    for (i = 0; i < 16; i++) {
        if (addr < start_addr || addr > end_addr) {
        tx_printf ("   ");
        addr++;
        } else
        tx_printf ("%02x ", (unsigned int) read_data_byte (&addr));
    }
    addr = save_addr;
    for (i = 0; i < 16; i++) {
        if (addr < start_addr || addr > end_addr) {
        tx_printf (" ");
        addr++;
        } else {
        c = read_data_byte (&addr);
        tx_printf ("%c", (char) ((isprint (c)) ? c : '.'));
        }
    }
    tx_printf ("\n");
    }

}/* dump_data */

#ifdef __STDC__
static void dump_opcode (unsigned long addr, int op, int class, int *par, int extra)
#else
static void dump_opcode (addr, op, class, par, extra)
unsigned long addr;
int op;
int class;
int *par;
int extra;
#endif
{
    int opers, modes, addr_mode, maxopers, count;
    unsigned char t;
    unsigned long save_addr;

    count = 0;

    addr--;
    if (class == EXTENDED_OPERAND) {
    addr--;
    tx_printf ("%02x ", (unsigned int) read_data_byte (&addr));
    count++;
    }
    tx_printf ("%02x ", (unsigned int) read_data_byte (&addr));
    count++;

    if (class == ONE_OPERAND)
    dump_operand (&addr, (op >> 4) & 0x03, 0, par, &count);

    if (class == TWO_OPERAND) {
    dump_operand (&addr, (op & 0x40) ? VARIABLE : BYTE_IMMED, 0, par, &count);
    dump_operand (&addr, (op & 0x20) ? VARIABLE : BYTE_IMMED, 1, par, &count);
    }

    if (class == VARIABLE_OPERAND || class == EXTENDED_OPERAND) {
    if ((op & 0x3f) == 0x2c || (op & 0x3f) == 0x3a) {
        save_addr = addr;
        modes = read_data_word (&addr);
        addr = save_addr;
        tx_printf ("%02x ", (unsigned int) read_data_byte (&addr));
        tx_printf ("%02x ", (unsigned int) read_data_byte (&addr));
        count += 2;
        maxopers = 8;
    } else {
        save_addr = addr;
        modes = read_data_byte (&addr);
        addr = save_addr;
        tx_printf ("%02x ", (unsigned int) read_data_byte (&addr));
        count++;
        maxopers = 4;
    }
    for (addr_mode = 0, opers = 0; (addr_mode != NO_OPERAND) && maxopers; maxopers--) {
        addr_mode = (modes >> ((maxopers - 1) * 2)) & 0x03;
        if (addr_mode != NO_OPERAND) {
        dump_operand (&addr, addr_mode, opers, par, &count);
        opers++;
        }
    }
    }

    if (extra == TEXT) {
    tx_printf ("...");
    count++;
    }

    if (extra == STORE || extra == BOTH) {
    tx_printf ("%02x ", (unsigned int) read_data_byte (&addr));
    count++;
    }

    if (extra == BRANCH || extra == BOTH) {
    t = (unsigned char) read_data_byte (&addr);
    tx_printf ("%02x ", (unsigned int) t);
    count++;
    if (((unsigned int) t & 0x40) == 0) {
        tx_printf ("%02x ", (unsigned int) read_data_byte (&addr));
        count++;
    }
    }

    if (count > 8)
    tx_printf ("\n                               ");
    else
    for (; count < 8; count++)
        tx_printf ("   ");

}/* dump_opcode */

#ifdef __STDC__
static void dump_operand (unsigned long *addr, int addr_mode, int opers, int *par, int *count)
#else
static void dump_operand (addr, addr_mode, opers, par, count)
unsigned long *addr;
int addr_mode;
int opers;
int *par;
int *count;
#endif
{

    if (opers < 4 && par[opers] == VAR)
    addr_mode = VARIABLE;

    if (addr_mode == WORD_IMMED) {
    tx_printf ("%02x ", (unsigned int) read_data_byte (addr));
    tx_printf ("%02x ", (unsigned int) read_data_byte (addr));
    *count += 2;
    }

    if (addr_mode == BYTE_IMMED || addr_mode == VARIABLE) {
    tx_printf ("%02x ", (unsigned int) read_data_byte (addr));
    (*count)++;
    }

}/* dump_operand */

#ifdef __STDC__
static void print_variable (int varnum)
#else
static void print_variable (varnum)
int varnum;
#endif
{
    if (varnum < 16) {
    if (option_symbols && print_local_name(start_of_routine, varnum - 1)) /* null */;
    else if (option_inform)
        tx_printf ("local%d", varnum - 1);
    else
        tx_printf ("L%02x", varnum - 1);
    } else
    if (option_symbols && print_global_name(start_of_routine, varnum - 16)) /* null */;
    else tx_printf ("%c%02x", (option_inform) ? 'g' : 'G', varnum - 16);
}
