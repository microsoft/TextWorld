// Pseudo-operations.

LABEL (jump_abs_L7)
LABEL (enter_function_L1)

LABEL (debug_step)

LABEL (args_stack_call_stub_discard)
LABEL (args_stack_call_stub_addr)
LABEL (args_stack_call_stub_local)
LABEL (args_stack_call_stub_stack)

LABEL (args_stack)
LABEL (args_0)
LABEL (args_1)
LABEL (args_2)
LABEL (args_3)

LABEL (call_stub_discard)
LABEL (call_stub_addr)
LABEL (call_stub_local)
LABEL (call_stub_stack)

LABEL (catch_stub_discard)
LABEL (catch_stub_addr)
LABEL (catch_stub_local)
LABEL (catch_stub_stack)

LABEL (save_stub_discard)
LABEL (save_stub_addr)
LABEL (save_stub_local)
LABEL (save_stub_stack)

LABEL (undo_stub_discard)
LABEL (undo_stub_addr)
LABEL (undo_stub_local)
LABEL (undo_stub_stack)

LABEL (tailcall)
LABEL (throw)

// Loading and storing registers.

#define LOAD_LABELS(tag)			\
	LABEL (L1_ ## tag)			\
	LABEL (L2_ ## tag)			\
	LABEL (L3_ ## tag)			\
	LABEL (L4_ ## tag)			\
	LABEL (L5_ ## tag)			\
	LABEL (L6_ ## tag)			\
	LABEL (L7_ ## tag)			\
	LABEL (L1_const_L2_ ## tag)		\
	LABEL (L1_stack_L2_ ## tag)		\
	LABEL (L1_local_L2_ ## tag)		\
	LABEL (L1_addr_L2_ ## tag)

#define STORE_LABELS(tag)			\
	LABEL (S1_ ## tag)			\
	LABEL (S2_ ## tag)

LOAD_LABELS(const)
LOAD_LABELS(stack)
LOAD_LABELS(local)
LOAD_LABELS(addr)

STORE_LABELS(stack)
STORE_LABELS(local)
STORE_LABELS(addr)

LABEL(L1_addr16)
LABEL(L1_addr8)

LABEL(S1_addr16)
LABEL(S1_addr8)

#undef LOAD_LABELS
#undef STORE_LABELS

// Labels corresponding to glulx opcodes.

LABEL (nop)

#define PEEPHOLE_STORE_LABELS(tag) \
	LABEL (add ## tag) \
	LABEL (sub ## tag) \
	LABEL (mul ## tag) \
	LABEL (div ## tag) \
	LABEL (mod ## tag) \
	LABEL (neg ## tag) \
	LABEL (bitand ## tag) \
	LABEL (bitor ## tag) \
	LABEL (bitxor ## tag) \
	LABEL (bitnot ## tag) \
	LABEL (shiftl ## tag) \
	LABEL (sshiftr ## tag) \
	LABEL (ushiftr ## tag) \
	LABEL (copys ## tag) \
	LABEL (copyb ## tag) \
	LABEL (sexs ## tag) \
	LABEL (sexb ## tag) \
	LABEL (aload ## tag) \
	LABEL (aloads ## tag) \
	LABEL (aloadb ## tag) \
	LABEL (aloadbit ## tag) \
	LABEL (fadd ## tag) \
	LABEL (fsub ## tag) \
	LABEL (fmul ## tag) \
	LABEL (fdiv ## tag)

PEEPHOLE_STORE_LABELS(_discard)
PEEPHOLE_STORE_LABELS(_S1_stack)
PEEPHOLE_STORE_LABELS(_S1_local)
PEEPHOLE_STORE_LABELS(_S1_addr)

#define PEEPHOLE_LOAD_LABELS(tag) \
	LABEL (return_L1_ ## tag) \
	LABEL (astore_L3_ ## tag) \
	LABEL (astores_L3_ ## tag) \
	LABEL (astoreb_L3_ ## tag) \
	LABEL (astorebit_L3_ ## tag)

PEEPHOLE_LOAD_LABELS(const)
PEEPHOLE_LOAD_LABELS(stack)
PEEPHOLE_LOAD_LABELS(addr)
PEEPHOLE_LOAD_LABELS(local)

LABEL (return)
LABEL (astore)
LABEL (astores)
LABEL (astoreb)
LABEL (astorebit)

#undef PEEPHOLE_STORE_LABELS

#define BRANCH_LABELS(tag)    \
	LABEL (jump ## tag)   \
	LABEL (jz ## tag)     \
	LABEL (jnz ## tag)    \
	LABEL (jeq ## tag)    \
	LABEL (jne ## tag)    \
	LABEL (jlt ## tag)    \
	LABEL (jge ## tag)    \
	LABEL (jgt ## tag)    \
	LABEL (jle ## tag)    \
	LABEL (jltu ## tag)   \
	LABEL (jgeu ## tag)   \
	LABEL (jgtu ## tag)   \
	LABEL (jleu ## tag)   \
	LABEL (jflt ## tag)   \
	LABEL (jfge ## tag)   \
	LABEL (jfgt ## tag)   \
	LABEL (jfle ## tag)   \
	LABEL (jisnan ## tag) \
	LABEL (jisinf ## tag) \
	LABEL (jfeq ## tag)   \
	LABEL (jfne ## tag)

BRANCH_LABELS(_var)
BRANCH_LABELS(_const)
BRANCH_LABELS(_by)
BRANCH_LABELS(_return0)
BRANCH_LABELS(_return1)

LABEL (stkcount)
LABEL (stkpeek)
LABEL (stkswap)
LABEL (stkroll)
LABEL (stkcopy)

LABEL (streamchar)
LABEL (streamnum)
LABEL (streamstr)
LABEL (streamunichar)

LABEL (gestalt)
LABEL (debugtrap)
LABEL (getmemsize)
LABEL (setmemsize)
LABEL (jumpabs)

LABEL (random)
LABEL (setrandom)

LABEL (quit)
LABEL (verify)
LABEL (restart)
LABEL (restore)
LABEL (restoreundo)
LABEL (protect)

LABEL (glk)

LABEL (getstringtbl)
LABEL (setstringtbl)
LABEL (getiosys)
LABEL (setiosys)

LABEL (linearsearch)
LABEL (binarysearch)
LABEL (linkedsearch)

LABEL (mzero)
LABEL (mcopy)
LABEL (malloc)
LABEL (mfree)

LABEL (accelfunc)
LABEL (accelparam)

LABEL (numtof)
LABEL (ftonumz)
LABEL (ftonumn)
LABEL (ceil)
LABEL (floor)
LABEL (fmod)
LABEL (sqrt)
LABEL (exp)
LABEL (log)
LABEL (pow)
LABEL (sin)
LABEL (cos)
LABEL (tan)
LABEL (asin)
LABEL (acos)
LABEL (atan)
LABEL (atan2)

LABEL (git_setcacheram)
LABEL (git_prunecache)

LABEL (error_bad_opcode)
LABEL (recompile)

// No more labels to define.
#undef LABEL
