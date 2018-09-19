#ifndef _SF_FROTZ_H
#define _SF_FROTZ_H

#include "../common/frotz.h"
#include "../blorb/blorb.h"

// version info
#define SFROTZ_MAJOR 0
#define SFROTZ_MINOR 2

// typedef unsigned char byte;
// typedef unsigned short word;
// typedef unsigned long ulong;
#include <stdint.h>
typedef uint8_t byte;
typedef uint16_t word;
// typedef uint32_t ulong;
#define ulong uint32_t

typedef struct {
  bb_result_t bbres;
  ulong type;
  FILE *file;
  } myresource;

int sf_getresource( int num, int ispic, int method, myresource * res);
void sf_freeresource( myresource *res);

#ifndef true
#define true 1
#endif
#ifndef false
#define false 0
#endif

#define NON_STD_COLS 238

// thiss assumes RGBA with lsb = R

static inline ulong RGB5ToTrue( word w)
  {
  int _r = w & 0x001F; int _g = (w & 0x03E0)>>5; int _b = (w & 0x7C00)>>10;
  _r = (_r<<3) | (_r>>2);
  _g = (_g<<3) | (_g>>2);
  _b = (_b<<3) | (_b>>2);
  return (ulong) ( _r | (_g<<8) | (_b<<16));
  }

static inline word TrueToRGB5( ulong u)
  {
  return (word)(((u >> 3) & 0x001f) | ((u >> 6) & 0x03e0) | ((u >> 9) & 0x7c00));
  }

void reset_memory(void);
void replay_close(void);
void set_header_extension (int entry, zword val);
int colour_in_use(zword colour);

// various data

extern bool 	m_tandy;
extern bool	m_quetzal;
//	CRect m_wndSize;
//	CString m_propFontName;
//	CString m_fixedFontName;
//	int m_fontSize;
extern int 	m_v6scale;
extern int	m_gfxScale;
extern ulong	m_defaultFore;
extern ulong	m_defaultBack;
extern ulong	m_colours[11];
extern ulong	m_nonStdColours[NON_STD_COLS];
extern int	m_nonStdIndex;
extern bool	m_exitPause;
extern bool	m_lineInput;
//extern bool	m_IsInfocomV6;
//	bool m_fastScroll;
extern bool	m_morePrompts;
//	int m_leftMargin;
//	int m_rightMargin;
//	FILE* m_blorbFile;
//	bb_map_t* m_blorbMap;
//	GameInfo m_gameInfo;
extern int	AcWidth;
extern int	AcHeight;
extern int	m_random_seed;
extern int	m_fullscreen;
extern int	m_reqW, m_reqH;
extern char *	m_fontfiles[8];
extern bool	m_localfiles;
extern int	m_no_sound;
extern int 	m_vga_fonts;
extern int	SFdticks;
extern volatile bool	SFticked;
extern char *	m_fontdir;
extern bool	m_aafonts;
extern char *	m_setupfile;
extern int m_frequency;

extern double 	m_gamma;

// sf_resource.c

// must be called as soon as possible (i.e. by os_process_arguments())
int sf_load_resources( char *givenfn);

typedef struct {
  int number;		// 0 means unallocated
  int width, height;
  byte *pixels;
  } sf_picture;

#define DEFAULT_GAMMA 2.2

void sf_setgamma( double gamma);

//int sf_loadpic( int num, sf_picture *gfx);

// get pointer from cache
sf_picture * sf_getpic( int num);

void sf_flushtext();

// glyph
typedef struct {
  byte dx;
  byte w, h;
  char xof, yof;
  byte bitmap[0];
  } SF_glyph;

typedef struct sfontstruct SFONT;

extern SFONT * (*ttfontloader)( char *fspec, int *err);
extern void    (*ttfontsdone)();

struct sfontstruct {
  int refcount;
  void (*destroy)(SFONT *);
  int (*height)(SFONT *);
  int (*ascent)(SFONT *);
  int (*descent)(SFONT *);
  int (*minchar)(SFONT *);
  int (*maxchar)(SFONT *);
  int (*hasglyph)(SFONT *,word,int);
  SF_glyph *(*getglyph)(SFONT *,word,int);
  int antialiased;
  void *data;
  };

typedef struct {
  SFONT *font;
  int proportional;
  int style, zfontnum;
  int cx, cy;		// cursor position - 0 based
  int oh;		// overhang
  unsigned long fore, back;
  bool foreDefault, backDefault, backTransparent;
  } SF_textsetting;

SF_textsetting * sf_curtextsetting();

void sf_writeglyph( SF_glyph *g);

void sf_fillrect( unsigned long color, int x, int y, int w, int h);


int sf_GetProfileInt( const char *sect, const char *id, int def);
double sf_GetProfileDouble( const char *sect, const char *id, double def);
char * sf_GetProfileString( const char *sect, const char *id, char * def);

void sf_readsettings();

ulong sf_GetColour( int colour);
ulong sf_GetDefaultColour(bool fore);
int sf_GetColourIndex( ulong colour);

void sf_initvideo( int w, int h, int full);

int sf_initsound();

void sf_cleanup_all();
void sf_regcleanfunc( void *f, const char *nam);
#define CLEANREG( f) sf_regcleanfunc( (void *)f, #f)

const char * sf_msgstring( int id);

// consts for msg ids
enum { IDS_BLORB_GLULX, IDS_BLORB_NOEXEC, IDS_MORE, IDS_HIT_KEY_EXIT, IDS_TITLE,
 IDS_FATAL, IDS_FROTZ, IDS_FAIL_DIRECTSOUND, IDS_FAIL_MODPLUG, IDS_ABOUT_INFO,
 IDS_SAVE_FILTER, IDS_SAVE_TITLE, IDS_RESTORE_TITLE,
 IDS_SCRIPT_FILTER, IDS_SCRIPT_TITLE,
 IDS_RECORD_FILTER, IDS_RECORD_TITLE, IDS_PLAYBACK_TITLE,
 IDS_AUX_FILTER, IDS_SAVE_AUX_TITLE, IDS_LOAD_AUX_TITLE };

bool sf_IsInfocomV6();

ulong sf_blend( int a, ulong s, ulong d);

void sf_sleep( int millisecs);

unsigned long sf_ticks (void);

void sf_DrawInput(zchar * buffer, int pos, int ptx, int pty, int width, bool cursor);

int sf_aiffwav( FILE *f, int foffs, void ** wav, int *size);

int sf_pkread( FILE *f, int foffs,  void ** out, int *size);

ulong * sf_savearea( int x, int y, int w, int h);
void sf_restoreareaandfree( ulong *s);
#define SF_NOTIMP (-9999)

zword sf_read_key( int timeout, int cursor, int allowed);

int sf_user_fdialog( bool exist, const char *def, const char *filt, const char *title, char **res);
extern int (*sf_osdialog)( bool ex, const char *def, const char *filt, const char *tit, char **res,
	ulong *sbuf, int sbp, int ew, int eh, int isfull);

#ifdef WIN32
#define OS_PATHSEP ';'
#else
#define OS_PATHSEP ':'
#endif

// virtual keys
#define VK_TAB	0x16
#define VK_INS	0x17

// for AIFF resampling

typedef struct CONVstruct CONV;
struct CONVstruct {
	double ratio;
	// input
	int channels;
	int bytespersam;
	// returns num of output samples
	int (* doCONV)( CONV *, FILE *, void *, int, int );
	void (* finishCONV)( CONV *);
	int maxin, maxout;
	float *inbuf, *outbuf;
	void *aux;
};


#endif



/*** screen window ***/
/*
typedef struct {
    zword y_pos;
    zword x_pos;
    zword y_size;
    zword x_size;
    zword y_cursor;
    zword x_cursor;
    zword left;
    zword right;
    zword nl_routine;
    zword nl_countdown;
    zword style;
    zword colour;
    zword font;
    zword font_size;
    zword attribute;
    zword line_count;
    zword true_fore;
    zword true_back;
} Zwindow;
*/
