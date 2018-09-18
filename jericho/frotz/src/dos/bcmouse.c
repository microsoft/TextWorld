/*
 * file "BCmouse.c"
 *
 * Borland C front end, mouse support
 *
 */

#include <dos.h>
#include "frotz.h"
#include "bcfrotz.h"

/*
 * detect_mouse
 *
 * Return true if a mouse driver is present.
 *
 */

bool detect_mouse (void)
{

    asm xor ax,ax
    asm int 0x33

    return _AX;

}/* detect_mouse */

/*
 * read_mouse
 *
 * Report any mouse clicks. Return 2 for a double click, 1 for a single
 * click or 0 if there was no mouse activity at all.
 *
 */

int read_mouse (void)
{
    int click;

    /* Read the current mouse status */

    for (click = 0; click < 2; click++) {

	if (click == 1)
	    delay (222);

	asm mov ax,6
	asm xor bx,bx
	asm int 0x33

	if (_BX == 0)
	    break;

	mouse_x = _CX;
	mouse_y = _DX;

	if (display <= _TEXT_) {
	    mouse_x /= 8;
	    mouse_y /= 8;
	}

	if (display == _MCGA_)
	    mouse_x /= 2;

	mouse_x++;
	mouse_y++;

    }

    /* Return single or double click */

    return click;

}/* read_mouse */
