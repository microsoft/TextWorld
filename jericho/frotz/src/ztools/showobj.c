/*
 * showobj - part of infodump
 *
 * Object display routines.
 */

#include "tx.h"

#ifdef __STDC__
void configure_object_tables
    (unsigned int *, unsigned long *, unsigned long *, unsigned long *,
     unsigned long *);
static unsigned int get_object_address
    (unsigned int);
static void print_property_list
    (unsigned long *, unsigned long);
static void print_object
    (int, int);
static void print_object_desc
    (int);
#else
void configure_object_tables ();
static unsigned int get_object_address ();
static void print_property_list ();
static void print_object ();
static void print_object_desc ();
#endif

/*
 * configure_object_tables
 *
 * Determine the object table start and end addresses, together with the
 * property data start and end addresses, and the number of objects.
 *
 * Format:
 *
 * The object information consists of two parts. Firstly a fixed table of
 * objects and secondly, an area of variable property data.
 *
 * The format of the object varies between game types. For pre-V4 games
 * the format is:
 *
 * struct zobject {
 *    unsigned short attributes[2];
 *    unsigned char parent;
 *    unsigned char next;
 *    unsigned char child;
 *    unsigned short property_offset;
 * }
 *
 * Post-V3 the format is:
 *
 * struct zobject {
 *    unsigned short attributes[3];
 *    unsigned short parent;
 *    unsigned short next;
 *    unsigned short child;
 *    unsigned short property_offset;
 * }
 *
 * Attributes are an array of bits that can be tested, set and cleared. The
 * parent, next and child fields are object numbers. These fields are used to
 * construct an object tree that represents concepts such as object contains
 * or room contains. The property offset is the address in the data file of the
 * start of the property data for the object. Objects are numbered from 1.
 * Object 0 is used as the NULL object to terminate object lists.
 *
 * Note: The start of the object table contains a list of default property
 * values that are used when a property is not present for an object. The size
 * of this table in words is the maximum number of properties minus 1.
 *
 * The format of the object properties is complex. It is:
 *
 * [Common prefix][property n]...[property n][property 0]
 *
 * Properties occur in descending order from highest property number to zero.
 * Property zero always terminates the list, but is not referenced by the Z-code.
 * Instead, property zero is used to terminate the scan down the property list, if
 * a property is not defined. This behaviour is required when loading a default
 * property list item, or to catch setting undefined property values.
 *
 * The size information is ignored for property 0, which is actually just specified
 * as a byte containing 0x00.
 *
 * Key:
 *
 * (n) = size of block in bytes
 * max = maximum number of recurring blocks
 * min = minimum number of recurring blocks
 *
 * Common prefix:
 *
 *  (1)       (2)          (2)
 * +-------+ +------+     +------+
 * | count | | text | ... | text | max=255, min=0
 * +-------+ +------+     +------+
 *
 * count = number of following text blocks
 * text = object description, encoded
 *
 * Property n (V3 format):
 *
 *  (1)             (1)          (1)
 * +--------+----+ +------+     +------+
 * | size-1 | id | | data | ... | data | max=8, min=1
 * +--------+----+ +------+     +------+
 *  7      5 4  0
 *
 * size-1 = size of property - 1
 * id = property identifier
 * data = property data
 *
 * Maximum property number = 31
 *
 * Property n (V4 format):
 *
 *  (1) Property header byte       (1) Property size byte         (1)          (1)
 * +-----------+-----------+----+ +-----------+---------+------+ +------+     +------+
 * | size byte | word data | id | | size byte | ignored | size | | data | ... | data | max=63, min=0
 * +-----------+-----------+----+ +-----------+---------+------+ +------+     +------+
 *            7           6 5  0             7         6 5    0
 *
 * size byte = if set then next data block is a the property size byte
 *             if clear then the 'word data' flag is checked and the property has no size byte
 * word data = if set then 2 data blocks follow
 *             if clear 1 data block follows
 * ignored = this flag is not used by the property manipulation opcodes, it can be set to an arbitary value
 *           (note: this bit could be used to increase the property size from 63 to 127 bytes)
 * id = property identifier
 * size = size of property
 * data = property data
 *
 * Maximum property number = 63
 */

#ifdef __STDC__
void configure_object_tables (unsigned int *obj_count,
                              unsigned long *obj_table_base,
                              unsigned long *obj_table_end,
                              unsigned long *obj_data_base,
                              unsigned long *obj_data_end)
#else
void configure_object_tables (obj_count,
                              obj_table_base,
                              obj_table_end,
                              obj_data_base,
                              obj_data_end)
unsigned int *obj_count;
unsigned long *obj_table_base;
unsigned long *obj_table_end;
unsigned long *obj_data_base;
unsigned long *obj_data_end;
#endif
{
    unsigned long object_address, address;
    unsigned int data_count, data;

    *obj_table_base = 0;
    *obj_table_end = 0;
    *obj_data_base = 0;
    *obj_data_end = 0;
    *obj_count = 0;

    /* The object table address comes from the header */

    *obj_table_base = (unsigned long) header.objects;

    /* Calculate the number of objects and property addresses range */

    do {

        /* Count this object and get its address */

        (*obj_count)++;
        object_address = (unsigned long) get_object_address (*obj_count);

        /* Check if we have got to the end of the object list */

        if (*obj_data_base == 0 || object_address < *obj_data_base) {

            /* Calculate the range of property data */

            if ((unsigned int) header.version < V4)
                object_address += O3_PROPERTY_OFFSET;
            else
                object_address += O4_PROPERTY_OFFSET;
            address = read_data_word (&object_address);
            if (*obj_data_base == 0 || address < *obj_data_base)
                *obj_data_base = address;
            if (*obj_data_end == 0 || address > *obj_data_end)
                *obj_data_end = address;
        }
    } while (object_address < *obj_data_base);

    *obj_table_end = object_address - 1;

    /* Skip any description for the last property */

    if ((unsigned int) read_data_byte (obj_data_end))
        while (((unsigned int) read_data_word (obj_data_end) & 0x8000) == 0)
            ;

    /* Skip any properties to calculate the end address of the last property */

    while ((data = read_data_byte (obj_data_end)) != 0) {
        if ((unsigned int) header.version < V4)
            data_count = ((data & property_size_mask) >> 5) + 1;
        else if (data & 0x80)
            data_count = (unsigned int) read_data_byte (obj_data_end) & property_size_mask;
        else if (data & 0x40)
            data_count = 2;
        else
            data_count = 1;
        *obj_data_end += data_count;
    }

    (*obj_data_end)--;

}/* configure_object_tables */

/*
 * show_objects
 *
 * List all objects and property data.
 */

#ifdef __STDC__
void show_objects (int symbolic)
#else
void show_objects (symbolic)
int symbolic;
#endif
{
    unsigned long object_address, address;
    unsigned long obj_table_base, obj_table_end, obj_data_base, obj_data_end;
    unsigned int obj_count, data, pobj, nobj, cobj;
    int i, j, k, list;
    unsigned short inform_version;
    unsigned long class_numbers_base, class_numbers_end;
    unsigned long property_names_base, property_names_end;
    unsigned long attr_names_base, attr_names_end;

    /* Get objects configuration */

    configure_object_tables (&obj_count, &obj_table_base, &obj_table_end,
                             &obj_data_base, &obj_data_end);

    if (symbolic) {
    	configure_inform_tables(obj_data_end, &inform_version, &class_numbers_base, &class_numbers_end,
    				    &property_names_base, &property_names_end, &attr_names_base, &attr_names_end);
    }
    else {
	attr_names_base = property_names_base = class_numbers_base = 0;
    }

    tx_printf ("\n    **** Objects ****\n\n");
    tx_printf ("  Object count = %d\n", (int) obj_count);

    /* Iterate through each object */

    for (i = 1; (unsigned int) i <= obj_count; i++) {
        tx_printf ("\n");

        /* Get address of object */

        object_address = (unsigned long) get_object_address ((unsigned int) i);

        /* Display attributes */

        tx_printf ("%3d. Attributes: ", (int) i);
        list = 0;
        for (j = 0; j < (((unsigned int) header.version < V4) ? 4 : 6); j++) {
            data = (unsigned int) read_data_byte (&object_address);
            for (k = 7; k >= 0; k--) {
                if ((data >> k) & 1) {
					tx_printf ("%s", (list++) ? ", " : "");
					if (print_attribute_name(attr_names_base, (int) ((j * 8) + (7 - k))))
	                    tx_printf ("(%d)", (int) ((j * 8) + (7 - k)));
					else
	                    tx_printf ("%d", (int) ((j * 8) + (7 - k)));
				}
            }
        }
        if (list == 0)
            tx_printf ("None");
        tx_printf ("\n");

        /* Get object linkage information */

        if ((unsigned int) header.version < V4) {
            pobj = (unsigned int) read_data_byte (&object_address);
            nobj = (unsigned int) read_data_byte (&object_address);
            cobj = (unsigned int) read_data_byte (&object_address);
        } else {
            pobj = (unsigned int) read_data_word (&object_address);
            nobj = (unsigned int) read_data_word (&object_address);
            cobj = (unsigned int) read_data_word (&object_address);
        }
        address = read_data_word (&object_address);
        tx_printf ("     Parent object: %3d  ", (int) pobj);
	tx_printf ("Sibling object: %3d  ", (int) nobj);
	tx_printf ("Child object: %3d\n", (int) cobj);
        tx_printf ("     Property address: %04lx\n", (unsigned long) address);
        tx_printf ("         Description: \"");

        /* If object has a description then display it */

        if ((unsigned int) read_data_byte (&address))
            (void) decode_text (&address);
        tx_printf ("\"\n");

        /* Print property list */

        tx_printf ("          Properties:\n");
	print_property_list (&address, property_names_base);
    }

}/* show_objects */

/*
 * get_object_address
 *
 * Given an object number calculate the data file address of the object data.
 */

#ifdef __STDC__
static unsigned int get_object_address (unsigned int obj)
#else
static unsigned int get_object_address (obj)
unsigned int obj;
#endif
{
    unsigned int offset;

    /* Address calculation is object table base + size of default properties area +
       object number-1 * object size */

    offset = (unsigned int) header.objects;
    if ((unsigned int) header.version <= V3)
        offset += ((P3_MAX_PROPERTIES - 1) * 2) + ((obj - 1) * O3_SIZE);
    else
        offset += ((P4_MAX_PROPERTIES - 1) * 2) + ((obj - 1) * O4_SIZE);

    return (offset);

}/* get_object_address */

/*
 * print_property_list
 *
 * Display the data associated with each object property.
 */

#ifdef __STDC__
static void print_property_list (unsigned long *address, unsigned long property_names_base)
#else
static void print_property_list (address, property_names_base)
unsigned long *address;
unsigned long property_names_base;
#endif
{
    int data, count;

    /* Scan down the property address displaying each property */

    for (data = read_data_byte (address); data; data = read_data_byte (address)) {
	tx_printf ("            ");
	if (print_property_name(property_names_base, (int) (data & property_mask)))
		tx_printf ("\n              ");
	else
		tx_printf ("  ");
	tx_printf ("[%2d] ", (int) (data & property_mask));
	if ((unsigned int) header.version <= V3)
	    count = ((data & property_size_mask) >> 5) + 1;
	else if (data & 0x80)
	    count = (unsigned int) read_data_byte (address) & property_size_mask;
	else if (data & 0x40)
	    count = 2;
	else
	    count = 1;
        while (count--)
            tx_printf ("%02x ", (unsigned int) read_data_byte (address));
        tx_printf ("\n");
    }

}/* print_property_list */

/*
 * show_tree
 *
 * Use the object linkage information to display a hierarchical list of
 * objects.
 */

#ifdef __STDC__
void show_tree (void)
#else
void show_tree ()
#endif
{
    unsigned long object_address;
    unsigned long obj_table_base, obj_table_end, obj_data_base, obj_data_end;
    unsigned int i, obj_count, parent;

    /* Get objects configuration */

    configure_object_tables (&obj_count, &obj_table_base, &obj_table_end,
                             &obj_data_base, &obj_data_end);

    tx_printf ("\n    **** Object tree ****\n\n");

    /* Iterate through each object */

    for (i = 1; i <= obj_count; i++) {

        /* Get object address */

        object_address = (unsigned long) get_object_address ((unsigned int) i);

        /* Get parent for this object */

        if ((unsigned int) header.version <= V3) {
            object_address += O3_PARENT;
            parent = read_data_byte (&object_address);
        } else {
            object_address += O4_PARENT;
            parent = read_data_word (&object_address);
        }

        /*
         * If object has no parent then it is a root object so display the tree
         * from the object.
         */

        if (parent == 0)
            print_object ((int) i, 0);
    }

}/* show_tree */

/*
 * print_object
 *
 * Print an object description and its children for a point in the object tree.
 */

#ifdef __STDC__
static void print_object (int obj, int depth)
#else
static void print_object (obj, depth)
int obj;
int depth;
#endif
{
    unsigned long object_address, address;
    int child, i;

    /* Continue until the next object number is NULL */

    while (obj) {

        /* Display object depth and description */

        for (i = 0; i < depth; i++)
            tx_printf (" . ");
        tx_printf ("[%3d] ", (int) obj);
        print_object_desc (obj);
        tx_printf ("\n");

        /* Get object address */

        object_address = (unsigned long) get_object_address ((unsigned int) obj);

        /* Get any child object and the next object at this level */

        if ((unsigned int) header.version <= V3) {
            address = object_address + O3_CHILD;
            child = read_data_byte (&address);
            address = object_address + O3_NEXT;
            obj = read_data_byte (&address);
        } else {
            address = object_address + O4_CHILD;
            child = read_data_word (&address);
            address = object_address + O4_NEXT;
            obj = read_data_word (&address);
        }

        /* If this object has a child then print its tree */

        if (child)
            print_object (child, depth + 1);
    }

}/* print_object */

/*
 * print_object_description
 *
 * Display the description of an object.
 */

#ifdef __STDC__
static void print_object_desc (int obj)
#else
static void print_object_desc (obj)
int obj;
#endif
{
    unsigned long object_address, address;

    tx_printf ("\"");

    /* Check for a NULL object number */

    if (obj) {

        /* Get object address */

        object_address = (unsigned long) get_object_address ((unsigned int) obj);
	if ((unsigned int) header.version <= V3)
            address = object_address + O3_PROPERTY_OFFSET;
        else
            address = object_address + O4_PROPERTY_OFFSET;

        /* Get the property address */

        address = read_data_word (&address);

        /* Display the description if the object has one */

        if ((unsigned int) read_data_byte (&address))
            (void) decode_text (&address);
    }
    tx_printf ("\"");

}/* print_object_desc */
