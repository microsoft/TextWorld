// $Id: opcodes.c,v 1.20 2004/12/22 12:40:07 iain Exp $

#include "git.h"
#include "opcodes.h"

static void parseModeNibbles (git_uint32* pc, int numModes, int * modeBuffer)
{
    int * mode = modeBuffer;

    while (numModes > 0)
    {
        // Load byte.
        git_uint32 byte = memRead8((*pc)++);

        // Load low nibble.
        *mode++ = byte & 0x0f;
        --numModes;

        // Check whether we need to load any more.
        if (numModes == 0)
            break;

        // Load high nibble.
        *mode++ = (byte >> 4) & 0x0f;
        --numModes;
    }
}

static void parseLS (git_uint32* pc, Label op)
{
    int modes [2];
    parseModeNibbles (pc, 2, modes);

    parseLoad (pc, reg_L1, modes [0], size32, NULL);
    emitCode (op);
    parseStore (pc, reg_S1, modes [1], size32);
}
static void parseLLS (git_uint32* pc, Label op)
{
    int modes [3];
    parseModeNibbles (pc, 3, modes);

    parseLoad (pc, reg_L1, modes [0], size32, NULL);
    parseLoad (pc, reg_L2, modes [1], size32, NULL);
    emitCode (op);
    parseStore (pc, reg_S1, modes [2], size32);
}
static void parseLLSS (git_uint32* pc, Label op)
{
    int modes [4];
    parseModeNibbles (pc, 4, modes);

    parseLoad (pc, reg_L1, modes [0], size32, NULL);
    parseLoad (pc, reg_L2, modes [1], size32, NULL);
    emitCode (op);
    parseStore (pc, reg_S1, modes [2], size32);
    parseStore (pc, reg_S2, modes [3], size32);
}
static void parseL (git_uint32* pc, Label op)
{
    int modes [1];
    parseModeNibbles (pc, 1, modes);

    parseLoad (pc, reg_L1, modes [0], size32, NULL);
    emitCode (op);
}
static void parseLL (git_uint32* pc, Label op)
{
    int modes [2];
    parseModeNibbles (pc, 2, modes);

    parseLoad (pc, reg_L1, modes [0], size32, NULL);
    parseLoad (pc, reg_L2, modes [1], size32, NULL);
    emitCode (op);
}
static void parse_finish_branch (git_uint32* pc, Label op, LoadReg reg, int mode)
{
    git_sint32 val;
    if (parseLoad (pc, reg, mode, size32, &val))
    {
        // The branch offset is a constant, so we can
        // check for the special values 0 and 1 right here.
        
        if (val == 0)
        {
            emitCode (op - label_jeq_var + label_jeq_return0);
        }
        else if (val == 1)
        {
            emitCode (op - label_jeq_var + label_jeq_return1);
        }
        else
        {
            // Calculate the destination address and
            // emit a constant branch opcode.
            emitConstBranch (op - label_jeq_var + label_jeq_const, *pc + val - 2);
        }
    }
    else
    {
        // The branch offset isn't a constant, so just
        // emit the normal opcode plus the current PC.
        
        emitCode (op);
        emitData(*pc);
    }
}
static void parseLLLL_branch (git_uint32* pc, Label op)
{
    int modes [4];
    parseModeNibbles (pc, 4, modes);

    parseLoad (pc, reg_L1, modes [0], size32, NULL);
    parseLoad (pc, reg_L2, modes [1], size32, NULL);
    parseLoad (pc, reg_L3, modes [2], size32, NULL);
    parse_finish_branch (pc, op, reg_L4, modes [3]);
}
static void parseLLL_branch (git_uint32* pc, Label op)
{
    int modes [3];
    parseModeNibbles (pc, 3, modes);

    parseLoad (pc, reg_L1, modes [0], size32, NULL);
    parseLoad (pc, reg_L2, modes [1], size32, NULL);
    parse_finish_branch (pc, op, reg_L3, modes [2]);
}
static void parseLL_branch (git_uint32* pc, Label op)
{
    int modes [2];
    parseModeNibbles (pc, 2, modes);

    parseLoad (pc, reg_L1, modes [0], size32, NULL);
    parse_finish_branch (pc, op, reg_L2, modes [1]);
}
static void parseL_branch (git_uint32* pc, Label op)
{
    int modes [1];
    parseModeNibbles (pc, 1, modes);

    parse_finish_branch (pc, op, reg_L1, modes [0]);
}
static void parseLLL (git_uint32* pc, Label op)
{
    int modes [3];
    parseModeNibbles (pc, 3, modes);

    parseLoad (pc, reg_L1, modes [0], size32, NULL);
    parseLoad (pc, reg_L2, modes [1], size32, NULL);
    parseLoad (pc, reg_L3, modes [2], size32, NULL);
    emitCode (op);
}
static void parseS (git_uint32* pc, Label op)
{
    int modes [1];
    parseModeNibbles (pc, 1, modes);

    emitCode (op);
    parseStore (pc, reg_S1, modes [0], size32);
}
static void parseSS (git_uint32* pc, Label op)
{
    int modes [2];
    parseModeNibbles (pc, 2, modes);

    emitCode (op);
    parseStore (pc, reg_S1, modes [0], size32);
    parseStore (pc, reg_S2, modes [1], size32);
}
static void parseCatch (git_uint32 * pc)
{
    int modes [2];
    parseModeNibbles (pc, 2, modes);

    parseCatchStub (pc, modes);
}
void parseInstruction (git_uint32* pc, int * done)
{
    git_uint32 pcStart = *pc;
    int modes [8];
    git_uint32 opcode;
    
    static int ops = 0;
    ++ops;
    
    // Fetch the opcode.
    opcode = memRead8((*pc)++);

    // Check for multi-byte opcode.
    if (opcode & 0x80)
    {
        if (opcode & 0x40)
        {
            // Four-byte opcode.
            opcode &= 0x3F;
            opcode = (opcode << 8) | memRead8((*pc)++);
            opcode = (opcode << 8) | memRead8((*pc)++);
            opcode = (opcode << 8) | memRead8((*pc)++);
        }
        else
        {
            // Two-byte opcode.
            opcode &= 0x7F;
            opcode = (opcode << 8) | memRead8((*pc)++);
        }
    }

    if (gDebug)
    {
        emitCode (label_debug_step);
        emitData (pcStart);
        emitData (opcode);
    }
    
    // printf (" opcode=0x%x", opcode);
    
    // Now we have an opcode number,
    // parse the operands and emit code.
    
    switch (opcode)
    {
        case op_nop: emitCode (label_nop); break;

        // Arithmetic and logic

        case op_add: parseLLS (pc, label_add_discard); break;
        case op_sub: parseLLS (pc, label_sub_discard); break;        
        case op_mul: parseLLS (pc, label_mul_discard); break;
        case op_div: parseLLS (pc, label_div_discard); break;
        case op_mod: parseLLS (pc, label_mod_discard); break;
        
        case op_bitand: parseLLS (pc, label_bitand_discard); break;
        case op_bitor:  parseLLS (pc, label_bitor_discard);  break;
        case op_bitxor: parseLLS (pc, label_bitxor_discard); break;

        case op_neg:    parseLS (pc, label_neg_discard);    break;
        case op_bitnot: parseLS (pc, label_bitnot_discard); break;

        case op_shiftl:  parseLLS (pc, label_shiftl_discard);  break;
        case op_ushiftr: parseLLS (pc, label_ushiftr_discard); break;
        case op_sshiftr: parseLLS (pc, label_sshiftr_discard); break;

        // Branches

        case op_jump: parseL_branch (pc, label_jump_var); *done = 1; break;
        case op_jz:   parseLL_branch (pc, label_jz_var);  break;
        case op_jnz:  parseLL_branch (pc, label_jnz_var); break;
        case op_jeq:  parseLLL_branch (pc, label_jeq_var);  break;
        case op_jne:  parseLLL_branch (pc, label_jne_var);  break;
        case op_jlt:  parseLLL_branch (pc, label_jlt_var);  break;
        case op_jgt:  parseLLL_branch (pc, label_jgt_var);  break;
        case op_jle:  parseLLL_branch (pc, label_jle_var);  break;
        case op_jge:  parseLLL_branch (pc, label_jge_var);  break;
        case op_jltu: parseLLL_branch (pc, label_jltu_var); break;
        case op_jgtu: parseLLL_branch (pc, label_jgtu_var); break;
        case op_jleu: parseLLL_branch (pc, label_jleu_var); break;
        case op_jgeu: parseLLL_branch (pc, label_jgeu_var); break;
        
        case op_jumpabs: parseL (pc, label_jumpabs); *done = 1; break;

        // Moving data

        case op_copy:
            parseModeNibbles (pc, 2, modes);
            parseLoad (pc, reg_L1, modes [0], size32, NULL);
            parseStore (pc, reg_S1, modes [1], size32);
            break;

        case op_copys:
            parseModeNibbles (pc, 2, modes);
            parseLoad (pc, reg_L1, modes [0], size16, NULL);
            emitCode (label_copys_discard);
            parseStore (pc, reg_S1, modes [1], size16);
            break;
        
        case op_copyb:
            parseModeNibbles (pc, 2, modes);
            parseLoad (pc, reg_L1, modes [0], size8, NULL);
            emitCode (label_copyb_discard);
            parseStore (pc, reg_S1, modes [1], size8);
            break;

        case op_sexs: parseLS (pc, label_sexs_discard); break;
        case op_sexb: parseLS (pc, label_sexb_discard); break;

        // Array data

        case op_aload:    parseLLS (pc, label_aload_discard);    break;
        case op_aloads:   parseLLS (pc, label_aloads_discard);   break;
        case op_aloadb:   parseLLS (pc, label_aloadb_discard);   break;
        case op_aloadbit: parseLLS (pc, label_aloadbit_discard); break;
        
        case op_astore:    parseLLL (pc, label_astore);    break;
        case op_astores:   parseLLL (pc, label_astores);   break;
        case op_astoreb:   parseLLL (pc, label_astoreb);   break;
        case op_astorebit: parseLLL (pc, label_astorebit); break;

        // The stack

        case op_stkcount: parseS (pc, label_stkcount);  break;
        case op_stkpeek:  parseLS (pc, label_stkpeek);  break;
        case op_stkswap:  emitCode (label_stkswap); break;
        case op_stkcopy:  parseL (pc, label_stkcopy);   break;
        case op_stkroll:  parseLL (pc, label_stkroll);  break;

        // Functions

        case op_call:
            parseModeNibbles (pc, 3, modes);        
            parseLoad (pc, reg_L1, modes [0], size32, NULL);
            parseLoad (pc, reg_L2, modes [1], size32, NULL);
            emitCode (label_args_stack);
            parseCallStub (pc, modes [2]);
            break;

        case op_callf:
            parseModeNibbles (pc, 2, modes);
            parseLoad (pc, reg_L1, modes [0], size32, NULL);
            emitCode (label_args_0);
            parseCallStub (pc, modes [1]);
            break;

        case op_callfi:
            parseModeNibbles (pc, 3, modes);
            parseLoad (pc, reg_L1, modes [0], size32, NULL);
            parseLoad (pc, reg_L2, modes [1], size32, NULL);
            emitCode (label_args_1);
            parseCallStub (pc, modes [2]);
            break;

        case op_callfii:
            parseModeNibbles (pc, 4, modes);
            parseLoad (pc, reg_L1, modes [0], size32, NULL);
            parseLoad (pc, reg_L2, modes [1], size32, NULL);
            parseLoad (pc, reg_L3, modes [2], size32, NULL);
            emitCode (label_args_2);
            parseCallStub (pc, modes [3]);
            break;

        case op_callfiii:
            parseModeNibbles (pc, 5, modes);
            parseLoad (pc, reg_L1, modes [0], size32, NULL);
            parseLoad (pc, reg_L2, modes [1], size32, NULL);
            parseLoad (pc, reg_L3, modes [2], size32, NULL);
            parseLoad (pc, reg_L4, modes [3], size32, NULL);
            emitCode (label_args_3);
            parseCallStub (pc, modes [4]);
            break;

        case op_return:
            parseL (pc, label_return);
            *done = 1;
            break;

        case op_tailcall:
            parseModeNibbles (pc, 2, modes);        
            parseLoad (pc, reg_L1, modes [0], size32, NULL);
            parseLoad (pc, reg_L2, modes [1], size32, NULL);
            emitCode (label_args_stack);
            emitCode (label_tailcall);
            *done = 1;
            break;

        // Continuations

        case op_catch: parseCatch (pc); break;
        case op_throw:
            parseLL (pc, label_throw);
            *done = 1;
            break;

        case op_random:  parseLS (pc, label_random); break;
        case op_setrandom:  parseL (pc, label_setrandom); break;

        case op_getmemsize: parseS (pc, label_getmemsize); break;
        case op_setmemsize: parseLS (pc, label_setmemsize); break;
        
        case op_quit:
            emitCode (label_quit);
            *done = 1;
            break;
        
        case op_restart:
            emitCode (label_restart);
            *done = 1;
            break;
        
        case op_restore: parseLS (pc, label_restore); break;
        case op_restoreundo: parseS (pc, label_restoreundo); break;
        case op_protect: parseLL (pc, label_protect); break;
        case op_verify: parseS (pc, label_verify); break;

        case op_save:
            parseModeNibbles (pc, 2, modes);
            parseLoad (pc, reg_L1, modes [0], size32, NULL);
            parseSaveStub (pc, modes [1]);
            break;

        case op_saveundo:
            parseModeNibbles (pc, 1, modes);
            parseUndoStub (pc, modes [0]);
            break;

        case op_getiosys: parseSS (pc, label_getiosys);  break;
        case op_setiosys: parseLL (pc, label_setiosys);  break;

        case op_getstringtbl: parseS (pc, label_getstringtbl);  break;
        case op_setstringtbl: parseL (pc, label_setstringtbl);  break;

        case op_streamchar:    parseL (pc, label_streamchar);    emitData(*pc); break;
        case op_streamnum:     parseL (pc, label_streamnum);     emitData(*pc); break;
        case op_streamstr:     parseL (pc, label_streamstr);     emitData(*pc); break;
        case op_streamunichar: parseL (pc, label_streamunichar); emitData(*pc); break;
 
        case op_glk: parseLLS (pc, label_glk); break;
        case op_gestalt: parseLLS (pc, label_gestalt); break;

        case op_binarysearch:
        case op_linearsearch:
            parseModeNibbles (pc, 8, modes);
            parseLoad (pc, reg_L1, modes [0], size32, NULL);
            parseLoad (pc, reg_L2, modes [1], size32, NULL);
            parseLoad (pc, reg_L3, modes [2], size32, NULL);
            parseLoad (pc, reg_L4, modes [3], size32, NULL);
            parseLoad (pc, reg_L5, modes [4], size32, NULL);
            parseLoad (pc, reg_L6, modes [5], size32, NULL);
            parseLoad (pc, reg_L7, modes [6], size32, NULL);
            emitCode (opcode == op_linearsearch ? label_linearsearch : label_binarysearch);
            parseStore (pc, reg_S1, modes [7], size32);
            break;

        case op_linkedsearch:
            parseModeNibbles (pc, 7, modes);
            parseLoad (pc, reg_L1, modes [0], size32, NULL);
            parseLoad (pc, reg_L2, modes [1], size32, NULL);
            parseLoad (pc, reg_L3, modes [2], size32, NULL);
            parseLoad (pc, reg_L4, modes [3], size32, NULL);
            parseLoad (pc, reg_L5, modes [4], size32, NULL);
            parseLoad (pc, reg_L6, modes [5], size32, NULL);
            emitCode (label_linkedsearch);
            parseStore (pc, reg_S1, modes [6], size32);
            break;
        
        case op_debugtrap:
            parseL (pc, label_debugtrap);
            break;
        
        // Memory management
            
        case op_mzero: parseLL (pc, label_mzero); break;
        case op_mcopy: parseLLL (pc, label_mcopy); break;
        
        case op_malloc: parseLS (pc, label_malloc); break;
        case op_mfree: parseL (pc, label_mfree); break;
        
        // Function acceleration
            
        case op_accelfunc: parseLL (pc, label_accelfunc); break;
        case op_accelparam: parseLL (pc, label_accelparam); break;

        // Floating point

        case op_numtof: parseLS (pc, label_numtof); break;
        case op_ftonumz: parseLS (pc, label_ftonumz); break;
        case op_ftonumn: parseLS (pc, label_ftonumn); break;
        case op_ceil: parseLS (pc, label_ceil); break;
        case op_floor: parseLS (pc, label_floor); break;
        case op_sqrt: parseLS (pc, label_sqrt); break;
        case op_exp: parseLS (pc, label_exp); break;
        case op_log: parseLS (pc, label_log); break;

        case op_fadd: parseLLS (pc, label_fadd_discard); break;
        case op_fsub: parseLLS (pc, label_fsub_discard); break;
        case op_fmul: parseLLS (pc, label_fmul_discard); break;
        case op_fdiv: parseLLS (pc, label_fdiv_discard); break;
        case op_pow: parseLLS (pc, label_pow); break;
        case op_atan2: parseLLS (pc, label_atan2); break;

        case op_fmod: parseLLSS (pc, label_fmod); break;

        case op_sin: parseLS (pc, label_sin); break;
        case op_cos: parseLS (pc, label_cos); break;
        case op_tan: parseLS (pc, label_tan); break;
        case op_asin: parseLS (pc, label_asin); break;
        case op_acos: parseLS (pc, label_acos); break;
        case op_atan: parseLS (pc, label_atan); break;

        case op_jfeq: parseLLLL_branch (pc, label_jfeq_var); break;
        case op_jfne: parseLLLL_branch (pc, label_jfne_var); break;

        case op_jflt: parseLLL_branch (pc, label_jflt_var); break;
        case op_jfle: parseLLL_branch (pc, label_jfle_var); break;
        case op_jfgt: parseLLL_branch (pc, label_jfgt_var); break;
        case op_jfge: parseLLL_branch (pc, label_jfge_var); break;

        case op_jisnan: parseLL_branch (pc, label_jisnan_var); break;
        case op_jisinf: parseLL_branch (pc, label_jisinf_var); break;

        // Special Git opcodes
        
        case op_git_setcacheram: parseL (pc, label_git_setcacheram); break;
        case op_git_prunecache: parseLL (pc, label_git_prunecache); break;
        
        default:
            // Unknown opcode.
            abortCompilation();
            break;
    }
}
