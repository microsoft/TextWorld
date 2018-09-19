#include <math.h>
#include <stdio.h>
#include <stdarg.h>
#include <stdlib.h>
#include <string.h>

#include "sf_frotz.h"

#include "samplerate.h"

static int myconv( CONV *conv, FILE *f, void *dest, int nin, int eod)
  {
  int nbrd, i, j, v=0;
  float *sdata;
  unsigned char c1, c2; char c;
  SRC_DATA src;
  sdata = src.data_in = conv->inbuf; src.data_out = conv->outbuf;
  src.input_frames = nin; src.output_frames = conv->maxout;
  src.src_ratio = conv->ratio;
  src.end_of_input = eod;
	// load input data
  nbrd = conv->bytespersam;
  switch (conv->bytespersam)
    {
    case 1:
	for (i=0;i<nin*conv->channels;i++)
		{
		c = fgetc(f);
		*sdata++ = (((short)c) << 8)/32768.0;
		}
	break;
    case 2:
	for (i=0;i<nin*conv->channels;i++)
		{
		c1 = fgetc(f);
		c2 = fgetc(f);
		*sdata++ = ((short)(((unsigned short)c1) << 8 + (unsigned short)c2))
			/ 32768.0;
		}
    }
	// do conversion
  src_process ((SRC_STATE *)conv->aux, &src);
	// save output
  nbrd = src.output_frames_gen;
  src_float_to_short_array (conv->outbuf, (short *)dest, nbrd*conv->channels) ;

  return nbrd;
  }

static void finish( CONV *conv)
  {
  if (conv->inbuf) free(conv->inbuf);
  if (conv->outbuf) free(conv->outbuf);
  if (conv->aux) src_delete(conv->aux);
  conv->inbuf = conv->outbuf = NULL;
  conv->aux = NULL;
  }

extern int (*sfx_exinitconv)( CONV *conv);

static int my_exinitconv( CONV *conv)
  {
  int err;
  if (!conv) return 0;
  conv->inbuf = malloc(conv->maxin*conv->channels*sizeof(float));
  if (!conv->inbuf) return 0;
  conv->outbuf = malloc(conv->maxout*conv->channels*sizeof(float));
  if (!conv->outbuf) { free(conv->inbuf); return 0;}
  conv->aux = src_new(SRC_SINC_FASTEST,conv->channels,&err);
  if (!conv->aux){ finish(conv); return 0;}
  conv->finishCONV = finish;
  conv->doCONV = myconv;
  return 1;
  }

static void MyInitFunc(void) __attribute__ ((constructor));
static void MyInitFunc(void)
  {
  sfx_exinitconv = my_exinitconv;
  }
