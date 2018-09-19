#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <math.h>

#include <ft2build.h>
#include FT_FREETYPE_H

#include "sf_frotz.h"

/////////////////////////////////////////////////////////////////

static char * sf_searchfile( char *fn, int fnlen, char *buf, char *paths)
  {
  char *p;
  if (!fn) return NULL;
  if (!paths) paths = "";
  if (fnlen < 0) fnlen = strlen(fn);
  if (!fnlen) return NULL;
  for (;;)
    {
    int plen;
    p = strchr(paths,OS_PATHSEP);
    if (p)
	plen = p-paths;
    else
	plen = strlen(paths);
    if (plen) strncpy(buf,paths,plen);
    buf[plen] = 0;
    if ((plen) && (buf[plen-1] != '\\') && (buf[plen-1] != '/'))
	strcat(buf,"/");
    plen = strlen(buf);
    strncpy(buf+plen,fn,fnlen);
    buf[plen+fnlen] = 0;
//printf("try[%s]\n",buf);
    if (access(buf,F_OK)==0) return buf;
    if (p) paths = p+1;
    else break;
    }
  return NULL;
  }

/////////////////////////////////////////////////////////////////

typedef struct {
  SFONT sfont;
  int ascent, descent, height;
  int minchar, maxchar, totglyphs;
  SF_glyph *glyphs[0];
  } MYFONT;

// destructor
static void bdestroy( SFONT *s)
  {
  if (s)
    {
    int i; MYFONT *f = (MYFONT *)s;
    for (i=0;i<f->totglyphs;i++)
	if (f->glyphs[i]) free(f->glyphs[i]);
    free(s);
    }
  }

static int bheight( SFONT *s)
  {
  if (s) return ((MYFONT *)s)->height;
  return 0;
  }

static int bascent( SFONT *s)
  {
  if (s) return ((MYFONT *)s)->ascent;
  return 0;
  }

static int bdescent( SFONT *s)
  {
  if (s) return ((MYFONT *)s)->descent;
  return 0;
  }

static int bminchar( SFONT *s)
  {
  if (s) return ((MYFONT *)s)->minchar;
  return 0;
  }

static int bmaxchar( SFONT *s)
  {
  if (s) return ((MYFONT *)s)->maxchar;
  return 0;
  }

static SF_glyph *getglyph( SFONT *s, word c, int allowdef)
  {
  if (s)
    {
    int i; MYFONT *f = (MYFONT *)s;
    if (c < f->minchar || c > f->maxchar)
	{
	if (allowdef) c = 0;
	else return NULL;
	}
    return f->glyphs[c];
    }
  return NULL;
  }

static int hasglyph( SFONT *fo, word c, int allowdef)
  {
  return (getglyph(fo,c,allowdef) != NULL);
  }

static int inited = 0, initerr = 0;
static FT_Library library;

static void libfinish()
  {
  if (!inited) return;
  FT_Done_FreeType( library );
  inited = 0;
  }

static void libinit()
  {
  if (initerr) return;
  if (inited) return;
  initerr = FT_Init_FreeType( &library );  /* initialize library */
  /* error handling omitted */
  if (initerr)
	printf("FT_Init_FreeType: error %d\n",initerr);
  else
	{
	inited = 1;
	atexit(libfinish);
	}
  }


static MYFONT * makefont( int totglyphs)
  {
  MYFONT * res;
  res = calloc(1,sizeof(MYFONT)+totglyphs*sizeof(SF_glyph *));
  if (!res) return NULL;
  res->sfont.destroy = bdestroy;
  res->sfont.height = bheight;
  res->sfont.ascent = bascent;
  res->sfont.descent = bdescent;
  res->sfont.minchar = bminchar;
  res->sfont.maxchar = bmaxchar;
  res->sfont.hasglyph = hasglyph;
  res->sfont.getglyph = getglyph;
  res->totglyphs = totglyphs;
  res->maxchar = totglyphs - 1;
  return res;
  }

#define MAXUNI 0x153

static void setglyph( MYFONT *f, FT_Face face, int ch)
  {
  int err, gid = FT_Get_Char_Index( face, ch);
  int mode = FT_RENDER_MODE_MONO;
  SF_glyph *res;
  FT_GlyphSlot slot = face->glyph;
  int i,j, nbypr, pitch;
  unsigned char *s;
  FT_Bitmap *bitmap;

  if (m_aafonts) mode = FT_RENDER_MODE_NORMAL;

  err = FT_Load_Glyph( face, gid, 0);
  if (err) return;
  if (slot->format != FT_GLYPH_FORMAT_BITMAP)
    {
    err = FT_Render_Glyph(slot, mode);
    if (err) return;
    }
  bitmap = &slot->bitmap;
  nbypr = m_aafonts ? bitmap->width : (bitmap->width+7)/8;
  res = calloc(1,sizeof(SF_glyph) + nbypr*bitmap->rows);
  if (!res) return;
  for (i=0;i<bitmap->rows;i++)
    for (j=0;j<nbypr;j++)
	res->bitmap[i*nbypr+j] = bitmap->buffer[i*bitmap->pitch+j];

//printf("%c %d %p  w%d\n",ch,bitmap->pitch,res,bitmap->width);
//{
//int i,j; unsigned char *p = &(res->bitmap[0]);
//for (i=0;i<bitmap->rows;i++){
//  for (j=0;j<nbypr;j++) printf("%02x",*p++);
//  printf("\n");
//  }
//}
  res->w = bitmap->width;
  res->h = bitmap->rows;
  res->dx = slot->advance.x/64;
  res->xof = slot->bitmap_left;
  res->yof = slot->bitmap_top - bitmap->rows;

  f->glyphs[ch] = res;
  }

static SFONT * loadftype( char *fname, int size, int *err)
  {
  MYFONT *res;
  FT_Face face;
  int i;

  *err = 0;
  if (!fname) { *err = -8; return NULL;}
  libinit();
  if (initerr) { *err = -99; return NULL;}

  res = makefont( MAXUNI+1);
  if (!res) { *err = -3; return NULL;}

  *err = FT_New_Face( library, fname, 0, &face ); /* create face object */
  if (*err){ res->sfont.destroy(&res->sfont); return NULL; }

  *err = FT_Set_Pixel_Sizes( face, size, size);
  if (*err){ res->sfont.destroy(&res->sfont); return NULL; }

  res->ascent = face->size->metrics.ascender/64;
  res->descent = -face->size->metrics.descender/64;
  res->height = res->ascent+res->descent; //face->size->metrics.height/64;

  res->sfont.antialiased = m_aafonts;
  res->minchar = 32;
  setglyph(res,face,0);
  for (i=32;i<127;i++) setglyph(res,face,i);
  for (i=0xa0;i<256;i++) setglyph(res,face,i);
  setglyph(res,face,0x152);
  setglyph(res,face,0x153);

  FT_Done_Face( face );

  return (SFONT *) res;
  }

#define DEFSIZE 14

#ifdef WIN32
#define SYSFONTS "c:/windows/fonts"
#else
#define SYSFONTS "/usr/share/fonts/freetype"
#endif

SFONT * sf_loadftype( char *fspec, int *err)
  {
  char buf[FILENAME_MAX], *fn, *at, *fenv;
  int size = DEFSIZE, fnlen=-1;

  at = strchr(fspec,'@');
  if (at)
	{
	fnlen = at-fspec;
	size = atoi(at+1);
	}

  fn = sf_searchfile( fspec, fnlen, buf, "");
  if (!fn) fn = sf_searchfile( fspec, fnlen, buf, "./");
  if (!fn)
    if (m_fontdir)
	fn = sf_searchfile( fspec, fnlen, buf, m_fontdir);
  if (!fn) fn = sf_searchfile( fspec, fnlen, buf, SYSFONTS);
  if (!fn)
	{
	fenv = getenv("FONTS");
	if (fenv) fn = sf_searchfile( fspec, fnlen, buf, fenv);
	}

  if (!fn) return NULL;

  return loadftype(fn,size,err);
  }

//////////////////////////////////////////

static void initloader() __attribute__((constructor));
static void initloader()
  {
  ttfontloader = sf_loadftype;
  ttfontsdone = libfinish;
  }

