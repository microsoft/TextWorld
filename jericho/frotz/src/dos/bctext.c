/*
 * file "BCtext.c"
 *
 * Borland C front end, text functions
 *
 */

#include <alloc.h>
#include <stdio.h>
#include <string.h>
#include <conio.h>
#include <dos.h>
#include "frotz.h"
#include "BCfrotz.h"
#include "fontdata.h"

extern byte far *get_scrnptr (int);

int current_bg = 0;
int current_fg = 0;
int current_style = 0;
int current_font = 0;

byte text_bg = 0;
byte text_fg = 0;
byte bg = 0;
byte fg = 0;
byte scrn_attr = 0;

int cursor_x = 0;
int cursor_y = 0;

char latin1_to_ascii[] =
    "   !  c  L  >o<Y  |  S  '' C  a  << not-  R  _  "
    "^0 +/-^2 ^3 '  my P  .  ,  ^1 o  >> 1/41/23/4?  "
    "A  A  A  A  Ae A  AE C  E  E  E  E  I  I  I  I  "
    "Th N  O  O  O  O  Oe *  O  U  U  U  Ue Y  Th ss "
    "a  a  a  a  ae a  ae c  e  e  e  e  i  i  i  i  "
    "th n  o  o  o  o  oe :  o  u  u  u  ue y  th y  ";

char latin1_to_ibm[] = {
    0x20, 0xad, 0xbd, 0x9c, 0xcf, 0xbe, 0xdd, 0xf5,
    0xf9, 0xb8, 0xa6, 0xae, 0xaa, 0xf0, 0xa9, 0xee,
    0xf8, 0xf1, 0xfd, 0xfc, 0xef, 0xe6, 0xf4, 0xfa,
    0xf7, 0xfb, 0xa7, 0xaf, 0xac, 0xab, 0xf3, 0xa8,
    0xb7, 0xb5, 0xb6, 0xc7, 0x8e, 0x8f, 0x92, 0x80,
    0xd4, 0x90, 0xd2, 0xd3, 0xde, 0xd6, 0xd7, 0xd8,
    0xd1, 0xa5, 0xe3, 0xe0, 0xe2, 0xe5, 0x99, 0x9e,
    0x9d, 0xeb, 0xe9, 0xea, 0x9a, 0xed, 0xe8, 0xe1,
    0x85, 0xa0, 0x83, 0xc6, 0x84, 0x86, 0x91, 0x87,
    0x8a, 0x82, 0x88, 0x89, 0x8d, 0xa1, 0x8c, 0x8b,
    0xd0, 0xa4, 0x95, 0xa2, 0x93, 0xe4, 0x94, 0xf6,
    0x9b, 0x97, 0xa3, 0x96, 0x81, 0xec, 0xe7, 0x98
};

static byte far *graphics_font = NULL;
static byte far *mcga_font = NULL;
static byte far *mcga_width = NULL;
static word far *serif_font = NULL;
static byte far *serif_width = NULL;

/*
 * load_fonts
 *
 * Load the proportional and graphics fonts. In the release version all
 * font data is appended to the end of the executable.
 *
 */

void load_fonts (void)
{
    static chunk_offset[] = {
	0x6660,
	0x6300,
	0x4A40,
	0x3180,
	0x18C0,
	0x00
    };

    if (display == _MCGA_) {
	mcga_font = font_data + chunk_offset[1];
	mcga_width = (byte *) mcga_font + 0x300;
    } else
	graphics_font = font_data + chunk_offset[0];

    if (display == _AMIGA_ && user_font != 0) {
	serif_font = (word *)(font_data + chunk_offset[1 + user_font]);
	serif_width = (byte *) serif_font + 0x1800;
    }

}/* load_fonts */

/*
 * os_font_data
 *
 * Return true if the given font is available. The font can be
 *
 *    TEXT_FONT
 *    PICTURE_FONT
 *    GRAPHICS_FONT
 *    FIXED_WIDTH_FONT
 *
 * The font size should be stored in "height" and "width". If the given
 * font is unavailable then these values must _not_ be changed.
 *
 */

int os_font_data (int font, int *height, int *width)
{

    /* All fonts of this interface have the same size */

    *height = h_font_height;
    *width = h_font_width;

    /* Not every font is available in every mode */

    if (font == TEXT_FONT)
	return TRUE;
    if (font == GRAPHICS_FONT && (display == _CGA_ || display >= _EGA_))
	return TRUE;
    if (font == FIXED_WIDTH_FONT)
	return TRUE;

    /* Unavailable font */

    return FALSE;

}/* os_font_data */

/*
 * switch_scrn_attr
 *
 * Parts of the screen are usually erased to background colour.  However,
 * for deleting text in the input routine it can be useful to erase to
 * the current text background colour.  The two colours can be different,
 * for example when the reverse text style is used.  This helper function
 * toggles between the two possible behaviours.
 *
 */

void switch_scrn_attr (bool flag)
{
    byte scrn_bg;
    byte scrn_fg;

    if (flag) {
	scrn_bg = text_bg;
	scrn_fg = text_fg;
    } else {
	scrn_bg = bg;
	scrn_fg = fg;
    }

    if (display <= _TEXT_)
	scrn_attr = (scrn_bg << 4) | scrn_fg;
    else if (display == _CGA_)
	scrn_attr = (scrn_bg != BLACK) ? 0xff : 0x00;
    else
	scrn_attr = scrn_bg;

}/* switch_scrn_attr */

/*
 * adjust_style
 *
 * Set the current colours. This combines the current colour selection
 * and the current text style.
 *
 */

static void adjust_style (void)
{
    static byte amiga_palette[][3] = {
	{ 0x00, 0x00, 0x00 },
	{ 0x2a, 0x00, 0x00 },
	{ 0x00, 0x2a, 0x00 },
	{ 0x3f, 0x3f, 0x15 },
	{ 0x00, 0x00, 0x2a },
	{ 0x2a, 0x00, 0x2a },
	{ 0x00, 0x2a, 0x2a },
	{ 0x3f, 0x3f, 0x3f },
	{ 0x30, 0x30, 0x30 },
	{ 0x20, 0x20, 0x20 },
	{ 0x10, 0x10, 0x10 },
    };

    static byte pc_colour[] = {
	BLACK,
	RED,
	GREEN,
	YELLOW,
	BLUE,
	MAGENTA,
	CYAN,
	WHITE,
	DARKGRAY
    };

    static byte palette_bg = 0xff;
    static byte palette_fg = 0xff;

    fg = current_fg;
    bg = current_bg;

    /* V6 game, Amiga mode: Alter the palette registers if the colours
       of window 0 have changed. DAC register #79 holds the foreground,
       DAC register #64 the background colour. */

    if (display == _AMIGA_ && h_version == V6 && cwin == 0) {

	if (fg < 16 && fg != palette_fg) {

	    byte R = amiga_palette[fg - 2][0];
	    byte G = amiga_palette[fg - 2][1];
	    byte B = amiga_palette[fg - 2][2];

	    asm mov ax,0x1010
	    asm mov bx,79
	    asm mov dh,R
	    asm mov ch,G
	    asm mov cl,B
	    asm int 0x10

	    palette_fg = fg;

	}

	if (bg < 16 && bg != palette_bg) {

	    byte R = amiga_palette[bg - 2][0];
	    byte G = amiga_palette[bg - 2][1];
	    byte B = amiga_palette[bg - 2][2];

	    asm mov ax,0x1010
	    asm mov bx,64
	    asm mov dh,R
	    asm mov ch,G
	    asm mov cl,B
	    asm int 0x10

	    palette_bg = bg;

	}

    }

    /* Handle colours */

    if (fg < 16)

	if (display == _MONO_)
	    fg = (fg == WHITE_COLOUR) ? LIGHTGRAY : BLACK;
	else if (h_version == V6 && display == _AMIGA_)
	    fg = (palette_fg == fg) ? 15 : 0;
	else
	    fg = pc_colour[fg - 2];

    else fg -= 16;

    if (bg < 16)

	if (display == _MONO_)
	    bg = (bg == WHITE_COLOUR) ? LIGHTGRAY : BLACK;
	else if (h_version == V6 && display == _AMIGA_)
	    bg = (palette_bg == bg) ? 0 : 15;
	else
	    bg = pc_colour[bg - 2];

    else bg -= 16;

    /* Handle reverse text style */

    if (current_style & REVERSE_STYLE) {
	text_fg = (user_reverse_fg != -1) ? user_reverse_fg : bg;
	text_bg = (user_reverse_bg != -1) ? user_reverse_bg : fg;
    } else {
	text_fg = fg;
	text_bg = bg;
    }

    /* Handle emphasis style */

    if (current_style & EMPHASIS_STYLE) {

	if (display == _MONO_ && text_bg == BLACK)
	    text_fg = BLUE;	/* blue in monochrome mode is underlined */
	if (display == _TEXT_)
	    text_fg = (user_emphasis != -1) ? user_emphasis : YELLOW;

    }

    /* Handle boldface style */

    if (current_style & BOLDFACE_STYLE) {

	if (display == _MONO_)
	    text_fg = WHITE;
	if (display == _TEXT_)
	    text_fg ^= 8;

    }

    /* Set the screen attribute for scrolling and erasing */

    switch_scrn_attr (FALSE);

}/* adjust_style */

/*
 * os_set_colour
 *
 * Set the foreground and background colours which can be:
 *
 *     DEFAULT_COLOUR
 *     BLACK_COLOUR
 *     RED_COLOUR
 *     GREEN_COLOUR
 *     YELLOW_COLOUR
 *     BLUE_COLOUR
 *     MAGENTA_COLOUR
 *     CYAN_COLOUR
 *     WHITE_COLOUR
 *
 *     MS-DOS 320 columns MCGA mode only:
 *
 *     GREY_COLOUR
 *
 *     Amiga only:
 *
 *     LIGHTGREY_COLOUR
 *     MEDIUMGREY_COLOUR
 *     DARKGREY_COLOUR
 *
 * There may be more colours in the range from 16 to 255; see the remarks
 * on os_peek_colour.
 *
 */

void os_set_colour (int new_foreground, int new_background)
{

    current_fg = new_foreground;
    current_bg = new_background;

    /* Apply changes */

    adjust_style ();

}/* os_set_colour */

/*
 * os_set_text_style
 *
 * Set the current text style. Following flags can be set:
 *
 *     REVERSE_STYLE
 *     BOLDFACE_STYLE
 *     EMPHASIS_STYLE (aka underline aka italics)
 *     FIXED_WIDTH_STYLE
 *
 */

void os_set_text_style (int new_style)
{

    current_style = new_style;

    /* Apply changes */

    adjust_style ();

}/* os_set_text_style */

/*
 * os_set_font
 *
 * Set the font for text output. The interpreter takes care not to
 * choose fonts which aren't supported by the interface.
 *
 */

void os_set_font (int new_font)
{

    current_font = new_font;

}/* os_set_font */

/*
 * write_pattern
 *
 * Helper function for drawing characters in EGA and Amiga mode.
 *
 */

void write_pattern (byte far *screen, byte val, byte mask)
{

    if (mask != 0) {

	if (display == _CGA_) {

	    if (text_bg == BLACK)
		*screen &= ~mask;
	    if (text_bg == WHITE)
		*screen |= mask;
	    if (text_fg != text_bg)
		*screen ^= val;

	} else if (display == _MCGA_) {

	    byte i;

	    for (i = 0x80; (mask & i) != 0; i >>= 1)
		*screen++ = (val & i) ? text_fg : text_bg;

	} else {

	    asm mov dx,0x03cf
	    asm mov al,mask
	    asm out dx,al
	    asm les bx,screen
	    asm mov ch,text_bg
	    asm mov al,es:[bx]
	    asm mov es:[bx],ch
	    asm mov al,val
	    asm out dx,al
	    asm mov ch,text_fg
	    asm mov al,es:[bx]
	    asm mov es:[bx],ch

	}

    }

}/* write_pattern */

/*
 * os_display_char
 *
 * Display a character of the current font using the current colours and
 * text style. The cursor moves to the next position. Printable codes are
 * all ASCII values from 32 to 126, ISO Latin-1 characters from 160 to
 * 255, ZC_GAP (gap between two sentences) and ZC_INDENT (paragraph
 * indentation). The screen should not be scrolled after printing to the
 * bottom right corner.
 *
 */

void os_display_char (zchar c)
{
    int width = os_char_width (c);

    /* Handle accented characters */

    if (c >= ZC_LATIN1_MIN && (story_id != BEYOND_ZORK || (h_flags & GRAPHICS_FLAG)))

	if (display == _CGA_ || display == _MCGA_) {

	    char *ptr = latin1_to_ascii + 3 * (c - ZC_LATIN1_MIN);

	    char c1 = *ptr++;
	    char c2 = *ptr++;
	    char c3 = *ptr++;

	    os_display_char (c1);

	    if (c2 != ' ')
		os_display_char (c2);
	    if (c3 != ' ')
		os_display_char (c3);

	    return;

	} else if (display == _AMIGA_ && current_font == TEXT_FONT && !(current_style & FIXED_WIDTH_STYLE) && user_font != 0) {

	    if (c >= ZC_LATIN1_MIN)
		c -= 32;

	} else c = latin1_to_ibm[c - ZC_LATIN1_MIN];

    /* Handle special indentations */

    if (c == ZC_INDENT)
	{ os_display_char (' '); os_display_char (' '); os_display_char (' '); return; }
    if (c == ZC_GAP)
	{ os_display_char (' '); os_display_char (' '); return; }

    /* Display character */

    if (display <= _TEXT_) {

	asm mov ah,2
	asm mov bh,0
	asm mov dh,byte ptr cursor_y
	asm mov dl,byte ptr cursor_x
	asm int 0x10
	asm mov ah,9
	asm mov bh,0
	asm mov bl,byte ptr text_bg
	asm mov cl,4
	asm shl bl,cl
	asm or bl,byte ptr text_fg
	asm mov cx,1
	asm mov al,byte ptr c
	asm int 0x10

    } else {

	void far *table;
	word mask;
	word val;
	byte mask0;
	byte mask1;
	int align;
	int underline;
	int boldface;
	int type;

	int shift = (display != _MCGA_) ? cursor_x % 8 : 0;
	int offset = (display != _MCGA_) ? cursor_x / 8 : cursor_x;

	int i;

	if (current_font == GRAPHICS_FONT) {
	    table = graphics_font + 8 * (c - 32);
	    mask = 0xff;
	    underline = -1;
	    boldface = -1;
	    align = 0;
	    type = 1;
	} else if (display == _AMIGA_ && current_font == TEXT_FONT && !(current_style & FIXED_WIDTH_STYLE) && user_font != 0) {
	    table = serif_font + 16 * (c - 32);
	    mask = 0xffff << (16 - width);
	    underline = 14;
	    boldface = 1;
	    align = 0;
	    type = 2;
	} else if (display == _CGA_) {
	    table = (byte far *) MK_FP (0xf000, 0xfa6e) + 8 * c;
	    mask = 0xff;
	    underline = 7;
	    boldface = (user_bold_typing != -1) ? 1 : -1;
	    align = 0;
	    type = 3;
	} else if (display >= _EGA_) {
	    table = (byte far *) getvect (0x43) + h_font_height * c;
	    mask = 0xff;
	    underline = h_font_height - 1;
	    boldface = (user_bold_typing != -1) ? 1 : -1;
	    align = 0;
	    type = 3;
	} else {
	    table = mcga_font + 8 * (c - 32);
	    mask = 0xff & (0xff << (8 - width));
	    underline = 7;
	    boldface = -1;
	    align = (width + 1 - mcga_width[c - 32]) / 2;
	    type = 3;
	}

	mask0 = mask >> shift;
	mask1 = mask << (8 - shift);

	if (!(current_style & BOLDFACE_STYLE))
	    boldface = -1;
	if (!(current_style & EMPHASIS_STYLE))
	    underline = -1;

	if (display >= _EGA_) {
	    outport (0x03ce, 0x0205);
	    outport (0x03ce, 0xff08);
	}

	for (i = 0; i < h_font_height; i++) {

	    byte far *screen = get_scrnptr (cursor_y + i) + offset;

	    if (type == 1)
		val = *((byte far *) table + 8 * i / h_font_height);
	    if (type == 2)
		val = *((word far *) table + i);
	    if (type == 3)
		val = *((byte far *) table + i);

	    if (align != 0)
		val >>= align;

	    if (boldface == 1)
		val |= val >> 1;
	    if (underline == i)
		val ^= mask;

	    if (type == 2)
		write_pattern (screen++, val >> (8 + shift), mask >> (8 + shift));

	    write_pattern (screen + 0, val >> shift, mask0);
	    write_pattern (screen + 1, val << (8 - shift), mask1);

	}

    }

    /* Move cursor to next position */

    cursor_x += width;

}/* os_display_char */

/*
 * os_display_string
 *
 * Pass a string of characters to os_display_char.
 *
 */

void os_display_string (const zchar *s)
{

    zchar c;

    while ((c = *s++) != 0)

	if (c == ZC_NEW_FONT || c == ZC_NEW_STYLE) {

	    int arg = *s++;

	    if (c == ZC_NEW_FONT)
		os_set_font (arg);
	    if (c == ZC_NEW_STYLE)
		os_set_text_style (arg);

	} else os_display_char (c);

}/* os_display_string */

/*
 * os_char_width
 *
 * Return the width of the character in screen units.
 *
 */

int os_char_width (zchar c)
{

    /* Handle accented characters */

    if (c >= ZC_LATIN1_MIN && (story_id != BEYOND_ZORK || (h_flags & GRAPHICS_FLAG)))

	if (display == _CGA_ || display == _MCGA_) {

	    const char *ptr = latin1_to_ascii + 3 * (c - ZC_LATIN1_MIN);

	    int width = 0;

	    char c1 = *ptr++;
	    char c2 = *ptr++;
	    char c3 = *ptr++;

	    width = os_char_width (c1);

	    if (c2 != ' ')
		width += os_char_width (c2);
	    if (c3 != ' ')
		width += os_char_width (c3);

	    return width;

	} else if (display == _AMIGA_ && current_font == TEXT_FONT && !(current_style & FIXED_WIDTH_STYLE) && user_font != 0)

	    if (c >= ZC_LATIN1_MIN)
		c -= 32;

    /* Handle special indentations */

    if (c == ZC_INDENT)
	return 3 * os_char_width (' ');
    if (c == ZC_GAP)
	return 2 * os_char_width (' ');

    /* Calculate width */

    if (display <= _TEXT_)
	return 1;
    if (display == _CGA_)
	return 8;
    if (display == _EGA_)
	return 8;

    if (current_font == GRAPHICS_FONT)
	return 8;
    if (current_font == FIXED_WIDTH_FONT || (current_style & FIXED_WIDTH_STYLE) || (display == _AMIGA_ && user_font == 0))
	return (display == _AMIGA_) ? 8 : 5;

    if (display == _MCGA_)
	return mcga_width[c - 32];
    if (display == _AMIGA_)
	return serif_width[c - 32] + ((current_style & BOLDFACE_STYLE) ? 1 : 0);

    return 0;

}/* os_char_width */

/*
 * os_string_width
 *
 * Calculate the length of a word in screen units. Apart from letters,
 * the word may contain special codes:
 *
 *    ZC_NEW_STYLE - next character is a new text style
 *    ZC_NEW_FONT  - next character is a new font
 *
 */

int os_string_width (const zchar *s)
{
    int width = 0;

    int saved_font = current_font;
    int saved_style = current_style;

    zchar c;

    while ((c = *s++) != 0)

	if (c == ZC_NEW_STYLE || c == ZC_NEW_FONT) {

	    int arg = *s++;

	    if (c == ZC_NEW_FONT)
		current_font = arg;
	    if (c == ZC_NEW_STYLE)
		current_style = arg;

	} else width += os_char_width (c);

    current_font = saved_font;
    current_style = saved_style;

    return width;

}/* os_string_width */

/*
 * os_set_cursor
 *
 * Place the text cursor at the given coordinates. Top left is (1,1).
 *
 */

void os_set_cursor (int y, int x)
{

    cursor_y = y - 1;
    cursor_x = x - 1;

}/* os_set_cursor */

/*
 * os_more_prompt
 *
 * Display a MORE prompt, wait for a keypress and remove the MORE
 * prompt from the screen.
 *
 */

void os_more_prompt (void)
{
    int saved_x;

    /* Save text font and style */

    int saved_font = current_font;
    int saved_style = current_style;

    /* Choose plain text style */

    current_font = TEXT_FONT;
    current_style = 0;

    adjust_style ();

    /* Wait until the user presses a key */

    saved_x = cursor_x;

    os_display_string ((zchar *) "[MORE]");
    os_read_key (0, TRUE);

    os_erase_area (cursor_y + 1,
		   saved_x + 1,
		   cursor_y + h_font_height,
		   cursor_x + 1,
		   -1);

    cursor_x = saved_x;

    /* Restore text font and style */

    current_font = saved_font;
    current_style = saved_style;

    adjust_style ();

}/* os_more_prompt */
