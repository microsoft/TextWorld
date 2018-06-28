// $Id: config.h,v 1.4 2003/10/18 23:19:52 iain Exp $
// Platform-dependent configuration for Git

#ifndef GIT_CONFIG_H
#define GIT_CONFIG_H

// Various compile-time options. You can define them in the
// makefile or uncomment them here, whichever's easiest.

// Define if we're big-endian and can read and write unaligned data.
// #define USE_BIG_ENDIAN_UNALIGNED

// Define this to use GCC's labels-as-values extension for a big speedup.
// #define USE_DIRECT_THREADING

// Define this if we can use the "inline" keyword.
// #define USE_INLINE

// Define this to memory-map the game file to speed up loading. (Unix-specific)
// #define USE_MMAP

// Define this to use an OS-specific git_powf() power math function. This
// is useful if your compiler's powf() doesn't implement every special case
// of the C99 standard.
// #define USE_OWN_POWF

// -------------------------------------------------------------------

// Make sure we're compiling for a sane platform. For now, this means
// 8-bit bytes and 32-bit pointers. We'll support 64-bit machines at
// some point in the future, but we will probably never support machines
// that can't read memory 8 bits at a time; it's just too much hassle.

#include <limits.h>

#if CHAR_BIT != 8
#error "Git needs 8-bit bytes"
#endif

// This check doesn't work on all compilers, unfortunately.
// It's checked by an assert() at runtime in initCompiler().
#if 0
// #if sizeof(void*) != 4
#error "Git needs 32-bit pointers"
#endif

// Now we determine what types to use for 8-bit, 16-bit and 32-bit ints.

#if UCHAR_MAX==0xff
typedef signed char   git_sint8;
typedef unsigned char git_uint8;
#else
#error "Can't find an 8-bit integer type"
#endif

#if SHRT_MAX==0x7fff
typedef signed   short git_sint16;
typedef unsigned short git_uint16;
#elif INT_MAX==0x7fff
typedef signed   int git_sint16;
typedef unsigned int git_uint16;
#else
#error "Can't find a 16-bit integer type"
#endif

#if INT_MAX==0x7fffffff
typedef signed   int git_sint32;
typedef unsigned int git_uint32;
#elif LONG_MAX==0x7fffffff
typedef signed   long git_sint32;
typedef unsigned long git_uint32;
#else
#error "Can't find a 32-bit integer type"
#endif

// USE_INLINE is pretty simple to deal with.

#ifdef USE_INLINE
#define GIT_INLINE static inline
#else
#define GIT_INLINE static
#endif

typedef float git_float;


#if defined(__GNUC__)
// GCC and compatible compilers such as clang
#  define maybe_unused  __attribute__((__unused__))
#  define git_noreturn  __attribute__((__noreturn__))
#elif defined(_MSC_VER)
// Microsoft Visual Studio
#  define maybe_unused
#  define git_noreturn  __declspec(noreturn)
#else
#  define maybe_unused
#  define git_noreturn
#endif

#endif // GIT_CONFIG_H
