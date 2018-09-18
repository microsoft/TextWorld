/* inforead.c V7/3
 *
 * Read Infocom data files from an IBM bootable diskette
 *
 * usage: inforead datafile-name [start-track [drive#]]
 *
 *    datafile-name is required
 *    start-track is optional (default is 6, should be OK)
 *    drive# is optional (default is 0 for a:, use 1 for b:)
 *
 * The data file is extracted starting at track 6 and continues
 * for the length of the data area. The data file that is created
 * is the correct length and is verified using the checksum in the
 * data area.
 *
 * This only works for type 3 games on IBM 5 1/4" diskettes. I
 * believe that all of the bootable Infocom games were type 3.
 *
 * (Note: Seems to work for 3 1/2" diskettes as well -- S.J.)
 *
 * Once you have extracted the datafile use the /G switch with
 * a type 3 Infocom interpreter, for example:
 *
 * C> zork1/ginfidel.dat
 *
 * NB. no space between the /g and the data file name and nothing
 * after the data file name.
 *
 * (Note: Nowadays you will probably want to use one of the freely
 * available interpreters such as "Zip" or "Frotz" -- S.J.)
 *
 * This C program was written with MicroSoft C specifically for the
 * IBM PC.
 *
 * (Note: It also compiles under Borland C -- S.J.)
 *
 * I also have a CBM 64/128 version of this program for Commodore disks.
 *
 * Mark Howell 20 January 1992 howell_ma@movies.enet.dec.com
 *
 * DJGPP changes provided by Esa A E Peuha <peuha@cc.helsinki.fi> -- MTR
 *
 */

#include <bios.h>
#include <stdio.h>
#include <stdlib.h>

#define TRACK_SIZE 4096

int read_track (int drive, int track, unsigned char *tp);

int main (int argc, char *argv[])
{
    int track = 6;
    int drive = 0;
    FILE *fp;
    unsigned char *tp;
    int i, j, size, status;
    unsigned long int glength;
    unsigned short gchksum, chksum = 0;

    if (argc >= 4)
	drive = atoi (argv[3]);
    if (drive < 0 || drive > 1) {
	fprintf (stderr, "invalid drive #%d\n", drive);
	exit (1);
    }
    if (argc >= 3)
	track = atoi (argv[2]);
    if (track < 0 || track > 39) {
	fprintf (stderr, "invalid track #%d\n", track);
	exit (1);
    }
    if (argc < 2) {
	fprintf (stderr, "usage: %s story-file-name [start track [drive]]\n\n", argv[0]);
	fprintf (stderr, "INFOREAD version 6/8 - convert Infocom boot disks to files. By Mark Howell\n");
	fprintf (stderr, "Works with V3 Infocom games.\n");
	exit (1);
    }

    if ((tp = (unsigned char *) malloc (TRACK_SIZE)) == NULL) {
	perror ("malloc");
	exit (1);
    }
    if ((fp = fopen (argv[1], "wb")) == NULL) {
	perror ("fopen");
	exit (1);
    }

    for (i = track; i < 40; i++) {
	if (status = read_track (drive, i, tp)) {
	    fprintf (stderr, "error %d from drive #%d, track #%d\n",
		     status, drive, track);
	    exit (1);
	}
	if (i == track) {
	    glength = ((unsigned) tp[26] * 256) + tp[27];
	    gchksum = ((unsigned) tp[28] * 256) + tp[29];
	    glength = (glength * 2) - TRACK_SIZE;
	    for (j = 64; j < TRACK_SIZE; j++)
		chksum += tp[j];
	    if (fwrite (tp, TRACK_SIZE, 1, fp) != 1) {
		perror ("fwrite");
		exit (1);
	    }
	} else {
	    if (glength > TRACK_SIZE) {
		size = TRACK_SIZE;
		glength -= TRACK_SIZE;
	    } else {
		size = (int) glength;
		i = 40;
	    }
	    for (j = 0; j < size; j++)
		chksum += tp[j];
	    if (fwrite (tp, (size_t) size, 1, fp) != 1) {
		perror ("fwrite");
		exit (1);
	    }
	}
    }

    if (gchksum == chksum)
	printf ("game copied OK\n");
    else
	fprintf (stderr, "game copy failed!\n");

    free (tp);
    fclose (fp);

    exit (0);

    return (0);

}/* main */

int read_track (int drive, int track, unsigned char *tp)
{
    struct diskinfo_t di;
    unsigned int status;
    int i;

    di.drive = drive;
    di.head = 0;
    di.track = track;
    di.sector = 1;
    di.nsectors = 8;
#ifdef __DJGPP
    di.buffer = (void *) tp;
#else
    di.buffer = (void far *) tp;
#endif

    for (i = 0; i < 3; i++) {
	status = _bios_disk (_DISK_READ, &di);
	if (status == 8)
	    return (0);
	_bios_disk (_DISK_RESET, NULL);
    }

    return (status >> 8);

}/* read_track */
