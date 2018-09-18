
#include <pthread.h>
#include <stdbool.h>

#include "ux_locks.h"

static bool    music_playing = false;
static pthread_mutex_t music_playing_mutex = PTHREAD_MUTEX_INITIALIZER;

static int     musicnum = 0;
static pthread_mutex_t musicnum_mutex = PTHREAD_MUTEX_INITIALIZER;

bool
get_music_playing (void)
{
	bool value;

	pthread_mutex_lock (&music_playing_mutex);
    value = music_playing;
    pthread_mutex_unlock (&music_playing_mutex);
    return value;
}


bool
set_music_playing (bool new_value)
{
	bool old_value;

	pthread_mutex_lock (&music_playing_mutex);
    old_value = music_playing;
    music_playing = new_value;
    pthread_mutex_unlock (&music_playing_mutex);
    return old_value;
}


int
get_musicnum (void)
{
	int value;

	pthread_mutex_lock (&musicnum_mutex);
    value = musicnum;
    pthread_mutex_unlock (&musicnum_mutex);
    return value;
}


int
set_musicnum (int new_value)
{
	int old_value;

	pthread_mutex_lock (&musicnum_mutex);
    old_value = musicnum;
    musicnum = new_value;
    pthread_mutex_unlock (&musicnum_mutex);
    return old_value;
}
