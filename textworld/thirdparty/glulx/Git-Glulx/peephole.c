// $Id: peephole.c,v 1.6 2003/10/13 22:53:04 iain Exp $
// Peephole optimiser for git

#include "git.h"

static Label sLastOp;

extern void resetPeepholeOptimiser ()
{
    sLastOp = label_nop;
}

#define REPLACE_SINGLE(lastOp,thisOp,newOp) \
    case label_ ## thisOp:                  \
        if (sLastOp == label_ ## lastOp)    \
        {                                   \
            op = label_ ## newOp;           \
            goto replaceNoOperands;         \
        }                                   \
        break

#define CASE_NO_OPERANDS(lastOp,newOp) \
    case label_ ## lastOp: op = label_ ## newOp; goto replaceNoOperands

#define CASE_ONE_OPERAND(lastOp,newOp) \
    case label_ ## lastOp: op = label_ ## newOp; goto replaceOneOperand

#define REPLACE_STORE(storeOp) \
    case label_ ## storeOp:                                             \
        switch(sLastOp)                                                 \
        {                                                               \
            CASE_NO_OPERANDS (add_discard,      add_ ## storeOp);       \
            CASE_NO_OPERANDS (sub_discard,      sub_ ## storeOp);       \
            CASE_NO_OPERANDS (mul_discard,      mul_ ## storeOp);       \
            CASE_NO_OPERANDS (div_discard,      div_ ## storeOp);       \
            CASE_NO_OPERANDS (mod_discard,      mod_ ## storeOp);       \
            CASE_NO_OPERANDS (neg_discard,      neg_ ## storeOp);       \
            CASE_NO_OPERANDS (bitand_discard,   bitand_ ## storeOp);    \
            CASE_NO_OPERANDS (bitor_discard,    bitor_ ## storeOp);     \
            CASE_NO_OPERANDS (bitxor_discard,   bitxor_ ## storeOp);    \
            CASE_NO_OPERANDS (bitnot_discard,   bitnot_ ## storeOp);    \
            CASE_NO_OPERANDS (shiftl_discard,   shiftl_ ## storeOp);    \
            CASE_NO_OPERANDS (sshiftr_discard,  sshiftr_ ## storeOp);   \
            CASE_NO_OPERANDS (ushiftr_discard,  ushiftr_ ## storeOp);   \
            CASE_NO_OPERANDS (copys_discard,    copys_ ## storeOp);     \
            CASE_NO_OPERANDS (copyb_discard,    copyb_ ## storeOp);     \
            CASE_NO_OPERANDS (sexs_discard,     sexs_ ## storeOp);      \
            CASE_NO_OPERANDS (sexb_discard,     sexb_ ## storeOp);      \
            CASE_NO_OPERANDS (aload_discard,    aload_ ## storeOp);     \
            CASE_NO_OPERANDS (aloads_discard,   aloads_ ## storeOp);    \
            CASE_NO_OPERANDS (aloadb_discard,   aloadb_ ## storeOp);    \
            CASE_NO_OPERANDS (aloadbit_discard, aloadbit_ ## storeOp);  \
            CASE_NO_OPERANDS (fadd_discard,     fadd_ ## storeOp);      \
            CASE_NO_OPERANDS (fsub_discard,     fsub_ ## storeOp);      \
            CASE_NO_OPERANDS (fmul_discard,     fmul_ ## storeOp);      \
            CASE_NO_OPERANDS (fdiv_discard,     fdiv_ ## storeOp);      \
            default: break;                                             \
        }                                                               \
        break

#define REPLACE_L1_L2(mode2)                                    \
    case label_L2_ ## mode2:                                    \
        switch(sLastOp)                                         \
        {                                                       \
            CASE_ONE_OPERAND (L1_const, L1_const_L2_ ## mode2); \
            CASE_NO_OPERANDS (L1_stack, L1_stack_L2_ ## mode2); \
            CASE_ONE_OPERAND (L1_local, L1_local_L2_ ## mode2); \
            CASE_ONE_OPERAND (L1_addr,  L1_addr_L2_ ## mode2);  \
            default: break;                                     \
        }                                                       \
        break

#define REPLACE_LOAD_OP(loadOp,reg)                                         \
    case label_ ## loadOp:                                                  \
        switch(sLastOp)                                                     \
        {                                                                   \
            CASE_ONE_OPERAND (reg ## _const, loadOp ## _ ## reg ## _const); \
            CASE_NO_OPERANDS (reg ## _stack, loadOp ## _ ## reg ## _stack); \
            CASE_ONE_OPERAND (reg ## _local, loadOp ## _ ## reg ## _local); \
            CASE_ONE_OPERAND (reg ## _addr,  loadOp ## _ ## reg ## _addr);  \
            default: break;                                                 \
        }                                                                   \
        break

extern void emitCode (Label op)
{
    git_uint32 temp;

    if (gPeephole)
    {
        switch (op)
        {
            REPLACE_SINGLE (args_stack, call_stub_discard, args_stack_call_stub_discard);
            REPLACE_SINGLE (args_stack, call_stub_addr,    args_stack_call_stub_addr);
            REPLACE_SINGLE (args_stack, call_stub_local,   args_stack_call_stub_local);
            REPLACE_SINGLE (args_stack, call_stub_stack,   args_stack_call_stub_stack);

            REPLACE_STORE (S1_stack);
            REPLACE_STORE (S1_local);
            REPLACE_STORE (S1_addr);

            REPLACE_L1_L2 (const);
            REPLACE_L1_L2 (stack);
            REPLACE_L1_L2 (local);
            REPLACE_L1_L2 (addr);

            REPLACE_LOAD_OP (return, L1);
            REPLACE_LOAD_OP (astore, L3);
            REPLACE_LOAD_OP (astores, L3);
            REPLACE_LOAD_OP (astoreb, L3);
            REPLACE_LOAD_OP (astorebit, L3);
            
            default: break;
        }
    }
    goto noPeephole;

replaceOneOperand:
    // The previous opcode has one operand, so
    // we have to go back two steps to update it.
    temp = undoEmit();  // Save the operand.
    undoEmit();         // Remove the old opcode.
    emitFinalCode (op); // Emit the new opcode.
    emitData (temp);    // Emit the operand again.
    goto done;

replaceNoOperands:
    undoEmit();
    // ... fall through
noPeephole:
    emitFinalCode (op);
    // ... fall through
done:
    sLastOp = op;
}
