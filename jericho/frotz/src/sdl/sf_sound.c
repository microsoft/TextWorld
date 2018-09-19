#include <stdarg.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "sf_frotz.h"
#include "../blorb/blorblow.h"

#include <SDL.h>
#include <SDL_thread.h>
#include <SDL_mixer.h>

/////////////// AUDIO!!!

enum {SFX_TYPE, MOD_TYPE};

typedef struct EFFECT {
  void (*destroy)(struct EFFECT *);
  int number;
  int type;
  int active;
  int voice;
  Mix_Music * mod;
  Mix_Chunk * sam;
  int repeats;
  int volume;
  int ended;
  zword eos;
  ulong endtime;
  } EFFECT;

// no effects cache

static EFFECT *e_sfx = NULL;
static EFFECT *e_mod = NULL;

int SFaudiorunning = 0;
volatile int end_of_sound_flag = 0;
int m_no_sound = 0;
int m_frequency = 44100;

static int audio_rate, audio_channels;
		// set this to any of 512,1024,2048,4096
		// the higher it is, the more FPS shown and CPU needed
static int audio_buffers=512;
static Uint16 audio_format;
static int volume = SDL_MIX_MAXVOLUME;
static int bits;

static void finishaudio()
  {
  if (!SFaudiorunning) return;
  os_stop_sample(0);
  SFaudiorunning = 0;

	// flush cache
//printf("Flushing sound cache\n");
  if (e_sfx) e_sfx->destroy(e_sfx);
  if (e_mod) e_mod->destroy(e_mod);

  e_sfx = e_mod = NULL;

  Mix_CloseAudio();
  }

static void music_finished(void);
static void channel_finished(int channel);

int sf_initsound()
  {
  if (SFaudiorunning) return 1;
  if (m_no_sound) return 0;
  SFaudiorunning = 1;

	// initialize sdl mixer, open up the audio device
  if (Mix_OpenAudio(m_frequency,MIX_DEFAULT_FORMAT,2,audio_buffers) < 0)
	{
	SFaudiorunning = 0;
	return 0;
	}
	
  Mix_QuerySpec(&audio_rate, &audio_format, &audio_channels);
  bits = audio_format & 0xFF;

	// hook for end-of-music
  Mix_HookMusicFinished(music_finished);
	// hook for end-of-sfx
  Mix_ChannelFinished(channel_finished);

  Mix_AllocateChannels(1);
  CLEANREG(finishaudio);
//  sf_initresample();
  return 1;
  }

static void baredestroy(EFFECT * r)
  {
  if (r)
	{
	if (r->mod) Mix_FreeMusic(r->mod);
	if (r->sam) Mix_FreeChunk(r->sam);
	free(r);
	}
  }

static EFFECT * new_effect( int type, int num)
  {
  EFFECT * reader = (EFFECT *)calloc(1,sizeof(EFFECT));
  if (reader) 
	{
	reader->type = type;
	reader->number = num;
	reader->destroy = baredestroy;
	}
  return (EFFECT *)reader;
  }

// according to specs, this is only called when music ends "naturally",
// which I take for "not halted programmatically"
static void music_finished(void)
  {
  if (!e_mod) return;
  if (!e_mod->active) return;
  e_mod->active = 0;
  e_mod->ended = 1;
  }

// this may be called also via a Mix_Haltetc.
static void channel_finished(int channel)
  {
  if (channel != 0) return;
  if (!e_sfx) return;
  if (!e_sfx->active) return;
  e_sfx->active = 0;
  e_sfx->ended = 1;	// stopsample will take care of this...
  }

static void stopsample()
  {
  if (!e_sfx) return;
  e_sfx->active = 0;
  Mix_HaltChannel(0);
  e_sfx->ended = 0;
  }

static void stopmodule()
  {
  if (!e_mod) return;
  e_mod->active = 0;
//  Player_Mute(MUTE_INCLUSIVE,0,64);
//  Player_SetVolume(0);	// bug??
  Mix_HaltMusic();
  e_mod->ended = 0;
  }

static void startsample()
  {
  if (!e_sfx) return;
  Mix_PlayChannel(0,e_sfx->sam,e_sfx->repeats);
  Mix_Volume(0,e_sfx->volume);
//  Voice_SetPanning(v,PAN_CENTER);
//  while (Voice_Stopped(v)){ 
//	MikMod_Update(); sf_sleep(10);
//	}
//  e_sfx->voice = v;
  e_sfx->active = 1;
  }

//static int samplefinished(){
//  if (!Voice_Stopped(e_sfx->voice)) return 0;
//  return (sf_ticks() >= e_sfx->endtime);
//  }

static void startmodule()
  {
  if (!e_mod) return;
  Mix_PlayMusic(e_mod->mod,e_mod->repeats);
  Mix_VolumeMusic(e_mod->volume);
  e_mod->active = 1;
  }

static EFFECT *getaiff( FILE *f, size_t pos, int len, int num)
  {
  EFFECT *res;
  void * data; int size;

  res = new_effect(SFX_TYPE,num);
  if (!res) return res;

  if (sf_aiffwav(f,pos,&data,&size)==0)
	{
	res->sam = Mix_LoadWAV_RW(SDL_RWFromMem( data, size),0);
  	if (data) free(data);
	}

  if (!res->sam)
	{
//printf("Sample_LoadGeneric failure: %s\n",MikMod_strerror(MikMod_errno));
	res->destroy(res);
	return NULL;
	}
//printf("AIFF loaded\n");
  return res;
  }

static EFFECT *getmodule( FILE *f, size_t pos, int len, int num)
  {
  EFFECT *res;
  byte h[2];

  res = new_effect(MOD_TYPE,num);
  if (!res)
	return NULL;

  fseek(f,pos,SEEK_SET);
  fread(h,1,2,f);
  fseek(f,pos,SEEK_SET);
  if (h[0] == 'P' && h[1] == 'K')	// zipped module
	{
	int size; void *data;
	int st = sf_pkread(f,pos,&data,&size);
	if (st)
		{
//printf("Error %d from sf_pkread()\n",st);
		res->destroy(res);
		return NULL;
		}
	res->mod = Mix_LoadMUS_RW(SDL_RWFromMem( data, size));
	free(data);
	}
  else
	{
	FILE *f2 = fdopen(dup(fileno(f)),"rb");
	fseek(f2,pos,SEEK_SET);
	res->mod = Mix_LoadMUS_RW(SDL_RWFromFP(f2,1));
	}
  if (!res->mod)
	{
//printf("Player_Load failure: %s\n",MikMod_strerror(MikMod_errno));
	res->destroy(res);
	return NULL;
	}
//printf("Module loaded\n");
  return res;
  }

static EFFECT *geteffect( num)
  {
  myresource res;
  EFFECT *result = NULL;
  unsigned int id;

  if ((e_sfx) && (e_sfx->number == num)) return e_sfx;
  if ((e_mod) && (e_mod->number == num)) return e_mod;

  if (sf_getresource(num,0,bb_method_FilePos,&res) != bb_err_None)
	return NULL;

	// Look for a recognized format
  id = res.type;

  if (id == bb_make_id('F','O','R','M'))
	{
	result = getaiff( res.file, res.bbres.data.startpos, res.bbres.length, num);
	}
  else if (id == bb_make_id('M','O','D',' ') ||
		id == bb_make_id('O','G','G','V'))
	{
	result = getmodule( res.file, res.bbres.data.startpos, res.bbres.length, num);
	}
  sf_freeresource(&res);

  return result;
  }

// sound handling

/*
 * os_beep
 *
 * Play a beep sound. Ideally, the sound should be high- (number == 1)
 * or low-pitched (number == 2).
 *
 */
void os_beep(int number)
  {
  if (m_no_sound) return;
  printf("\a"); fflush(stdout);
  if (!SFaudiorunning) return;
/*	theWnd->FlushDisplay();
	::MessageBeep(MB_ICONEXCLAMATION);*/
  }

/*
 * os_finish_with_sample
 *
 * Remove the current sample from memory (if any).
 *
 */
void os_finish_with_sample(int number)
  {
  if (!SFaudiorunning) return;
  os_stop_sample(number);
//	FrotzSound::Stop(number);
  }

/*
 * os_prepare_sample
 *
 * Load the given sample from the disk.
 *
 */
void os_prepare_sample(int number)
  {
  if (!SFaudiorunning) return;
  }

/*
 * os_start_sample
 *
 * Play the given sample at the given volume (ranging from 1 to 8 and
 * 255 meaning a default volume). The sound is played once or several
 * times in the background (255 meaning forever). The end_of_sound
 * function is called as soon as the sound finishes, passing in the
 * eos argument.
 *
 */
void os_start_sample(int number, int volume, int repeats, zword eos)
  {
  EFFECT *e;

  if (!SFaudiorunning) return;

//printf("start %d vol %d rep %d\n",number,volume,repeats);

	// NOTE: geteffect may return an already loaded effect
  e = geteffect(number);
  if (!e) return;
  if (e->type == SFX_TYPE) stopsample();
  else stopmodule();
  if (repeats < 1) repeats = 1;
  if (repeats == 255) repeats = -1;
  if (volume < 0) volume = 0;
  if (volume > 8) volume = 8;
  if (e->type == SFX_TYPE && repeats > 0) repeats--;
  e->repeats = repeats;
  e->volume = 32*volume;
  e->eos = eos;
  e->ended = 0;
  if (e->type == SFX_TYPE)
	{
	if ((e_sfx) && (e_sfx != e)) e_sfx->destroy(e_sfx);
	e_sfx = e;
	startsample();
	}
  else
	{
	if ((e_mod) && (e_mod != e)) e_mod->destroy(e_mod);
	e_mod = e;
	startmodule();
	}
  }

/*
 * os_stop_sample
 *
 * Turn off the current sample.
 *
 */
void os_stop_sample(int number)
  {
  if (!SFaudiorunning) return;
  if (number == 0)
	{
	stopsample();
	stopmodule();
	return;
	}
  if ((e_sfx) && (e_sfx->number == number)) stopsample();
  if ((e_mod) && (e_mod->number == number)) stopmodule();

//	FrotzSound::Stop(number);
  }

void sf_checksound()
  {
  if ((e_sfx) && (e_sfx->ended))
	{
	e_sfx->ended = 0;
	if (e_sfx->eos)
		{
		end_of_sound_flag = 1;
		end_of_sound(e_sfx->eos);
		}
	}
  if ((e_mod) && (e_mod->ended))
	{
	e_mod->ended = 0;
	if (e_mod->eos)
		{
		end_of_sound_flag = 1;
		end_of_sound(e_mod->eos);
		}
	}
  }

void os_tick()
  {
  sf_checksound();
  if (SFticked)
	{
	SFticked = false;
	sf_flushdisplay();
	}
  }

///////////////////////////////////////

