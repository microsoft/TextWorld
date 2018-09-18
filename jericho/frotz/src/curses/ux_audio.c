/*
 * ux_audio.c - Unix interface, sound support
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
 * Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA
 * Or visit http://www.fsf.org/
 */

#define __UNIX_PORT_FILE

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <pthread.h>
#include <semaphore.h>
#include <signal.h>

#ifdef USE_NCURSES_H
#include <ncurses.h>
#else
#include <curses.h>
#endif

#include "ux_frotz.h"
#include "ux_blorb.h"
#include "ux_locks.h"

#ifndef NO_SOUND

#include <ao/ao.h>
#include <sndfile.h>
#include <samplerate.h>
#include <vorbis/codec.h>
#include <vorbis/vorbisfile.h>
#include <libmodplug/modplug.h>

#define MAX(x,y) ((x)>(y)) ? (x) : (y)
#define MIN(x,y) ((x)<(y)) ? (x) : (y)

enum sound_type {
    FORM,
    OGGV,
    MOD
};

typedef struct {
    FILE *fp;
    bb_result_t result;
    enum sound_type type;
    int number;
    int vol;
    int repeats;
} EFFECT;

static void *playaiff(EFFECT *);
static void *playmusic(EFFECT *);
static void *playmod(EFFECT *);
static void *playogg(EFFECT *);

static void floattopcm16(short *, float *, int);
static void pcm16tofloat(float *, short *, int);
static void stereoize(float *, float *, size_t);

static int mypower(int, int);
static char *getfiledata(FILE *, long *);
static void *mixer(void *);

static pthread_t	mixer_id;
static pthread_t	playaiff_id;
static pthread_t	playmusic_id;
static pthread_mutex_t	mutex;
static sem_t		playaiff_okay;
static sem_t		playmusic_okay;

bool    bleep_playing = FALSE;
bool	bleep_stop = FALSE;

int	bleepcount;
int	bleepnum;

bool    music_playing = FALSE;
bool	music_stop = FALSE;

typedef struct
{
    sem_t   full;
    sem_t   empty;
    float  *samples;
    int     nsamples;
} audiobuffer;

audiobuffer bleep_buffer;
audiobuffer music_buffer;

void audiobuffer_init(audiobuffer *ab)
{
    sem_init(&ab->full, 0, 0);
    sem_init(&ab->empty, 0, 0);
    sem_post(&ab->empty);
    ab->samples = malloc(BUFFSIZE * 2 * sizeof(float));
    ab->nsamples = 0;
}


/*
 * os_init_sound
 *
 * Do any required setup for sound output.
 * Here we start a thread to act as a mixer.
 *
 */
void os_init_sound(void)
{
    int err;
    static pthread_attr_t attr;

    pthread_mutex_init(&mutex, NULL);
    audiobuffer_init(&music_buffer);
    audiobuffer_init(&bleep_buffer);
    sem_init(&playaiff_okay, 0, 0);
    sem_init(&playmusic_okay, 0, 0);

    pthread_attr_init(&attr);
    pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_DETACHED);

    err = pthread_create(&(mixer_id), &attr, (void *) &mixer, NULL);
    if (err != 0) {
	printf("Can't create mixer thread :[%s]", strerror(err));
	exit(1);
    }
}


/*
 * os_beep
 *
 * Play a beep sound. Ideally, the sound should be high- (number == 1)
 * or low-pitched (number == 2).
 *
 */
void os_beep (int number)
{
    int i = number;
    i++;

    beep();
}/* os_beep */


/*
 * os_prepare_sample
 *
 * Load the sample from the disk.
 *
 * Actually it's more efficient these days to load and play a sound in
 * the same operation.  This function therefore does nothing.
 *
 */
void os_prepare_sample (int number)
{
    int i = number;
    i++;

    return;
}/* os_prepare_sample */


/*
 * os_start_sample
 *
 * Play the given sample at the given volume (ranging from 1 to 8 and
 * 255 meaning a default volume). The sound is played once or several
 * times in the background (255 meaning forever). In Z-code 3 the
 * repeats value is always 0 and the number of repeats is taken from
 * the sound file itself. The end_of_sound function is called as soon
 * as the sound finishes.
 *
 */
void os_start_sample (int number, int volume, int repeats, zword eos)
{
    bb_result_t resource;
    EFFECT myeffect;
    int err;
    static pthread_attr_t attr;
    zword foo = eos;

    foo++;

    if (blorb_map == NULL) return;

    if (bb_err_None != bb_load_resource(blorb_map, bb_method_FilePos, &resource, bb_ID_Snd, number))
	return;

    myeffect.fp = blorb_fp;
    myeffect.result = resource;
    myeffect.vol = volume;
    myeffect.repeats = repeats;
    myeffect.number = number;

    pthread_attr_init(&attr);

    if (blorb_map->chunks[resource.chunknum].type == bb_make_id('F','O','R','M'))
	myeffect.type = FORM;
    else if (blorb_map->chunks[resource.chunknum].type == bb_make_id('M','O','D',' '))
	myeffect.type = MOD;
    else if (blorb_map->chunks[resource.chunknum].type == bb_make_id('O','G','G','V'))
	myeffect.type = OGGV;

    if (myeffect.type == FORM) {
	if (bleep_playing) {
	    bleep_playing = FALSE;
	    pthread_join(playaiff_id, NULL);
	}
	err = pthread_create(&playaiff_id, &attr, (void *) &playaiff, &myeffect);
	if (err != 0) {
	    printf("Can't create playaiff thread :[%s]", strerror(err));
	    return;
	}
	sem_wait(&playaiff_okay);
    } else if (myeffect.type == MOD || myeffect.type == OGGV) {
	if (music_playing) {
	    music_playing = FALSE;
	    pthread_join(playmusic_id, NULL);
	}
	err = pthread_create(&playmusic_id, &attr, (void *) &playmusic, &myeffect);
	if (err != 0) {
	    printf("Can't create playmusic thread :[%s]", strerror(err));
	    return;
	}
	sem_wait(&playmusic_okay);
    } else {
	/* Something else was presented as an audio chunk.  Ignore it. */
    }
}/* os_start_sample */


/*
 * os_stop_sample
 *
 * Turn off the current sample.
 *
 */
void os_stop_sample (int number)
{
    if (bleep_playing && (number == bleepnum || number == 0)) {
        bleep_playing = FALSE;
        sem_post(&bleep_buffer.empty);
        pthread_join(playaiff_id, 0);
    }

    if (get_music_playing() && (number == get_musicnum () || number == 0)) {
        set_music_playing(false);
        sem_post(&music_buffer.empty);
        pthread_join(playmusic_id, 0);
    }

    return;
}/* os_stop_sample */


/*
 * os_finish_with_sample
 *
 * Remove the current sample from memory (if any).
 *
 */
void os_finish_with_sample (int number)
{
    os_stop_sample(number);

}/* os_finish_with_sample */


/*
 * os_wait_sample
 *
 * Stop repeating the current sample and wait until it finishes.
 *
 */
void os_wait_sample (void)
{

    /* Not implemented */

}/* os_wait_sample */


/*
 **********************************************
 * These functions are internal to ux_audio.c
 *
 **********************************************
 */

/*
 * mixer
 *
 * In a classic producer/consumer arrangement, this mixer watches for audio
 * data to be placed in *bleepbuffer or *musicbuffer.  When a semaphore for
 * either is raised, the mixer processes the buffer.
 *
 * Data presented to the mixer must be floats at 44100hz
 *
 */
static void *mixer(void * UNUSED(arg))
{
    short *shortbuffer;
    int default_driver;
    ao_device *device;
    ao_sample_format format;
    int samplecount;

    ao_initialize();
    default_driver = ao_default_driver_id();

    shortbuffer = malloc(BUFFSIZE * sizeof(short) * 2);
    if (shortbuffer == NULL) {
        printf("Unable to malloc shortbuffer\n");
        exit(1);
    }

    memset(&format, 0, sizeof(ao_sample_format));

    format.byte_format = AO_FMT_NATIVE;
    format.bits = 16;
    format.channels = 2;
    format.rate = SAMPLERATE;

    device = NULL;

    while (1) {
        if(music_playing) {
            sem_wait(&music_buffer.full);          /* Wait until output buffer is full */
        }
        if(bleep_playing ) {
            sem_wait(&bleep_buffer.full);          /* Wait until output buffer is full */
        }

        pthread_mutex_lock(&mutex);     /* Acquire mutex */

        if (device == NULL) {
            device = ao_open_live(default_driver, &format, NULL);
            if (device == NULL) {
                printf(" Error opening sound device.\n");
            }
        }

        if (bleep_playing && !music_playing) {
            floattopcm16(shortbuffer, bleep_buffer.samples, bleep_buffer.nsamples);
            ao_play(device, (char *) shortbuffer, bleep_buffer.nsamples * sizeof(short));
            bleep_buffer.nsamples = 0;
        }

        if (music_playing && !bleep_playing) {
            floattopcm16(shortbuffer, music_buffer.samples, music_buffer.nsamples);
            ao_play(device, (char *) shortbuffer, music_buffer.nsamples * sizeof(short));
            music_buffer.nsamples = 0;
        }

        if (music_playing && bleep_playing) {
            int samples = 100000;
            if(bleep_buffer.nsamples == -1)
                bleep_buffer.nsamples = 0;
            if(music_buffer.nsamples == -1)
                music_buffer.nsamples = 0;
            if(samples > bleep_buffer.nsamples && bleep_buffer.nsamples > 0)
                samples = bleep_buffer.nsamples;

            if(samples > music_buffer.nsamples && music_buffer.nsamples > 0)
                samples = music_buffer.nsamples;

            //both buffers have invalid sample data or are empty
            if(samples == 100000)
                samples = 0;

            float *outbuf = calloc(samples+1,sizeof(float));
            for(int i=0; i < samples; ++i)
                outbuf[i] += music_buffer.samples[i];
            for(int i=0; i < samples; ++i)
                outbuf[i] += bleep_buffer.samples[i];

            //only partially consume data
            if(bleep_buffer.nsamples > samples) {
                memmove(bleep_buffer.samples, bleep_buffer.samples+samples,
                        sizeof(float)*(bleep_buffer.nsamples-samples));
            }
            if(bleep_buffer.nsamples > 0)
                bleep_buffer.nsamples -= samples;

            if(music_buffer.nsamples > samples) {
                memmove(music_buffer.samples, music_buffer.samples+samples,
                        sizeof(float)*(music_buffer.nsamples-samples));
            }
            if(music_buffer.nsamples > 0)
                music_buffer.nsamples -= samples;


            samplecount = samples;
            floattopcm16(shortbuffer, outbuf, samples);
            ao_play(device, (char *) shortbuffer, samplecount * sizeof(short));
            free(outbuf);
        }

        if (!bleep_playing && !music_playing) {
            ao_close(device);
            device = NULL;
        }

        pthread_mutex_unlock(&mutex);   /* release the mutex lock */

        if(bleep_buffer.nsamples) {
            sem_post(&bleep_buffer.full);
        }
        if(music_buffer.nsamples) {
            sem_post(&music_buffer.full);
        }

        int tmp;
        sem_getvalue(&bleep_buffer.empty, &tmp);

        if(bleep_buffer.nsamples <= 0 && tmp == 0) {
            sem_post(&bleep_buffer.empty);         /* signal empty */
        }

        sem_getvalue(&music_buffer.empty, &tmp);
        if(music_buffer.nsamples <= 0 && tmp == 0) {
            sem_post(&music_buffer.empty);         /* signal empty */
        }
    }
} /* mixer */


/* Convert back to shorts */
static void floattopcm16(short *outbuf, float *inbuf, int length)
{
    int   count;

    const float mul = (32768.0f);
    for (count = 0; count <= length; count++) {
	int32_t tmp = (int32_t)(mul * inbuf[count]);
	tmp = MAX( tmp, -32768 ); // CLIP < 32768
	tmp = MIN( tmp, 32767 );  // CLIP > 32767
	outbuf[count] = tmp;
    }
}


/* Convert the buffer to floats. (before resampling) */
static void pcm16tofloat(float *outbuf, short *inbuf, int length)
{
    int   count;

    const float div = (1.0f/32768.0f);
    for (count = 0; count <= length; count++) {
	outbuf[count] = div * (float) inbuf[count];
    }
}


/*
 * stereoize
 *
 * Copy the single channel of a monaural stream to both channels
 * of a stereo stream.
 *
 */
static void stereoize(float *outbuf, float *inbuf, size_t length)
{
    size_t count;
    int outcount;

    outcount = 0;

    for (count = 0; count < length; count++) {
	outbuf[outcount] = outbuf[outcount+1] = inbuf[count];
	outcount += 2;
    }
}


/*
 * mypower
 *
 * Just a simple recursive integer-based power function because I don't
 * want to use the floating-point version from libm.
 *
 */
static int mypower(int base, int exp) {
    if (exp == 0)
        return 1;
    else if (exp % 2)
        return base * mypower(base, exp - 1);
    else {
        int temp = mypower(base, exp / 2);
        return temp * temp;
    }
}


/*
 * playaiff
 *
 * This function takes a file pointer to a Blorb file and a bb_result_t
 * struct describing what chunk to play.  It's up to the caller to make
 * sure that an AIFF chunk is to be played.  Volume and repeats are also
 * handled here.
 *
 * This function should be able to play OGG chunks, but because of a bug
 * or oversight in Libsndfile, that library is incapable of playing OGG
 * data which are embedded in a larger file.
 *
 */
void *playaiff(EFFECT *raw_effect)
{
//    long filestart;

    int volcount;
    int volfactor;

    float *floatbuffer;
    float *floatbuffer2;

    SNDFILE     *sndfile;
    SF_INFO     sf_info;

    SRC_STATE	*src_state;
    SRC_DATA	src_data;
    int		error;
    sf_count_t	output_count = 0;

    EFFECT myeffect = *raw_effect;

    sem_post(&playaiff_okay);

    sf_info.format = 0;
    bleepnum = myeffect.number;

//    filestart = ftell(myeffect.fp);
    lseek(fileno(myeffect.fp), myeffect.result.data.startpos, SEEK_SET);
    sndfile = sf_open_fd(fileno(myeffect.fp), SFM_READ, &sf_info, 0);

    if (myeffect.vol < 1) myeffect.vol = 1;
    if (myeffect.vol > 8) myeffect.vol = 8;
    volfactor = mypower(2, -myeffect.vol + 8);

    floatbuffer = malloc(BUFFSIZE * sf_info.channels * sizeof(float));
    floatbuffer2 = malloc(BUFFSIZE * 2 * sizeof(float));
    memset(bleep_buffer.samples, 0, BUFFSIZE * sizeof(float) * 2);

    /* Set up for conversion */
    if ((src_state = src_new(SRC_SINC_FASTEST, sf_info.channels, &error)) == NULL) {
	printf("Error: src_new() failed: %s.\n", src_strerror(error));
	exit(1);
    }
    src_data.end_of_input = 0;
    src_data.input_frames = 0;
    src_data.data_in = floatbuffer;
    src_data.src_ratio = (1.0 * SAMPLERATE) / sf_info.samplerate;
    src_data.data_out = floatbuffer2;
    src_data.output_frames = BUFFSIZE / sf_info.channels;

    bleep_playing = TRUE;

    while (1) {
        /* Check if we're being told to stop. */
        if (!bleep_playing) break;
        sem_wait(&bleep_buffer.empty);
        pthread_mutex_lock(&mutex);

        /* If floatbuffer is empty, refill it. */
        if (src_data.input_frames == 0) {
            src_data.input_frames = sf_readf_float(sndfile, floatbuffer, BUFFSIZE / sf_info.channels);
            src_data.data_in = floatbuffer;
            /* Mark end of input. */
            if (src_data.input_frames < BUFFSIZE / sf_info.channels)
                src_data.end_of_input = SF_TRUE;
        }

        /* Do the sample rate conversion. */
        if ((error = src_process(src_state, &src_data))) {
            printf("Error: %s\n", src_strerror(error));
            exit(1);
        }

        bleep_buffer.nsamples = src_data.output_frames_gen * 2;

        /* Stereoize monaural sound-effects. */
        if (sf_info.channels == 1) {
            /* Remember that each monaural frame contains just one sample. */
            stereoize(bleep_buffer.samples, floatbuffer2, src_data.output_frames_gen);
        } else {
            /* It's already stereo.  Just copy the buffer. */
            memcpy(bleep_buffer.samples, floatbuffer2, sizeof(float) * src_data.output_frames_gen * 2);
        }

        /* Adjust volume. */
        for (volcount = 0; volcount <= bleep_buffer.nsamples; volcount++)
            bleep_buffer.samples[volcount] /= volfactor;

        /* If that's all, terminate and signal that we're done. */
        if (src_data.end_of_input && src_data.output_frames_gen == 0) {
            sem_post(&bleep_buffer.full);
            pthread_mutex_unlock(&mutex);
            break;
        }

        /* Get ready for the next chunk. */
        output_count += src_data.output_frames_gen;
        src_data.data_in += src_data.input_frames_used * sf_info.channels;
        src_data.input_frames -= src_data.input_frames_used;

        /* By this time, the buffer is full.  Signal the mixer to play it. */
        pthread_mutex_unlock(&mutex);
        sem_post(&bleep_buffer.full);
    }

    /* The two ways to exit the above loop are to process all the
     * samples in the AIFF file or else get told to stop early.
     * Whichever, we need to clean up and terminate this thread.
     */

    bleep_playing = FALSE;
    memset(bleep_buffer.samples, 0, BUFFSIZE * sizeof(float) * 2);

    //    fseek(myeffect.fp, filestart, SEEK_SET);

    //    pthread_mutex_unlock(&mutex);
    //    sem_post(&audio_empty);

    sf_close(sndfile);
    free(floatbuffer);
    free(floatbuffer2);

    pthread_exit(NULL);
} /* playaiff */


/*
 * playmusic
 *
 * To more easily make sure only one of MOD or OGGV plays at one time.
 *
 */
static void *playmusic(EFFECT *raw_effect)
{
    EFFECT myeffect = *raw_effect;

    sem_post(&playmusic_okay);

    if (myeffect.type == MOD)		playmod(&myeffect);
    else if (myeffect.type == OGGV)	playogg(&myeffect);
    else { } /* do nothing */

    pthread_exit(NULL);

} /* playmusic */


/*
 * playmod
 *
 * This function takes a file pointer to a Blorb file and a bb_result_t
 * struct describing what chunk to play.  It's up to the caller to make
 * sure that a MOD chunk is to be played.  Volume and repeats are also
 * handled here.
 *
 */
static void *playmod(EFFECT *raw_effect)
{
    short *shortbuffer;

//    int modlen;
//    int count;

    char *filedata;
    long size;
    ModPlugFile *mod;
    ModPlug_Settings settings;

    long filestart;

    EFFECT myeffect = *raw_effect;

    set_musicnum(myeffect.number);

    filestart = ftell(myeffect.fp);
    fseek(myeffect.fp, myeffect.result.data.startpos, SEEK_SET);

    ModPlug_GetSettings(&settings);

    /* Note: All "Basic Settings" must be set before ModPlug_Load. */
    settings.mResamplingMode = MODPLUG_RESAMPLE_FIR; /* RESAMP */
    settings.mChannels = 2;
    settings.mBits = 16;
    settings.mFrequency = SAMPLERATE;
    settings.mStereoSeparation = 128;
    settings.mMaxMixChannels = 256;

    /* insert more setting changes here */
    ModPlug_SetSettings(&settings);

    /* remember to free() filedata later */
    filedata = getfiledata(myeffect.fp, &size);

    mod = ModPlug_Load(filedata, size);
    fseek(myeffect.fp, filestart, SEEK_SET);
    if (!mod) {
        printf("Unable to load MOD chunk.\n\r");
        return 0;
    }

    if (myeffect.vol < 1) myeffect.vol = 1;
    if (myeffect.vol > 8) myeffect.vol = 8;
    ModPlug_SetMasterVolume(mod, mypower(2, myeffect.vol));

    shortbuffer = malloc(BUFFSIZE * sizeof(short) * 2);

    music_playing = TRUE;

    while (1) {
        sem_wait(&music_buffer.empty);
        pthread_mutex_lock(&mutex);
        memset(music_buffer.samples, 0, BUFFSIZE * sizeof(float) * 2);
        if (!music_playing) {
            break;
        }
        music_buffer.nsamples = ModPlug_Read(mod, shortbuffer, BUFFSIZE) / 2;
        pcm16tofloat(music_buffer.samples, shortbuffer, music_buffer.nsamples);
        if (music_buffer.nsamples == 0) break;
        pthread_mutex_unlock(&mutex);
        sem_post(&music_buffer.full);
    }

    music_playing = FALSE;
    memset(music_buffer.samples, 0, BUFFSIZE * sizeof(float) * 2);

    pthread_mutex_unlock(&mutex);
    sem_post(&music_buffer.empty);

    ModPlug_Unload(mod);
    free(shortbuffer);
    free(filedata);

    return 0;
} /* playmod */


/*
 * getfiledata
 *
 * libmodplug requires the whole file to be pulled into memory.
 * This function does that and then closes the file.
 */
static char *getfiledata(FILE *fp, long *size)
{
    char *data;
    long offset;

    offset = ftell(fp);
    fseek(fp, 0L, SEEK_END);
    (*size) = ftell(fp);
    fseek(fp, offset, SEEK_SET);
    data = (char*)malloc(*size);
    fread(data, *size, sizeof(char), fp);
    fseek(fp, offset, SEEK_SET);
    return(data);
} /* getfiledata */


/*
 * playogg
 *
 * This function takes a file pointer to a Blorb file and a bb_result_t
 * struct describing what chunk to play.  It's up to the caller to make
 * sure that an OGG chunk is to be played.  Volume and repeats are also
 * handled here.
 *
 * Libsndfile is capable of reading OGG files, but not if the file is
 * embedded in another file.  That's why we're using libvorbisfile
 * directly instead of going through libsndfile.  Erikd, main developer
 * of libsndfile is working on a fix.
 *
 */
static void *playogg(EFFECT *raw_effect)
{
    ogg_int64_t toread;
    ogg_int64_t frames_read;
    ogg_int64_t count;

    vorbis_info *info;

    OggVorbis_File vf;

    int current_section;
    short *shortbuffer;

//    long filestart;
    int volcount;
    int volfactor;

    EFFECT myeffect = *raw_effect;

//    filestart = ftell(myeffect.fp);
    fseek(myeffect.fp, myeffect.result.data.startpos, SEEK_SET);

    if (ov_open_callbacks(myeffect.fp, &vf, NULL, 0, OV_CALLBACKS_NOCLOSE) < 0) {
	printf("Unable to load OGGV chunk.\n\r");
	return 0;
    }

    info = ov_info(&vf, -1);
    if (info == NULL) {
	printf("Unable to get info on OGGV chunk.\n\r");
	return 0;
    }

    if (myeffect.vol < 1) myeffect.vol = 1;
    if (myeffect.vol > 8) myeffect.vol = 8;
    volfactor = mypower(2, -myeffect.vol + 8);

    shortbuffer = malloc(BUFFSIZE * info->channels * sizeof(short));

    frames_read = 0;
    toread = ov_pcm_total(&vf, -1) * 2 * info->channels;
    count = 0;

    music_playing = TRUE;

    while (count < toread) {
	sem_wait(&music_buffer.empty);
	pthread_mutex_lock(&mutex);
	memset(music_buffer.samples, 0, BUFFSIZE * sizeof(float) * 2);
	if (!music_playing) break;

        frames_read = ov_read(&vf, (char *)shortbuffer, BUFFSIZE, 0,2,1,&current_section);

        pcm16tofloat(music_buffer.samples, shortbuffer, frames_read);
        for (volcount = 0; volcount <= frames_read / 2; volcount++) {
            ((float *) music_buffer.samples)[volcount] /= volfactor;
        }

	music_buffer.nsamples  = frames_read / 2;
    if(music_buffer.nsamples == -1)
        music_buffer.nsamples  = 0;
    //perform mix down
    count += frames_read;

	pthread_mutex_unlock(&mutex);
	sem_post(&music_buffer.full);
    }

//    fseek(myeffect.fp, filestart, SEEK_SET);
    music_playing = FALSE;

    pthread_mutex_unlock(&mutex);
    sem_post(&music_buffer.empty);

    ov_clear(&vf);

    free(shortbuffer);

    return 0;
} /* playogg */

#endif /* NO_SOUND */
