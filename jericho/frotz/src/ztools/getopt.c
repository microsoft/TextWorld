#include <stdio.h>
#include <string.h>

#define ERR(s, c) \
    if (opterr) {\
        char errbuf[2];\
        errbuf[0] = (char) c; errbuf[1] = '\n';\
        (void) fwrite (argv[0], strlen (argv[0]), 1, stderr);\
        (void) fwrite (s, strlen (s), 1, stderr);\
        (void) fwrite (errbuf, 2, 1, stderr);\
    }

int opterr = 1;
int optind = 1;
int optopt;
const char *optarg;

#ifdef __STDC__
int getopt (int argc, char *argv[], const char *opts)
#else
int getopt (argc, argv, opts)
int argc;
char *argv[];
const char *opts;
#endif
{
    static int sp = 1;
    int c;
    char *cp;

    if (sp == 1)
        if (optind >= argc || argv[optind][0] != '-' || argv[optind][1] == '\0')
            return (EOF);
        else if (strcmp (argv[optind], "--") == 0) {
            optind++;
            return (EOF);
        }
    optopt = c = argv[optind][sp];
    if (c == ':' || (cp = strchr (opts, c)) == NULL) {
        ERR (": illegal option -- ", c);
        if (argv[optind][++sp] == '\0') {
            optind++;
            sp = 1;
        }
        return ('?');
    }
    if (*++cp == ':') {
        if (argv[optind][sp+1] != '\0')
            optarg = &argv[optind++][sp+1];
        else if (++optind >= argc) {
            ERR (": option requires an argument -- ", c);
            sp = 1;
            return ('?');
        } else
            optarg = argv[optind++];
        sp = 1;
    } else {
        if (argv[optind][++sp] == '\0') {
            sp = 1;
            optind++;
        }
        optarg = NULL;
    }

    return (c);

}/* getopt */
