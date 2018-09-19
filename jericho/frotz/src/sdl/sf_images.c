#include <stdarg.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "sf_frotz.h"

#include <math.h>

#include "png.h"
#include <setjmp.h>

#include "../blorb/blorblow.h"

// static double m_gamma = DEFAULT_GAMMA;
static byte toLinear[256];
static byte fromLinear[256];

ulong sf_blend( int a, ulong s, ulong d){
  ulong r;
  r = fromLinear[(toLinear[s & 0xff]*a + toLinear[d & 0xff]*(256-a))>>8];
  s >>= 8; d >>= 8;
  r |= (fromLinear[(toLinear[s & 0xff]*a + toLinear[d & 0xff]*(256-a))>>8]) << 8;
  s >>= 8; d >>= 8;
  r |= (fromLinear[(toLinear[s & 0xff]*a + toLinear[d & 0xff]*(256-a))>>8]) << 16;
  return r;
  }

// Set the screen gamma and build gamma correction tables
void sf_setgamma(double gamma)
  {
  int i;

  m_gamma = gamma;
  for (i = 0; i < 256; i++)
	toLinear[i] = (int)((pow(i/255.0,gamma) * 255.0) + 0.5);
  gamma = 1.0/gamma;
  for (i = 0; i < 256; i++)
	fromLinear[i] = (int)((pow(i/255.0,gamma) * 255.0) + 0.5);
  }

/////////////////////////////////////////////////////////////////////////////
// Loader for PNG images
/////////////////////////////////////////////////////////////////////////////

typedef struct {
  byte * gfxData;
  unsigned long offset;
  } PNGData;

static void readPNGData(
	png_structp png_ptr, png_bytep data, png_size_t length)
  {
  PNGData* pngData = (PNGData*)png_get_io_ptr(png_ptr);
  memcpy(data,pngData->gfxData+pngData->offset,length);
  pngData->offset += length;
  }

static int loadpng( byte *data, int length, sf_picture *graphic)
  {
  png_bytep * rowPointers = NULL;
  png_structp png_ptr = NULL;
  png_infop info_ptr = NULL;
  png_infop end_info = NULL;
  PNGData pngData;
  png_uint_32 width, height;
  int i, bit_depth, color_type, size;
  double gamma;

  graphic->pixels = NULL;
  graphic->width = graphic->height = 0;

  if (!png_check_sig(data,8))
	return 0;

  png_ptr = png_create_read_struct
	(PNG_LIBPNG_VER_STRING,(png_voidp)NULL,NULL,NULL);
  if (!png_ptr)
	return 0;

  info_ptr = png_create_info_struct(png_ptr);
  if (!info_ptr)
	{
	png_destroy_read_struct(&png_ptr,
			(png_infopp)NULL,(png_infopp)NULL);
	return 0;
	}

  end_info = png_create_info_struct(png_ptr);
  if (!end_info)
	{
	png_destroy_read_struct(&png_ptr,&info_ptr,(png_infopp)NULL);
	return 0;
	}

  if (setjmp(png_ptr->jmpbuf))
	{
	png_destroy_read_struct(&png_ptr,&info_ptr,&end_info);
	if (rowPointers) free(rowPointers);
	if (graphic->pixels)
		{
		free(graphic->pixels);
		graphic->pixels = NULL;
		}
	return 0;
	}

  pngData.gfxData = data;
  pngData.offset = 8;
  png_set_read_fn(png_ptr,&pngData,readPNGData);

  png_set_sig_bytes(png_ptr,8);
  png_read_info(png_ptr,info_ptr);

  width = png_get_image_width(png_ptr,info_ptr);
  height = png_get_image_height(png_ptr,info_ptr);
  bit_depth = png_get_bit_depth(png_ptr,info_ptr);
  color_type = png_get_color_type(png_ptr,info_ptr);

  graphic->width = width;
  graphic->height = height;

  if (color_type == PNG_COLOR_TYPE_PALETTE && bit_depth <= 8)
	png_set_palette_to_rgb(png_ptr);
  if (color_type == PNG_COLOR_TYPE_GRAY && bit_depth < 8)
  #ifdef __WIN32__
    os_fatal("Missing png_set_gray_1_2_4_to_8\n");
  #else
	png_set_gray_1_2_4_to_8(png_ptr);
  #endif
  if (png_get_valid(png_ptr,info_ptr,PNG_INFO_tRNS))
	png_set_tRNS_to_alpha(png_ptr);

  if (png_get_gAMA(png_ptr,info_ptr,&gamma))
	png_set_gamma(png_ptr,m_gamma,gamma);

  if (bit_depth == 16)
	png_set_strip_16(png_ptr);
  if (bit_depth < 8)
	png_set_packing(png_ptr);
  if (color_type == PNG_COLOR_TYPE_GRAY || 
		color_type == PNG_COLOR_TYPE_GRAY_ALPHA)
	png_set_gray_to_rgb(png_ptr);

 // png_set_bgr(png_ptr);
  png_set_filler(png_ptr,0xFF,PNG_FILLER_AFTER);

//	graphic->m_header = new BITMAPINFOHEADER;
//	::ZeroMemory(graphic->m_header,sizeof(BITMAPINFOHEADER));
//	graphic->m_header->biSize = sizeof(BITMAPINFOHEADER);
//	graphic->m_header->biWidth = width;
//	graphic->m_header->biHeight = height*-1;
//	graphic->m_header->biPlanes = 1;
//	graphic->m_header->biBitCount = 32;
//	graphic->m_header->biCompression = BI_RGB;

  size = width*height*4;
  graphic->pixels = (byte *)malloc(size);

  rowPointers = (png_bytep *) malloc(height*sizeof(png_bytep));
  for (i = 0; i < (int)height; i++)
	rowPointers[i] = graphic->pixels+(width*i*4);
  png_read_image(png_ptr,rowPointers);

	// Get the palette after reading the image, so that the gamma
	// correction is applied
//	png_colorp palette;
//	int num_palette;
//	if (png_get_PLTE(png_ptr,info_ptr,&palette,&num_palette))
//	{
//		for (int i = 0; i < num_palette; i++)
//		{
//			DWORD colour =
//				(palette[i].red<<16)|(palette[i].green<<8)|palette[i].blue;
//			graphic->m_palette.Add(colour);
//			graphic->m_invPalette[colour] = i;
//		}
//	}

  png_read_end(png_ptr,end_info);
  png_destroy_read_struct(&png_ptr,&info_ptr,&end_info);
  if (rowPointers) free( rowPointers);

  return 1;
  }

/////////////////////////////////////////////////////////////////////////////
// Loader for JPEG images
/////////////////////////////////////////////////////////////////////////////

#include <jpeglib.h>

// Error Handling

struct JPEGErrorInfo {
  struct jpeg_error_mgr base;
  jmp_buf errorJump;
  };

static void errorJPEGExit(j_common_ptr cinfo)
  {
  struct JPEGErrorInfo* error = (struct JPEGErrorInfo*)cinfo->err;
  (*cinfo->err->output_message)(cinfo);
  longjmp(error->errorJump,1);
  }

static void outputJPEGMessage(j_common_ptr cinfo)
  {
  char buffer[JMSG_LENGTH_MAX];
  (*cinfo->err->format_message)(cinfo,buffer);
//  TRACE("JPEG: %s\n",buffer);
  }

// Memory Data Source

static void memJPEGInit(j_decompress_ptr unused)
  {
  }

static int memJPEGFillInput(j_decompress_ptr unused)
  {
  return 0;
  }

static void memJPEGSkipInput(j_decompress_ptr cinfo, long num_bytes)
  {
  if (num_bytes > 0)
	{
	if (num_bytes > (long)cinfo->src->bytes_in_buffer)
		num_bytes = (long)cinfo->src->bytes_in_buffer;

	cinfo->src->next_input_byte += num_bytes;
	cinfo->src->bytes_in_buffer -= num_bytes;
	}
  }

static void memJPEGTerm(j_decompress_ptr unused)
  {
  }

static int loadjpeg( byte *data, int length, sf_picture *graphic)
  {
  struct jpeg_decompress_struct info;
  struct JPEGErrorInfo error;
  int width, height, size;
  JSAMPARRAY buffer;

  graphic->pixels = NULL;
  graphic->width = graphic->height = 0;

  info.err = jpeg_std_error(&(error.base));
  error.base.error_exit = errorJPEGExit;
  error.base.output_message = outputJPEGMessage;
  if (setjmp(error.errorJump))
	{
	jpeg_destroy_decompress(&info);
	if (graphic->pixels)
		{
		free(graphic->pixels);
		graphic->pixels = NULL;
		}
	return 0;
	}

  jpeg_create_decompress(&info);

  info.src = (struct jpeg_source_mgr *)(info.mem->alloc_small)
	((j_common_ptr)(&info),JPOOL_PERMANENT,sizeof(struct jpeg_source_mgr));
  info.src->init_source = memJPEGInit;
  info.src->fill_input_buffer = memJPEGFillInput;
  info.src->skip_input_data = memJPEGSkipInput;
  info.src->resync_to_restart = jpeg_resync_to_restart;
  info.src->term_source = memJPEGTerm;
  info.src->bytes_in_buffer = length;
  info.src->next_input_byte = data;

  jpeg_read_header(&info,TRUE);
  jpeg_calc_output_dimensions(&info);
  width = info.output_width;
  height = info.output_height;

  graphic->width = width;
  graphic->height = height;
  size = width*height*4;
  graphic->pixels = (byte *)malloc(size);
		
//	graphic->m_header = new BITMAPINFOHEADER;
//	::ZeroMemory(graphic->m_header,sizeof(BITMAPINFOHEADER));
//	graphic->m_header->biSize = sizeof(BITMAPINFOHEADER);
//	graphic->m_header->biWidth = width;
//	graphic->m_header->biHeight = height*-1;
//	graphic->m_header->biPlanes = 1;
//	graphic->m_header->biBitCount = 32;
//	graphic->m_header->biCompression = BI_RGB;
//	graphic->m_pixels = new BYTE[width*height*4];

	// Force RGB output
  info.out_color_space = JCS_RGB;

	// Get an output buffer
  buffer = (*info.mem->alloc_sarray)
	((j_common_ptr)&info,JPOOL_IMAGE,width*3,1);

  jpeg_start_decompress(&info);
  while ((int)info.output_scanline < height)
	{
	byte * pixelRow; int i;
	jpeg_read_scanlines(&info,buffer,1);

	pixelRow = graphic->pixels+
			(width*(info.output_scanline-1)*4);
	for (i = 0; i < width; i++)
		{
/*		pixelRow[(i*4)+0] = (*buffer)[(i*3)+2];
		pixelRow[(i*4)+1] = (*buffer)[(i*3)+1];
		pixelRow[(i*4)+2] = (*buffer)[(i*3)+0];*/
		pixelRow[(i*4)+0] = (*buffer)[(i*3)+0];
		pixelRow[(i*4)+1] = (*buffer)[(i*3)+1];
		pixelRow[(i*4)+2] = (*buffer)[(i*3)+2];
		pixelRow[(i*4)+3] = 0xFF;
		}
	}
  jpeg_finish_decompress(&info);
  jpeg_destroy_decompress(&info);

  return 1;
  }

/////////////////////////////////////////////////////////////////////////////
// Loader for simple rectangles
/////////////////////////////////////////////////////////////////////////////

static int loadrect( byte *data, int length, sf_picture *graphic)
  {
  graphic->width = (data[0]<<24)|(data[1]<<16)|(data[2]<<8)|data[3];
  graphic->height = (data[4]<<24)|(data[5]<<16)|(data[6]<<8)|data[7];
  graphic->pixels = NULL;
  return 1;
  }

///////////////////////////////

// Get a picture from the Blorb resource map
static int sf_loadpic( int picture, sf_picture *graphic)
  {
  myresource res;
  int st = 0;

  if (sf_getresource( picture, 1, bb_method_Memory,&res) == bb_err_None)
	{
	byte * data = (byte *)res.bbres.data.ptr;
	int length = res.bbres.length;
	unsigned int id = res.type;

		// Look for a recognized format
	if (id == bb_make_id('P','N','G',' '))
		{
		st = loadpng( data, length, graphic);
		if (!st) st = loadjpeg( data, length, graphic);
		}
	else if (id == bb_make_id('J','P','E','G'))
		{
		st = loadjpeg( data, length, graphic);
		if (!st) st = loadpng( data, length, graphic);
		}
	else if (id == bb_make_id('R','e','c','t'))
		st = loadrect( data, length, graphic);
	sf_freeresource(&res);
	}

  if (st) graphic->number = picture;
  return st;
  }

////////////////////
// CACHE

#define MAXCACHE 1

static sf_picture cached[MAXCACHE];
static int cacheinited = 0;

static void cacheflush()
  {
  int i;
  if (!cacheinited) return;
  for (i=0;i<MAXCACHE;i++)
	{
	cached[i].number = -1;
	if (cached[i].pixels) free(cached[i].pixels);
	cached[i].pixels = NULL;
	}
  cacheinited = 0;
  }

static void cacheinit(){
  int i;
  if (cacheinited) return;
  CLEANREG(cacheflush);
  for (i=0;i<MAXCACHE;i++)
	{
	cached[i].number = -1;
	cached[i].pixels = NULL;
	}
  cacheinited = 1;
  }

static sf_picture * cachefind( int n){
  int i;
  for (i=0;i<MAXCACHE;i++)
	if (cached[i].number == n) return (cached+i);
  if (n < 0){
	cached[0].number = -1;
	if (cached[0].pixels) free(cached[0].pixels);
	cached[0].pixels = NULL;
	return (cached+0);
	}
  return NULL;
  }

sf_picture * sf_getpic( int num){
  sf_picture *res;
  cacheinit();
  res = cachefind(num);
  if (res) return res;
	// not found, peek a slot
  res = cachefind(-1);
  if (sf_loadpic( num, res)) return res;
  return NULL;
  }

