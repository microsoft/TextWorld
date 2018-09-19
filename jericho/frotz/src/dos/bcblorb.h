#include "blorb.h"
#include "blorblow.h"


typedef struct sampledata_struct {
	unsigned short channels;
	unsigned long samples;
	unsigned short bits;
	double rate;
} sampledata_t;


bb_err_t	blorb_err;
bb_map_t	*blorb_map;
bb_result_t	blorb_res;


/* uint32 *findchunk(uint32 *data, char *chunkID, int length); */
char *findchunk(char *pstart, char *fourcc, int n);
unsigned short ReadShort(const unsigned char *bytes);
unsigned long ReadLong(const unsigned char *bytes);
double ReadExtended(const unsigned char *bytes);

#define UnsignedToFloat(u) (((double)((long)(u - 2147483647L - 1))) + 2147483648.0)





