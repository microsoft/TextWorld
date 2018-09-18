/*
 * showverb - part of infodump
 *
 * Verb and grammar display routines.
 */

#include "tx.h"

#ifdef __STDC__
static void show_verb_parse_table
    (unsigned long, unsigned int, unsigned int, unsigned int, unsigned long, unsigned long);
static void show_action_tables
    (unsigned long, unsigned int, unsigned int, unsigned int, unsigned int,
     unsigned int, unsigned long, unsigned long, unsigned long, unsigned long, unsigned long);
static void show_preposition_table
    (unsigned int, unsigned long, unsigned int);
static void show_preposition
    (unsigned int, int, unsigned long);
static void show_words
    (unsigned int, unsigned long, unsigned int, unsigned int);
static unsigned long lookup_word
    (unsigned long, unsigned int, unsigned int, unsigned int);
#else
static void show_verb_parse_table ();
static void show_action_tables ();
static void show_preposition_table ();
static void show_preposition ();
static void show_words ();
static unsigned long lookup_word ();
#endif

static const int verb_sizes[4] = { 2, 4, 7, 0 };

/*
 * configure_parse_tables
 *
 * Determine the start of the parse table, the start of the parse data, the
 * start of the action routine table, the start of the pre-action routine
 * table, the start of the preposition list and other sundry things.
 *
 * Format of the verb parse tables:
 *
 * base:
 *    Table of pointers (2 bytes) to each verb entry. Each verb in the
 *    dictionary has an index (1 byte) into this table. The index in the
 *    dictionary is inverted so an index of 255 = table entry 0, etc.
 *    In GV2 the index is 2 bytes and it is not inverted -- except that
 *    Inform 6.10 uses the old method.  Thus type GV2A is used internally
 *    to indicate the 2-byte form which will presumably be used in
 *    later Inform versions.
 *
 *    Next comes the parse data for each verb pointed to by the table of
 *    pointers. The format of the parse data varies between games. Basically,
 *    each entry has a count (1 byte) of parse structures corresponding to
 *    different sentence structures. For example, the verb 'take' in the
 *    dictionary may have two forms; 'take object' or 'take object with object'.
 *    Each form has an index (1 byte) into the pre-action and action routine
 *    tables.
 *
 *    Next come the action routine tables. There is an entry (2 bytes) for
 *    each verb form index. The entries are packed addresses of the Z-code
 *    routines that perform the main verb processing.
 *
 *    Next come the pre-action routine tables. There is an entry (2 bytes) for
 *    each verb form index. The entries are packed addresses of the Z-code
 *    routines that are called before the main verb action routine.
 *
 *    Finally, there is a list of prepositions that can be used by any verb
 *    in the verb parse table. This list has a count (2 bytes) followed by
 *    the address of the preposition in the dictionary and an index.
 *
 * Verb parse entry format:
 *
 *    The format of the data varies between games. The information in the
 *    entry is the same though:
 *
 *    An object count (0, 1 or 2)
 *    A preposition index for the verb
 *    Data for object(s) 1
 *    A preposition index for the objects
 *    Data for object(s) 2
 *    A pre-action/action routine table index
 *
 *    This means a sentence can have the following form:
 *
 *    verb [+ prep]                              'look [at]'
 *    verb [+ prep] + object                     'look [at] book'
 *    verb [+ prep] + object [+ prep] + object   'look [at] book [with] glasses'
 *
 *    The verb and prepositions can only be a single word each. The object
 *    could be a multiple words 'green book' or a list depending on the object
 *    data.
 *
 * Notes:
 *
 * Story files produced by Graham Nelson's Inform compiler do not have a
 * concept of pre-actions. Instead, the pre-actions table is filled with
 * pointers to general parsing routines which are related to certain verb
 * parse entries. The format of the parse entries has changed, too. Parse
 * entries have now become a string of tokens. Objects have token values
 * between 0x00 and 0xaf, prepositions correspond to token values from 0xb0
 * to 0xff. Therefore more complicated verb structures with more than two
 * prepositions are possible. See the "Inform Technical Manual" for further
 * information.
 *
 * Inform 6 reduces the size of the pre-action table (which no longer holds
 * any pre-action routines, see above) to the number of parsing routines.
 *
 * Inform 6.10 adds a new grammar form, called GV2, which does away with
 * the pre-action table and preposition table entirely, and completely
 * changes the parse entry format.  Again, see the "Inform Technical Manual"
 * for further information.  Also note that Inform (in both GV1 and GV2)
 * uses the flags bytes in the dictionary entry in a slightly different
 * manner than Infocom games.
 *
 * Graphic (V6) Infocom games use a different grammar format.  The basic  
 * elements are mostly still there, but in a different set of tables.  
 * The table of pointers to the verb entries is gone.  Instead, the
 * first word of 'extra' dictionary information contains a pointer to the
 * verb entry. Pointers to the action and preaction tables are in
 * the next-to-last and last global variables respectively, but in practice 
 * the tables are in their usual location right after the verb grammar table,
 * which is in its usual location at the base of dynamic memory.  The 
 * verb grammar table has the following format
 *
 * Bytes 0-1: Action/pre-action index of the 0-object entry.  That is, action
 *            if this verb is used alone.  $FFFF if this verb cannot be used
 *            as a sentence in itself
 *
 * Bytes 2-3: Doesn't seem to be used.  Might be intended for actions with
 *            no objects but with a preposition.
 *
 * Bytes 4-5: Pointer to grammar entries for 1-object entries -- i.e. those
 *            of the form "verb [+ prep] + object"
 *
 * Bytes 6-7: Pointer to grammar entries for 2-object entries -- i.e. those
 *            of the form "verb [+ prep] + object [+ prep] + object"
 *
 * The grammar entries area is new.  Each item contains data of the following
 * format:
 *
 * Bytes 0-1: Number of entries in this item.  Entries immediately follow
 * For each entry in the item:
 * Bytes 0-1: Action/pre-action index for this item.
 * Bytes 2-3: Byte address of the dictionary word for the preposition
 *            $0000 if no preposition.
 *
 * Byte    4: Attribute # associated with this entry.  This does not appear
 *            to be used by the parser itself, but instead by the helper
 *            which suggests possible commands, in order to suggest
 *            sensible ones.  Actually verifying that the object has the
 *            attribute seems to be left to the action routine.
 *
 * Byte    5: I'm not sure about this one.  $80 appears to mean anything can
 *            be used, particularly including quoted strings.  $0F seems to
 *            mean an object in scope.  $14 may mean an object being held. I
 *            suspect it's a flags byte.
 *
 * Bytes 6-7: (Two object entries only) Same as bytes 2-3, for second preposition
 * Bytes 8-9: (Two object entries only) Same as bytes 4-5, for second object
 *
 *
 * Note also that the dictionary flags have moved from the first to the last byte
 * of each dictionary entry, and that while Zork Zero has only three bytes of
 * extra dictionary data (as with V1-5), Shogun and Arthur have four.
 * Also, I believe there is more grammar data than I've listed here, though how 
 * much is for the parser proper and how much for the helper I don't know -- MTR
 *
 * Journey has no grammar.
 *
 */

#ifdef __STDC__
void configure_parse_tables (unsigned int *verb_count,
                             unsigned int *action_count,
                             unsigned int *parse_count,
                             unsigned int *parser_type,
                             unsigned int *prep_type,
                             unsigned long *verb_table_base,
                             unsigned long *verb_data_base,
                             unsigned long *action_table_base,
                             unsigned long *preact_table_base,
                             unsigned long *prep_table_base,
                             unsigned long *prep_table_end)
#else
void configure_parse_tables (verb_count,
                             action_count,
                             parse_count,
                             parser_type,
                             prep_type,
                             verb_table_base,
                             verb_data_base,
                             action_table_base,
                             preact_table_base,
                             prep_table_base,
                             prep_table_end)
unsigned int *verb_count;
unsigned int *action_count;
unsigned int *parse_count;
unsigned int *parser_type;
unsigned int *prep_type;
unsigned long *verb_table_base;
unsigned long *verb_data_base;
unsigned long *action_table_base;
unsigned long *preact_table_base;
unsigned long *prep_table_base;
unsigned long *prep_table_end;
#endif
{
    unsigned long address, first_entry, second_entry, verb_entry;
    unsigned int entry_count, object_count, prep_count, action_index;
    unsigned int parse_index, val;
    int i, j;

    *verb_table_base = 0;
    *verb_data_base = 0;
    *action_table_base = 0;
    *preact_table_base = 0;
    *prep_table_base = 0;
    *prep_table_end = 0;
    *verb_count = 0;
    *action_count = 0;
    *parser_type = 0;
    *prep_type = 0;

    if (header.serial[0] >= '0' && header.serial[0] <= '9' &&
        header.serial[1] >= '0' && header.serial[1] <= '9' &&
        header.serial[2] >= '0' && header.serial[2] <= '1' &&
        header.serial[3] >= '0' && header.serial[3] <= '9' &&
        header.serial[4] >= '0' && header.serial[4] <= '3' &&
        header.serial[5] >= '0' && header.serial[5] <= '9' &&
        header.serial[0] != '8') {
        *parser_type = inform5_grammar;

        if (header.name[4] >= '6')
                *parser_type = inform_gv1;
    }

    if ((*parser_type < inform5_grammar) && (unsigned int) header.version == V6) {

        unsigned long word_address, first_word, last_word;
        unsigned short word_size, word_count;
        unsigned long vbase, vend;
        unsigned long area2base, area2end;
        unsigned long parse_address;

        *parser_type = infocom6_grammar;
        address = header.objects - 4;
        *action_table_base = (unsigned short)read_data_word(&address);
        *preact_table_base = (unsigned short)read_data_word(&address);

        /* Calculate dictionary bounds and entry size */

        address = (unsigned long) header.dictionary;
        address += (unsigned long) read_data_byte (&address);
        word_size = read_data_byte (&address);
        word_count = read_data_word (&address);
        first_word = address;
        last_word = address + ((word_count - 1) * word_size);

        vbase = area2base = 0xFFFF;
        vend = area2end = 0;

        for (word_address = first_word; word_address <= last_word; word_address += word_size) {
            address = word_address + 6;
            parse_index = (unsigned short)read_data_word(&address);
            address = word_address + word_size - 1;
            val = read_data_byte(&address); /* flags */
            if ((val&1) && !(val & 0x80) && (parse_index != 0) && (parse_index < *action_table_base)) { /* dictionary verb */
                if (vbase > parse_index)
                        vbase = parse_index;
                if (vend <= parse_index)
                        vend = parse_index + 8;
                address = parse_index + 4;

                /* retrieve direct-object only parse entries */
                parse_address = (unsigned short)read_data_word(&address);
                if (parse_address && (area2base > parse_address))
                        area2base = parse_address;

                if (parse_address && (area2end <= parse_address)) {
                        val = (unsigned short)read_data_word(&parse_address);
                        area2end = (parse_address + 6 * val);
                }

                /* retrieve indrect-object parse entries */
                parse_address = (unsigned short)read_data_word(&address);
                if (parse_address && (area2base > parse_address))
                        area2base = parse_address;

                if (parse_address && (area2end <= parse_address)) {
                        val = (unsigned short)read_data_word(&parse_address);
                        area2end = (parse_address + 10 * val);
                }
            }
        }
        if (vend == 0) /* no verbs */
                return;
        *verb_count = (vend - vbase)/8;
        *verb_table_base = vbase;
        *verb_data_base = area2base;
        /* there is no preposition table, but *prep_table_base bounds the verb data area */
        *prep_table_base = area2end;
        *prep_table_end = area2end;
        *action_count = (*preact_table_base - *action_table_base) / 2;
        return;
    }

   /* Start of table comes from the header */

    *verb_table_base = (unsigned long) header.dynamic_size;

    /*
     * Calculate the number of verb entries in the table. This can be done
     * because the verb entries immediately follow the verb table.
     */

    address = *verb_table_base;
    first_entry = read_data_word (&address);
    if (first_entry == 0) /* No verb entries at all */
        return;
    *verb_count = (unsigned int) ((first_entry - *verb_table_base) / sizeof (zword_t));

    /*
     * Calculate the form of the verb parse table entries. Basically,
     * Infocom used two types of table. The first types have 8 bytes per
     * entry, and the second type has a variable sized amount of data per
     * entry. In addition, Inform uses two new types of table. We look at
     * the serial number to distinguish Inform story files from Infocom
     * games, and we look at the last header entry to identify Inform 6
     * story files because Inform 6 writes its version number into the
     * last four bytes of this entry.
     */

    /*
     * Inform 6.10 addes an additional table format, called GV2.  GV1 is the
     * Inform 6.0-6.05 format, and is essentially similar to the Inform 5
     * format except that the parsing routine table is not padded out
     * to the length of the action table.
     * Infocom: parser_type = 0,1
     * Inform 1?-5: parser_type = 2
     * Inform 6 GV1: parser_type = 3
     * Inform 6 GV2: parser_type = 4
     */

    address = *verb_table_base;
    first_entry = read_data_word (&address);
    second_entry = read_data_word (&address);
    *verb_data_base = first_entry;
    entry_count = (unsigned int) read_data_byte (&first_entry);

    if (*parser_type < inform5_grammar) {
        *parser_type = infocom_fixed;

        if (((second_entry - first_entry) / entry_count) <= 7)
            *parser_type = infocom_variable;
    }

    /* Distinguishing between GV1 and GV2 isn't trivial.
       Here I check the length of the first entry.  It will be 1 mod 3
       for GV2 and 1 mod 8 for GV1. If it's 1 mod 24, first I check to see if
       its length matches the GV1 length.  Then I check for illegal GV1 values. 
       If they aren't found, I assume GV1.  I believe it is actually possible for
       a legal (if somewhat nonsensical) GV1 table to be the same as a legal GV2
       table, but I haven't actually constructed such a weird table.  In practice,
       the ENDIT (15) byte of the GV2 table will probably cause an illegal token
       if the table is interpreted as GV1 -- MTR.
    */

    if (*parser_type == inform_gv1) {
        first_entry = *verb_data_base;
        if (((second_entry - first_entry) % 3) == 1) {
            entry_count = read_data_byte (&first_entry);
            if ((entry_count * 8 + 1) == (second_entry - first_entry)) {
                /* this is the most ambiguous case */
                for (i = 0; i < entry_count && (*parser_type == inform_gv1); i++) {
                    if (read_data_byte (&first_entry) > 6) {
                        *parser_type = inform_gv2;
                        break;
                    }
                    for (j = 1; j < 7; j++) {
                        val = read_data_byte (&first_entry);
                        if ((val >= 9) || (val <= 15) || (val >= 112) || (val <= 127)) {
                                *parser_type = inform_gv2;
                                break;
                        }
                    }
                    read_data_byte (&first_entry); /* action number.  This can be anything */
                }
            }
            else {
                    *parser_type = inform_gv2;
            }
        }
        else if (((second_entry - first_entry) % 8) != 1) {
            fprintf(stderr, "Grammar table illegal size!");
        }
    }

    /*
     * Make a pass through the verb parse table looking at the pre-action and
     * action routine indices. We need to know what the highest index is to
     * find the size of the pre-action and action tables. Before Inform 6
     * both tables had the same size. For Inform 6 story files we also need
     * to know the number of parsing routines that occupy the pre-action
     * table (instead of pre-actions).
     */

    *action_count = 0;
    *parse_count = 0;
    address = *verb_table_base;
    for (i = 0; (unsigned int) i < *verb_count; i++) {
        verb_entry = (unsigned long) read_data_word (&address);
        entry_count = (unsigned int) read_data_byte (&verb_entry);
        while (entry_count--) {
            if (*parser_type == infocom_fixed) {
                verb_entry += 7;
                action_index = (unsigned int) read_data_byte (&verb_entry);
            } else if (*parser_type == infocom_variable) {
                object_count = (unsigned int) read_data_byte (&verb_entry);
                action_index = (unsigned int) read_data_byte (&verb_entry);
                verb_entry += verb_sizes[(object_count >> 6) & 0x03] - 2;
            } else if ((*parser_type == inform_gv1) || (*parser_type == inform5_grammar)) {
                /* GV1 */
                object_count = (unsigned int) read_data_byte (&verb_entry);
                for (j = 0; j < 6; j++) {
                    val = read_data_byte (&verb_entry);
                    if (val < 16 || val >= 112)
                        continue;
                    parse_index = (val - 16) % 32;
                    if (parse_index > *parse_count)
                        *parse_count = parse_index;
                }
                action_index = (unsigned int) read_data_byte (&verb_entry);
            }
            else {
                /* GV2 */
                action_index = (unsigned int) (read_data_word (&verb_entry) & 0x3FF);
                val = read_data_byte (&verb_entry);
                while (val != 15) {
                        read_data_byte (&verb_entry);
                        read_data_byte (&verb_entry);
                        val = read_data_byte (&verb_entry);
                }
            }
            if (action_index > *action_count)
                *action_count = action_index;
        }
    }
    (*action_count)++;
    if ((*parser_type == inform_gv1) || (*parser_type == inform5_grammar))
        (*parse_count)++;

    while ((unsigned int) read_data_byte (&verb_entry) == 0) /* Skip padding, if any */
        ;

    /*
     * Set the start addresses of the pre-action and action routines tables
     * and the preposition table.
     */

    *action_table_base = verb_entry - 1;
    *preact_table_base = *action_table_base + (*action_count * sizeof (zword_t));

    if (*parser_type >= inform_gv2) {
        /* GV2 has neither preaction/parse table nor preposition table */
        *prep_table_base =  *preact_table_base;
        *prep_table_end =  *preact_table_base;
    }
    else {
            if (*parser_type < inform_gv1)
                *prep_table_base = *preact_table_base + (*action_count * sizeof (zword_t));
            else
                *prep_table_base = *preact_table_base + (*parse_count * sizeof (zword_t));

            /*
             * Set the preposition table type by looking to see if the byte index
             * is stored in a word (an hence the upper 8 bits are zero).
             */

            address = *prep_table_base;
            prep_count = (unsigned int) read_data_word (&address);
            address += 2; /* Skip first address */
            if ((unsigned int) read_data_byte (&address) == 0) {
                *prep_type = 0;
                *prep_table_end = *prep_table_base + 2 + (4 * prep_count) - 1;
            } else {
                *prep_type = 1;
                *prep_table_end = *prep_table_base + 2 + (3 * prep_count) - 1;
            }
    }

}/* configure_parse_tables */

/*
 * show_verbs
 *
 * Display the verb parse tables, sentence structure, action routines and
 * prepositions.
 */

#ifdef __STDC__
void show_verbs (int symbolic)
#else
void show_verbs (symbolic)
int symbolic;
#endif
{
    unsigned long verb_table_base, verb_data_base;
    unsigned long action_table_base, preact_table_base;
    unsigned long prep_table_base, prep_table_end;
    unsigned int verb_count, action_count, parse_count, parser_type, prep_type;

    unsigned int obj_count;
    unsigned long obj_table_base, obj_table_end, obj_data_base, obj_data_end;
    unsigned int inform_version;
    unsigned long class_numbers_base, class_numbers_end;
    unsigned long property_names_base, property_names_end;
    unsigned long attr_names_base, attr_names_end;
    unsigned long action_names_base;

    /* Get parse table configuration */

    configure_parse_tables (&verb_count, &action_count, &parse_count, &parser_type, &prep_type,
                            &verb_table_base, &verb_data_base,
                            &action_table_base, &preact_table_base,
                            &prep_table_base, &prep_table_end);

    /* I wonder weather you can guess which author required the following test? */

    if (verb_count == 0) {
        tx_printf ("\n    **** There are no parse tables ****\n\n");
        tx_printf ("  Verb entries = 0\n\n");

        return;
    }

    if (symbolic) {
        configure_object_tables (&obj_count, &obj_table_base, &obj_table_end,
                          &obj_data_base, &obj_data_end);
        configure_inform_tables(obj_data_end, &inform_version, &class_numbers_base, &class_numbers_end,
                            &property_names_base, &property_names_end, &attr_names_base, &attr_names_end);
    }
    else {
        attr_names_base = property_names_base = class_numbers_base = 0;
    }

    action_names_base = attr_names_base?attr_names_end + 1:0;

    /* Display parse data */

    show_verb_parse_table (verb_table_base, verb_count, parser_type,
                           prep_type, prep_table_base, attr_names_base);

    /* Display action routines */

    show_action_tables (verb_table_base,
                        verb_count, action_count, parse_count, parser_type, prep_type,
                        action_table_base, preact_table_base,
                        prep_table_base, attr_names_base, action_names_base);

    /* Display prepositions */
    if ((parser_type <= inform_gv2) && (parser_type != infocom6_grammar)) /* no preposition table in GV2 */
            show_preposition_table (prep_type, prep_table_base, parser_type);

}/* show_verbs */

/*
 * show_verb_parse_table
 *
 * Display the parse information associated with each verb. The entry into the
 * table is found from the dictionary. Each verb has a parse table entry index.
 * These indices range from 255 to 0*. Each parse table entry can have one or
 * more sentence formats associated with the verb. Once the verb and sentence
 * structure match, an index taken from the parse data is used to index into the
 * pre-action and action routine tables. This format allows multiple similar
 * verb and sentence structures to parse to the same action routine.
 * * 0 to 65535 in GV2
 *
 * Synonyms for each verb are also show. The first verb in the dictionary is
 * used in the sentence structure text. This can lead to bizarre looking
 * sentences, but they all work!
 *
 * The index used to find the action routine is the same number printed when
 * debugging is turned on in games that support this. The number is printed as
 * performing: nn
 */

#ifdef __STDC__
static void show_verb_parse_table (unsigned long verb_table_base,
                                   unsigned int verb_count,
                                   unsigned int parser_type,
                                   unsigned int prep_type,
                                   unsigned long prep_table_base,
                                   unsigned long attr_names_base)
#else
static void show_verb_parse_table (verb_table_base,
                                   verb_count,
                                   parser_type,
                                   prep_type,
                                   prep_table_base,
                                   attr_names_base)
unsigned long verb_table_base;
unsigned int verb_count;
unsigned int parser_type;
unsigned int prep_type;
unsigned long prep_table_base;
unsigned long attr_names_base;
#endif
{
    unsigned long address, verb_entry, parse_entry;
    unsigned int entry_count, object_count, parse_data;
    int i, j, verb_size;

    tx_printf ("\n    **** Parse tables ****\n\n");
    tx_printf ("  Verb entries = %d\n", (int) verb_count);

    /* Go through each verb and print its parse information and grammar */

    address = verb_table_base;
    for (i = 0; (unsigned int) i < verb_count; i++) {

        /* Get start of verb entry and number of entries */

        if (parser_type == infocom6_grammar) {
            unsigned long do_address, doio_address;
            unsigned int verb_address;

            verb_address = (unsigned int)address; /* cast is guaranteed to work provided unsigned int >= 16 bits */
            tx_printf ("\n%3d. @ $%04x, verb = ", i, address);
            show_words ((unsigned int)address, 0L, VERB_V6, parser_type);
            tx_printf ("\n    Main data");
            tx_printf ("\n    [");
            parse_data = (unsigned int) read_data_word (&address);
            tx_printf ("%04x ", (unsigned int) parse_data);
            read_data_word (&address);  /* I don't know what this word does */
            tx_printf ("%04x ", (unsigned int) parse_data);
            do_address = (unsigned int) read_data_word (&address);
            tx_printf ("%04x ", (unsigned int) do_address);
            doio_address = (unsigned int) read_data_word (&address);
            tx_printf ("%04x", (unsigned int) doio_address);
            tx_printf ("] ");
            if (verb_entry != 0xFFFF)
                show_verb_grammar (parse_entry, verb_address, (int) parser_type, 0, 0, 0L, 0L);

            if (do_address) {
                tx_printf ("\n    One object entries:\n");
                verb_entry = do_address;
                entry_count = (unsigned int) read_data_word (&verb_entry);
                verb_size = 3; /* words */
                while (entry_count --) {
                    parse_entry = verb_entry;
                    tx_printf ("    [");
                    for (j = 0; j < verb_size; j++) {
                        parse_data = (unsigned int) read_data_word (&verb_entry);
                        tx_printf ("%04x", (unsigned int) parse_data);
                        if (j < (verb_size - 1))
                            tx_printf (" ");
                    }
                    tx_printf ("] ");
                    show_verb_grammar (parse_entry, verb_address, (int) parser_type, 1,
                               0, 0L, 0L);
                    tx_printf ("\n");
                }
            }
            if (doio_address) {
                tx_printf ("\n    Two object entries:\n");
                verb_entry = doio_address;
                entry_count = (unsigned int) read_data_word (&verb_entry);
                verb_size = 5; /* words */
                while (entry_count --) {
                    parse_entry = verb_entry;
                    tx_printf ("    [");
                    for (j = 0; j < verb_size; j++) {
                        parse_data = (unsigned int) read_data_word (&verb_entry);
                        tx_printf ("%04x", (unsigned int) parse_data);
                        if (j < (verb_size - 1))
                            tx_printf (" ");
                    }
                    tx_printf ("] ");
                    show_verb_grammar (parse_entry, verb_address, (int) parser_type, 2,
                               0, 0L, 0L);
                    tx_printf ("\n");
                }
            }
        }
        else { /* everything but Zork Zero, Shogun, and Arthur */
            verb_entry = (unsigned long) read_data_word (&address);
            entry_count = (unsigned int) read_data_byte (&verb_entry);

            /* Show the verb index, entry count, verb and synonyms */

            tx_printf ("\n%3d. %d entr%s, verb = ", (int) VERB_NUM(i, parser_type),
                       (int) entry_count, (entry_count == 1) ? "y" : "ies");
            show_words (VERB_NUM(i, parser_type), 0L, VERB, parser_type);
            tx_printf ("\n");

            /* Show parse data and grammar for each verb entry */

            while (entry_count--) {
                parse_entry = verb_entry;

                /* Calculate the amount of verb data */

                if (parser_type != infocom_variable) {
                    verb_size = 8;
                } else {
                    object_count = (unsigned int) read_data_byte (&parse_entry);
                    verb_size = verb_sizes[(object_count >> 6) & 0x03];
                    parse_entry = verb_entry;
                }

                /* Show parse data for each verb */

                tx_printf ("    [");

                if (parser_type < inform_gv2) {
                        for (j = 0; j < verb_size; j++) {
                            parse_data = (unsigned int) read_data_byte (&verb_entry);
                            tx_printf ("%02x", (unsigned int) parse_data);
                            if (j < (verb_size - 1))
                                tx_printf (" ");
                        }
                }
                else {
                    /* GV2 variable entry format
                       <flags and action high> <action low> n*(<token type> <token data 1> <token data 2>) <ENDIT>*/
                    for (j = 0; (j == 0) || (j%3 != 0) || (parse_data != ENDIT); j++) {
                            if (j != 0)
                                tx_printf (" ");
                            parse_data = (unsigned int) read_data_byte (&verb_entry);
                            tx_printf ("%02x", (unsigned int) parse_data);
                    }
                    verb_size = j;
                }
                tx_printf ("] ");
                for (; j < 8; j++)
                    tx_printf ("   ");

                /* Show the verb grammar for this entry */

                show_verb_grammar (parse_entry, VERB_NUM(i, parser_type), (int) parser_type, 0,
                                   (int) prep_type, prep_table_base, attr_names_base);
                tx_printf ("\n");
            }
        }
    }

}/* show_verb_parse_table */

/* show_syntax_of_action
 *
 * Display the syntax entries for a given action number.  Used by
 * txd as well as by show_action_tables.  A pre-action number works as well
 * (because they are the same as action numbers), but not a parsing routine
 * number (see show_syntax_of_parsing_routine)
 *
 */

#ifdef __STDC__
void show_syntax_of_action(     int action,
                                unsigned long verb_table_base,
                                unsigned int verb_count,
                                unsigned int parser_type,
                                unsigned int prep_type,
                                unsigned long prep_table_base,
                                unsigned long attr_names_base)
#else
void show_syntax_of_action(     action,
                                verb_table_base,
                                verb_count,
                                parser_type,
                                prep_type,
                                prep_table_base,
                                attr_names_base)
int action;
unsigned long verb_table_base;
unsigned int verb_count;
unsigned int parser_type;
unsigned int prep_type;
unsigned long prep_table_base;
unsigned long attr_names_base;
#endif
{
    unsigned long address;
    unsigned long verb_entry, parse_entry;
    unsigned int entry_count, object_count, val, action_index;
    int i;
    int matched = 0;

    address = verb_table_base;
    for (i = 0; (unsigned int) i < verb_count; i++) {

        if (parser_type == infocom6_grammar) {
            unsigned long do_address, doio_address;
            unsigned int verb_address;

            verb_address = (unsigned int)address;
            parse_entry = address;
            action_index = read_data_word(&address);
            if (action_index == (unsigned int) action) {
                show_verb_grammar (parse_entry, verb_address, (int) parser_type, 0,
                                   (int) 0, 0L, 0L);
                tx_printf ("\n");
                matched = 1;
            }
            read_data_word(&address);
            do_address = read_data_word(&address);
            doio_address = read_data_word(&address);

            if (do_address) {
                verb_entry = do_address;
                entry_count = (unsigned int) read_data_word (&verb_entry);
                while (entry_count --) {
                    parse_entry = verb_entry;
                    action_index = read_data_word(&verb_entry);
                    if (action_index == (unsigned int) action) {
                        show_verb_grammar (parse_entry, verb_address, (int) parser_type, 1,
                               0, 0L, 0L);
                        tx_printf ("\n");
                        matched = 1;
                    }
                    verb_entry += 4; /* skip preposition and object */
                }
            }

            if (doio_address) {
                verb_entry = doio_address;
                entry_count = (unsigned int) read_data_word (&verb_entry);
                while (entry_count --) {
                    parse_entry = verb_entry;
                    action_index = read_data_word(&verb_entry);
                    if (action_index == (unsigned int) action) {
                        show_verb_grammar (parse_entry, verb_address, (int) parser_type, 2,
                               0, 0L, 0L);
                        tx_printf ("\n");
                        matched = 1;
                    }
                    verb_entry += 8; /* skip preposition and direct object and preposition and indirect object*/
                }
            }
        }       
        else {
            /* Get the parse data address for this entry */
        
            verb_entry = (unsigned long) read_data_word (&address);
            entry_count = (unsigned int) read_data_byte (&verb_entry);
        
            /* Look through the sentence structures looking for a match */
        
            while (entry_count--) { 
                parse_entry = verb_entry;
                if (parser_type >= inform_gv2) { /* GV2, variable length with terminator */
                    action_index = read_data_word(&verb_entry) & 0x3FF;
                    val = read_data_byte(&verb_entry);
                    while (val != ENDIT) {
                        read_data_word(&verb_entry);
                        val = read_data_byte(&verb_entry);
                    }   
                }
                else if (parser_type != infocom_variable) { /* Index is in last (8th) byte */
                    verb_entry += 7;
                    action_index = (unsigned int) read_data_byte (&verb_entry);
                } else { /* Index is in second byte */
                    object_count = (unsigned int) read_data_byte (&verb_entry);
                    action_index = (unsigned int) read_data_byte (&verb_entry);
                    verb_entry += verb_sizes[(object_count >> 6) & 0x03] - 2;
                }
        
                /* Check if this verb/sentence structure uses the action routine */
        
                if (action_index == (unsigned int) action) {
                    show_verb_grammar (parse_entry, VERB_NUM(i, parser_type), (int) parser_type, 0,
                                       (int) prep_type, prep_table_base, attr_names_base);
                    tx_printf ("\n");
                    matched = 1;
                }
            }
        }
    }
    if (!matched) {
        tx_printf ("\n");
    }
}

#ifdef __STDC__
int is_gv2_parsing_routine(unsigned long parsing_routine,
                                    unsigned long verb_table_base,
                                    unsigned int verb_count)
#else
int is_gv2_parsing_routine(parsing_routine,
                                    verb_table_base,
                                    verb_count)
unsigned long parsing_routine;
unsigned long verb_table_base;
unsigned int verb_count;
#endif
{
    unsigned long address;
    unsigned long verb_entry;
    unsigned short token_data;
    unsigned int entry_count, val;
    int i, found;
    unsigned long parsing_routine_packed = (parsing_routine - (unsigned long) story_scaler * header.routines_offset)/ code_scaler;

    address = verb_table_base;
    found = 0;
    for (i = 0; !found && (unsigned int) i < verb_count; i++) {

        /* Get the parse data address for this entry */

        verb_entry = (unsigned long) read_data_word (&address);
        entry_count = (unsigned int) read_data_byte (&verb_entry);
        while (!found && entry_count--) {
            read_data_word(&verb_entry); /* skip action # and flags */
            val = (unsigned int) read_data_byte (&verb_entry);
            while (val != ENDIT) {
                token_data = read_data_word(&verb_entry);
                if (((val & 0xC0) == 0x80) && (token_data == parsing_routine_packed))
                    found = 1;
                val = (unsigned int) read_data_byte (&verb_entry);
            }
        }
    }
    return found;
}

/* show_syntax_of_parsing_routine
 *
 * Display the syntax entries for a given parsing routine number or address.  Used by
 * txd as well as by show_action_tables. For Inform 5 and GV1, the input should be
 * the parsing routine number.  For GV2, it should be the parsing routine address.
 *
 */

#ifdef __STDC__
void show_syntax_of_parsing_routine(unsigned long parsing_routine,
                                    unsigned long verb_table_base,
                                    unsigned int verb_count,
                                    unsigned int parser_type,
                                    unsigned int prep_type,
                                    unsigned long prep_table_base,
                                    unsigned long attr_names_base)
#else
void show_syntax_of_parsing_routine(parsing_routine,
                                    verb_table_base,
                                    verb_count,
                                    parser_type,
                                    prep_type,
                                    prep_table_base,
                                    attr_names_base)
unsigned long parsing_routine;
unsigned long verb_table_base;
unsigned int verb_count;
unsigned int parser_type;
unsigned int prep_type;
unsigned long prep_table_base;
unsigned long attr_names_base;
#endif
{
    unsigned long address;
    unsigned long verb_entry, parse_entry;
    unsigned short token_data;
    unsigned int entry_count, object_count, val;
    unsigned long parsing_routine_packed = (parsing_routine - (unsigned long) story_scaler * header.routines_offset)/ code_scaler;
    int i, found;

    address = verb_table_base;
    for (i = 0; (unsigned int) i < verb_count; i++) {

        /* Get the parse data address for this entry */

        verb_entry = (unsigned long) read_data_word (&address);
        entry_count = (unsigned int) read_data_byte (&verb_entry);
        while (entry_count--) {
            parse_entry = verb_entry;
            found = 0;
            if (parser_type < inform_gv2) {
                object_count = (unsigned int) read_data_byte (&verb_entry);
                while (object_count) {
                    val = (unsigned int) read_data_byte (&verb_entry);
                    if (val < 0xb0) {
                        object_count--;
                        if (val >= 0x10 && val < 0x70 && ((val - 0x10) & 0x1f) == (unsigned int) parsing_routine)
                            found = 1;
                    }
                }
                verb_entry = parse_entry + 8;
            }
            else {
                read_data_word(&verb_entry); /* skip action # and flags */
                val = (unsigned int) read_data_byte (&verb_entry);
                while (val != ENDIT) {
                    token_data = read_data_word(&verb_entry);
                    if (((val & 0xC0) == 0x80) && (token_data == parsing_routine_packed)) /* V7/V6 issue here */
                        found = 1;
                    val = (unsigned int) read_data_byte (&verb_entry);
                }
            }
            if (found) {
                show_verb_grammar (parse_entry, VERB_NUM(i, parser_type), (int) parser_type, (int) prep_type, 0,
                                   prep_table_base, attr_names_base);
                tx_printf ("\n");
            }
        }
    }
}

/*
 * show_action_tables
 *
 * Display the pre-action and action routine addresses. The list of
 * verb/sentence structures is displayed with each routine. A list of
 * verb/sentence structures against each routine indicate that the routine
 * is called when any of the verb/sentence structures are typed. Inform
 * written games, however, do not have a concept of pre-actions. Their
 * pre-actions table is filled with so-called parsing routines which
 * are linked to single objects within verb/sentence structures. Usually
 * these routines decide if a specific object or text matches these
 * sentence structures.
 */

#ifdef __STDC__
static void show_action_tables (unsigned long verb_table_base,
                                unsigned int verb_count,
                                unsigned int action_count,
                                unsigned int parse_count,
                                unsigned int parser_type,
                                unsigned int prep_type,
                                unsigned long action_table_base,
                                unsigned long preact_table_base,
                                unsigned long prep_table_base,
                                unsigned long attr_names_base,
                                unsigned long action_names_base)
#else
static void show_action_tables (verb_table_base,
                                verb_count,
                                action_count,
                                parse_count,
                                parser_type,
                                prep_type,
                                action_table_base,
                                preact_table_base,
                                prep_table_base,
                                attr_names_base,
                                action_names_base)
unsigned long verb_table_base;
unsigned int verb_count;
unsigned int action_count;
unsigned int parse_count;
unsigned int parser_type;
unsigned int prep_type;
unsigned long action_table_base;
unsigned long preact_table_base;
unsigned long prep_table_base;
unsigned long attr_names_base;
unsigned long action_names_base;
#endif
{
    unsigned long actions_address, preacts_address;
    unsigned long routine_address;
    int action;

    tx_printf ("\n    **** Verb action routines ****\n\n");
    tx_printf ("  Action table entries = %d\n\n", (int) action_count);
    tx_printf ("action# ");
    if (parser_type <= infocom6_grammar)
        tx_printf ("pre-action-routine ");
    tx_printf ("action-routine \"verb...\"\n\n");

    actions_address = action_table_base;
    preacts_address = preact_table_base;

    /* Iterate through all routine entries for pre-action and action routines */

    for (action = 0; (unsigned int) action < action_count; action++) {

        /* Display the routine index and addresses */

        tx_printf ("%3d. ", (int) action);
        if (parser_type <= infocom6_grammar) {
            routine_address = (unsigned long) read_data_word (&preacts_address) * code_scaler;
            if (routine_address)
                routine_address += (unsigned long) story_scaler * header.routines_offset;
            tx_printf ("%5lx ", routine_address);
        }
        routine_address = (unsigned long) read_data_word (&actions_address) * code_scaler;
        if (routine_address)
            routine_address += (unsigned long) story_scaler * header.routines_offset;
        tx_printf ("%5lx ", routine_address);
        tx_printf (" ");
        tx_fix_margin (1);
        if (action_names_base) {
            tx_printf ("<");
            print_inform_action_name(action_names_base, action);
            tx_printf (">\n");
        }

        /*
         * Now scan down the parse table looking for all verb/sentence formats
         * that cause this action routine to be called.
         */
        show_syntax_of_action(  action,
                                verb_table_base,
                                verb_count,
                                parser_type,
                                prep_type,
                                prep_table_base,
                                attr_names_base);

        tx_fix_margin (0);
    }

    if ((parser_type >= inform5_grammar) && (parser_type < inform_gv2)) {

        /* Determine number of parsing routines (ie. the number of
           non-zero entries in the former pre-actions table) */

        tx_printf ("\n    **** Parsing routines ****\n\n");
        tx_printf ("  Number of parsing routines = %d\n\n", (int) parse_count);
        tx_printf ("parse# parsing-routine \"verb...\"\n\n");

        for (action = 0; (unsigned int) action < parse_count; action++) {

            /* Display the routine index and addresses */

            tx_printf ("%3d. ", (int) action);
            tx_printf ("%5lx ", (unsigned long) read_data_word (&preacts_address) * code_scaler + (unsigned long) story_scaler * header.routines_offset);
            tx_printf (" ");
            tx_fix_margin (1);
            /*
             * Now scan down the parse table looking for all verb/sentence formats
             * that this parsing routine applies to.
             */

            show_syntax_of_parsing_routine((unsigned long)action,
                                           verb_table_base,
                                           verb_count,
                                           parser_type,
                                           prep_type,
                                           prep_table_base,
                                           attr_names_base);
            tx_fix_margin (0);
        }
    }

}/* show_action_tables */

/*
 * show_preposition table
 *
 * Displays all the prepositions and their synonyms. The preposition index can
 * be found in the sentence structure data in the parse tables.
 */

#ifdef __STDC__
static void show_preposition_table (unsigned int prep_type,
                                    unsigned long prep_table_base,
                                    unsigned int parser_type)
#else
static void show_preposition_table (prep_type,
                                    prep_table_base,
                                    parser_type)
unsigned int prep_type;
unsigned long prep_table_base;
unsigned int parser_type;
#endif
{
    unsigned long address, prep_address;
    unsigned int count, prep_index;
    int i;

    /* Get the base address and count of prepositions */

    address = prep_table_base;
    count = (unsigned int) read_data_word (&address);

    tx_printf ("\n    **** Prepositions ****\n\n");
    tx_printf ("  Table entries = %d\n\n", (int) count);

    /* Iterate through all prepositions */

    for (i = 0; (unsigned int) i < count; i++) {

        /* Read the dictionary address of the text for this entry */

        prep_address = read_data_word (&address);

        /* Pick up the index */

        if (prep_type == 0)
            prep_index = (unsigned int) read_data_word (&address);
        else
            prep_index = (unsigned int) read_data_byte (&address);

        /* Display index and word */

        tx_printf ("%3d. ", (int) prep_index);
        show_words (prep_index, prep_address, PREP, parser_type);
        tx_printf ("\n");
    }

}/* show_preposition_table */

/*
 * show_words
 *
 * Display any verb/preposition and synonyms by index. Inform written games
 * do not have synonyms for prepositions.
 */

#ifdef __STDC__
static void show_words (unsigned int indx,
                        unsigned long prep_address,
                        unsigned int type,
                        unsigned int parser_type)
#else
static void show_words (indx, prep_address, type, parser_type)
unsigned int indx;
unsigned long prep_address;
unsigned int type;
unsigned int parser_type;
#endif
{
    unsigned long address, word_address;
    int flag = 0;

    /* If this is a preposition then we have an address */

    if (type == PREP)
        word_address = prep_address;
    else
        word_address = lookup_word (0L, indx, type, parser_type);

    /* If the word address is NULL then there are no entries */

    if (word_address == 0) {
        tx_printf (" no-");
        if ((type == VERB) || (type == VERB_V6))
            tx_printf ("verb");
        if (type == PREP)
            tx_printf ("preposition");
    }

    /* Display all synonyms for the verb or preposition */

    for (flag = 0; word_address; flag++) {
        if (flag)
            tx_printf (", ");
        if (flag == 1) {
            tx_printf ("synonyms = ");
            tx_fix_margin (1);
        }

        /* Display the current word */

        address = word_address;
        tx_printf ("\"");
        (void) decode_text (&address);
        tx_printf ("\"");

        /* Lookup the next synonym (but skip the word itself) */

        if (type == PREP && flag == 0)
            word_address = 0;
        if (type != PREP || parser_type <= infocom_variable) {
            word_address = lookup_word (word_address, indx, type, parser_type);
            if (type == PREP && word_address == prep_address)
                word_address = lookup_word (word_address, indx, type, parser_type);
        }
    }
    if (flag)
        tx_fix_margin (0);

}/* show_words */

/*
 * show_verb_grammar
 *
 * Display the sentence structure associated with a parse table entry.
 */

#ifdef __STDC__
void show_verb_grammar (unsigned long verb_entry,
                        unsigned int verb_index,
                        int parser_type,
                        int v6_number_objects,
                        int prep_type,
                        unsigned long prep_table_base,
                        unsigned long attr_names_base)
#else
void show_verb_grammar (verb_entry,
                        verb_index,
                        parser_type,
                        v6_number_objects,
                        prep_type,
                        prep_table_base,
                        attr_names_base)
unsigned long verb_entry;
unsigned int verb_index;
int parser_type;
int prep_type;
unsigned long prep_table_base;
#endif
{
    unsigned long address, verb_address, prep_address;
    unsigned int parse_data, objs, preps[2], val;
    unsigned int token_type, token_data, action;
    int i;
    static char *GV2_elementary[] = {"noun" ,"held", "multi", "multiheld",
                                        "multiexcept", "multiinside", "creature",
                                        "special", "number", "topic" };
    enum gv2_tokentype {TT_ILLEGAL, TT_ELEMENTARY, TT_PREPOSITION, TT_NOUNR, TT_ATTRIBUTE, TT_SCOPER, TT_ROUTINE};

    address = verb_entry;

    if (parser_type == infocom6_grammar) {
        tx_printf ("\"");
        verb_address = lookup_word (0L, verb_index, VERB_V6, parser_type);
        if (verb_address)
            (void) decode_text (&verb_address);
        else
            tx_printf ("no-verb");
        
        if (v6_number_objects > 0) {
            tx_printf(" ");

            action = read_data_word(&address);
            while (v6_number_objects--) {
                token_data = read_data_word(&address);
                token_type = read_data_word(&address);
                if (token_data) {
                        prep_address = token_data;
                        decode_text(&prep_address);
                        tx_printf(" ");
                }
#if 0
                tx_printf("$%04x", token_type);  /* turn this on if you want to see the attribute and flag? info for the object */
#else
                tx_printf("OBJ");
#endif
                if (v6_number_objects)
                  tx_printf(" ");
            }
        }
        tx_printf ("\"");
    }
    else if (parser_type >= inform_gv2) {
        /* Inform 6 GV2 verb entry */
        
        tx_printf ("\"");

        /* Print verb if one is present */

        verb_address = lookup_word (0L, verb_index, VERB, parser_type);

        if (verb_address)
            (void) decode_text (&verb_address);
        else
            tx_printf ("no-verb");

        action = read_data_word(&address); /* Action # and flags*/
        
        val = read_data_byte(&address);
        while (val != ENDIT) {
            if (((val & 0x30) == 0x10) || ((val & 0x30) == 0x30)) /* 2nd ... nth byte of alternative list */
                tx_printf(" /");
            tx_printf(" ");
            token_type = val&0xF;
            token_data = read_data_word(&address);
            switch (token_type) {
                case TT_ELEMENTARY: 
                    if (token_data < (sizeof(GV2_elementary)/ sizeof (char *)))
                        tx_printf(GV2_elementary[token_data]);
                    else
                        tx_printf("UNKNOWN_ELEMENTARY");
                    break;
                case TT_PREPOSITION:
                    prep_address = token_data;
                    decode_text(&prep_address);
                    break;
                case TT_NOUNR:
                    tx_printf("noun = [parse $%04x]", token_data);
                    break;
                case TT_ATTRIBUTE:
                    tx_printf("ATTRIBUTE(");
                    if (!print_attribute_name(attr_names_base, token_data)) {
                        tx_printf("%d", token_data);
                    }
                    tx_printf(")", token_data);
                    break;
                case TT_SCOPER:
                    tx_printf("scope = [parse $%04x]", token_data);
                    break;
                case TT_ROUTINE:
                    tx_printf("[parse $%04x]", token_data);
                    break;
                default:
                    tx_printf("UNKNOWN");
            }
            val = read_data_byte(&address);
        }
        tx_printf ("\"");
        if (action & 0x0400)
            tx_printf(" REVERSE");
    }
    else if (parser_type >= inform5_grammar) {

        /* Inform 5 and GV1 verb entries are just a series of tokens */

        tx_printf ("\"");

        /* Print verb if one is present */

        verb_address = lookup_word (0L, verb_index, VERB, parser_type);

        if (verb_address)
            (void) decode_text (&verb_address);
        else
            tx_printf ("no-verb");

        objs = read_data_byte (&address);

        for (i = 0; i < 8; i++) {
            val = read_data_byte (&address);
            if (val < 0xb0) {
                if (val == 0 && objs == 0)
                    break;
                tx_printf (" ");
                if (val == 0)
                    tx_printf ("NOUN");
                else if (val == 1)
                    tx_printf ("HELD");
                else if (val == 2)
                    tx_printf ("MULTI");
                else if (val == 3)
                    tx_printf ("MULTIHELD");
                else if (val == 4)
                    tx_printf ("MULTIEXCEPT");
                else if (val == 5)
                    tx_printf ("MULTIINSIDE");
                else if (val == 6)
                    tx_printf ("CREATURE");
                else if (val == 7)
                    tx_printf ("SPECIAL");
                else if (val == 8)
                    tx_printf ("NUMBER");
                else if (val >= 16 && val < 48)
                    tx_printf ("NOUN [parse %d]", val - 16);
                else if (val >= 48 && val < 80)
                    tx_printf ("TEXT [parse %d]", val - 48);
                else if (val >= 80 && val < 112)
                    tx_printf ("SCOPE [parse %d]", val - 80);
                else if (val >= 128 && val < 176) {
                    tx_printf ("ATTRIBUTE(");
                    if (!print_attribute_name(attr_names_base, val - 128)) {
                        tx_printf("%d", val - 128);
                    }
                    tx_printf (")");
                }
                else
                    tx_printf ("UNKNOWN");
                objs--;
            } else {
                tx_printf (" ");
                show_preposition (val, prep_type, prep_table_base);
            }
        }

        tx_printf ("\"");

    } else {

        address = verb_entry;
        preps[0] = preps[1] = 0;

        /* Calculate noun count and prepositions */

        if (parser_type == infocom_fixed) {

            /* Fixed length parse table format */

            /* Object count in 1st byte, preposition indices in next two bytes */

            objs = (unsigned int) read_data_byte (&address);
            preps[0] = (unsigned int) read_data_byte (&address);
            preps[0] = (preps[0] >= 0x80) ? preps[0] : 0;
            preps[1] = (unsigned int) read_data_byte (&address);
            preps[1] = (preps[1] >= 0x80) ? preps[1] : 0;
        } else {

            /* Variable length parse table format */

            /* Object count in top two bits of first byte */

            parse_data = (unsigned int) read_data_byte (&address);
            objs = (parse_data >> 6) & 0x03;

            /* 1st preposition in bottom 6 bits of first byte. Fill in top two bits */

            preps[0] = (parse_data & 0x3f) ? parse_data | 0xc0 : 0;
            parse_data = (unsigned int) read_data_byte (&address);

            /* Check for more than one object */

            if (objs > 0) {

                /* Skip object data */

                parse_data = (unsigned int) read_data_byte (&address);
                parse_data = (unsigned int) read_data_byte (&address);

                /* Check for more than two objects */

                if (objs > 1) {

                    /* 2nd preposition in bottom 6 bits of byte. Fill in top two bits */

                    parse_data = (unsigned int) read_data_byte (&address);
                    preps[1] = (parse_data & 0x3f) ? parse_data | 0xc0 : 0;
                }
            }
        }

        /* Check that there are 0 - 2 objects only */

        if (objs > 2) {

            tx_printf ("Bad object count (%d)", (int) objs);

        } else {

            tx_printf ("\"");

            /* Print verb if one is present */

            verb_address = lookup_word (0L, verb_index, VERB, parser_type);

            if (verb_address)
                (void) decode_text (&verb_address);
            else
                tx_printf ("no-verb");

            /* Display any prepositions and objects if present */

            for (i = 0; i < 2; i++) {
                if (preps[i] != 0) {
                    tx_printf (" ");
                    show_preposition (preps[i], prep_type, prep_table_base);
                }
                if (objs > (unsigned int) i)
                    tx_printf (" OBJ");
            }

            tx_printf ("\"");

        }
    }

}/* show_verb_grammar */

/*
 * show_preposition
 *
 * Display a preposition by index.
 */

#ifdef __STDC__
static void show_preposition (unsigned int prep,
                              int prep_type,
                              unsigned long prep_table_base)
#else
static void show_preposition (prep,
                              prep_type,
                              prep_table_base)
unsigned int prep;
int prep_type;
unsigned long prep_table_base;
#endif
{
    unsigned long address, text_address;
    unsigned int prep_count, prep_num;
    int i;

    address = prep_table_base;
    prep_count = (unsigned int) read_data_word (&address);

    /* Iterate through the preposition table looking for a match */

    for (i = 0; (unsigned int) i < prep_count; i++) {
        text_address = read_data_word (&address);
        if (prep_type == 0)
            prep_num = (unsigned int) read_data_word (&address);
        else
            prep_num = (unsigned int) read_data_byte (&address);

        /* If the indices match then print the preposition text */

        if (prep == prep_num) {
            (void) decode_text (&text_address);
            return;
        }
    }

}/* show_preposition */

/*
 * lookup_word
 *
 * Look up a word in the dictionary based on its type; verb, preposition, etc.
 * The return entry is used to restart the search from the last word found.
 */

#ifdef __STDC__
static unsigned long lookup_word (unsigned long entry,
                                  unsigned int number,
                                  unsigned int mask,
                                  unsigned int parser_type)
#else
static unsigned long lookup_word (entry, number, mask, parser_type)
unsigned long entry;
unsigned int number;
unsigned int mask;
unsigned int parser_type;
#endif
{
    unsigned long address, word_address, first_word, last_word;
    unsigned int word_count, word_size, flags, data;

    /* Calculate dictionary bounds and entry size */

    address = (unsigned long) header.dictionary;
    address += (unsigned long) read_data_byte (&address);
    word_size = read_data_byte (&address);
    word_count = read_data_word (&address);
    first_word = address;
    last_word = address + ((word_count - 1) * word_size);

    /* If entry is 0 then set to first word, otherwise advance to next word */

    if (entry == 0)
        entry = first_word;
    else
        entry += word_size;

    /* Correct Inform verb mask -- Inform sets both 0x40 and 0x01, but only 0x01 is documented */
    if ((mask == VERB) && (parser_type >= inform5_grammar))
        mask = VERB_INFORM;
    
    /* Scan down the dictionary from entry looking for a match */

    for (word_address = entry; word_address <= last_word; word_address += word_size) {

        /* Skip to flags byte and read it */

        if (parser_type != infocom6_grammar) {
            address = word_address + (((unsigned int) header.version < V4) ? 4 : 6);
            flags = read_data_byte (&address);
        }
        else {
            address = word_address + word_size - 1;
            flags = read_data_byte (&address);
            address = word_address + 6;
        }

        /* Check if this word is the type we are looking for */

        if (flags & mask) {

            if ((parser_type == infocom6_grammar) || (parser_type >= inform_gv2a)) {
                    data = (unsigned int) read_data_word (&address);
            }
            else if (parser_type <= inform_gv1) {
                /* Infocom, Inform 5, GV1.  Verbs only for Inform */
                    /* Read the data for the word */
        
                    data = (unsigned int) read_data_byte (&address);
        
                    /* Skip to next byte under some circumstances */
        
                    if (((mask == VERB) && (flags & DATA_FIRST) != VERB_FIRST) ||
                        ((mask == DESC) && (flags & DATA_FIRST) != ADJ_FIRST))
                        data = (unsigned int) read_data_byte (&address);
            }
            else {
                    /* GV2, Inform 6.10 version */
                    data = (unsigned int) read_data_byte (&address);
            }

            /* If this word matches the type and index then return its address */

            if (data == number)
                return (word_address);
        }
    }

    /* Return 0 if no more words found */

    return (0);

}/* lookup_word */
