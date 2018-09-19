/*
 * ux_pic.c - Unix interface, picture outline functions
 *
 * This file is part of Frotz.
 *
 * Frotz is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * Frotz is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
 * Or visit http://www.fsf.org/
 */

#define __UNIX_PORT_FILE

#include <stdlib.h>
#include <string.h>

#ifdef USE_NCURSES_H
#include <ncurses.h>
#else
#include <curses.h>
#endif

#include "ux_frotz.h"

#define PIC_FILE_HEADER_FLAGS 1
#define PIC_FILE_HEADER_NUM_IMAGES 4
#define PIC_FILE_HEADER_ENTRY_SIZE 8
#define PIC_FILE_HEADER_VERSION 14

#define PIC_HEADER_NUMBER 0
#define PIC_HEADER_WIDTH 2
#define PIC_HEADER_HEIGHT 4

static void safe_mvaddch(int, int, int);

static struct {
  int z_num;
  int width;
  int height;
  int orig_width;
  int orig_height;
} *pict_info;
static int num_pictures = 0;


static unsigned char lookupb(unsigned char *p, int n)
{
  return p[n];
}


static unsigned short lookupw(unsigned char *p, int n)
{
  return (p[n + 1] << 8) | p[n];
}


/*
 * Do a rounding division, rounding to even if fraction part is 1/2.
 * We assume x and y are nonnegative.
 *
 */
static int round_div(int x, int y)
{
	int quotient = x / y;
	int dblremain = (x % y) << 1;

	if ((dblremain > y) || ((dblremain == y) && (quotient & 1)))
		quotient++;
	return quotient;
}


bool unix_init_pictures (void)
{
  FILE *file = NULL;
  int success = FALSE;
  unsigned char gheader[16];
  unsigned char *raw_info = NULL;

  char *filename;
  const char *basename, *dotpos;
  int namelen;

  if ((filename = malloc(2 * strlen(f_setup.story_name) + 10)) == NULL)
    return FALSE;

  basename = strrchr(f_setup.story_name, '/');
  if (basename) basename++; else basename = f_setup.story_name;
  dotpos = strrchr(basename, '.');
  namelen = (dotpos ? dotpos - basename : (int) strlen(basename));
  sprintf(filename, "%.*sgraphics/%.*s.mg1",
          (int)(basename - f_setup.story_name), f_setup.story_name, namelen, basename);

  do {
    int i, entry_size, flags, x_scale, y_scale;

    if (((file = fopen (filename, "rb")) == NULL)
	|| (fread(&gheader, sizeof (gheader), 1, file) != 1))
      break;

    num_pictures = lookupw(gheader, PIC_FILE_HEADER_NUM_IMAGES);
    entry_size = lookupb(gheader, PIC_FILE_HEADER_ENTRY_SIZE);
    flags = lookupb(gheader, PIC_FILE_HEADER_FLAGS);

    raw_info = malloc(num_pictures * entry_size);

    if (fread(raw_info, num_pictures * entry_size, 1, file) != 1)
      break;

    pict_info = malloc((num_pictures + 1) * sizeof(*pict_info));
    pict_info[0].z_num = 0;
    pict_info[0].height = num_pictures;
    pict_info[0].width = lookupw(gheader, PIC_FILE_HEADER_VERSION);

    y_scale = 200;
    x_scale = (flags & 0x08) ? 640 : 320;

    /* Copy and scale.  */
    for (i = 1; i <= num_pictures; i++) {
      unsigned char *p = raw_info + entry_size * (i - 1);
      pict_info[i].z_num = lookupw(p, PIC_HEADER_NUMBER);
      pict_info[i].orig_height = lookupw(p, PIC_HEADER_HEIGHT);
      pict_info[i].orig_width = lookupw(p, PIC_HEADER_WIDTH);

      pict_info[i].height = round_div(pict_info[i].orig_height *
		h_screen_rows, y_scale);
      pict_info[i].width = round_div(pict_info[i].orig_width *
		h_screen_cols, x_scale);

      /* Don't let dimensions get rounded to nothing. */
      if (pict_info[i].orig_height && !pict_info[i].height)
         pict_info[1].height = 1;
      if (pict_info[i].orig_width && !pict_info[i].width)
         pict_info[i].width = 1;
    }
    success = TRUE;
  } while (0);
  if (file)
    fclose(file);
  if (raw_info)
    free(raw_info);
  return success;
}


/* Convert a Z picture number to an index into pict_info.  */
static int z_num_to_index(int n)
{
  int i;
  for (i = 0; i <= num_pictures; i++)
    if (pict_info[i].z_num == n)
      return i;
  return -1;
}


/*
 * os_picture_data
 *
 * Return true if the given picture is available. If so, write the
 * width and height of the picture into the appropriate variables.
 * Only when picture 0 is asked for, write the number of available
 * pictures and the release number instead.
 *
 */
int os_picture_data(int num, int *height, int *width)
{
  int index;

  *height = 0;
  *width = 0;

  if (!pict_info)
    return FALSE;

  if ((index = z_num_to_index(num)) == -1)
    return FALSE;

  *height = pict_info[index].height;
  *width = pict_info[index].width;

  return TRUE;
}


/*
 * Do a mvaddch if the coordinates aren't too large.
 *
 */
static void safe_mvaddch(int y, int x, int ch)
{
	if ((y < h_screen_rows) && (x < h_screen_cols))
		mvaddch(y, x, ch);
}


/*
 * Set n chars starting at (x, y), doing bounds checking.
 *
 */
static void safe_scrnset(int y, int x, int ch, int n)
{
	if ((y < h_screen_rows) && (x < h_screen_cols)) {
		move(y, x);
		if (x + n > h_screen_cols)
			n = h_screen_cols - x;
		while (n--)
			addch(ch);
	}
}


/*
 * os_draw_picture
 *
 * Display a picture at the given coordinates. Top left is (1,1).
 *
 */
/* TODO: handle truncation correctly.  Spec 8.8.3 says all graphics should
 * be clipped to the current window.  To do that, we should probably
 * modify z_draw_picture in the frotz core to pass some extra parameters.
 */
void os_draw_picture (int num, int row, int col)
{
  int width, height, r, c;
  int saved_x, saved_y;
  static int plus, ltee, rtee, ttee, btee, hline, vline, ckboard;
  static int urcorner, ulcorner, llcorner, lrcorner;
  static bool acs_initialized = FALSE;

  if (!acs_initialized) {
    plus     = u_setup.plain_ascii ? '+'  : ACS_PLUS;
    ltee     = u_setup.plain_ascii ? '<'  : ACS_LTEE;
    rtee     = u_setup.plain_ascii ? '>'  : ACS_RTEE;
    ttee     = u_setup.plain_ascii ? '^'  : ACS_TTEE;
    btee     = u_setup.plain_ascii ? 'v'  : ACS_BTEE;
    hline    = u_setup.plain_ascii ? '-'  : ACS_HLINE;
    vline    = u_setup.plain_ascii ? '|'  : ACS_VLINE;
    ckboard  = u_setup.plain_ascii ? ':'  : ACS_CKBOARD;
    urcorner = u_setup.plain_ascii ? '\\' : ACS_URCORNER;
    ulcorner = u_setup.plain_ascii ? '/'  : ACS_ULCORNER;
    llcorner = u_setup.plain_ascii ? '\\' : ACS_LLCORNER;
    lrcorner = u_setup.plain_ascii ? '/'  : ACS_LRCORNER;
    acs_initialized = TRUE;
  }

  if (!os_picture_data(num, &height, &width) || !width || !height)
    return;
  col--, row--;

  getyx(stdscr, saved_y, saved_x);

  /* General case looks like:
   *                            /----\
   *                            |::::|
   *                            |::42|
   *                            \----/
   *
   * Special cases are:  1 x n:   n x 1:   1 x 1:
   *
   *                                ^
   *                                |
   *                     <----->    |        +
   *                                |
   *                                v
   */

  if ((height == 1) && (width == 1))
    safe_mvaddch(row, col, plus);
  else if (height == 1) {
    safe_mvaddch(row, col, ltee);
    safe_scrnset(row, col + 1, hline, width - 2);
    safe_mvaddch(row, col + width - 1, rtee);
  } else if (width == 1) {
    safe_mvaddch(row, col, ttee);
    for (r = row + 1; r < row + height - 1; r++)
      safe_mvaddch(r, col, vline);
    safe_mvaddch(row + height - 1, col, btee);
  } else {
    safe_mvaddch(row, col, ulcorner);
    safe_scrnset(row, col + 1, hline, width - 2);
    safe_mvaddch(row, col + width - 1, urcorner);
    for (r = row + 1; r < row + height - 1; r++) {
      safe_mvaddch(r, col, vline);
      safe_scrnset(r, col + 1, ckboard, width - 2);
      safe_mvaddch(r, col + width - 1, vline);
    }
    safe_mvaddch(row + height - 1, col, llcorner);
    safe_scrnset(row + height - 1, col + 1, hline, width - 2);
    safe_mvaddch(row + height - 1, col + width - 1, lrcorner);
  }

  /* Picture number.  */
  if (height > 2) {
    for (c = col + width - 2; c > col && num > 0; c--, (num /= 10))
      safe_mvaddch(row + height - 2, c, '0' + num % 10);
  }

  move(saved_y, saved_x);
}


/*
 * os_peek_colour
 *
 * Return the colour of the pixel below the cursor. This is used
 * by V6 games to print text on top of pictures. The coulor need
 * not be in the standard set of Z-machine colours. To handle
 * this situation, Frotz extends the colour scheme: Values above
 * 15 (and below 256) may be used by the interface to refer to
 * non-standard colours. Of course, os_set_colour must be able to
 * deal with these colours. Interfaces which refer to characters
 * instead of pixels might return the current background colour
 * instead.
 *
 */
int os_peek_colour (void)
{
  if (u_setup.color_enabled) {
#ifdef COLOR_SUPPORT
    short fg, bg;
    pair_content(PAIR_NUMBER(inch() & A_COLOR), &fg, &bg);
    switch(bg) {
          case COLOR_BLACK: return BLACK_COLOUR;
          case COLOR_RED: return RED_COLOUR;
          case COLOR_GREEN: return GREEN_COLOUR;
          case COLOR_YELLOW: return YELLOW_COLOUR;
          case COLOR_BLUE: return BLUE_COLOUR;
          case COLOR_MAGENTA: return MAGENTA_COLOUR;
          case COLOR_CYAN: return CYAN_COLOUR;
          case COLOR_WHITE: return WHITE_COLOUR;
    }
    return 0;
#endif /* COLOR_SUPPORT */
  } else {
    return (inch() & A_REVERSE) ? h_default_foreground : h_default_background;
  }
}
