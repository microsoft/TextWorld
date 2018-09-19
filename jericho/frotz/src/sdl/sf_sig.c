#include <stdio.h>
#include <signal.h>
#include <stdlib.h>

#include "sf_frotz.h"

#ifdef WIN32

static void resethandlers()
  {
  signal(SIGINT,SIG_DFL);
  signal(SIGFPE,SIG_DFL);
  signal(SIGSEGV,SIG_DFL);
  }

static const char * signame( int sig)
  {
  switch (sig)
	{
	case SIGINT: return "[SIGINT]";
	case SIGFPE: return "[SIGFPE]";
	case SIGSEGV: return "[SIGSEGV]";
	default: return "";
	}
  }

static void myhandler( int s)
  {
  resethandlers();
  os_fatal("Signal %d received %s",s,signame(s));
  }

void sf_installhandlers()
  {
//  CLEANREG(resethandlers);
  signal(SIGINT,myhandler);
  signal(SIGFPE,myhandler);
  signal(SIGSEGV,myhandler);
  }


#else

#include <execinfo.h>

/* get REG_EIP from ucontext.h */
#ifndef __USE_GNU
#define __USE_GNU
#include <ucontext.h>
#endif

// REG_EIP does not exist on 64bit CPU
#if defined(__amd64__) || defined (__x86_64__)
#define _PROG_COUNTER REG_RIP
#else
#define _PROG_COUNTER REG_EIP
#endif

static struct { int sig; char *name;} NAMES[] = {
	{SIGSEGV,"SIGSEGV"},
	{SIGFPE,"SIGFPE"},
	{SIGILL,"SIGILL"},
	{0,NULL}};

static char *getsigname( int s){
  int i = 0;
  while (NAMES[i].name)
	{
	if (NAMES[i].sig == s) return NAMES[i].name;
	i++;
	}
  return NULL;
  }

static void bt_sighandler(int sig, siginfo_t *info,
                                   void *secret) {

  void *trace[16];
  char **messages = (char **)NULL;
  char *nam;
  int i, trace_size = 0;
  ucontext_t *uc = (ucontext_t *)secret;

  if (sig == SIGINT)
    os_fatal("Emergency exit!\n\n(Signal SIGINT received)");

  /* Do something useful with siginfo_t */

  printf("\nInterpreter bug!\nSignal %d ", sig);
  if ((nam = getsigname(sig))) printf("[%s] ",nam);
  printf("from %p", uc->uc_mcontext.gregs[_PROG_COUNTER]);

  if (sig == SIGSEGV)
        printf(" [faulty address is %p]",info->si_addr);

  printf("\n");

  trace_size = backtrace(trace, 16);
  /* overwrite sigaction with caller's address */
  trace[1] = (void *) uc->uc_mcontext.gregs[_PROG_COUNTER];

  /* skip first stack frame (points here) */
  printf("Backtrace:\n");
//   messages = backtrace_symbols(trace, trace_size);
//   for (i=1; i<trace_size; ++i)
//         printf("[bt] %s\n", messages[i]);

  for (i=1;i<trace_size;i++)
    {
    printf("  "); fflush(stdout);
    backtrace_symbols_fd(trace+i, 1,fileno(stdout));
    }

  exit(0);
  }

void sf_installhandlers()
  {

  /* Install our signal handler */
  struct sigaction sa;

  sa.sa_sigaction = (void *)bt_sighandler;
  sigemptyset (&sa.sa_mask);
  sa.sa_flags = SA_RESTART | SA_SIGINFO;

  sigaction(SIGSEGV, &sa, NULL);
  sigaction(SIGUSR1, &sa, NULL);
  sigaction(SIGFPE, &sa, NULL);
  sigaction(SIGINT, &sa, NULL);
  sigaction(SIGILL, &sa, NULL);

  }

#endif
