/*
 * ux_input.c - Unix interface, input functions
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

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>

#include <sys/time.h>

#ifdef USE_NCURSES_H
#include <ncurses.h>
#else
#include <curses.h>
#endif

#include "ux_frotz.h"

static int start_of_prev_word(int, const zchar*);
static int end_of_next_word(int, const zchar*, int);

static struct timeval global_timeout;

/* Some special characters. */
#define MOD_CTRL 0x40
#define MOD_META 0x80
#define CHR_DEL (MOD_CTRL ^'?')

/* These are useful for circular buffers.
 */
#define RING_DEC( ptr, beg, end) (ptr > (beg) ? --ptr : (ptr = (end)))
#define RING_INC( ptr, beg, end) (ptr < (end) ? ++ptr : (ptr = (beg)))

#define MAX_HISTORY 20
static char *history_buffer[MAX_HISTORY];
static char **history_next = history_buffer; /* Next available slot. */
static char **history_view = history_buffer; /* What the user is looking at. */
#define history_end (history_buffer + MAX_HISTORY - 1)

extern bool is_terminator (zchar);
extern void read_string (int, zchar *);
extern int completion (const zchar *, zchar *);

/*
 * unix_set_global_timeout
 *
 * This sets up a time structure to determine when unix_read_char should
 * return zero (representing input timeout).  When current system time
 * equals global_timeout, boom.
 *
 */
static void unix_set_global_timeout(int timeout)
{
    if (!timeout) global_timeout.tv_sec = 0;
    else {
        gettimeofday(&global_timeout, NULL);
        global_timeout.tv_sec += (timeout/10);
        global_timeout.tv_usec += ((timeout%10)*100000);
        if (global_timeout.tv_usec > 999999) {
          global_timeout.tv_sec++;
          global_timeout.tv_usec -= 1000000;
        }
    }
    return;
}


/*
 * timeout_to_ms
 *
 * This returns the number of milliseconds until the input timeout
 * elapses or zero if it has already elapsed.  -1 is returned if no
 * timeout is in effect, otherwise the return value is non-negative.
 */
static int timeout_to_ms()
{
    struct timeval now, diff;

    if (global_timeout.tv_sec == 0) return -1;
    gettimeofday( &now, NULL);
    diff.tv_usec = global_timeout.tv_usec - now.tv_usec;
    if (diff.tv_usec < 0) {
	/* Carry */
	now.tv_sec++;
	diff.tv_usec += 1000000;
    }
    diff.tv_sec = global_timeout.tv_sec - now.tv_sec;
    if (diff.tv_sec < 0) return 0;
    if (diff.tv_sec >= INT_MAX / 1000 - 1) /* Paranoia... */
	return INT_MAX - 1000;
    return diff.tv_sec * 1000 + diff.tv_usec / 1000;
}


/*
 * unix_read_char
 *
 * This uses the curses getch() routine to get the next character
 * typed, and returns it.  It returns values which the standard
 * considers to be legal input, and also returns editing and frotz hot
 * keys.  If called with extkeys set it will also return line-editing
 * keys like INSERT etc.
 *
 * If unix_set_global_timeout has been used to set a global timeout
 * this routine may also return ZC_TIME_OUT if input times out.
 */
static int unix_read_char(int extkeys)
{
    int c;

    while(1) {
	timeout( timeout_to_ms());
	c = getch();

	/* Catch 98% of all input right here... */
	if ((c >= ZC_ASCII_MIN && c <= ZC_ASCII_MAX)
	    || (!u_setup.plain_ascii
		&& c >= ZC_LATIN1_MIN && c <= ZC_LATIN1_MAX))
	    return c;

	/* ...and the other 2% makes up 98% of the code. :( */

	/* On many terminals the backspace key returns DEL. */
	if (c == erasechar()) return ZC_BACKSPACE;;

	if (c == killchar()) return ZC_ESCAPE;

	switch(c) {
	/* Normally ERR means timeout.  I suppose we might also get
	   ERR if a signal hits getch. */
	case ERR:
	    if (timeout_to_ms() == 0)
		return ZC_TIME_OUT;
	    else
		continue;

/*
 * Under ncurses, getch() will return OK (defined to 0) when Ctrl-@ or
 * Ctrl-Space is pressed.  0 is also the ZSCII character code for
 * ZC_TIME_OUT.  This causes a fatal error "Call to non-routine", after
 * which Frotz aborts.  This doesn't happen with all games nor is the
 * crashing consistent.  Sometimes repeated tests on a single game will
 * yield some crashes and some non-crashes.  When linked with ncurses,
 * we must make sure that unix_read_char() does not return a bogus
 * ZC_TIME_OUT.
 *
 */
#ifdef USE_NCURSES_H
	case 0:
		continue;
#endif /* USE_NCURSES_H */

	/* Screen decluttering. */
	case MOD_CTRL ^ 'L': case MOD_CTRL ^ 'R':
	    clearok( curscr, 1); refresh(); clearok( curscr, 0);
	    continue;
	/* Lucian P. Smith reports KEY_ENTER on Irix 5.3.  LF has never
	   been reported, but I'm leaving it in just in case. */
	case '\n': case '\r': case KEY_ENTER: return ZC_RETURN;
	/* I've seen KEY_BACKSPACE returned on some terminals. */
	case KEY_BACKSPACE: case '\b': return ZC_BACKSPACE;
	/* On terminals with 8-bit character sets or 7-bit connections
	   "Alt-Foo" may be returned as an escape followed by the ASCII
	   value of the letter.  We have to decide here whether to
	   return a single escape or a frotz hot key. */
	case ZC_ESCAPE:
	    nodelay(stdscr, TRUE); c = getch(); nodelay(stdscr, FALSE);
	    switch(c) {
	    case ERR: return ZC_ESCAPE;
	    case 'p': return ZC_HKEY_PLAYBACK;
	    case 'r': return ZC_HKEY_RECORD;
	    case 's': return ZC_HKEY_SEED;
	    case 'u': return ZC_HKEY_UNDO;
	    case 'n': return ZC_HKEY_RESTART;
	    case 'x': return ZC_HKEY_QUIT;
	    case 'd': return ZC_HKEY_DEBUG;
	    case 'h': return ZC_HKEY_HELP;
	    case 'f': return ZC_WORD_RIGHT;
	    case 'b': return ZC_WORD_LEFT;
	    default: continue;	/* Ignore unknown combinations. */
	    }
	/* The standard function key block. */
	case KEY_UP: return ZC_ARROW_UP;
	case KEY_DOWN: return ZC_ARROW_DOWN;
	case KEY_LEFT: return ZC_ARROW_LEFT;
	case KEY_RIGHT: return ZC_ARROW_RIGHT;
	case KEY_F(1): return ZC_FKEY_MIN;
	case KEY_F(2): return ZC_FKEY_MIN + 1;
	case KEY_F(3): return ZC_FKEY_MIN + 2;
	case KEY_F(4): return ZC_FKEY_MIN + 3;
	case KEY_F(5): return ZC_FKEY_MIN + 4;
	case KEY_F(6): return ZC_FKEY_MIN + 5;
	case KEY_F(7): return ZC_FKEY_MIN + 6;
	case KEY_F(8): return ZC_FKEY_MIN + 7;
	case KEY_F(9): return ZC_FKEY_MIN + 8;
	case KEY_F(10): return ZC_FKEY_MIN + 9;
	case KEY_F(11): return ZC_FKEY_MIN + 10;
	case KEY_F(12): return ZC_FKEY_MIN + 11;
	/* Curses can't differentiate keypad numbers from cursor keys,
	   which is annoying, as cursor and keypad keys have
	   nothing to do with each other on, say, a vt200.
	   So we can only read 1, 3, 5, 7 and 9 from the keypad.  This
	   would be so silly that we choose not to provide keypad keys at all.
	*/
        /* Catch the meta key on those plain old ASCII terminals where
	   it sets the high bit.  This only works in
	   u_setup.plain_ascii mode: otherwise these character codes
	   would have been interpreted according to ISO-Latin-1
	   earlier. */
	case MOD_META | 'p': return ZC_HKEY_PLAYBACK;
	case MOD_META | 'r': return ZC_HKEY_RECORD;
	case MOD_META | 's': return ZC_HKEY_SEED;
	case MOD_META | 'u': return ZC_HKEY_UNDO;
	case MOD_META | 'n': return ZC_HKEY_RESTART;
	case MOD_META | 'x': return ZC_HKEY_QUIT;
	case MOD_META | 'd': return ZC_HKEY_DEBUG;
	case MOD_META | 'h': return ZC_HKEY_HELP;
	case MOD_META | 'f': return ZC_WORD_RIGHT;
	case MOD_META | 'b': return ZC_WORD_LEFT;

	/* these are the emacs-editing characters */
	case MOD_CTRL ^ 'B': return ZC_ARROW_LEFT;
	case MOD_CTRL ^ 'F': return ZC_ARROW_RIGHT;
	case MOD_CTRL ^ 'P': return ZC_ARROW_UP;
	case MOD_CTRL ^ 'N': return ZC_ARROW_DOWN;
	case MOD_CTRL ^ 'A': c = KEY_HOME; break;
	case MOD_CTRL ^ 'E': c = KEY_END; break;
	case MOD_CTRL ^ 'D': c = KEY_DC; break;
	case MOD_CTRL ^ 'K': c = KEY_EOL; break;
	case MOD_CTRL ^ 'W': c = ZC_DEL_WORD; break;

	default: break; /* Who knows? */
	}

	/* Control-N through Control-U happen to map to the frotz hot
	 * key codes, but not in any mnemonic manner.  It annoys an
	 * emacs user (or this one anyway) when he tries out of habit
	 * to use one of the emacs keys that isn't implemented and he
	 * gets a random hot key function.  It's less jarring to catch
	 * them and do nothing.  [APP] */
      if ((c >= ZC_HKEY_MIN) && (c <= ZC_HKEY_MAX)) continue;

	/* Finally, if we're in full line mode (os_read_line), we
	   might return codes which aren't legal Z-machine keys but
	   are used by the editor. */
	if (extkeys) return c;
    }
}


/*
 * unix_add_to_history
 *
 * Add the given string to the next available history buffer slot.
 *
 */
static void unix_add_to_history(zchar *str)
{

    if (*history_next != NULL)
	free( *history_next);
    *history_next = (char *)malloc(strlen((char *)str) + 1);
    strcpy( *history_next, (char *)str);
    RING_INC( history_next, history_buffer, history_end);
    history_view = history_next; /* Reset user frame after each line */

    return;
}


/*
 * unix_history_back
 *
 * Copy last available string to str, if possible.  Return 1 if successful.
 * Only lines of at most maxlen characters will be considered.  In addition
 * the first searchlen characters of the history entry must match those of str.
 */
static int unix_history_back(zchar *str, int searchlen, int maxlen)
{
    char **prev = history_view;

    do {
	RING_DEC( history_view, history_buffer, history_end);
	if ((history_view == history_next)
	    || (*history_view == NULL)) {
	    os_beep(BEEP_HIGH);
	    history_view = prev;
	    return 0;
	}
    } while (strlen( *history_view) > (size_t) maxlen
	     || (searchlen != 0 && strncmp( (char *)str, *history_view, searchlen)));
    strcpy((char *)str + searchlen, *history_view + searchlen);
    return 1;
}


/*
 * unix_history_forward
 *
 * Opposite of unix_history_back, and works in the same way.
 */
static int unix_history_forward(zchar *str, int searchlen, int maxlen)
{
    char **prev = history_view;

    do {
	RING_INC( history_view, history_buffer, history_end);
	if ((history_view == history_next)
	    || (*history_view == NULL)) {

	    os_beep(BEEP_HIGH);
	    history_view = prev;
	    return 0;
	}
    } while (strlen( *history_view) > (size_t) maxlen
	     || (searchlen != 0 && strncmp( (char *)str, *history_view, searchlen)));
    strcpy((char *)str + searchlen, *history_view + searchlen);
    return 1;
}


/*
 * scrnmove
 *
 * In the row of the cursor, move n characters starting at src to dest.
 *
 */
static void scrnmove(int dest, int src, int n)
{
    int col, x, y;

    getyx(stdscr, y, x);
    if (src > dest) {
      for (col = src; col < src + n; col++) {
	chtype ch = mvinch(y, col);
	mvaddch(y, col - src + dest, ch);
      }
    } else if (src < dest) {
      for (col = src + n - 1; col >= src; col--) {
	chtype ch = mvinch(y, col);
	mvaddch(y, col - src + dest, ch);
      }
    }
    move(y, x);

    return;
}


/*
 * scrnset
 *
 * In the row of the cursor, set n characters starting at start to c.
 *
 */
static void scrnset(int start, int c, int n)
{
    int y, x;
    getyx(stdscr, y, x);
    while (n--)
	mvaddch(y, start + n, c);
    move(y, x);

    return;
}


/*
 * os_read_line
 *
 * Read a line of input from the keyboard into a buffer. The buffer
 * may already be primed with some text. In this case, the "initial"
 * text is already displayed on the screen. After the input action
 * is complete, the function returns with the terminating key value.
 * The length of the input should not exceed "max" characters plus
 * an extra 0 terminator.
 *
 * Terminating keys are the return key (13) and all function keys
 * (see the Specification of the Z-machine) which are accepted by
 * the is_terminator function. Mouse clicks behave like function
 * keys except that the mouse position is stored in global variables
 * "mouse_x" and "mouse_y" (top left coordinates are (1,1)).
 *
 * Furthermore, Frotz introduces some special terminating keys:
 *
 *     ZC_HKEY_KEY_PLAYBACK (Alt-P)
 *     ZC_HKEY_RECORD (Alt-R)
 *     ZC_HKEY_SEED (Alt-S)
 *     ZC_HKEY_UNDO (Alt-U)
 *     ZC_HKEY_RESTART (Alt-N, "new game")
 *     ZC_HKEY_QUIT (Alt-X, "exit game")
 *     ZC_HKEY_DEBUGGING (Alt-D)
 *     ZC_HKEY_HELP (Alt-H)
 *
 * If the timeout argument is not zero, the input gets interrupted
 * after timeout/10 seconds (and the return value is ZC_TIME_OUT).
 *
 * The complete input line including the cursor must fit in "width"
 * screen units.
 *
 * The function may be called once again to continue after timeouts,
 * misplaced mouse clicks or hot keys. In this case the "continued"
 * flag will be set. This information can be useful if the interface
 * implements input line history.
 *
 * The screen is not scrolled after the return key was pressed. The
 * cursor is at the end of the input line when the function returns.
 *
 * Since Inform 2.2 the helper function "completion" can be called
 * to implement word completion (similar to tcsh under Unix).
 *
 */
zchar os_read_line (int max, zchar *buf, int timeout, int width, int continued)
{
    int ch, y, x, len = strlen( (char *)buf);
    /* These are static to allow input continuation to work smoothly. */
    static int scrpos = 0, searchpos = -1, insert_flag = 1;

    /* Set x and y to be at the start of the input area.  */
    getyx(stdscr, y, x);
    x -= len;

    if (width < max) max = width;
    /* Better be careful here or it might segv.  I wonder if we should just
       ignore 'continued' and check for len > 0 instead?  Might work better
       with Beyond Zork. */
    if (!(continued && scrpos <= len && searchpos <= len)) {
	scrpos = len;
	history_view = history_next; /* Reset user's history view. */
	searchpos = -1;		/* -1 means initialize from len. */
	insert_flag = 1;	/* Insert mode is now default. */
    }

    unix_set_global_timeout(timeout);
    for (;;) {
	move(y, x + scrpos);
	/* Maybe there's a cleaner way to do this, but refresh() is */
	/* still needed here to print spaces.  --DG */
	refresh();
        switch (ch = unix_read_char(1)) {
	case ZC_BACKSPACE:	/* Delete preceeding character */
	    if (scrpos != 0) {
		len--; scrpos--; searchpos = -1;
		scrnmove(x + scrpos, x + scrpos + 1, len - scrpos);
		mvaddch(y, x + len, ' ');
		memmove(buf + scrpos, buf + scrpos + 1, len - scrpos);
	    }
	    break;
	case ZC_DEL_WORD:
		if (scrpos != 0) {
			int newoffset = start_of_prev_word(scrpos, buf);
			searchpos = -1;
			int delta = scrpos - newoffset;
			int oldlen = len;
			int oldscrpos = scrpos;
			len -= delta;
			scrpos -= delta;
			scrnmove(x + scrpos, x + oldscrpos, len - scrpos);
			memmove(buf + scrpos, buf + oldscrpos, len - scrpos);
			int i = newoffset;
			for (i = len; i <= oldlen ; i++) {
				mvaddch(y, x + i, ' ');
			}
		}
		break;
	case CHR_DEL:
	case KEY_DC:		/* Delete following character */
	    if (scrpos < len) {
		len--; searchpos = -1;
		scrnmove(x + scrpos, x + scrpos + 1, len - scrpos);
		mvaddch(y, x + len, ' ');
		memmove(buf + scrpos, buf + scrpos + 1, len - scrpos);
	    }
	    continue;		/* Don't feed is_terminator bad zchars. */

	case KEY_EOL:		/* Delete from cursor to end of line.  */
	    scrnset(x + scrpos, ' ', len - scrpos);
	    len = scrpos;
	    continue;
	case ZC_ESCAPE:		/* Delete whole line */
	    scrnset(x, ' ', len);
	    len = scrpos = 0;
	    searchpos = -1;
	    history_view = history_next;
	    continue;

	/* Cursor motion */
	case ZC_ARROW_LEFT: if (scrpos) scrpos--; continue;
	case ZC_ARROW_RIGHT: if (scrpos < len) scrpos++; continue;
	case KEY_HOME: scrpos = 0; continue;
	case KEY_END: scrpos = len; continue;
	case ZC_WORD_RIGHT:
		if (scrpos < len) {
			scrpos = end_of_next_word(scrpos, buf, len);
		}
		continue;
	case ZC_WORD_LEFT:
		if (scrpos > 0) {
			scrpos = start_of_prev_word(scrpos, buf);
		}
		continue;
	case KEY_IC:		/* Insert Character */
	    insert_flag = !insert_flag;
	    continue;

	case ZC_ARROW_UP: case ZC_ARROW_DOWN:
	    if (searchpos < 0)
		searchpos = len;
	    if ((ch == ZC_ARROW_UP ? unix_history_back : unix_history_forward)
		(buf, searchpos, max)) {
		scrnset(x, ' ', len);
		mvaddstr(y, x, (char *) buf);
		scrpos = len = strlen((char *) buf);
            }
	    continue;

	/* Passthrough as up/down arrows for Beyond Zork. */
	case KEY_PPAGE: ch = ZC_ARROW_UP; break;
	case KEY_NPAGE: ch = ZC_ARROW_DOWN; break;
	case '\t':
	    /* This really should be fixed to work also in the middle of a
	       sentence. */
	    {
		int status;
		zchar extension[10], saved_char;

		saved_char = buf[scrpos];
		buf[scrpos] = '\0';
		status = completion( buf, extension);
		buf[scrpos] = saved_char;

		if (status != 2) {
		    int ext_len = strlen((char *) extension);
		    if (ext_len > max - len) {
			ext_len = max - len;
			status = 1;
		    }
		    memmove(buf + scrpos + ext_len, buf + scrpos,
			len - scrpos);
		    memmove(buf + scrpos, extension, ext_len);
		    scrnmove(x + scrpos + ext_len, x + scrpos, len - scrpos);
		    mvaddnstr(y, x + scrpos, (char *) extension, ext_len);
		    scrpos += ext_len;
		    len += ext_len;
		    searchpos = -1;
		}
		if (status) os_beep(BEEP_HIGH);
	    }
	    continue;		/* TAB is invalid as an input character. */
	default:
	    /* ASCII or ISO-Latin-1 */
	    if ((ch >= ZC_ASCII_MIN && ch <= ZC_ASCII_MAX)
		|| (!u_setup.plain_ascii
		    && ch >= ZC_LATIN1_MIN && ch <= ZC_LATIN1_MAX)) {
		searchpos = -1;
		if ((scrpos == max) || (insert_flag && (len == max))) {
		    os_beep(BEEP_HIGH);
		    continue;
		}
		if (insert_flag && (scrpos < len)) {
		    /* move what's there to the right */
		    scrnmove(x + scrpos + 1, x + scrpos, len - scrpos);
		    memmove(buf + scrpos + 1, buf + scrpos, len - scrpos);
		}
		if (insert_flag || scrpos == len)
		    len++;
		mvaddch(y, x + scrpos, ch);
		buf[scrpos++] = ch;
		continue;
	    }
        }
	if (is_terminator(ch)) {
	    buf[len] = '\0';
	    if (ch == ZC_RETURN)
		unix_add_to_history(buf);
	    /* Games don't know about line editing and might get
	       confused if the cursor is not at the end of the input
	       line. */
	    move(y, x + len);
	    return ch;
	}
    }
}/* os_read_line */


/*
 * os_read_key
 *
 * Read a single character from the keyboard (or a mouse click) and
 * return it. Input aborts after timeout/10 seconds.
 *
 */
zchar os_read_key (int timeout, int cursor)
{
    zchar c;

    refresh();
    if (!cursor) curs_set(0);

    unix_set_global_timeout(timeout);
    c = (zchar) unix_read_char(0);

    if (!cursor) curs_set(1);
    return c;

}/* os_read_key */


/*
 * os_read_file_name
 *
 * Return the name of a file. Flag can be one of:
 *
 *    FILE_SAVE     - Save game file
 *    FILE_RESTORE  - Restore game file
 *    FILE_SCRIPT   - Transcript file
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

int os_read_file_name (char *file_name, const char *default_name, int UNUSED(flag))
{
    int saved_replay = istream_replay;
    int saved_record = ostream_record;
    int i;
    char *tempname;

    /* Turn off playback and recording temporarily */

    istream_replay = 0;
    ostream_record = 0;

    /* If we're restoring a game before the interpreter starts,
     * our filename is already provided.  Just go ahead silently.
     */
    if (f_setup.restore_mode) {
	file_name[0]=0;
    } else {
	print_string ("Enter a file name.\nDefault is \"");
	print_string (default_name);
	print_string ("\": ");
	read_string (FILENAME_MAX, (zchar *)file_name);
    }

    /* Use the default name if nothing was typed */

    if (file_name[0] == 0)
        strcpy (file_name, default_name);

    /* Check if we're restricted to one directory. */

    if (f_setup.restricted_path != NULL) {
	for (i = strlen(file_name); i > 0; i--) {
	    if (file_name[i] == PATH_SEPARATOR) {
		i++;
		break;
	    }
	}
	tempname = strdup(file_name + i);
	strcpy(file_name, f_setup.restricted_path);
	if (file_name[strlen(file_name)-1] != PATH_SEPARATOR) {
	    strcat(file_name, "/");
	}
	strcat(file_name, tempname);
    }

    /* Restore state of playback and recording */

    istream_replay = saved_replay;
    ostream_record = saved_record;

    return 1;

} /* os_read_file_name */


/*
 * os_read_mouse
 *
 * Store the mouse position in the global variables "mouse_x" and
 * "mouse_y" and return the mouse buttons currently pressed.
 *
 */
zword os_read_mouse (void)
{
	/* INCOMPLETE */
    return 0;
} /* os_read_mouse */




/* What's this? */
/*
 * Local Variables:
 * c-basic-offset: 4
 * End:
 */


#ifdef NO_MEMMOVE
/*
 * This is for operating systems based on 4.2BSD or older or SYSVR3 or
 * older.  Since they lack the memmove(3) system call, it is provided
 * here.  Because I don't have a machine like this to play with, this code
 * is untested.  If you happen to have a spare SunOS 4.1.x install CD
 * lying around, please consider sending it my way.  Dave.
 *
 */
void *memmove(void *s, void *t, size_t n)
{
	char *p = s; char *q = t;

	if (p < q) {
		while (n--) *p++ = *q++;
	} else {
		p += n; q += n;
		while (n--) *--p = *--q;
	}
	return;
}

#endif /* NO_MEMMOVE */


/*
 * Search for start of preceding word
 * param currpos marker position
 * param buf input buffer
 * returns new position
 */
static int start_of_prev_word(int currpos, const zchar* buf) {
	int i, j;
	for (i = currpos - 1; i > 0 && buf[i] == ' '; i--) {}
	j = i;
	for (; i > 0 && buf[i] != ' '; i--) {}
	if (i < j && i != 0) {
		i += 1;
	}
	return i;
}

/*
 * Search for end of next word
 * param currpos marker position
 * param buf input buffer
 * param len length of buf
 * returns new position
 */
static int end_of_next_word(int currpos, const zchar* buf, int len) {
	int i;
	for (i = currpos; i < len && buf[i] == ' '; i++) {}
	for (; i < len && buf[i] != ' '; i++) {}
	return i;
}
