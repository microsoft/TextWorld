#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include <zlib.h>

#ifdef __WIN32__
#include <io.h>
#endif

#include "sf_frotz.h"


typedef void (*CLEANFUNC)();

typedef struct cfstruct cfrec;

struct cfstruct {
  CLEANFUNC func;
  cfrec *next;
  const char *name;
  };

static cfrec *cflist = NULL;

void sf_regcleanfunc( void *f, const char *p){
  cfrec *n = calloc(1,sizeof(cfrec));
  if (n)
	{
	if (!p) p = "";
	n->func = (CLEANFUNC) f;
	n->name = p;
	n->next = cflist;
	cflist = n;
	}
  }

void sf_cleanup_all()
  {
  while (cflist)
	{
	cfrec *n = cflist->next;
//printf("cleanup c%p [%s] n%p\n",cflist,cflist->name,n);
	if (cflist->func) cflist->func();
	free(cflist);
	cflist = n;
	}
//printf("Cleanup done.\n");
  }

/*
 * os_reset_screen
 *
 * Reset the screen before the program ends.
 *
 */
void os_reset_screen(void)
  {
  sf_flushdisplay();
//	theWnd->FlushDisplay();
//	theWnd->ResetOverhang();

  if (m_exitPause)
	{
	const char *hit = sf_msgstring(IDS_HIT_KEY_EXIT);
	os_set_font(TEXT_FONT);
	os_set_text_style(0);
	screen_new_line();

	while (*hit)
		os_display_char((*hit++));
	os_read_key(0,1);
	}

  sf_cleanup_all();
  }




int user_background = -1;
int user_foreground = -1;
int user_emphasis = -1;
int user_bold_typing = -1;
int user_reverse_bg = -1;
int user_reverse_fg = -1;
int user_screen_height = -1;
int user_screen_width = -1;
int user_tandy_bit = -1;
//int user_random_seed = -1;
int user_font = 1;
int m_random_seed = -1;
int m_fullscreen = -1;
int m_reqW = 0, m_reqH = 0;
int m_vga_fonts = 0;
extern char * m_setupfile;
extern char	m_names_format;
static char user_names_format = 0;
extern char *m_reslist_file;
extern int option_scrollback_buffer;

static char *info1 =
	"\n"
	"SDL Frotz V%d.%02d build %s - interpreter for z-code games.\n"
	"Complies with Standard 1.0; supports Blorb resources and Quetzal save files.\n"
	"Based on Frotz 2.40 by Stefan Jokisch and WindowsFrotz2000 by David Kinder.\n"
	"\n"
	"Syntax: sfrotz [options] story-file\n\n";

static char *infos[] = {
	"-a   watch attribute setting",
	"-A   watch attribute testing",
	"-b # background colour",
	"-c # context lines",
	"-f # foreground colour",
	"-F   fullscreen mode",
	"-h # screen height",
	"-i   ignore runtime errors",
	"-l # left margin",
	"-L   use local resources",
	"-o   watch object movement",
	"-O   watch object locating",
	"-p   alter piracy opcode",
	"-q   quiet (disable sound)",
	"-r # right margin",
	"-R   save/restore in old Frotz format",
	"-s # random number seed value",
	"-S # transcript width",
	"-t   set Tandy bit",
	"-u # slots for multiple undo",
	"-w # screen width",
	"-x   expand abbreviations g/x/z",
	"-V   force VGA fonts",
	"-Z # error checking (see below)",
	NULL};

static char *info2 = 
	"\nError checking: 0 none, 1 first only (default), 2 all, 3 exit after any error.\n"
	"For more options and explanations, please read the HTML manual.\n";

static char * getbuilddatetime( int tf);

#define WIDCOL 40
static void usage()
  {
  char **p = infos; int i=0,len=0;
  printf(info1,SFROTZ_MAJOR,SFROTZ_MINOR,getbuilddatetime(1));
  while (*p)
	{
	if (i)
		{
		while (len > 0){ fputc(' ',stdout); len--;}
		puts(*p);
		}
	else
		{
		fputs("  ",stdout);
		fputs(*p,stdout);
		len = WIDCOL-strlen(*p)-2;
		}
	i = 1-i;
	p++;
	}
  if (i) fputc('\n',stdout);
  puts (info2);
  }

/*
 * parse_options
 *
 * Parse program options and set global flags accordingly.
 *
 */

static const char *progname = NULL;

extern char script_name[];
extern char command_name[];
extern char save_name[];
extern char auxilary_name[];

char stripped_story_name[100];

extern char *optarg;
extern int optind;
extern int m_timerinterval;

static char *options = "@:aAb:B:c:D:f:Fh:iI:l:Lm:N:oOpqr:Rs:S:tTu:Vw:xZ:";

static int limit( int v, int m, int M)
  {
  if (v < m) return m;
  if (v > M) return M;
  return v;
  }

static void parse_options (int argc, char **argv)
  {
  int c;

  do {

	int num = 0, copt = 0;;

	c = getopt (argc, argv, options);

	if (optarg != NULL)
	    {
	    num = atoi (optarg);
	    copt = optarg[0];
	    }

	if (c == 'a')
	    f_setup.attribute_assignment = 1;
	if (c == 'A')
	    f_setup.attribute_testing = 1;
	if (c == 'b')
	    user_background = num;
	if (c == 'B')
	    option_scrollback_buffer = num;
	if (c == 'c')
	    f_setup.context_lines = num;
	if (c == 'D')
		{
		if (copt == 'k') m_reqW = -1;
		else sscanf(optarg,"%dx%d",&m_reqW,&m_reqH);
		m_fullscreen = 1;
		}
	if (c == 'm')
	    m_timerinterval = limit(num,10,1000000);
	if (c == 'N')
	    user_names_format = copt;
	if (c == '@')
	    m_reslist_file = optarg;
	if (c == 'I')
	    m_setupfile = optarg;
	if (c == 'f')
	    user_foreground = num;
	if (c == 'F')
	    m_fullscreen = 1;
	if (c == 'h')
	    user_screen_height = num;
	if (c == 'i')
	    f_setup.ignore_errors = 1;
	if (c == 'l')
	    f_setup.left_margin = num;
	if (c == 'L')
	    m_localfiles = true;
	if (c == 'q')
	    m_no_sound = 1;
	if (c == 'o')
	    f_setup.object_movement = 1;
	if (c == 'O')
	    f_setup.object_locating = 1;
	if (c == 'p')
	    f_setup.piracy = 1;
	if (c == 'r')
	    f_setup.right_margin = num;
	if (c == 'R')
	    f_setup.save_quetzal = 0;
	if (c == 's')
	    m_random_seed = num;
	if (c == 'S')
	    f_setup.script_cols = num;
	if (c == 't')
	    user_tandy_bit = 1;
	if (c == 'T')
	    sf_osdialog = NULL;
	if (c == 'u')
	    f_setup.undo_slots = num;
	if (c == 'V')
	    m_vga_fonts = 1;
	if (c == 'w')
	    user_screen_width = num;
	if (c == 'x')
	    f_setup.expand_abbreviations = 1;
	if (c == 'Z')
	    if (num >= ERR_REPORT_NEVER && num <= ERR_REPORT_FATAL)
	      f_setup.err_report_mode = num;
	if (c == '?')
		optind = argc;
	} while (c != EOF && c != '?');

  }/* parse_options */



/*
 * os_process_arguments
 *
 * Handle command line switches. Some variables may be set to activate
 * special features of Frotz:
 *
 *     option_attribute_assignment
 *     option_attribute_testing
 *     option_context_lines
 *     option_object_locating
 *     option_object_movement
 *     option_left_margin
 *     option_right_margin
 *     option_ignore_errors
 *     option_piracy
 *     option_undo_slots
 *     option_expand_abbreviations
 *     option_script_cols
 *
 * The global pointer "story_name" is set to the story file name.
 *
 */

void os_process_arguments (int argc, char *argv[])
  {
  const char *p;
  int i;

	// install signal handlers

  sf_installhandlers();

    /* Parse command line options */

  parse_options(argc, argv);

  if (optind != argc - 1) 
	{
	usage();
	exit (EXIT_FAILURE);
	}

    /* Set the story file name */

  story_name = argv[optind];

	// load resources
	// it's useless to test the retval, as in case of error it does not return
  sf_load_resources( story_name);

    /* Strip path and extension off the story file name */

  p = story_name;

  for (i = 0; story_name[i] != 0; i++)
	if (story_name[i] == '\\' || story_name[i] == '/'
	    || story_name[i] == ':')
	    p = story_name + i + 1;

    for (i = 0; p[i] != 0 && p[i] != '.'; i++)
	stripped_story_name[i] = p[i];

    stripped_story_name[i] = 0;

    /* Create nice default file names */

  strcpy (script_name, stripped_story_name);
  strcpy (command_name, stripped_story_name);
  strcpy (save_name, stripped_story_name);
  strcpy (auxilary_name, stripped_story_name);

  strcat (script_name, ".scr");
  strcat (command_name, ".rec");
  strcat (save_name, ".sav");
  strcat (auxilary_name, ".aux");

    /* Save the executable file name */

  progname = argv[0];

  sf_readsettings();

  if (user_screen_width > 0) AcWidth = user_screen_width;
  if (user_screen_height > 0) AcHeight = user_screen_height;

  if (user_names_format) m_names_format = user_names_format;

  if (user_background != -1) m_defaultBack = sf_GetColour(user_background);
  if (user_foreground != -1) m_defaultFore = sf_GetColour(user_foreground);
  if (user_tandy_bit != -1) m_tandy = user_tandy_bit;

  sf_initfonts();

  }/* os_process_arguments */

#ifdef WIN32
#include <windows.h>
#else
#include <time.h>
#include <sys/time.h>
#endif

#ifdef WIN32

void sf_sleep( int msecs){
  Sleep(msecs);
  }

unsigned long sf_ticks( void){
  return (GetTickCount());
  }

#else

//#include <unistd.h>

void sf_sleep( int msecs){
  usleep(msecs/1000);
  }

unsigned long sf_ticks (void) {
  struct timeval now;
  static struct timeval start;
  static int started = 0;
  unsigned long ticks;
  now.tv_sec = now.tv_usec = 0;
  gettimeofday(&now, NULL);
  if (!started){
	started = 1;
	start = now;
	}
  ticks = (now.tv_sec-start.tv_sec)*1000 + (now.tv_usec-start.tv_usec)/1000;
//  ticks = now.tv_sec*1000 + now.tv_usec/1000;
  return ticks;
  }

#endif

/*
 * os_read_file_name
 *
 * Return the name of a file. Flag can be one of:
 *
 *    FILE_SAVE     - Save game file
 *    FILE_RESTORE  - Restore game file
 *    FILE_SCRIPT   - Transscript file
 *    FILE_RECORD   - Command file for recording
 *    FILE_PLAYBACK - Command file for playback
 *    FILE_SAVE_AUX - Save auxilary ("preferred settings") file
 *    FILE_LOAD_AUX - Load auxilary ("preferred settings") file
 *
 * The length of the file name is limited by MAX_FILE_NAME. Ideally
 * an interpreter should open a file requester to ask for the file
 * name. If it is unable to do that then this function should call
 * print_string and read_string to ask for a file name.
 *
 */

extern char stripped_story_name[];

static char *getextension( int flag)
  {
  char *ext = ".aux";

  if (flag == FILE_SAVE || flag == FILE_RESTORE)
	ext = ".sav";
  else if (flag == FILE_SCRIPT)
	ext = ".scr";
  else if (flag == FILE_RECORD || flag == FILE_PLAYBACK)
	ext = ".rec";

  return ext;
  }

static bool newfile( int flag)
  {
  if (flag == FILE_SAVE || flag == FILE_SAVE_AUX || flag == FILE_RECORD)
	return true;
  return false;
  }

static char buf[FILENAME_MAX];

static const char *getnumbername( const char *def, char *ext)
  {
  int len, number = 0;
  strcpy(buf,stripped_story_name);
  len = strlen(buf);
  for (;;){
	sprintf(buf+len,"%03d%s",number++,ext);
	if (access(buf,F_OK)) break;
	}
  return buf;
  }

static const char *getdatename( const char *def, char *ext)
  {
  char *p;

  time_t t; struct tm *tm;
  time(&t);
  tm = localtime(&t);

  strcpy(buf,stripped_story_name);
  p = buf + 1;
  if (*p) p++;
  sprintf(p,"%04d%02d%02d%02d%02d%s",
 	tm->tm_year + 1900, tm->tm_mon + 1, tm->tm_mday,
	tm->tm_hour, tm->tm_min, ext);
  return buf;
  }

// fdialog( existing, defname, filter, title, &resultstr)
static int ingame_read_file_name (char *file_name, const char *default_name, int flag);
static int dialog_read_file_name (char *file_name, const char *default_name, int flag);

int os_read_file_name (char *file_name, const char *default_name, int flag)
  {
  int st;
  const char *initname = default_name;
  char *ext = ".aux";

  if (newfile(flag))
    {
    char *ext = getextension(flag);
    if (m_names_format == 'd') initname = getdatename(initname,ext);
    else if (m_names_format == 'n') initname = getnumbername(initname,ext);
    }

  st = dialog_read_file_name( file_name, initname, flag);
  if (st == SF_NOTIMP) st = ingame_read_file_name( file_name, initname, flag);
  return st;
  }

static int ingame_read_file_name (char *file_name, const char *default_name, int flag)
  {
  char *extension;
  FILE *fp;
  bool terminal;
  bool result;

  bool saved_replay = istream_replay;
  bool saved_record = ostream_record;

    /* Turn off playback and recording temporarily */

  istream_replay = FALSE;
  ostream_record = FALSE;

    /* Select appropriate extension */

  extension = getextension(flag);

    /* Input file name (reserve four bytes for a file name extension) */

  print_string ("Enter file name (\"");
  print_string (extension);
  print_string ("\" will be added).\nDefault is \"");
  print_string (default_name);
  print_string ("\": ");

  read_string (MAX_FILE_NAME - 4, (byte *) file_name);

    /* Use the default name if nothing was typed */

  if (file_name[0] == 0)
	strcpy (file_name, default_name);
  if (strchr (file_name, '.') == NULL)
	strcat (file_name, extension);

    /* Make sure it is safe to use this file name */

  result = TRUE;

    /* OK if the file is opened for reading */

  if (!newfile(flag))
	goto finished;

    /* OK if the file does not exist */

  if ((fp = fopen (file_name, "rb")) == NULL)
	goto finished;

    /* OK if this is a pseudo-file (like PRN, CON, NUL) */

  terminal = isatty(fileno(fp));

  fclose (fp);

  if (terminal)
	goto finished;

    /* OK if user wants to overwrite */

  result = read_yes_or_no ("Overwrite existing file");

finished:

    /* Restore state of playback and recording */

  istream_replay = saved_replay;
  ostream_record = saved_record;

  return result;

  }/* os_read_file_name */

static int dialog_read_file_name(char *file_name, const char *default_name, int flag)
  {
  int filter = 0;
  int title = 0, st;
  char *res;

  sf_flushdisplay();
//	theWnd->ResetOverhang();

  switch (flag)
	{
	case FILE_SAVE:
		filter = IDS_SAVE_FILTER;
		title = IDS_SAVE_TITLE;
		break;
	case FILE_RESTORE:
		filter = IDS_SAVE_FILTER;
		title = IDS_RESTORE_TITLE;
		break;
	case FILE_SCRIPT:
		filter = IDS_SCRIPT_FILTER;
		title = IDS_SCRIPT_TITLE;
		break;
	case FILE_RECORD:
		filter = IDS_RECORD_FILTER;
		title = IDS_RECORD_TITLE;
		break;
	case FILE_PLAYBACK:
		filter = IDS_RECORD_FILTER;
		title = IDS_PLAYBACK_TITLE;
		break;
	case FILE_SAVE_AUX:
		filter = IDS_AUX_FILTER;
		title = IDS_SAVE_AUX_TITLE;
		break;
	case FILE_LOAD_AUX:
		filter = IDS_AUX_FILTER;
		title = IDS_LOAD_AUX_TITLE;
		break;
	default:
		return 0;
	}

// fdialog( existing, defname, filter, title, &resultstr)
// returns 0 if OK
  st = sf_user_fdialog( !newfile(flag), default_name, sf_msgstring(filter), sf_msgstring(title), &res);
  if (st == SF_NOTIMP) return st;
  if (st == 0)
	{
	strncpy(file_name,res,MAX_FILE_NAME);
	file_name[MAX_FILE_NAME-1] = 0;
	return 1;
	}
  return 0;
  }

typedef struct {
  void *link;
  char *str;
  } Dynstr;

static Dynstr * strings = NULL;

static void freestrings()
  {
  while (strings)
	{
	Dynstr *r = strings->link;
	if (strings->str) free(strings->str);
	free(strings);
	strings = r;
	}
  }

static char *mystrdup( char *p)
  {
  Dynstr *r;
  if (!p) return p;
  p = strdup(p);
  if (!p) return p;
  r = calloc(1,sizeof(Dynstr));
  if (r)
	{
	if (!strings) CLEANREG(freestrings);
	r->link = strings;
	r->str = p;
	strings = r;
	}
  return p;
  }

static char *rc = NULL;

void sf_FinishProfile()
  {
//printf("finishprofile\n");
  if (!rc) return;
  free(rc);
  rc = NULL;
  }

void sf_InitProfile( const char *fn)
  {
  FILE *f; int size; char *s, *d;

  if (!fn) return;
  f = fopen(fn,"rb");
  if (!f) return;
  fseek(f,0,SEEK_END);
  size = ftell(f);
  if (!size) { fclose(f); return;}
  rc = malloc(size+1);
  if (!rc) { fclose(f); return;}
  fseek(f,0,0);
  fread(rc,1,size,f);
  fclose(f);
  rc[size] = 0;

  s = d = rc;

  while (*s)
    {
    if (*s == '#')
	{
	while ((*s) && (*s != '\n')) s++;
	if (!*s) break;
	}
    else
	*d++ = *s++;
    }
  *d = 0;

  CLEANREG(sf_FinishProfile);
  }


static char * findsect( const char *sect)
  {
  int ns = strlen(sect);
  char *r = rc;
  while (r)
    {
//printf("{%s}\n",r);
    r = strchr(r,'[');
    if (!r) return NULL;
    r++;
    if (strncmp(r,sect,ns)) continue;
    return (r+ns);
    }
  }

static char * findid( const char *sect, const char *id)
  {
  int nid = strlen(id);
  char *p, *r, *sav, *rq, *fnd = NULL;
  r = findsect(sect);
//printf("findsect(%s) %p\n",sect,r);
  if (!r) return NULL;
  sav = strchr(r,'['); if (sav) *sav = 0;
  while (r)
	{
	r = strstr(r,id);
	if (!r) break;
	rq = r+nid;
	if ((*(byte *)(r-1) <= ' ') && ((*rq == ' ') || (*rq == '=')))
		{
		while (*rq) if (*rq++ == '=') break;
		if (*rq) { fnd = rq; break;}
		}
	r = rq;
	}
  if (sav) *sav = '[';
  return fnd;
  }

int sf_GetProfileInt( const char *sect, const char *id, int def)
  {
  if (rc)
	{
	char *p = findid(sect,id);
	if (p) def = atoi(p);
	}
  return def;
  }

double sf_GetProfileDouble( const char *sect, const char *id, double def)
  {
  if (rc)
	{
	char *p = findid(sect,id);
	if (p) def = atof(p);
	}
  return def;
  }

char * sf_GetProfileString( const char *sect, const char *id, char * def)
  {
  char *q=NULL, sav=0;
  if (rc)
    {
    char *p = findid(sect,id);
//printf("findid(%s,%s) %p\n",sect,id,p);
    if (p)
	{
	int quoted = 0;
	while (*p)
		{
		if (*p == '\"') { quoted = 1; p++; break;}
		if ((byte)(*p) > ' ') break;
		}
	if (*p)
		{
		if (quoted) q = strchr(p,'\"');
		if (!q)
			{
			q = p;
			while (*q > ' ') q++;
			sav = *q; *q = 0;
			}
		}
	def = p;
	}
    }
  if (def) def = mystrdup(def);
  if (sav) *q = sav;
  return def;
  }

//  A.  Local file header:
// 
//         local file header signature   0  4 bytes  (0x04034b50)
//         version needed to extract     4  2 bytes
//         general purpose bit flag      6  2 bytes
//         compression method            8  2 bytes
//         last mod file time           10  2 bytes
//         last mod file date           12  2 bytes
//         crc-32                       14  4 bytes
//         compressed size              18  4 bytes
//         uncompressed size            22  4 bytes
//         file name length             26  2 bytes
//         extra field length           28  2 bytes
// 
//         file name (variable size)
//         extra field (variable size)

#define plong( b) (((int)((b)[3]) << 24) + ((int)((b)[2]) << 16) +\
	((int)((b)[1]) << 8) + (int)((b)[0]))

#define pshort( b) (((int)((b)[1]) << 8) + (int)((b)[0]))

static int myunzip( int csize, byte *cdata, byte *udata)
  {
  byte window[32768];
  z_stream z;
  int st;

  unsigned myin( void *d, byte **b){return 0;}
  int myout( void *d, byte *b, unsigned n)
	{
	memcpy(udata,b,n); udata += n;
	return 0;
	}

  memset(&z,0,sizeof(z));

  st = inflateBackInit( &z, 15, window);
  if (st) return st;

  z.next_in = cdata;
  z.avail_in = csize;

  for (;;){
	st = inflateBack( &z, myin, NULL, myout, NULL);
	if (st == Z_STREAM_END) break;
	if (st) return st;
	}

  st = inflateBackEnd(&z);
  return st;
  }

int sf_pkread( FILE *f, int foffs,  void ** out, int *size)
  {
  byte hd[30], *dest;
  byte *data, *cdata;
  int csize, usize, cmet, skip, st;

  fseek(f,foffs,SEEK_SET);
  fread(hd,1,30,f);
  cmet = pshort(hd+8);
  if (cmet != 8) return -10;
  csize = plong(hd+18);
  usize = plong(hd+22);
  if (csize <= 0) return -11;
  if (usize <= 0) return -12;
  data = malloc(usize);
  if (!data) return -13;
  cdata = malloc(csize);
  if (!cdata){ free(data); return -14;}
  skip = pshort(hd+26) + pshort(hd+28);
  fseek(f,foffs+30+skip,SEEK_SET);
  fread(cdata,1,csize,f);
//printf("%02x csize %d usize %d skip %d\n",cdata[0],csize,usize,skip);

  st = myunzip(csize,cdata,data);

  free(cdata);
  if (st)
	{
	free(data);
	return st;
	}
  *out = (void *)data;
  *size = usize;
  return st;
  }

//////////////////////////

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/stat.h>
#ifdef WIN32
#include <windows.h>
#else
#include <unistd.h>
#endif

static char * getexepath( char *buf){
#ifdef WIN32
  buf[0] = 0;
  GetModuleFileName(NULL,buf,262);
#else
  char baf[80];
  int n;
  sprintf(baf,"/proc/%d/exe",getpid());
  n = readlink(baf,buf,262);
  if (n < 0) n = 0;
  buf[n] = 0;
#endif
  return buf;
  }

#ifndef WIN32
#define _stat stat
#endif

static char * getbuilddatetime( int tf){
  time_t t; struct tm *tm;
  struct _stat sta;
  static char buf[263];

  getexepath(buf);
  _stat(buf,&sta);
  t = sta.st_mtime;
  tm = localtime(&t);
  buf[0] = 0;
  sprintf(buf,"%04d%02d%02d",
		tm->tm_year + 1900, tm->tm_mon + 1, tm->tm_mday);
  if (tf){
    strcat(buf,".");
    sprintf(buf+strlen(buf),"%02d%02d%02d",
	tm->tm_hour, tm->tm_min, tm->tm_sec);
    }
  return buf;
  }


