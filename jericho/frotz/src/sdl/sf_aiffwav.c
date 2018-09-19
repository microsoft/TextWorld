// sf_aiffwav.c
//
// Functions to read an AIFF file and convert (in memory) to WAV format,
// as libmikmod only reads WAV samples
//

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>

#include "sf_frotz.h"

#ifndef HUGE_INT32
#define HUGE_INT32 0x7fffffff
#endif						/* HUGE_VAL */

#ifndef Uint32
#define Uint32 unsigned int
#endif

/****************************************************************
 * Extended precision IEEE floating-point conversion routine.
 ****************************************************************/

static int IeeeExtendedToLong( unsigned char *bytes){
  int f = 0, expon; Uint32 hiMant, loMant;

  expon = ((bytes[0] & 0x7F) << 8) | (bytes[1] & 0xFF);
  hiMant = ((Uint32) (bytes[2] & 0xFF) << 24)
	| ((Uint32) (bytes[3] & 0xFF) << 16)
	| ((Uint32) (bytes[4] & 0xFF) << 8)
	| ((Uint32) (bytes[5] & 0xFF));
  loMant = ((Uint32) (bytes[6] & 0xFF) << 24)
	| ((Uint32) (bytes[7] & 0xFF) << 16)
	| ((Uint32) (bytes[8] & 0xFF) << 8)
	| ((Uint32) (bytes[9] & 0xFF));

  if (expon == 0 && hiMant == 0 && loMant == 0) f = 0;
  else if (expon == 0x7FFF) f = HUGE_INT32;
  else {
	expon -= 16382;
	expon = 32-expon;
	if (expon < 0) f = HUGE_INT32;
	else f = hiMant >> expon;
	}

  if (bytes[0] & 0x80)
	return -f;
  else
	return f;
  }

static void writeRIFFheader( unsigned char *f, int freq, int numsamples, int numchannels,
	int bytespersample);


// returns 1 if resampling, 0 if not needed, negative if error
static int initCONV( CONV *conv, double ratio, int ncha, int bytespersam, int maxinp);
static void finishCONV( CONV *conv);

#define BLOCKSIZE 1024

// hack to leave resampling to mixer in simpler cases
#define HACKING 0
static int hack( double ratio)
  {
  int m; double diff;
  if (HACKING == 0) return 0;
  if (ratio > 0.9)
	{
	m = ratio + 0.499;	// nint
	diff = fabs(ratio - (double)m)/ratio;
	if (diff < 0.01) return m;
	}
  else
	{
	m = 1.0/ratio + 0.499;
	diff = ratio*fabs(1.0/ratio - (double)m);
	if (diff < 0.01) return (-m);
	}
  return 0;
  }

#define MAXCHAN 8
// size of WAV header
#define HEADERSIZE 44

#define NPAD 30

#define glong( b) (((int)((b)[0]) << 24) + ((int)((b)[1]) << 16) +\
	((int)((b)[2]) << 8) + (int)((b)[3]))

#define gshort( b) (((int)((b)[0]) << 8) + (int)((b)[1]))

int sf_aiffwav( FILE *f, int foffs, void ** wav, int *length){

  unsigned char chk[18], fid[4];
  int len, bps=0, offs, bksize, size;
  int samples, frequency, channels, found = 0;
  int bytespersample, reqsize;
  int noutsam=0, noutreqsam, bytesneeded, outbytespersample=2, mhack;
  double ratio, cratio;
  CONV conv; int needCONV;

  unsigned char *bout = NULL;

  if (!f) return -20;
  if (!wav) return -21;

  fseek(f,foffs,0);

  samples = 0; frequency = 0;
  channels = 0;

  if (fread(chk,1,4,f) < 4) return -1;	// FORM
  if (memcmp(chk,"FORM",4)) return -3;
  if (fread(chk,1,4,f) < 4) return -1;	// size
  size = glong(chk);
  if (size & 1) size++;
  if (size < 20) return -99;
  if (fread(chk,1,4,f) < 4) return -1;	// AIFF
  if (memcmp(chk,"AIFF",4)) return -3;
  size -= 4;
  while (size > 8){
	if (fread(fid,1,4,f) < 4) return -1;	// chunck id
	if (fread(chk,1,4,f) < 4) return -1;	// and len
	size -= 8;
	len = glong(chk);
	if (len < 0) return -98;
	if (len & 1) len++;
	size -= len;
	if (size < 0) return -97;
	if (memcmp(fid,"COMM",4)==0){
		if (len != 18) return -5;
		if (fread(chk,1,18,f) < 18) return -1;
		channels = gshort(chk);
		if (channels < 1) return -9;
		if (channels > MAXCHAN) return -9;
		samples = glong(chk+2);
		if (samples < 1) return -9;
		frequency = IeeeExtendedToLong(chk+8);
		if (frequency <= 0) return -54;
		bps = gshort(chk+6);
		if (bps < 1 || bps > 16) return -51;
//		data = malloc(samples*sizeof(short));
//		if (!data) return -55;
		}
	else if (memcmp(fid,"SSND",4)==0){
		if (!channels) return -11;
		if (fread(chk,1,4,f) < 4) return -1;
		offs = glong(chk);
		if (fread(chk,1,4,f) < 4) return -1;
		bksize = glong(chk);
		if (bksize) return -77;
		if (offs) fseek(f,offs,SEEK_CUR);
		found = 1;
		break;
		}
	else fseek(f,len,SEEK_CUR);
	}
  if (!found) return -69;
  if (!channels) return -66;

		// her should check freq
  ratio = (double)m_frequency / (double)frequency;
  mhack = hack(ratio);
  cratio = ratio;
  if (mhack)
	{
	cratio = 1.0;
	if (mhack > 0) frequency = m_frequency/mhack;
	else frequency = m_frequency * (-mhack);
	}

  noutreqsam = cratio*samples + 0.49;
  bytesneeded = HEADERSIZE + noutreqsam*channels*outbytespersample;
  bout = malloc(bytesneeded);
  if (!bout) return -55;

  *wav = (void *)bout;
  bout += HEADERSIZE;

  noutsam = 0;

  if ((needCONV = initCONV(&conv,cratio,channels,(bps+7)/8,BLOCKSIZE)) < 0)
	{
	free(bout);
	*wav = NULL;
	return -997;
	}

  while (samples)
	{
	int nrd = BLOCKSIZE, nwr;
	if (nrd > samples) nrd = samples;
	nwr = conv.doCONV( &conv, f, bout, nrd, nrd == samples);
	samples -= nrd;
	noutsam += nwr;
	bout += nwr*channels*outbytespersample;
	}

  conv.finishCONV(&conv);

//printf("AIFF %d, req %d\n",frequency,m_frequency);
	// write RIFF header
  if (needCONV) frequency = m_frequency;
  writeRIFFheader( *wav, frequency, noutsam, channels, outbytespersample);

  *length = HEADERSIZE + noutsam*channels*outbytespersample;

/*{
FILE *f;
f = fopen("_TMP","w"); fwrite(*wav,1,*length,f); fclose(f);
}*/
  return 0;
  }

// returns num of output samples
static int NOCONV( CONV *conv, FILE *f, void *dest, int nin, int eod)
  {
  int nbrd, i, j, v=0;
  short *sdata = (short *)dest;
  unsigned char c1, c2; char c;

  nbrd = conv->bytespersam;;
  switch (conv->bytespersam)
    {
    case 1:
	for (i=0;i<nin*conv->channels;i++)
		{
		c = fgetc(f);
		*sdata++ = ((short)c) << 8;
		}
	break;
    case 2:
	for (i=0;i<nin*conv->channels;i++)
		{
		c1 = fgetc(f);
		c2 = fgetc(f);
		*sdata++ = (short)(((unsigned short)c1) << 8 + (unsigned short)c2);
		}
    }
  return nin;
  }

static void finishCONV( CONV *conv)
  {
  if (conv->inbuf) free(conv->inbuf);
  if (conv->outbuf) free(conv->outbuf);
  conv->inbuf = conv->outbuf = NULL;
  }

// needs a pre-initialized CONV
int (*sfx_exinitconv)( CONV *conv) = NULL;

static int initCONV( CONV *conv, double ratio, int ncha, int bytespersam, int maxinp)
  {
  int doconv;
  conv->ratio = ratio;
  conv->channels = ncha;
  conv->bytespersam = bytespersam;
  conv->maxin = maxinp;
  conv->maxout = ratio*maxinp+5;	// a little margin
  doconv = ((ratio != 1.0) && (sfx_exinitconv != NULL));
  conv->inbuf = conv->outbuf = NULL;
  if (doconv == 0)
	{
  	conv->doCONV = NOCONV;
	conv->finishCONV = finishCONV;
	}
  else
	{
	doconv = sfx_exinitconv(conv);
	}
  return doconv;
  }

#define PCwrite4( f, v) \
  *f++ = v & 0xff;\
  *f++ = (v >> 8) & 0xff;\
  *f++ = (v >> 16) & 0xff;\
  *f++ = v >> 24;

#define PCwrite2( f, v) \
  *f++ = v & 0xff;\
  *f++ = (v >> 8) & 0xff;

static void writeRIFFheader( unsigned char *f, int freq, int numsamples, int numchannels,
	int bytespersample){
	// write header
	// offset 0
  memcpy(f,"RIFF",4); f += 4;
	// offset 4
  PCwrite4(f,(36+numsamples*numchannels*bytespersample));
	// offset 8
  memcpy(f,"WAVEfmt ",8); f += 8;
	// offset 16
  PCwrite4(f,16);
	// offset 20
  PCwrite2(f,1);	// PCM
	// offset 22
  PCwrite2(f,numchannels);	// nchannels
	// offset 24
  PCwrite4(f,freq);
	// offset 28
  PCwrite4(f,(freq*numchannels*bytespersample));
	// offset 32
  PCwrite2(f,(numchannels*bytespersample));
	// offset 34
  PCwrite2(f,(8*bytespersample));
	// offset 36
  memcpy(f,"data",4); f += 4;
	// offset 40
  PCwrite4(f,(numsamples*numchannels*bytespersample));
	// offset 44
  }

