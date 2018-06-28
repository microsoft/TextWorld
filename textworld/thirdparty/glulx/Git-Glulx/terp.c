// $Id: terp.c,v 1.42 2004/12/22 14:33:40 iain Exp $
// Interpreter engine.

#include "git.h"
#include <assert.h>
#include <math.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

// -------------------------------------------------------------
// Global variables

git_sint32* gStackPointer;

#ifdef USE_DIRECT_THREADING
Opcode* gOpcodeTable;
#endif

// -------------------------------------------------------------
// Useful macros for manipulating the stack

#define LOCAL(n)   (locals[(n)])

#define PUSH(n)    *sp++ = (n)
#define POP        (*--sp)
#define READ_PC    ((git_uint32)(*pc++))

#define CHECK_FREE(n) if ((top - sp) < (n)) goto stack_overflow
#define CHECK_USED(n) if ((sp - values) < (n)) goto stack_underflow

// -------------------------------------------------------------
// Floating point support

GIT_INLINE git_uint32 ENCODE_FLOAT(git_float f)
{
  git_uint32 n;
  memcpy(&n, &f, 4);
  return n;
}

GIT_INLINE git_float DECODE_FLOAT(git_uint32 n) {
  git_float f;
  memcpy(&f, &n, 4);
  return f;
}

int floatCompare(git_sint32 L1, git_sint32 L2, git_sint32 L3)
{
  git_float F1, F2;

  if (((L3 & 0x7F800000) == 0x7F800000) && ((L3 & 0x007FFFFF) != 0))
    return 0;
  if ((L1 == 0x7F800000 || L1 == 0xFF800000) && (L2 == 0x7F800000 || L2 == 0xFF800000))
    return (L1 == L2);

  F1 = DECODE_FLOAT(L2) - DECODE_FLOAT(L1);
  F2 = fabs(DECODE_FLOAT(L3));
  return ((F1 <= F2) && (F1 >= -F2));
}

#ifdef USE_OWN_POWF
float git_powf(float x, float y);
#endif

// -------------------------------------------------------------
// Functions

void startProgram (size_t cacheSize, enum IOMode ioMode)
{
    Block pc; // Program counter (pointer into dynamically generated code)

    git_sint32 L1=0, L2=0, L3=0, L4=0, L5=0, L6=0, L7=0;
#define S1 L1
#define S2 L2
    git_float F1=0.0f, F2=0.0f, F3=0.0f, F4=0.0f;

    git_sint32* base;   // Bottom of the stack.
    git_sint32* frame;  // Bottom of the current stack frame.
    git_sint32* locals; // Start of the locals section of the current frame.
    git_sint32* values; // Start of the values section of the current frame.
    git_sint32* sp;     // Next free stack slot.
    git_sint32* top;    // The top of the stack -- that is, the first unusable slot.

    git_sint32 args [64]; // Array of arguments. Count is stored in L2.

    git_uint32 ioRock = 0;

    git_uint32 stringTable = memRead32(28);    
    git_uint32 startPos    = memRead32(24);
    git_uint32 stackSize   = memRead32(20);

    git_uint32 protectPos = 0;
    git_uint32 protectSize = 0;
    
    git_uint32 maybe_unused glulxPC = 0;
    git_uint32 maybe_unused glulxOpcode = 0;

    acceleration_func accelfunc;

    // Initialise the code cache.

#ifdef USE_DIRECT_THREADING
    static Opcode opcodeTable [] = {
#define LABEL(label) &&do_ ## label,
#include "labels.inc"
    NULL};
    gOpcodeTable = opcodeTable;
#endif    

    initCompiler (cacheSize);

    // Initialise the random number generator.
    srand (time(NULL));

    // Set up the stack.

    base = malloc (stackSize);
    if (base == NULL)
        fatalError ("Couldn't allocate stack");
        
    top = base + (stackSize / 4);
    frame = locals = values = sp = base;

    // Call the first function.

    L1 = startPos; // Initial PC.
    L2 = 0; // No arguments.
    goto do_enter_function_L1;

#ifdef USE_DIRECT_THREADING
#define NEXT do { goto **(pc++); } while(0)
#else
#define NEXT goto next
//#define NEXT do { CHECK_USED(0); CHECK_FREE(0); goto next; } while (0)
next:
    switch (*pc++)
    {
#define LABEL(foo) case label_ ## foo: goto do_ ## foo;
#include "labels.inc"
    default: fatalError("exec: bad opcode");
    }
#endif

do_debug_step:
    // This opcode lets us keep track of how the compiled
    // code relates to the original glulx code.
    glulxPC = READ_PC;     // Glulx program counter.
    glulxOpcode = READ_PC; // Glulx opcode number.
//    fprintf (stdout, "\nPC: 0x%08x\nOpcode: 0x%04x\n", glulxPC, glulxOpcode);
//    fprintf (stdout, "Stack:");
//    for (L7 = 0 ; L7 < (sp - base) ; ++L7)
//        fprintf (stdout," 0x%x", base[L7]);
//    fprintf (stdout, "\n");
    NEXT;

#define LOAD_INSTRUCTIONS(reg)                                  \
    do_ ## reg ## _const:   reg = READ_PC; NEXT;                \
    do_ ## reg ## _stack:   CHECK_USED(1); reg = POP; NEXT;     \
    do_ ## reg ## _addr:    reg = memRead32 (READ_PC); NEXT;    \
    do_ ## reg ## _local:   reg = LOCAL (READ_PC); NEXT

    LOAD_INSTRUCTIONS(L1);
    LOAD_INSTRUCTIONS(L2);
    LOAD_INSTRUCTIONS(L3);
    LOAD_INSTRUCTIONS(L4);
    LOAD_INSTRUCTIONS(L5);
    LOAD_INSTRUCTIONS(L6);
    LOAD_INSTRUCTIONS(L7);

#define STORE_INSTRUCTIONS(reg)                                 \
    do_ ## reg ## _stack:   CHECK_FREE(1); PUSH(reg); NEXT;     \
    do_ ## reg ## _addr:    memWrite32 (READ_PC, reg); NEXT;    \
    do_ ## reg ## _local:   LOCAL (READ_PC) = reg; NEXT

    STORE_INSTRUCTIONS(S1);
    STORE_INSTRUCTIONS(S2);

#define DOUBLE_LOAD(mode2) \
    do_L1_const_L2_ ## mode2: L1 = READ_PC;             goto do_L2_ ## mode2; \
    do_L1_stack_L2_ ## mode2: CHECK_USED(1); L1 = POP;  goto do_L2_ ## mode2; \
    do_L1_local_L2_ ## mode2: L1 = LOCAL (READ_PC);     goto do_L2_ ## mode2; \
    do_L1_addr_L2_ ## mode2:  L1 = memRead32 (READ_PC); goto do_L2_ ## mode2

    DOUBLE_LOAD(const);
    DOUBLE_LOAD(stack);
    DOUBLE_LOAD(local);
    DOUBLE_LOAD(addr);

#undef LOAD_INSTRUCTIONS
#undef STORE_INSTRUCTIONS
#undef DOUBLE_LOAD

do_L1_addr16: L1 = memRead16 (READ_PC); NEXT; 
do_L1_addr8:  L1 = memRead8 (READ_PC); NEXT;
do_S1_addr16: memWrite16 (READ_PC, S1); NEXT;
do_S1_addr8:  memWrite8 (READ_PC, S1); NEXT;

#define UL7 ((git_uint32)L7)

do_recompile:
    pc = compile (READ_PC);
	NEXT;
	
do_jump_abs_L7:
    pc = getCode (UL7);
    NEXT;

do_enter_function_L1: // Arg count is in L2.

    // Check for an accelerated function
    accelfunc = accel_get_func(L1);
    if (accelfunc) {
        S1 = accelfunc(L2, (glui32 *) args);
        goto do_pop_call_stub;
    }

    frame = sp;
    // Read the function type.
    L7 = memRead8(L1++);
    // Parse the local variables descriptor.
    L6 = L5 = L4 = 0;
    do
    {
        L6 = memRead8(L1++); // LocalType
        L5 = memRead8(L1++); // LocalCount
        if (L6 != 4 && L6 != 0) // We only support 4-byte locals.
        {
            if (L6 == 1 || L6 == 2)
                fatalError("Short local variables are not supported, use Glulxe");
            else
                fatalError("Local variable wasn't 4 bytes wide");
        }
        L4 += L5; // Cumulative local count.
    }
    while (L5 != 0);

    // Write out the stack frame.
    // Recall that the number of locals is stored in L4.

    CHECK_FREE(3 + L4);
    
    PUSH (L4*4 + 12); // FrameLen
    PUSH (12);        // LocalsPos
    if (L4 == 0)
        L6 = 0;
    else
        L6 = (4 << 24) | (L4 << 16);
    PUSH (L6);         // format of locals

    // This is where the local variables start, so:
    locals = sp;
    
    // Read the arguments, based on the function type.
    switch (L7)
    {
        case 0xC0: // arguments should be placed on the stack.
            // argc is in L2; we'll randomly use L5 as scratch.
            CHECK_FREE(L5 + 1);
            // Initialise the local variables.
            for ( ; L4 > 0 ; --L4)
                PUSH (0);
            // This is where the temporary values start, so:
            values = sp;
            // Push the args onto the stack.
            for (L5 = 0 ; L5 < L2 ; ++L5)
                PUSH (args [L5]);
            // Push the arg count.
            PUSH (L2);
            break;
    
        case 0xC1: // arguments should be written into locals.
            // argc is in L2, num locals is in L4.
            // Stuff as many locals as possible with arguments.
            for (L5 = 1 ; L5 <= L2 && L4 > 0 ; ++L5, --L4)
                PUSH (args [L2 - L5]);
            // Initialise any remaining locals.
            for ( ; L4 > 0 ; --L4)
                PUSH (0);
            // This is where the temporary values start, so:
            values = sp;
            break;
    
        default:
            // This isn't a function!
            fatalError("Not a function");
            break;
    }
        
    // Start executing the function.
    L7 = L1;
    goto do_jump_abs_L7;

    do_nop:     NEXT;

#define PEEPHOLE_STORE(tag, code)                     \
    do_ ## tag ## _discard:  code; NEXT;              \
    do_ ## tag ## _S1_stack: code; goto do_S1_stack;  \
    do_ ## tag ## _S1_local: code; goto do_S1_local;  \
    do_ ## tag ## _S1_addr:  code; goto do_S1_addr

    PEEPHOLE_STORE(add,     S1 = L1 + L2);
    PEEPHOLE_STORE(sub,     S1 = L1 - L2);
    PEEPHOLE_STORE(mul,     S1 = L1 * L2);
    PEEPHOLE_STORE(div,     if (L2 == 0) fatalError ("Divide by zero"); S1 = L1 / L2);
    PEEPHOLE_STORE(mod,     if (L2 == 0) fatalError ("Divide by zero"); S1 = L1 % L2);

    PEEPHOLE_STORE(neg,     S1 = -L1);
    PEEPHOLE_STORE(bitnot,  S1 = ~L1);

    PEEPHOLE_STORE(bitand,  S1 = L1 & L2);
    PEEPHOLE_STORE(bitor,   S1 = L1 | L2);
    PEEPHOLE_STORE(bitxor,  S1 = L1 ^ L2);

    PEEPHOLE_STORE(shiftl,  if (L2 > 31 || L2 < 0) S1 = 0; else S1 = L1 << ((git_uint32) L2));
    PEEPHOLE_STORE(sshiftr, if (L2 > 31 || L2 < 0) L2 = 31; S1 = ((git_sint32) L1) >> ((git_uint32) L2));
    PEEPHOLE_STORE(ushiftr, if (L2 > 31 || L2 < 0) S1 = 0; else S1 = ((git_uint32) L1) >> ((git_uint32) L2));

    PEEPHOLE_STORE(aload,   S1 = memRead32 (L1 + (L2<<2)));
    PEEPHOLE_STORE(aloads,  S1 = memRead16 (L1 + (L2<<1)));
    PEEPHOLE_STORE(aloadb,  S1 = memRead8  (L1 + L2));
    PEEPHOLE_STORE(aloadbit,S1 = (memRead8 (L1 + (L2>>3)) >> (L2 & 7)) & 1);

    PEEPHOLE_STORE(copys,   S1 = L1 & 0xFFFF);
    PEEPHOLE_STORE(copyb,   S1 = L1 & 0x00FF);
    PEEPHOLE_STORE(sexs,    S1 = (git_sint32)((signed short)(L1 & 0xFFFF)));
    PEEPHOLE_STORE(sexb,    S1 = (git_sint32)((signed char)(L1 & 0x00FF)));

    PEEPHOLE_STORE(fadd,    F1 = DECODE_FLOAT(L1) + DECODE_FLOAT(L2); S1 = ENCODE_FLOAT(F1));
    PEEPHOLE_STORE(fsub,    F1 = DECODE_FLOAT(L1) - DECODE_FLOAT(L2); S1 = ENCODE_FLOAT(F1));
    PEEPHOLE_STORE(fmul,    F1 = DECODE_FLOAT(L1) * DECODE_FLOAT(L2); S1 = ENCODE_FLOAT(F1));
    PEEPHOLE_STORE(fdiv,    F1 = DECODE_FLOAT(L1) / DECODE_FLOAT(L2); S1 = ENCODE_FLOAT(F1));

#define PEEPHOLE_LOAD(tag,reg) \
    do_ ## tag ## _ ## reg ## _const: reg = READ_PC; goto do_ ## tag; \
    do_ ## tag ## _ ## reg ## _stack: CHECK_USED(1); reg = POP; goto do_ ## tag; \
    do_ ## tag ## _ ## reg ## _local: reg = LOCAL(READ_PC); goto do_ ## tag; \
    do_ ## tag ## _ ## reg ## _addr:  reg = memRead32(READ_PC); goto do_ ## tag

    PEEPHOLE_LOAD (return, L1);
    PEEPHOLE_LOAD (astore, L3);
    PEEPHOLE_LOAD (astores, L3);
    PEEPHOLE_LOAD (astoreb, L3);
    PEEPHOLE_LOAD (astorebit, L3);

#undef PEEPHOLE_STORE

    do_astore:    memWrite32 (L1 + (L2<<2), L3); NEXT;
    do_astores:   memWrite16 (L1 + (L2<<1), L3); NEXT;
    do_astoreb:   memWrite8  (L1 + L2, L3); NEXT;
    do_astorebit:
        L4 = memRead8(L1 + (L2>>3));
        if (L3 == 0)
            L4 &= ~(1 << (L2 & 7));
        else
            L4 |= (1 << (L2 & 7));
        memWrite8(L1 + (L2>>3), L4);
        NEXT;

#define DO_JUMP(tag, reg, cond) \
    do_ ## tag ## _var:     L7 = READ_PC; if (cond) goto do_goto_ ## reg ## _from_L7; NEXT; \
    do_ ## tag ## _const:   L7 = READ_PC; if (cond) goto do_jump_abs_L7; NEXT;              \
    do_ ## tag ## _by:      L7 = READ_PC; if (cond) pc += L7; NEXT;                         \
    do_ ## tag ## _return0: if (cond) { L1 = 0; goto do_return; } NEXT;                     \
    do_ ## tag ## _return1: if (cond) { L1 = 1; goto do_return; } NEXT
    
    DO_JUMP(jump,   L1, 1 == 1);
    DO_JUMP(jz,     L2, L1 == 0);
    DO_JUMP(jnz,    L2, L1 != 0);
    DO_JUMP(jeq,    L3, L1 == L2);
    DO_JUMP(jne,    L3, L1 != L2);
    DO_JUMP(jlt,    L3, L1 < L2);
    DO_JUMP(jge,    L3, L1 >= L2);
    DO_JUMP(jgt,    L3, L1 > L2);
    DO_JUMP(jle,    L3, L1 <= L2);
    DO_JUMP(jltu,   L3, ((git_uint32)L1 < (git_uint32)L2));
    DO_JUMP(jgeu,   L3, ((git_uint32)L1 >= (git_uint32)L2));
    DO_JUMP(jgtu,   L3, ((git_uint32)L1 > (git_uint32)L2));
    DO_JUMP(jleu,   L3, ((git_uint32)L1 <= (git_uint32)L2));
    DO_JUMP(jisnan, L2, (((L1 & 0x7F800000) == 0x7F800000) && ((L1 & 0x007FFFFF) != 0)));
    DO_JUMP(jisinf, L2, ((L1 == 0x7F800000) || (L1 == 0xFF800000)));
    DO_JUMP(jflt,   L3, DECODE_FLOAT(L1) < DECODE_FLOAT(L2));
    DO_JUMP(jfge,   L3, DECODE_FLOAT(L1) >= DECODE_FLOAT(L2));
    DO_JUMP(jfgt,   L3, DECODE_FLOAT(L1) > DECODE_FLOAT(L2));
    DO_JUMP(jfle,   L3, DECODE_FLOAT(L1) <= DECODE_FLOAT(L2));
    DO_JUMP(jfeq,   L4, floatCompare(L1, L2, L3) != 0);
    DO_JUMP(jfne,   L4, floatCompare(L1, L2, L3) == 0);

#undef DO_JUMP

    do_jumpabs: L7 = L1; goto do_jump_abs_L7; NEXT;

    do_goto_L4_from_L7: L1 = L4; goto do_goto_L1_from_L7;
    do_goto_L3_from_L7: L1 = L3; goto do_goto_L1_from_L7;
    do_goto_L2_from_L7: L1 = L2; goto do_goto_L1_from_L7;
    do_goto_L1_from_L7:
        if (L1 == 0 || L1 == 1) goto do_return;
        L7 = L7 + L1 - 2; goto do_jump_abs_L7;

    do_args_stack:
        // The first argument is topmost in the stack; the count is in L2.
        CHECK_USED(L2);
        // We want to store the arguments in 'args' in the same order.
        for (L3 = L2 - 1 ; L3 >= 0 ; --L3)
            args [L3] = POP;
        NEXT;

    // Specialised versions of above:
    do_args_stack_call_stub_discard:
        CHECK_USED(L2);
        for (L3 = L2 - 1 ; L3 >= 0 ; --L3)
            args [L3] = POP;
        goto do_call_stub_discard;
        
    do_args_stack_call_stub_addr:
        CHECK_USED(L2);
        for (L3 = L2 - 1 ; L3 >= 0 ; --L3)
            args [L3] = POP;
        goto do_call_stub_addr;

    do_args_stack_call_stub_local:
        CHECK_USED(L2);
        for (L3 = L2 - 1 ; L3 >= 0 ; --L3)
            args [L3] = POP;
        goto do_call_stub_local;

    do_args_stack_call_stub_stack:
        CHECK_USED(L2);
        for (L3 = L2 - 1 ; L3 >= 0 ; --L3)
            args [L3] = POP;
        goto do_call_stub_stack;

    do_args_3:
        args [0] = L4;
        args [1] = L3;
        args [2] = L2;
        L2 = 3;
        NEXT;

    do_args_2:
        args [0] = L3;
        args [1] = L2;
        L2 = 2;
        NEXT;

    do_args_1:
        args [0] = L2;
        L2 = 1;
        NEXT;

    do_args_0:
        L2 = 0;
        NEXT;

    do_undo_stub_discard:
        CHECK_FREE(4);
        PUSH (0); // DestType
        PUSH (0); // DestAddr
        goto finish_undo_stub;

    do_undo_stub_addr:
        CHECK_FREE(4);
        PUSH (1);       // DestType
        PUSH (READ_PC); // DestAddr
        goto finish_undo_stub;

    do_undo_stub_local:
        CHECK_FREE(4);
        PUSH (2);       // DestType
        PUSH (READ_PC); // DestAddr
        goto finish_undo_stub;

    do_undo_stub_stack:
        CHECK_FREE(4);
        PUSH (3); // DestType
        PUSH (0); // DestAddr
        goto finish_undo_stub;

finish_undo_stub:
        PUSH (READ_PC);             // PC
        PUSH ((frame - base) * 4);  // FramePtr
        saveUndo (base, sp);
        S1 = 0;
        goto do_pop_call_stub;

    do_restoreundo:
        if (restoreUndo (base, protectPos, protectSize) == 0)
        {
            sp = gStackPointer;
            S1 = -1;
            goto do_pop_call_stub;
        }
        S1 = 1;
        NEXT;

    do_save_stub_discard:
        CHECK_FREE(4);
        PUSH (0); // DestType
        PUSH (0); // DestAddr
        goto finish_save_stub;

    do_save_stub_addr:
        CHECK_FREE(4);
        PUSH (1);       // DestType
        PUSH (READ_PC); // DestAddr
        goto finish_save_stub;

    do_save_stub_local:
        CHECK_FREE(4);
        PUSH (2);       // DestType
        PUSH (READ_PC); // DestAddr
        goto finish_save_stub;

    do_save_stub_stack:
        CHECK_FREE(4);
        PUSH (3); // DestType
        PUSH (0); // DestAddr
        goto finish_save_stub;

finish_save_stub:
        PUSH (READ_PC);                        // PC
        PUSH ((frame - base) * 4);  // FramePtr
        if (ioMode == IO_GLK)
            S1 = saveToFile (base, sp, L1);
        else
            S1 = 1;
        goto do_pop_call_stub;

    do_restore:
        if (ioMode == IO_GLK
         && restoreFromFile (base, L1, protectPos, protectSize) == 0)
        {
            sp = gStackPointer;
            S1 = -1;
            goto do_pop_call_stub;
        }
        S1 = 1;
        NEXT;

    do_catch_stub_discard:
        CHECK_FREE(4);
        L7 = 0;
        PUSH (0); // DestType
        goto finish_catch_stub_addr_L7;

    do_catch_stub_addr:
        CHECK_FREE(4);
        L7 = READ_PC;
        memWrite32(L7, (sp-base+4)*4);
        PUSH (1);       // DestType
        goto finish_catch_stub_addr_L7;

    do_catch_stub_local:
        CHECK_FREE(4);
        L7 = READ_PC;
        LOCAL(L7 / 4) = (sp-base+4)*4;
        PUSH (2);       // DestType
        goto finish_catch_stub_addr_L7;

    do_catch_stub_stack:
        CHECK_FREE(5);
        PUSH (3);                  // DestType
        PUSH (0);                  // DestAddr
        PUSH (READ_PC);            // PC
        PUSH ((frame - base) * 4); // FramePtr
        L7 = (sp - base)*4;        // Catch token.
	    PUSH (L7);
        NEXT;

finish_catch_stub_addr_L7:
        PUSH (L7);                 // DestAddr
        PUSH (READ_PC);            // PC
        PUSH ((frame - base) * 4); // FramePtr
        NEXT;

    do_throw:
        if (L2 < 16 || L2 > ((sp-base)*4))
            fatalError ("Invalid catch token in throw");
        sp = base + L2 / 4;
        goto do_pop_call_stub;
    
do_call_stub_discard:
        CHECK_FREE(4);
        PUSH (0); // DestType
        PUSH (0); // DestAddr
        goto finish_call_stub;

    do_call_stub_addr:
        CHECK_FREE(4);
        PUSH (1);       // DestType
        PUSH (READ_PC); // DestAddr
        goto finish_call_stub;

    do_call_stub_local:
        CHECK_FREE(4);
        PUSH (2);       // DestType
        PUSH (READ_PC); // DestAddr
        goto finish_call_stub;

    do_call_stub_stack:
        CHECK_FREE(4);
        PUSH (3); // DestType
        PUSH (0); // DestAddr
        goto finish_call_stub;

finish_call_stub:
        PUSH (READ_PC);             // PC
        PUSH ((frame - base) * 4);  // FramePtr
        goto do_enter_function_L1;
    
do_tailcall:
        // Zap the current stack frame, down to its call stub.
        sp = frame;
        // Call the function!
        goto do_enter_function_L1;
    
    do_return:
        sp = frame;
        // ...
        // fall through
        // ...
    do_pop_call_stub:// L1 holds the return value.
        if (sp - base < 4)
        {
            if (sp == base)
                // We just exited the top-level function.
                goto finished;
            else
                // Something nasty happened.
                goto stack_underflow;
        }
        L2 = POP;    // FramePtr
        L7 = POP;    // PC
        L6 = POP;    // DestAddr
        switch (POP) // DestType
        {
            case 0: // Do not store.
                frame = base + L2 / 4;
                locals = frame + frame[1]/4;
                values = frame + frame[0]/4;
                break;

            case 1: // Store in main memory.
                frame = base + L2 / 4;
                locals = frame + frame[1]/4;
                values = frame + frame[0]/4;
                memWrite32 (L6, L1);
                break;

            case 2: // Store in local variable.
                frame = base + L2 / 4;
                locals = frame + frame[1]/4;
                values = frame + frame[0]/4;
                LOCAL(L6/4) = L1;
                break;

            case 3: // Push on stack.
                frame = base + L2 / 4;
                locals = frame + frame[1]/4;
                values = frame + frame[0]/4;
                PUSH (L1);
                break;
            
            case 10: // Resume printing a compressed (E1) string.
                frame = base + L2 / 4;
                locals = frame + frame[1]/4;
                values = frame + frame[0]/4;
                goto resume_compressed_string_L7_bit_L6;
                
            case 11: // Resume executing function code after a string completes.
                // Don't restore the frame pointer.
                break;
                
            case 12: // Resume printing a signed decimal integer.
                frame = base + L2 / 4;
                locals = frame + frame[1]/4;
                values = frame + frame[0]/4;
                goto resume_number_L7_digit_L6;
                
            case 13: // Resume printing a C-style (E0) string.
                frame = base + L2 / 4;
                locals = frame + frame[1]/4;
                values = frame + frame[0]/4;
                goto resume_c_string_L7;
                
            case 14: // Resume printing a Unicode (E2) string.
                frame = base + L2 / 4;
                locals = frame + frame[1]/4;
                values = frame + frame[0]/4;
                goto resume_uni_string_L7;

            default:
                fatalError("Bad call stub");
        }
        // Restore the PC.
        goto do_jump_abs_L7;

    do_stkcount:
        S1 = sp - values; NEXT;
    
    do_stkpeek:
        if (L1 < 0 || L1 > (sp - values))
            fatalError("Out of bounds in stkpeek");
        S1 = sp[-1 - L1]; NEXT;

    do_stkswap:
        CHECK_USED(2);
        L1 = POP; L2 = POP; PUSH(L1); PUSH(L2); NEXT;

    do_stkcopy:
        CHECK_USED(L1);
        for (L2 = L1 ; L2 > 0 ; --L2)
        {
            L3 = sp[-L1];
            PUSH (L3);
        }
        NEXT;

    resume_number_L7_digit_L6:
    {
        char buffer [16];
        git_uint32 absn;
        
        // If the IO mode is 'null', do nothing.
        if (ioMode == IO_NULL)
            goto do_pop_call_stub;

        // Write the number into the buffer.
        absn = (L7 < 0) ? -L7 : L7; // Absolute value of number.
        L2 = 0;                     // Current buffer position.
        do
        {
            buffer [L2++] = '0' + (absn % 10);
            absn /= 10;
        }
        while (absn > 0);

        if (L7 < 0)
            buffer [L2++] = '-';
        
        if (L6 >= L2)
            goto do_pop_call_stub; // We printed the whole number already.

        // If we're in filter mode, push a call stub
        // and filter the next character.
        if (ioMode == IO_FILTER)
        {
            // Store the next character in the args array.
            args[0] = buffer [L2 - L6 - 1];
            ++L6;
            
            // Push a call stub to print the next character.
            CHECK_FREE(4);
            PUSH(12); // DestType
            PUSH(L6); // DestAddr (next digit)
            PUSH(L7); // PC       (number to print)
            PUSH ((frame - base) * 4); // FramePtr

            // Call the filter function.
            L1 = ioRock;
            L2 = 1;
            goto do_enter_function_L1;
        }
        else
        {
            // We're in Glk mode. Just print all the characters.
            for ( ; L6 < L2 ; ++L6)
                glk_put_char (buffer [L2 - L6 - 1]);
        }
    }
        goto do_pop_call_stub;

    resume_c_string_L7:
        // If the IO mode is 'null', or if we've reached the
        // end of the string, do nothing.
        L2 = memRead8(L7++);
        if (L2 == 0 || ioMode == IO_NULL)
            goto do_pop_call_stub;
        // Otherwise we're going to have to print something,
        // If the IO mode is 'filter', filter the next char.
        if (ioMode == IO_FILTER)
        {
            // Store this character in the args array.
            args [0] = L2;
            // Push a call stub.
            CHECK_FREE(4);
            PUSH(13); // DestType (resume C string)
            PUSH(L6); // DestAddr (ignored)
            PUSH(L7); // PC       (next char to print)
            PUSH ((frame - base) * 4); // FramePtr
            // Call the filter function.
            L1 = ioRock;
            L2 = 1;
            goto do_enter_function_L1;
        }
        // We're in Glk mode. Just print all the characters.
        while (L2 != 0)
        {
            glk_put_char ((unsigned char) L2);
            L2 = memRead8(L7++);
        }
        goto do_pop_call_stub;

    resume_uni_string_L7:
        // If the IO mode is 'null', or if we've reached the
        // end of the string, do nothing.
        L2 = memRead32(L7);
        L7 += 4;
        if (L2 == 0 || ioMode == IO_NULL)
            goto do_pop_call_stub;
        // Otherwise we're going to have to print something,
        // If the IO mode is 'filter', filter the next char.
        if (ioMode == IO_FILTER)
        {
            // Store this character in the args array.
            args [0] = L2;
            // Push a call stub.
            CHECK_FREE(4);
            PUSH(14); // DestType (resume Unicode string)
            PUSH(L6); // DestAddr (ignored)
            PUSH(L7); // PC       (next char to print)
            PUSH ((frame - base) * 4); // FramePtr
            // Call the filter function.
            L1 = ioRock;
            L2 = 1;
            goto do_enter_function_L1;
        }
        // We're in Glk mode. Just print all the characters.
        while (L2 != 0)
        {
#ifdef GLK_MODULE_UNICODE
            glk_put_char_uni ((glui32) L2);
#else
            unsigned char c = (L2 > 0 && L2 < 256) ? L2 : '?';
            glk_put_char (c);
#endif // GLK_MODULE_UNICODE
            L2 = memRead32(L7);
            L7 += 4;
        }
        goto do_pop_call_stub;

    resume_compressed_string_L7_bit_L6:
        // Load the first string table node into L1.
        // Its address is stored at stringTable + 8.
        L1 = memRead32 (stringTable + 8);
        // Load the node's type byte.
        L2 = memRead8 (L1++);
        // Is the root node a branch?
        if (L2 == 0)
        {
            // We'll keep a reservoir of input bits in L5.
            L5 = memRead8(L7);
            // Keep following branch nodes until we hit a leaf node.
            while (L2 == 0)
            {
                // Read the next bit.
                L4 = (L5 >> L6) & 1;
                // If we're finished reading this byte,
                // move on to the next one.
                if (++L6 > 7)
                {
                    L6 -= 8;
                    L5 = memRead8(++L7);
                }
                // Follow the branch.
                L1 = memRead32(L1 + 4 * L4);
                L2 = memRead8 (L1++);
            }
        }
        else if (L2 == 2 || L2 == 3)
        {
            // The root node prints a single character or a string.
            // This will produce infinite output in the Null or Glk
            // I/O modes, so we'll catch that here.

            if (ioMode != IO_FILTER)
                fatalError ("String table prints infinite strings!");

            // In Filter mode, the output will be sent to the current
            // filter function, which can change the string table
            // before returning, so we'll continue and see what happens.
        }
        // We're at a leaf node.
        switch (L2)
        {
            case 1: // Terminator.
                goto do_pop_call_stub;

            case 2: // Single char.
                if (ioMode == IO_NULL)
                    { /* Do nothing */ }
                else if (ioMode == IO_GLK)
                    glk_put_char ((unsigned char) memRead8(L1));
                else
                {
                    // Store this character in the args array.
                    args [0] = memRead8(L1);
                    // Push a call stub.
                    CHECK_FREE(4);
                    PUSH(10); // DestType
                    PUSH(L6); // DestAddr (bit number in string)
                    PUSH(L7); // PC       (byte address in string)
                    PUSH ((frame - base) * 4); // FramePtr
                    // Call the filter function.
                    L1 = ioRock;
                    L2 = 1;
                    goto do_enter_function_L1;
                }
                break;

            case 3: // C string.
                // Push a 'resume compressed string' call stub.
                CHECK_FREE(4);
                PUSH (10); // DestType
                PUSH (L6); // DestAddr (bit number in string)
                PUSH (L7); // PC       (byte address in string)
                PUSH ((frame - base) * 4); // FramePtr
                // Print the C string.
                L7 = L1;
                goto resume_c_string_L7;
                
            case 4: // Unicode char
                if (ioMode == IO_NULL)
                    { /* Do nothing */ }
                else if (ioMode == IO_GLK)
                {
#ifdef GLK_MODULE_UNICODE
                    glk_put_char_uni (memRead32(L1));
#else
                    git_uint32 c = memRead32(L1);
                    if (c > 255) c = '?';
                    glk_put_char ((unsigned char) c);
#endif // GLK_MODULE_UNICODE
                }
                else
                {
                    // Store this character in the args array.
                    args [0] = memRead32(L1);
                    // Push a call stub.
                    CHECK_FREE(4);
                    PUSH(10); // DestType
                    PUSH(L6); // DestAddr (bit number in string)
                    PUSH(L7); // PC       (byte address in string)
                    PUSH ((frame - base) * 4); // FramePtr
                    // Call the filter function.
                    L1 = ioRock;
                    L2 = 1;
                    goto do_enter_function_L1;
                }
                break;

            case 5: // Unicode string.
                // Push a 'resume compressed string' call stub.
                CHECK_FREE(4);
                PUSH (10); // DestType
                PUSH (L6); // DestAddr (bit number in string)
                PUSH (L7); // PC       (byte address in string)
                PUSH ((frame - base) * 4); // FramePtr
                // Print the Unicode string.
                L7 = L1;
                goto resume_uni_string_L7;

            case 8:  // Indirect reference.
                L3 = memRead32(L1);
                L2 = 0; goto indirect_L3_args_L2;

            case 9:  // Double-indirect reference.
                L3 = memRead32(L1); L3 = memRead32(L3);
                L2 = 0; goto indirect_L3_args_L2;

            case 10: // Indirect reference with args.
                L3 = memRead32(L1);
                L2 = memRead32(L1 + 4); goto indirect_L3_args_L2;

            case 11: // Double-indirect reference with args.
                L3 = memRead32(L1); L3 = memRead32(L3);
                L2 = memRead32(L1 + 4); goto indirect_L3_args_L2;

            indirect_L3_args_L2:
                // Push a 'resume compressed string' call stub.
                CHECK_FREE(4);
                PUSH (10); // DestType
                PUSH (L6); // DestAddr (bit number in string)
                PUSH (L7); // PC       (byte address in string)
                PUSH ((frame - base) * 4); // FramePtr
                // Check the type of the embedded object.
                switch (memRead8(L3))
                {
                    case 0xE0: // C string.
                        L7 = L3 + 1;
                        goto resume_c_string_L7;

                    case 0xE1: // Compressed string.
                        L7 = L3 + 1;
                        L6 = 0;
                        goto resume_compressed_string_L7_bit_L6;
                        
                    case 0xE2: // Unicode string.
                        L7 = L3 + 4; // Skip extra three padding bytes.
                        goto resume_uni_string_L7;

                    case 0xC0: case 0xC1: // Function.
                        // Retrieve arguments.
                        for (L1 += 8, L4 = L2; L4 > 0 ; --L4, L1+=4)
                            args[L4-1] = memRead32(L1);
                        // Enter function.
                        L1 = L3;
                        goto do_enter_function_L1;
                    
                    default: fatalError ("Embedded object in string has unknown type");
                }
                break;

            default: fatalError ("Unknown string table node type");
        }
        // Start back at the root node again.
        goto resume_compressed_string_L7_bit_L6;

    do_streamstr:
        // Push a 'resume function' call stub.
        CHECK_FREE(4);
        PUSH (11);                            // DestType
        PUSH (0);                             // Addr
        PUSH (READ_PC);                       // PC
        PUSH ((frame - base) * 4); // FramePtr

        // Load the string's type byte.
        L2 = memRead8(L1++);
        if (L2 == 0xE0)
        {
            // Uncompressed string.
            L7 = L1;
            goto resume_c_string_L7;
        }
        else if (L2 == 0xE1)
        {
            // Compressed string.
            L7 = L1;
            L6 = 0;
            goto resume_compressed_string_L7_bit_L6;
        }
        else if (L2 == 0xE2)
        {
            // Uncompressed Unicode string.
            L7 = L1 + 3; // Skip three padding bytes.
            goto resume_uni_string_L7;
        }
        else
        {
            fatalError ("Value used in streamstr was not a string");
            goto finished;
        }

    do_streamchar:
        L7 = READ_PC;
        if (ioMode == IO_NULL)
            { /* Do nothing */ }
        else if (ioMode == IO_GLK)
        {
            unsigned char c = (L1 & 0xff);
            glk_put_char (c);
        }
        else
        {
            // Store this character in the args array.
            args [0] = (L1 & 0xff);
            // Push a 'resume function' call stub.
            CHECK_FREE(4);
            PUSH (0);                  // DestType
            PUSH (0);                  // Addr
            PUSH (L7);                 // PC
            PUSH ((frame - base) * 4); // FramePtr
            // Call the filter function.
            L1 = ioRock;
            L2 = 1;
            goto do_enter_function_L1;
        }
        NEXT;

    do_streamunichar:
        L7 = READ_PC;
        if (ioMode == IO_NULL)
            { /* Do nothing */ }
        else if (ioMode == IO_GLK)
        {
#ifdef GLK_MODULE_UNICODE
            glk_put_char_uni ((glui32) L1);
#else
            unsigned char c = (L1 > 0 && L1 < 256) ? L1 : '?';
            glk_put_char (c);
#endif // GLK_MODULE_UNICODE
        }
        else
        {
            // Store this character in the args array.
            args [0] = L1;
            // Push a 'resume function' call stub.
            CHECK_FREE(4);
            PUSH (0);                  // DestType
            PUSH (0);                  // Addr
            PUSH (L7);                 // PC
            PUSH ((frame - base) * 4); // FramePtr
            // Call the filter function.
            L1 = ioRock;
            L2 = 1;
            goto do_enter_function_L1;
        }
        NEXT;

    do_streamnum:
        // Push a 'resume function' call stub.
        CHECK_FREE(4);
        PUSH (11);                            // DestType
        PUSH (0);                             // Addr
        PUSH (READ_PC);                       // PC
        PUSH ((frame - base) * 4); // FramePtr

        // Print the number.
        L7 = L1;
        L6 = 0;
        goto resume_number_L7_digit_L6;

    // Stub opcodes:

    do_getmemsize:
        S1 = gEndMem;
        NEXT;

    do_getiosys:
        S1 = ioMode;
        S2 = ioRock;
        NEXT;

    do_setiosys:    
        switch (L1)
        {
            case IO_NULL:
            case IO_FILTER:
            case IO_GLK:
                ioMode = (enum IOMode) L1;
                ioRock = L2;
                break;
            
            default:
                fatalError ("Illegal I/O mode");
                break;
        }
        NEXT;

    do_quit:
        goto finished;
        
    do_restart:
        // Reset game memory to its initial state.
        resetMemory(protectPos, protectSize);

        // Reset all the stack pointers.
        frame = locals = values = sp = base;

        // Call the first function.
        L1 = startPos; // Initial PC.
        L2 = 0; // No arguments.
        goto do_enter_function_L1;        

    do_verify:
        S1 = verifyMemory();
        NEXT;

    do_random:
        if (L1 > 0)
            S1 = rand() % L1;
        else if (L1 < 0)
            S1 = -(rand() % -L1);
        else
        {
            // The parameter is zero, so we should generate a
            // random number in "the full 32-bit range". The rand()
            // function might not cover the entire range, so we'll
            // generate the number with several calls.
#if (RAND_MAX < 0xffff)
            S1 = rand() ^ (rand() << 12) ^ (rand() << 24);
#else
            S1 = (rand() & 0xffff) | (rand() << 16);
#endif
        }
        NEXT;

    do_setrandom:
        srand (L1 ? L1 : time(NULL));
        NEXT;

    do_glk:
        // The first argument is topmost in the stack; count is in L2.
        CHECK_USED(L2);
        // We want to store the arguments in 'args' in the same order.
        for (L3 = 0 ; L3 < L2 ; ++L3)
            args [L3] = POP;
        gStackPointer = sp;
        S1 = git_perform_glk (L1, L2, (glui32*) args);
        sp = gStackPointer;
        NEXT;

    do_binarysearch:
        S1 = git_binary_search (L1, L2, L3, L4, L5, L6, L7);
        NEXT;

    do_linearsearch:
        S1 = git_linear_search (L1, L2, L3, L4, L5, L6, L7);
        NEXT;

    do_linkedsearch:
        S1 = git_linked_search (L1, L2, L3, L4, L5, L6);
        NEXT;

    do_gestalt:
        S1 = gestalt (L1, L2);
        NEXT;

    do_getstringtbl: S1 = stringTable; NEXT;
    do_setstringtbl: stringTable = L1; NEXT;
        
    do_debugtrap:
        // TODO: do something useful here.
        NEXT;

    do_stkroll:
        // We need to rotate the top L1 elements by L2 places.
        if (L1 < 0)
            fatalError ("Negative number of elements to rotate in stkroll");
        if (L1 > (sp - values))
            fatalError ("Tried to rotate too many elements in stkroll");
        if (L1 == 0)
            NEXT;
        // Now, let's normalise L2 into the range [0..L1).
        if (L2 >= 0)
            L2 = L2 % L1;
        else
            L2 = L1 - (-L2 % L1);
        // Avoid trivial cases.
        if (L2 == 0 || L2 == L1)
            NEXT;
        L2 = L1 - L2;
        // The problem is reduced to swapping elements [0..L2) with
        // elements [L2..L1). Let's call these two sequences A and B,
        // so we need to transform AB into BA. We do this sneakily
        // with reversals, as follows: AB -> A'B -> A'B' -> (A'B')',
        // where X' is the reverse of the sequence X.
#define SWAP(x,y) \
        do { L4 = sp[(x)-L1];sp[(x)-L1]=sp[(y)-L1];sp[(y)-L1]=L4; } while (0)

        // Reverse [0..L2).
        for (L3 = 0 ; L3 < L2/2 ; ++L3)
            SWAP (L3, L2-1-L3);
        // Reverse [L2..L1).
        for (L3 = L2 ; L3 < (L2 + (L1-L2)/2) ; ++L3)
            SWAP (L3, L1-1-(L3-L2));
        // Reverse [0..L1).
        for (L3 = 0 ; L3 < L1/2 ; ++L3)
            SWAP (L3, L1-1-L3);

#undef SWAP
        // And we're done!
        NEXT;
        
    do_setmemsize:
        S1 = resizeMemory (L1, 0);
        NEXT;
        
    do_protect:
        protectPos = L1;
        protectSize = L2;
        NEXT;
    
    // Memory management (new with glulx spec 3.1)
    
    do_mzero:
        if (L1 > 0) {
          if (L2 < gRamStart || (L2 + L1) > gEndMem)
            memWriteError(L2);
          memset(gMem + L2, 0, L1);
        }
        NEXT;
        
    do_mcopy:
        if (L1 > 0) {
            if (L2 < 0 || (L2 + L1) > gEndMem)
                memReadError(L2);
            if (L3 < gRamStart || (L3 + L1) > gEndMem)
                memWriteError(L3);
            memmove(gMem + L3, gMem + L2, L1);
        }
        NEXT;
        
    do_malloc:
        S1 = heap_alloc(L1);
        NEXT;
        
    do_mfree:
        heap_free(L1);
        NEXT;
        
    // Function acceleration (new with glulx spec 3.1.1)
        
    do_accelfunc:
        accel_set_func(L1, L2);
        NEXT;
        
    do_accelparam:
        accel_set_param(L1, L2);
        NEXT;
        
    // Floating point (new with glulx spec 3.1.2)

    do_numtof:
        F1 = (git_float) L1;
        S1 = ENCODE_FLOAT(F1);
        NEXT;

    do_ftonumz:
        F1 = DECODE_FLOAT(L1);
        if (!signbit(F1)) {
          if (isnan(F1) || isinf(F1) || (F1 > 2147483647.0))
            S1 = 0x7FFFFFFF;
          else
            S1 = (git_sint32) truncf(F1);
        } else {
          if (isnan(F1) || isinf(F1) || (F1 < -2147483647.0))
            S1 = 0x80000000;
          else
            S1 = (git_sint32) truncf(F1);
        }
        NEXT;

    do_ftonumn:
        F1 = DECODE_FLOAT(L1);
        if (!signbit(F1)) {
          if (isnan(F1) || isinf(F1) || (F1 > 2147483647.0))
            S1 = 0x7FFFFFFF;
          else
            S1 = (git_sint32) roundf(F1);
        } else {
          if (isnan(F1) || isinf(F1) || (F1 < -2147483647.0))
            S1 = 0x80000000;
          else
            S1 = (git_sint32) roundf(F1);
        }
        NEXT;

    do_ceil:
        F1 = ceilf(DECODE_FLOAT(L1));
        L2 = ENCODE_FLOAT(F1);
        if ((L2 == 0x0) || (L2 == 0x80000000))
          L2 = L1 & 0x80000000;
        S1 = L2;
        NEXT;

    do_floor:
        F1 = floorf(DECODE_FLOAT(L1));
        S1 = ENCODE_FLOAT(F1);
        NEXT;

    do_sqrt:
        F1 = sqrtf(DECODE_FLOAT(L1));
        S1 = ENCODE_FLOAT(F1);
        NEXT;

    do_exp:
        F1 = expf(DECODE_FLOAT(L1));
        S1 = ENCODE_FLOAT(F1);
        NEXT;

    do_log:
        F1 = logf(DECODE_FLOAT(L1));
        S1 = ENCODE_FLOAT(F1);
        NEXT;

    do_pow:
#ifdef USE_OWN_POWF
        F1 = git_powf(DECODE_FLOAT(L1), DECODE_FLOAT(L2));
#else
        F1 = powf(DECODE_FLOAT(L1), DECODE_FLOAT(L2));
#endif
        S1 = ENCODE_FLOAT(F1);
        NEXT;

    do_atan2:
        F1 = atan2f(DECODE_FLOAT(L1), DECODE_FLOAT(L2));
        S1 = ENCODE_FLOAT(F1);
        NEXT;

    do_fmod:
        F1 = DECODE_FLOAT(L1);
        F2 = DECODE_FLOAT(L2);
        F3 = fmodf(F1, F2);
        F4 = (F1 - F3) / F2;
        L4 = ENCODE_FLOAT(F4);
        if ((L4 == 0) || (L4 == 0x80000000))
          L4 = (L1 ^ L2) & 0x80000000;
        S1 = ENCODE_FLOAT(F3);
        S2 = L4;
        NEXT;

    do_sin:
        F1 = sinf(DECODE_FLOAT(L1));
        S1 = ENCODE_FLOAT(F1);
        NEXT;

    do_cos:
        F1 = cosf(DECODE_FLOAT(L1));
        S1 = ENCODE_FLOAT(F1);
        NEXT;

    do_tan:
        F1 = tanf(DECODE_FLOAT(L1));
        S1 = ENCODE_FLOAT(F1);
        NEXT;

    do_asin:
        F1 = asinf(DECODE_FLOAT(L1));
        S1 = ENCODE_FLOAT(F1);
        NEXT;

    do_acos:
        F1 = acosf(DECODE_FLOAT(L1));
        S1 = ENCODE_FLOAT(F1);
        NEXT;

    do_atan:
        F1 = atanf(DECODE_FLOAT(L1));
        S1 = ENCODE_FLOAT(F1);
        NEXT;

    // Special Git opcodes
    
    do_git_setcacheram:
        gCacheRAM = (L1 == 0) ? 0 : 1;
        NEXT;
        
    do_git_prunecache:
        pruneCodeCache (L1, L2);
        NEXT;
    
    // Error conditions:
    
    do_error_bad_opcode:
        fatalError ("Illegal instruction");
        goto finished;
    
    stack_overflow:
        fatalError ("Stack overflow");
        goto finished;
    
    stack_underflow:
        fatalError ("Stack underflow");
        goto finished;
        
// ---------------------------------

finished:

    free (base);
    shutdownCompiler();
}
