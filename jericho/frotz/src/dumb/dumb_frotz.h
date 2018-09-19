#ifndef dumb_frotz_h__
#define dumb_frotz_h__

/* dumb-frotz.h
 *
 * Frotz os functions for a standard C library and a dumb terminal.
 * Now you can finally play Zork Zero on your Teletype.
 *
 * Copyright 1997, 1998 Alembic Petrofsky <alembic@petrofsky.berkeley.ca.us>.
 * Any use permitted provided this notice stays intact.
 */
#include "../common/frotz.h"
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>
#include <ctype.h>
#include <time.h>

/* from ../common/setup.h */
extern f_setup_t f_setup;

bool do_more_prompts;

/* From input.c.  */
bool is_terminator (zchar);

/* dumb-input.c */
bool dumb_handle_setting(const char *setting, bool show_cursor, bool startup);
void dumb_init_input(void);
void load_story(char *s);

/* dumb-output.c */
void dumb_init_output(void);
bool dumb_output_handle_setting(const char *setting, bool show_cursor,
				bool startup);
void dumb_show_screen(bool show_cursor);
void dumb_show_prompt(bool show_cursor, char line_type);
void dumb_dump_screen(void);
void dumb_display_user_input(char *);
void dumb_discard_old_input(int num_chars);
void dumb_elide_more_prompt(void);
void dumb_set_picture_cell(int row, int col, char c);
void dumb_row_to_str(char *s);
void dumb_clear_output(void);
char* dumb_get_screen(void);
void dumb_clear_screen(void);

/* dumb-pic.c */
void dumb_init_pictures(char *graphics_filename);

void dumb_set_next_action(char *s);


#endif
