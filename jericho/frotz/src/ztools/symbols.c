#include "tx.h"
#include <fcntl.h>
/*
 * symbols.c
 *
 * Routines for printing out symbol names, however they may be derived.
 *
 * Matthew T. Russotto 7 February 1998 russotto@pond.com
 *
 * Future:  Add property type (e.g. name property contains dictionary words)
 *          Finish user-defined symbol table
 */

#define NAMELEN 80
#define LINBUFSIZ 256

enum symtypes {
	sym_unknown = 0,
	sym_routine = 1,
	sym_global,
	sym_local,
	sym_attribute,
	sym_property
};

enum valtypes 
{
	val_unknown = 0,
	val_long,
	val_short,
	val_byte,
	val_dictword,
	val_routine
};

struct symtab_entry_t {
	enum symtypes symtype;
	enum valtypes valtype;
	long number;
	char name[NAMELEN];
};

struct routine_entry_t {
	int symtype;
	int valtype;
	long number;
	char name[NAMELEN];
	int local_entries;
	struct symtab_entry_t *locals;
	int global_entries;
	struct symtab_entry_t *globals;
};

static struct symtab_entry_t *attribute_names_table;
static int attribute_entries;

static struct symtab_entry_t *property_names_table;
static int property_entries;

static struct symtab_entry_t *global_names_table;
static int global_entries;

static struct routine_entry_t *routines_table;
static int routine_entries;


#ifdef __STDC__
static int get_type_from_name(char *tname)
#else
static int get_type_from_name(tname)
char *tname;
#endif
{
	int ch = tname[0];
	
	if (isupper(ch))
		ch = tolower(ch);
		
	switch (ch) {
		case 'a':
			return sym_attribute;
		case 'p':
			return sym_property;
		case 'r':
			return sym_routine;
		case 'g':
			return sym_global;
		case 'l':
			return sym_local;
	}
	return sym_unknown;
}

/*
 * init_symbols
 *
 * Prints the name of the attribute, if known.
 */
#ifdef __STDC__
void init_symbols(char *fname)
#else
void init_symbols(fname)
char *fname;
#endif
{
	long tmp;
	FILE *symfile;
	char linbuf[LINBUFSIZ];
	char *s;
	char *symname;
	int symtype;
	int routine = 0;
	int global = 0;
	int attribute = 0;
	int property = 0;
	
	symfile = fopen(fname, "r");
	if (symfile == NULL)
		return;
		
	
	global_entries = -1;
	attribute_entries = -1;
	property_entries = -1;
	routine_entries = 0;
	
	fgets(linbuf, LINBUFSIZ, symfile);
	while (!feof(symfile)) {
		s = strtok(linbuf, "\t\n\r ");
		symtype = get_type_from_name(s);
		switch (symtype) {
			case sym_routine:
				routine_entries++;
				break;
				
			case sym_global:
				s = strtok(NULL, "\t\n\r ");
#ifdef HAS_STRTOUL
				tmp = strtoul(s, (char **)NULL, 0);
#else
				tmp = atoi(s);
#endif
				s = strtok(NULL, "\t\n\r "); /* skip name */
				s = strtok(NULL, "\t\n\r ");
				if ((s == NULL) && (tmp > global_entries))
					global_entries = tmp;
				break;
			
			case sym_local:
				break;
			case sym_attribute:
				s = strtok(NULL, "\t\n\r ");
#ifdef HAS_STRTOUL
				tmp = strtoul(s, (char **)NULL, 0);
#else
				tmp = atoi(s);
#endif
				if (tmp > attribute_entries)
					attribute_entries = tmp;
				break;
		
			case sym_property:
				s = strtok(NULL, "\t\n\r ");
#ifdef HAS_STRTOUL
				tmp = strtoul(s, (char **)NULL, 0);
#else
				tmp = atoi(s);
#endif
				if (tmp > property_entries)
					property_entries = tmp;
				break;
		}
		fgets(linbuf, LINBUFSIZ, symfile);
	}
	global_entries++;
	attribute_entries++;
	property_entries++;
	
	if (routine_entries > 0)
		routines_table = (struct routine_entry_t *)calloc(sizeof(struct routine_entry_t), routine_entries);
	if (global_entries > 0)
		global_names_table = (struct symtab_entry_t *)calloc(sizeof(struct symtab_entry_t), global_entries);
	if (attribute_entries > 0)
		attribute_names_table = (struct symtab_entry_t *)calloc(sizeof(struct symtab_entry_t), attribute_entries);
	if (property_entries > 0)
		property_names_table = (struct symtab_entry_t *)calloc(sizeof(struct symtab_entry_t), property_entries);
	fseek(symfile, 0, 0);
	
	fgets(linbuf, LINBUFSIZ, symfile);
	while (!feof(symfile)) {
		s = strtok(linbuf, "\t\n\r ");
		symtype = get_type_from_name(s);
		switch (symtype) {
			case sym_routine:
				s = strtok(NULL, "\t\n\r ");
#ifdef HAS_STRTOUL
				tmp = strtoul(s, (char **)NULL, 0);
#else
				tmp = atoi(s);
#endif
				routines_table[routine].symtype = sym_routine;
				routines_table[routine].number = tmp;
				symname = strtok(NULL, "\t\n\r ");
				strcpy(routines_table[routine].name, symname);
				routine++;
				break;
				
			case sym_global:
				s = strtok(NULL, "\t\n\r ");
#ifdef HAS_STRTOUL
				tmp = strtoul(s, (char **)NULL, 0);
#else
				tmp = atoi(s);
#endif
				symname = strtok(NULL, "\t\n\r ");
				s = strtok(NULL, "\t\n\r ");
				if (s == NULL) {
					global_names_table[tmp].symtype = sym_global;
					global_names_table[tmp].number = tmp;
					strcpy(global_names_table[tmp].name, symname);
				}
				break;
			
			case sym_local:
				break;
				
			case sym_attribute:
				s = strtok(NULL, "\t\n\r ");
#ifdef HAS_STRTOUL
				tmp = strtoul(s, (char **)NULL, 0);
#else
				tmp = atoi(s);
#endif
				symname = strtok(NULL, "\t\n\r ");
				attribute_names_table[tmp].symtype = sym_attribute;
				attribute_names_table[tmp].number = tmp;
				strcpy(attribute_names_table[tmp].name, symname);
				break;
		
			case sym_property:
				s = strtok(NULL, "\t\n\r ");
#ifdef HAS_STRTOUL
				tmp = strtoul(s, (char **)NULL, 0);
#else
				tmp = atoi(s);
#endif
				symname = strtok(NULL, "\t\n\r ");
				property_names_table[tmp].symtype = sym_property;
				property_names_table[tmp].number = tmp;
				strcpy(property_names_table[tmp].name, symname);
				break;
		}
		fgets(linbuf, LINBUFSIZ, symfile);
	}
	fclose(symfile);
}

/*
 * print_attribute_name
 *
 * Prints the name of the attribute, if known.
 */
#ifdef __STDC__
int print_attribute_name(unsigned long attr_names_base,
					 int attr_no)
#else
int print_attribute_name(attr_names_base, attr_no)
unsigned long attr_names_base;
int attr_no;
#endif
{
	if (attr_names_base) {
		return print_inform_attribute_name(attr_names_base, attr_no);
	}
	else if ((attr_no < attribute_entries) && attribute_names_table[attr_no].symtype == sym_attribute) {
		tx_printf(attribute_names_table[attr_no].name);
		return 1;
	}
	return 0;
}

#ifdef __STDC__
int print_property_name(unsigned long property_names_base,
					 int prop_no)
#else
int print_property_name(property_names_base, prop_no)
unsigned long property_names_base;
int prop_no;
#endif
{
	if (property_names_base) {
		return print_inform_attribute_name(property_names_base, prop_no);
	}
	else if ((prop_no < property_entries) && property_names_table[prop_no].symtype == sym_property) {
		tx_printf(property_names_table[prop_no].name);
		return 1;
	}
	return 0;
}

#ifdef __STDC__
int print_local_name(unsigned long start_of_routine,
					 int local_no)
#else
int print_local_name(start_of_routine, local_no)
unsigned long start_of_routine;
int local_no;
#endif
{
	start_of_routine;
	local_no;
	return 0;
}

#ifdef __STDC__
int print_global_name(unsigned long start_of_routine,
					 int global_no)
#else
int print_global_name(start_of_routine, global_no)
unsigned long start_of_routine;
int global_no;
#endif
{
	start_of_routine;
	if ((global_no < global_entries) && global_names_table[global_no].symtype == sym_global) {
		tx_printf(global_names_table[global_no].name);
		return 1;
	}
	return 0;
}
