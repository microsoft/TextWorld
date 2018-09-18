/*
 * infodump V7/3
 *
 * Infocom data file dumper, etc. for V1 to V8 games.
 * Works on everything I have, except for parsing information in V6 games.
 *
 * The most useful options are; -i to display the header information, such as
 * game version, serial number and release; -t to display the object tree which
 * shows where all objects start and which item is in which room; -g to show
 * the sentence grammar acceptable to the game; -d to see all the recognised
 * words.
 *
 * Required files:
 *    showhead.c - show header information
 *    showdict.c - show dictionary and abbreviations
 *    showobj.c  - show objects
 *    showverb.c - show verb grammar
 *    txio.c     - I/O support
 *    tx.h       - Include file required by everything above
 *    getopt.c   - The standard getopt function
 *
 * Usage: infodump [options...] story-file [story-file...]
 *     -i   show game information in header (default)
 *     -a   show abbreviations
 *     -m   show data file map
 *     -o   show objects
 *     -t   show object tree
 *     -g   show verb grammar
 *     -d n show dictionary (n = columns)
 *     -a   all of the above
 *     -w n display width (0 = no wrap)
 *
 * Mark Howell 28 August 1992 howell_ma@movies.enet.dec.com
 *
 * History:
 *    Fix verb table display for later V4 and V5 games
 *    Fix property list
 *    Add verb table
 *    Add support for V1 and V2 games
 *    Improve output
 *    Improve verb formatting
 *    Rewrite and add map
 *    Add globals address and V6 start PC
 *    Fix lint warnings and some miscellaneous bugs
 *    Add support for V7 and V8 games
 *    Fix Inform grammar tables
 *    Fix Inform adjectives table
 *    Add support for Inform 6 (helped by Matthew T. Russotto)
 *    Add header flag for "timed input"
 *    Add header extension table and Unicode table
 *    Add Inform and user symbol table support
 */

#include "tx.h"
#include "ztools.h"

#ifdef __STDC__
#ifndef HAS_GETOPT
extern int getopt (int, char *[], const char *);
#endif
extern void show_header (void);
extern void show_abbreviations (void);
extern void show_dictionary (int);
extern void show_objects (int);
extern void show_tree (void);
extern void show_verbs (int);
#else
extern int getopt ();
extern void show_header ();
extern void show_abbreviations ();
extern void show_dictionary ();
extern void show_objects ();
extern void show_tree ();
extern void show_verbs ();
#endif

#ifdef __STDC__
static void show_help (const char *);
static void fix_dictionary (void);
static void show_map (void);
#else
static void show_help ();
static void fix_dictionary ();
static void show_map ();
#endif

/* Options */

#define OPTION_A 0
#define OPTION_I 1
#define OPTION_O 2
#define OPTION_T 3
#define OPTION_G 4
#define OPTION_D 5
#define OPTION_M 6
#define MAXOPT   7

#ifndef HAS_GETOPT
/* getopt linkages */

extern int optind;
extern const char *optarg;
#endif

/*
 * main
 *
 * Process command line arguments and process each story file.
 */

/* #ifdef __STDC__ */
/* int main (int argc, char *argv[]) */
/* #else */
/* int main (argc, argv) */
/* int argc; */
/* char *argv[]; */
/* #endif */
/* { */
/*     int c, f, i, errflg = 0; */
/*     int columns, options[MAXOPT]; */
/*     int symbolic; */

/* /\* Clear all options *\/ */

/*     for (i = 0; i < MAXOPT; i++) */
/*  options[i] = 0; */
/*     columns = 0; */
/*     symbolic = 0; */

/*     /\* Parse the options *\/ */

/*     while ((c = getopt (argc, argv, "hafiotgmdsc:w:u:")) != EOF) { */
/*  switch (c) { */
/*      case 'f': */
/*      for (i = 0; i < MAXOPT; i++) */
/*          options[i] = 1; */
/*      break; */
/*      case 'a': */
/*      options[OPTION_A] = 1; */
/*      break; */
/*      case 'i': */
/*      options[OPTION_I] = 1; */
/*      break; */
/*      case 'o': */
/*      options[OPTION_O] = 1; */
/*      break; */
/*      case 't': */
/*      options[OPTION_T] = 1; */
/*      break; */
/*      case 'g': */
/*      options[OPTION_G] = 1; */
/*      break; */
/*      case 'm': */
/*      options[OPTION_M] = 1; */
/*      break; */
/*      case 'd': */
/*      options[OPTION_D] = 1; */
/*      break; */
/*      case 's': */
/*      symbolic = 1; */
/*      break; */
/*      case 'c': */
/*      columns = atoi (optarg); */
/*      break; */
/*      case 'w': */
/*      tx_set_width (atoi (optarg)); */
/*      break; */
/*      case 'u': */
/*          symbolic = 1; */
/*      init_symbols (optarg); */
/*      break; */
/*      case 'h': */
/*      case '?': */
/*      default: */
/*      errflg++; */
/*  } */
/*     } */

/*     /\* Display usage if unknown flag or no story file *\/ */

/*     if (errflg || optind >= argc) { */
/*  show_help (argv[0]); */
/*  exit (EXIT_FAILURE); */
/*     } */

/*     /\* If no options then force header option information on *\/ */

/*     for (f = 0, i = 0; i < MAXOPT; i++) */
/*  f += options[i]; */
/*     if (f == 0) */
/*  options[OPTION_I] = 1; */

/*     /\* Process any story files on the command line *\/ */

/*     for (; optind < argc; optind++) */
/*  process_story (argv[optind], options, columns, symbolic); */

/*     exit (EXIT_SUCCESS); */

/*     return (0); */

/* }/\* main *\/ */

/*
 * show_help
 */

#ifdef __STDC__
static void show_help (const char *program)
#else
static void show_help (program)
const char *program;
#endif
{

    (void) fprintf (stderr, "usage: %s [options...] story-file [story-file...]\n\n", program);
    (void) fprintf (stderr, "INFODUMP version 7/3 - display Infocom story file information. By Mark Howell\n");
    (void) fprintf (stderr, "Works with V1 to V8 Infocom games.\n\n");
    (void) fprintf (stderr, "\t-i   show game information in header (default)\n");
    (void) fprintf (stderr, "\t-a   show abbreviations\n");
    (void) fprintf (stderr, "\t-m   show data file map\n");
    (void) fprintf (stderr, "\t-o   show objects\n");
    (void) fprintf (stderr, "\t-t   show object tree\n");
    (void) fprintf (stderr, "\t-g   show verb grammar\n");
    (void) fprintf (stderr, "\t-d   show dictionary\n");
    (void) fprintf (stderr, "\t-f   full report (all of the above)\n");
    (void) fprintf (stderr, "\t-c n number of columns for dictionary display\n");
    (void) fprintf (stderr, "\t-w n display width (0 = no wrap)\n");
    (void) fprintf (stderr, "\t-s Display Inform symbolic names in object and grammar displays\n");
    (void) fprintf (stderr, "\t-u <file> Display symbols from file in object and grammar displays (implies -s)\n");

}/* show_help */

void print_dictionary (const char *name)
{
    open_story (name);
    configure (V1, V8);
    load_cache ();
    fix_dictionary ();
    show_dictionary (1);
    close_story ();
}

void print_verbs (const char *name)
{
    open_story (name);
    configure (V1, V8);
    load_cache ();
    fix_dictionary ();
    show_verbs (0);
    close_story ();
}


/*
 * process_story
 *
 * Load the story and display all parts of the data file requested.
 */
#ifdef __STDC__
void process_story (const char *name, int *options, int columns, int symbolic)
#else
void process_story (name, options, columns, symbolic)
const char *name;
int *options;
int columns;
int symbolic;
#endif
{

    tx_printf ("\nStory file is %s\n", name);

    open_story (name);

    configure (V1, V8);

    load_cache ();

    fix_dictionary ();

    if (options[OPTION_I])
    show_header ();

    if (options[OPTION_M])
    show_map ();

    if (options[OPTION_A])
    show_abbreviations ();

    if (options[OPTION_O])
    show_objects (symbolic);

    if (options[OPTION_T])
    show_tree ();

    if (options[OPTION_G])
    show_verbs (symbolic);

    if (options[OPTION_D])
    show_dictionary (columns);

    close_story ();

}/* process_story */

/*
 * fix_dictionary
 *
 * Fix the end of text flag for each word in the dictionary. Some older games
 * are missing the end of text flag on some words. All the words are fixed up
 * so that they can be printed.
 */

#ifdef __STDC__
static void fix_dictionary (void)
#else
static void fix_dictionary ()
#endif
{
    unsigned long address;
    int separator_count, word_size, word_count, i;

    address = header.dictionary;
    separator_count = read_data_byte (&address);
    address += separator_count;
    word_size = read_data_byte (&address);
    word_count = read_data_word (&address);

    for (i = 1; i <= word_count; i++) {

    /* Check that the word is in non-paged memory before writing */

      if ((address + 4) < (unsigned long) header.resident_size) {
        if ((unsigned int) header.version <= V3) {
          set_byte (address + 2, (unsigned int) get_byte (address + 2) | 0x80);
        } else {
          set_byte (address + 4, (unsigned int) get_byte (address + 4) | 0x80);
        }
      }

    address += word_size;
    }

}/* fix_dictionary */

#ifdef __STDC__
extern void configure_dictionary
    (unsigned int *, unsigned long *, unsigned long *);
extern void configure_abbreviations
    (unsigned int *, unsigned long *, unsigned long *, unsigned long *,
     unsigned long *);
extern void configure_object_tables
    (unsigned int *, unsigned long *, unsigned long *, unsigned long *,
     unsigned long *);
#else
extern void configure_dictionary ();
extern void configure_abbreviations ();
extern void configure_object_tables ();
#endif

#ifdef __STDC__
static int compare_area (const void *, const void *);
#else
static int compare_area ();
#endif

#define MAX_AREA 20

#define set_area(index, base_addr, end_addr, name_string) { \
    if (index == MAX_AREA) {                                \
    fprintf (stderr, "Area space exhausted!\n");        \
    exit (EXIT_FAILURE);                                \
    }                                                       \
    areas[index].base = base_addr;                          \
    areas[index].end = end_addr;                            \
    areas[index].name = name_string;                        \
    index++;                                                \
}

typedef struct area_s {
    unsigned long base;
    unsigned long end;
    const char *name;
} area_t;

/*
 * show_map
 *
 * Show the map of the data area. This is done by calling the configure routine
 * for each area. Each area is then sorted in ascending order and displayed.
 */

#ifdef __STDC__
static void show_map (void)
#else
static void show_map ()
#endif
{
    unsigned int abbr_count;
    unsigned long abbr_table_base, abbr_table_end, abbr_data_base, abbr_data_end;
    unsigned int word_count;
    unsigned long word_table_base, word_table_end;
    unsigned int obj_count;
    unsigned long obj_table_base, obj_table_end, obj_data_base, obj_data_end;
    unsigned int verb_count, action_count, verb_type, prep_type;
    unsigned int parse_count;
    unsigned long verb_table_base, verb_data_base;
    unsigned long action_table_base, preact_table_base;
    unsigned long prep_table_base, prep_table_end;
    unsigned int ext_table_size;
    unsigned long ext_table_base, ext_table_end;
    unsigned long unicode_table_base, unicode_table_end;
    unsigned short inform_version;
    unsigned long class_numbers_base, class_numbers_end;
    unsigned long property_names_base, property_names_end;
    unsigned long attr_names_base, attr_names_end;
    area_t areas[MAX_AREA];
    int i, area;

    /* Configure areas */

    area = 0;

    set_area (area, 0, 63, "Story file header");

    ext_table_base = header.mouse_table;
    if (ext_table_base) {
        ext_table_size = get_word(ext_table_base);
        ext_table_end = ext_table_base + 2 + ext_table_size * 2 - 1;
    set_area (area, ext_table_base, ext_table_end, "Header extension table");
    if (ext_table_size > 2) {
        unicode_table_base = get_word(ext_table_base + 6);
        if (unicode_table_base) {
        unicode_table_end = unicode_table_base + get_byte(unicode_table_base)*2; 
        set_area (area, unicode_table_base, unicode_table_end, "Unicode table");
        }
    }
    }
    
    configure_abbreviations (&abbr_count, &abbr_table_base, &abbr_table_end,
                 &abbr_data_base, &abbr_data_end);

    if (abbr_count) {
    set_area (area, abbr_table_base, abbr_table_end, "Abbreviation pointer table");
    set_area (area, abbr_data_base, abbr_data_end, "Abbreviation data");
    }

    configure_dictionary (&word_count, &word_table_base, &word_table_end);

    set_area (area, word_table_base, word_table_end, "Dictionary");

    configure_object_tables (&obj_count, &obj_table_base, &obj_table_end,
                 &obj_data_base, &obj_data_end);

    set_area (area, obj_table_base, obj_table_end, "Object table");
    set_area (area, obj_data_base, obj_data_end, "Property data");

    configure_parse_tables (&verb_count, &action_count, &parse_count, &verb_type, &prep_type,
                &verb_table_base, &verb_data_base,
                &action_table_base, &preact_table_base,
                &prep_table_base, &prep_table_end);

    if ((verb_count > 0) && (verb_type != infocom6_grammar)) {
    set_area (area, verb_table_base, verb_data_base - 1, "Grammar pointer table");
    set_area (area, verb_data_base, action_table_base - 1, "Grammar data");
    set_area (area, action_table_base, preact_table_base - 1, "Action routine table");
    if (verb_type < inform_gv2) {
        set_area (area, preact_table_base, prep_table_base - 1, (verb_type >= inform5_grammar) ? "Parsing routine table" : "Pre-action routine table");
        set_area (area, prep_table_base, prep_table_end, "Preposition table");
    }
    }
    else if (verb_count > 0) {
    set_area (area, verb_table_base, verb_table_base + 8 * verb_count - 1, "Verb grammar table");
    set_area (area, verb_data_base, prep_table_base - 1, "Grammar entries");
    set_area (area, action_table_base, preact_table_base - 1, "Action routine table");
    set_area (area, preact_table_base, preact_table_base + action_count * 2 - 1, "Pre-action routine table");
    }
    
    configure_inform_tables(obj_data_end, &inform_version, &class_numbers_base, &class_numbers_end,
                    &property_names_base, &property_names_end, &attr_names_base, &attr_names_end);
   
    if (inform_version >= INFORM_6) {
        set_area(area, class_numbers_base, class_numbers_end, "Class Prototype Object Numbers");
        set_area(area, property_names_base, property_names_end, "Property Names Table");
    if (inform_version >= INFORM_610) {
            set_area(area, attr_names_base, attr_names_end, "Attribute Names Table");
    }
    }

    set_area (area, (unsigned long) header.globals,
          (unsigned long) header.globals + (240 * 2) - 1,
          "Global variables");

    set_area (area, (unsigned long) header.resident_size,
          (unsigned long) file_size - 1,
          "Paged memory");

    if (header.alphabet)
    set_area (area, (unsigned long) header.alphabet,
          (unsigned long) header.alphabet + (26 * 3) - 1,
          "Alphabet");

    /* Sort areas */

    qsort (areas, (size_t) area, sizeof (area_t), compare_area);

    /* Print area map */

    tx_printf ("\n    **** Story file map ****\n\n");

    tx_printf (" Base    End   Size\n");
    for (i = 0; i < area; i++) {
    if (i && (areas[i].base - 1) > areas[i - 1].end)
        tx_printf ("%5lx  %5lx  %5lx\n",
               (unsigned long) (areas[i - 1].end + 1), (unsigned long) (areas[i].base - 1),
               (unsigned long) ((areas[i].base - 1) - (areas[i - 1].end + 1) + 1));
    tx_printf ("%5lx  %5lx  %5lx  %s\n",
           (unsigned long) areas[i].base, (unsigned long) areas[i].end,
           (unsigned long) (areas[i].end - areas[i].base + 1),
           areas[i].name);
    }

}/* show_map */

/*
 * compare_area
 *
 * Compare two areas and sort by ascending value
 */

#ifdef __STDC__
static int compare_area (const void *a, const void *b)
#else
static int compare_area (a, b)
const void *a;
const void *b;
#endif
{
    long diff;

    diff = ((const area_t *) a)->base - ((const area_t *) b)->base;

    if (diff < 0)
    return (-1);
    else if (diff > 0)
    return (1);

    return (0);

}/* compare_area */
