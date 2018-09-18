/*
 * "BCfrotz.h"
 *
 * Borland C interface, declarations
 *
 */

#define MASK_LINEAR(addr)	(addr & 0x000FFFFF)
#define RM_TO_LINEAR(addr)	(((addr & 0xFFFF0000) >> 12) + (addr & 0xFFFF))
#define RM_OFFSET(addr)		(addr & 0xF)
#define RM_SEGMENT(addr)	((addr >> 4) & 0xFFFF)

#define OS_PATHSEP ';'

#define byte0(v)	((byte *)&v)[0]
#define byte1(v)	((byte *)&v)[1]
#define byte2(v)	((byte *)&v)[2]
#define byte3(v)	((byte *)&v)[3]
#define word0(v)	((word *)&v)[0]
#define word1(v)	((word *)&v)[1]

#ifndef HISTORY_MIN_ENTRY
#define HISTORY_MIN_ENTRY 1
#endif

#define SPECIAL_KEY_MIN 256
#define SPECIAL_KEY_HOME 256
#define SPECIAL_KEY_END 257
#define SPECIAL_KEY_WORD_LEFT 258
#define SPECIAL_KEY_WORD_RIGHT 259
#define SPECIAL_KEY_DELETE 260
#define SPECIAL_KEY_INSERT 261
#define SPECIAL_KEY_PAGE_UP 262
#define SPECIAL_KEY_PAGE_DOWN 263
#define SPECIAL_KEY_TAB 264
#define SPECIAL_KEY_MAX 264

#define _MONO_	0
#define _TEXT_	1
#define _CGA_	2
#define _MCGA_	3
#define _EGA_	4
#define _AMIGA_	5

typedef unsigned char byte;
typedef unsigned short word;

extern display;

extern cursor_x;
extern cursor_y;

extern char latin1_to_ibm[];
extern char latin1_to_ascii[];

extern byte text_bg;
extern byte text_fg;

extern byte scrn_attr;

extern user_background;
extern user_foreground;
extern user_emphasis;
extern user_reverse_bg;
extern user_reverse_fg;
extern user_screen_height;
extern user_screen_width;
extern user_tandy_bit;
extern user_bold_typing;
extern user_random_seed;
extern user_font;

extern char stripped_story_name[];
extern char *prog_name;

extern current_bg;
extern current_fg;
extern current_style;
extern current_font;

extern scaler;

#ifdef SOUND_SUPPORT
extern volatile int end_of_sound_flag;
#endif

/* BCinit  */	int	dectoi (const char *);
/* BCinit  */	int	hextoi (const char *);
/* BCmouse */	bool 	detect_mouse (void);
/* BCmouse */	int 	read_mouse (void);
/* BCpic   */	bool 	init_pictures (void);
/* BCpic   */	void 	reset_pictures (void);

#ifdef SOUND_SUPPORT
/* BCsmpl  */	bool 	dos_init_sound (void);
/* BCsmpl  */	void 	dos_reset_sound (void);
/* BCinput */	void	end_of_sound(void);
#endif
/* BCtext  */	void	switch_scrn_attr (bool);
/* BCtext  */	void 	load_fonts (void);
