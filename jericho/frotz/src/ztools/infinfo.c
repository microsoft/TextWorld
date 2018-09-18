/*
 * informinfo V7/3
 *
 * Inform 6 specific routines.
 * 
 * Matthew T. Russotto 7 February 1998 russotto@pond.com
 *
 */

#include "tx.h"

#ifdef __STDC__
void configure_inform_tables (unsigned long obj_data_end, /* everything follows from this */
                              unsigned short *inform_version,
                              unsigned long *class_numbers_base,
                              unsigned long *class_numbers_end,
                              unsigned long *property_names_base,
                              unsigned long *property_names_end,
                              unsigned long *attr_names_base,
                              unsigned long *attr_names_end)
#else
void configure_inform_tables (obj_data_end,
			      inform_version,
			      class_numbers_base,
			      class_numbers_end,
			      property_names_base,
			      property_names_end,
			      attr_names_base,
			      attr_names_end)
unsigned long obj_data_end; /* everything follows from this */
unsigned short *inform_version;
unsigned long *class_numbers_base;
unsigned long *class_numbers_end;
unsigned long *property_names_base;
unsigned long *property_names_end;
unsigned long *attr_names_base;
unsigned long *attr_names_end;
#endif
{
	unsigned long address;
	zword_t num_properties;

	*attr_names_base = *attr_names_end = 0;
	*property_names_base = *property_names_end = 0;
	*class_numbers_base = *class_numbers_end = 0;

	if (header.serial[0] >= '0' && header.serial[0] <= '9' &&
		header.serial[1] >= '0' && header.serial[1] <= '9' &&
		header.serial[2] >= '0' && header.serial[2] <= '1' &&
		header.serial[3] >= '0' && header.serial[3] <= '9' &&
		header.serial[4] >= '0' && header.serial[4] <= '3' &&
		header.serial[5] >= '0' && header.serial[5] <= '9' &&
		header.serial[0] != '8') {
		if (header.name[4] >= '6') {
			*inform_version = (header.name[4] - '0')*100 + (header.name[6] - '0')*10 + (header.name[7] - '0');
			address = *class_numbers_base = obj_data_end + 1;
			while (read_data_word(&address)) /* do nothing */;
			*class_numbers_end = address - 1;
			*property_names_base = address;
			num_properties = read_data_word(&address) - 1;
			address += num_properties * sizeof(zword_t);
			*property_names_end = address - 1;
			if (*inform_version >= INFORM_610) {
				*attr_names_base = address;
				address += (48 * sizeof(zword_t));
				*attr_names_end = address - 1;
				/* then come the action names, the individual property values, the dynamic arrays, etc */
			}
		}
	}
	else
		*inform_version = 0;
	tx_printf("Inform Version: %d\n", *inform_version);
}

#ifdef __STDC__
int print_inform_attribute_name(unsigned long attr_names_base, int attr_no)
#else
int print_inform_attribute_name(attr_names_base, attr_no)
unsigned long attr_names_base;
int attr_no;
#endif
{
	unsigned long address;
	
	address = attr_names_base + attr_no * 2;
	address = (unsigned long) read_data_word (&address);
	if (address == 0)
		return 0;
	address = address * code_scaler + (unsigned long) story_scaler * header.strings_offset;
	decode_text(&address);
	return 1;
}

#ifdef __STDC__
int print_inform_property_name(unsigned long prop_names_base, int prop_no)
#else
int print_inform_property_name(prop_names_base, prop_no)
unsigned long prop_names_base;
int prop_no;
#endif
{
	unsigned long address;
	
	address = prop_names_base + prop_no * 2;
	address = (unsigned long) read_data_word (&address);
	if (address == 0)
		return 0;
	address = address * code_scaler + (unsigned long) story_scaler * header.strings_offset;
	decode_text(&address);
	return 1;
}

#ifdef __STDC__
int print_inform_action_name(unsigned long action_names_base, int action_no)
#else
int print_inform_action_name(action_names_base, action_no)
unsigned long action_names_base;
int action_no;
#endif
{
	unsigned long address;
	
	address = action_names_base + action_no * 2;
	address = (unsigned long) read_data_word (&address);
	if (address == 0)
		return 0;
	address = address * code_scaler + (unsigned long) story_scaler * header.strings_offset;
	decode_text(&address);
	return 1;
}
