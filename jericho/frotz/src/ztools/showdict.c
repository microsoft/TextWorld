/*
 * showdict - part of infodump
 *
 * Dictionary and abbreviation table routines.
 */

#include "tx.h"

#ifdef __STDC__
void configure_dictionary
    (unsigned int *, unsigned long *, unsigned long *);
void configure_abbreviations
    (unsigned int *, unsigned long *, unsigned long *, unsigned long *,
     unsigned long *);
#else
void configure_dictionary ();
void configure_abbreviations ();
#endif

/*
 * show_dictionary
 *
 * List the dictionary in the number of columns specified. If the number of
 * columns is one then also display the data associated with each word.
 */

#ifdef __STDC__
void show_dictionary (int columns)
#else
void show_dictionary (columns)
int columns;
#endif
{
    unsigned long dict_address, word_address, word_table_base, word_table_end;
    unsigned int separator_count, word_size, word_count, length;
    int i, flag;
    int inform_flags = 0;
    int dictpar1;

    /* Force default column count if none specified */

    if (columns == 0)
        columns = ((unsigned int) header.version < V4) ? 5 : 4;

    /* Get dictionary configuration */

    configure_dictionary (&word_count, &word_table_base, &word_table_end);

    if (header.serial[0] >= '0' && header.serial[0] <= '9' &&
        header.serial[1] >= '0' && header.serial[1] <= '9' &&
        header.serial[2] >= '0' && header.serial[2] <= '1' &&
        header.serial[3] >= '0' && header.serial[3] <= '9' &&
        header.serial[4] >= '0' && header.serial[4] <= '3' &&
        header.serial[5] >= '0' && header.serial[5] <= '9' &&
        header.serial[0] != '8') {
        inform_flags = TRUE;
    }

    tx_printf ("\n    **** Dictionary ****\n\n");

    /* Display the separators */

    dict_address = word_table_base;
    separator_count = read_data_byte (&dict_address);
    tx_printf ("  Word separators = \"");
    for (; separator_count; separator_count--)
        tx_printf ("%c", (char) read_data_byte (&dict_address));
    tx_printf ("\"\n");

    /* Get word size and count */

    word_size = read_data_byte (&dict_address);
    word_count = read_data_word (&dict_address);

    tx_printf ("  Word count = %d, word size = %d\n", (int) word_count, (int) word_size);

    /* Display each entry in the dictionary */

    for (i = 1; (unsigned int) i <= word_count; i++) {

        /* Set column breaks */

        if (columns == 1 || (i % columns) == 1)
            tx_printf ("\n");

        tx_printf ("[%4d] ", (int) i);

        /* Calculate address of next entry */

        word_address = dict_address;
        dict_address += word_size;

        if (columns == 1)
              tx_printf ("@ $%02x ", (unsigned int) word_address);

        /* Display the text for the word */

        for (length = decode_text (&word_address); length <= word_size; length++)
            tx_printf (" ");

        /* For a single column list also display the data for each entry */

        if (columns == 1) {
            tx_printf ("[");
            for (flag = 0; word_address < dict_address; flag++) {
                if (flag)
                    tx_printf (" ");
                else
                  dictpar1 = get_byte(word_address);

                tx_printf ("%02x", (unsigned int) read_data_byte (&word_address));
            }
            tx_printf ("]");

            if (inform_flags) {
              if (dictpar1 & NOUN)
                   tx_printf (" <noun>");
              if (dictpar1 & PREP)
                   tx_printf (" <prep>");
              if (dictpar1 & PLURAL)
                   tx_printf (" <plural>");
              if (dictpar1 & META)
                   tx_printf (" <meta>");
              if (dictpar1 & VERB_INFORM)
                   tx_printf (" <verb>");
            }
            else if (header.version != V6) {
                flag = dictpar1 & DATA_FIRST;
                switch (flag) {
                    case DIR_FIRST:
                        if (dictpar1 & DIR)
                           tx_printf (" <dir>");
                        break;
                    case ADJ_FIRST:
                        if (dictpar1 & DESC)
                           tx_printf (" <adj>");
                        break;
                    case VERB_FIRST:
                        if (dictpar1 & VERB)
                           tx_printf (" <verb>");
                        break;
                    case PREP_FIRST:
                        if (dictpar1 & PREP)
                           tx_printf (" <prep>");
                        break;
                }
                if ((dictpar1 & DIR) && (flag != DIR_FIRST))
                   tx_printf (" <dir>");
                if ((dictpar1 & DESC) && (flag != ADJ_FIRST))
                   tx_printf (" <adj>");
                if ((dictpar1 & VERB) && (flag != VERB_FIRST))
                   tx_printf (" <verb>");
                if ((dictpar1 & PREP) && (flag != PREP_FIRST))
                   tx_printf (" <prep>");
                if (dictpar1 & NOUN)
                   tx_printf (" <noun>");
                if (dictpar1 & SPECIAL)
                   tx_printf (" <special>");
            }
        }
    }
    tx_printf ("\n");

}/* show_dictionary */

/*
 * configure_dictionary
 *
 * Determine the dictionary start and end addresses, together with the number
 * of word entries.
 *
 * Format:
 *
 * As ASCIC string listing the punctuation to be treated as words. Correct
 * recognition of punctuation is important for parsing.
 *
 * A byte word size. Not the size of the displayed word, but the amount of data
 * occupied by each word entry in the dictionary.
 *
 * A word word count. Total size of dictionary is word count * word size.
 *
 * Word count word entries. The format of the textual part of the word is fixed
 * by the Z machine, but the data following each word can vary. The text for
 * the word starts each entry. It is a packed string. The data
 * associated with each word is used in parsing a sentence. It includes flags
 * to identify the type of word (verb, noun, etc.) and data specific to each
 * word type.
 */

#ifdef __STDC__
void configure_dictionary (unsigned int *word_count,
                           unsigned long *word_table_base,
                           unsigned long *word_table_end)
#else
void configure_dictionary (word_count,
                           word_table_base,
                           word_table_end)
unsigned int *word_count;
unsigned long *word_table_base;
unsigned long *word_table_end;
#endif
{
    unsigned long dict_address;
    unsigned int separator_count, word_size;

    *word_table_base = 0;
    *word_table_end = 0;
    *word_count = 0;

    /* Dictionary base address comes from the header */

    *word_table_base = (unsigned long) header.dictionary;

    /* Skip the separator list */

    dict_address = *word_table_base;
    separator_count = read_data_byte (&dict_address);
    dict_address += separator_count;

    /* Get entry size and count */

    word_size = (unsigned int) read_data_byte (&dict_address);
    *word_count = (unsigned int) read_data_word (&dict_address);

    /* Calculate dictionary end address */

    *word_table_end = (dict_address + (word_size * *word_count)) - 1;

}/* configure_dictionary */

/*
 * show_abbreviations
 *
 * Display the list of abbreviations used to compress text strings.
 */

#ifdef __STDC__
void show_abbreviations (void)
#else
void show_abbreviations ()
#endif
{
    unsigned long table_address, abbreviation_address;
    unsigned long abbr_table_base, abbr_table_end, abbr_data_base, abbr_data_end;
    unsigned int abbr_count;
    int i;

    /* Get abbreviations configuration */

    configure_abbreviations (&abbr_count, &abbr_table_base, &abbr_table_end,
                 &abbr_data_base, &abbr_data_end);

    tx_printf ("\n    **** Abbreviations ****\n\n");

    /* No abbreviations if count is zero (V1 games only) */

    if (abbr_count == 0) {
    tx_printf ("No abbreviation information.\n");
    } else {

    /* Display each abbreviation */

    table_address = abbr_table_base;

    for (i = 0; (unsigned int) i < abbr_count; i++) {

        /* Get address of abbreviation text from table */

        abbreviation_address = (unsigned long) read_data_word (&table_address) * 2;
            tx_printf ("[%2d] \"", (int) i);
        (void) decode_text (&abbreviation_address);
            tx_printf ("\"\n");
        }
    }

}/* show_abbreviations */

/*
 * configure_abbreviations
 *
 * Determine the abbreviation table start and end addresses, together
 * with the abbreviation text start and end addresses, and the number
 * of abbreviation entries.
 *
 * Format:
 *
 * The abbreviation information consists of two parts. Firstly a table of
 * word sized pointers corresponding to the abbreviation number, and
 * secondly, the packed string data for each abbreviation.
 *
 * Note: the pointers have to be multiplied by 2 *regardless* of the game
 * version to get the byte address for each abbreviation.
 */

#ifdef __STDC__
void configure_abbreviations (unsigned int *abbr_count,
                  unsigned long *abbr_table_base,
                  unsigned long *abbr_table_end,
                  unsigned long *abbr_data_base,
                  unsigned long *abbr_data_end)
#else
void configure_abbreviations (abbr_count,
                  abbr_table_base,
                  abbr_table_end,
                  abbr_data_base,
                  abbr_data_end)
unsigned int *abbr_count;
unsigned long *abbr_table_base;
unsigned long *abbr_table_end;
unsigned long *abbr_data_base;
unsigned long *abbr_data_end;
#endif
{
    unsigned long table_address, address;
    int i, tables;

    *abbr_table_base = 0;
    *abbr_table_end = 0;
    *abbr_data_base = 0;
    *abbr_data_end = 0;
    *abbr_count = 0;

    /* The abbreviation table address comes from the header */

    *abbr_table_base = (unsigned long) header.abbreviations;

    /* Check if there is any abbreviation table (V2 games and above) */

    if (*abbr_table_base) {

    /* Calculate the number of abbreviation tables (V2 = 1, V3+ = 3) */

    tables = ((unsigned int) header.version < V3) ? 1 : 3;

    /* Calculate abbreviation count and table end address */

    *abbr_count = tables * 32;
    *abbr_table_end = *abbr_table_base + (*abbr_count * 2) - 1;

    /* Calculate the high and low address for the abbreviation strings */

    table_address = *abbr_table_base;
    for (i = 0; (unsigned int) i < *abbr_count; i++) {
            address = (unsigned long) read_data_word (&table_address) * 2;
        if (*abbr_data_base == 0 || address < *abbr_data_base)
        *abbr_data_base = address;
        if (*abbr_data_end == 0 || address > *abbr_data_end)
        *abbr_data_end = address;
        }

        /* Scan last string to get the actual end of the string */

    while (((unsigned int) read_data_word (abbr_data_end) & 0x8000) == 0)
            ;

    (*abbr_data_end)--;
    }

}/* configure_abbreviations */
