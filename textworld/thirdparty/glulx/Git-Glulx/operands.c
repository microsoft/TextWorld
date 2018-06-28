// $Id: operands.c,v 1.11 2004/02/02 00:13:46 iain Exp $

#include "git.h"
#include <assert.h>

git_uint32 parseLoad (git_uint32 * pc, LoadReg reg, int mode, TransferSize size, git_sint32 * constVal)
{
    git_uint32 value;

    switch (mode)
    {
        case 0x0: // Constant zero. (Zero bytes)
            value = 0;
            goto load_const;

        case 0x1: // Constant, -80 to 7F. (One byte)
            value = (git_sint32) ((git_sint8) memRead8(*pc));
            *pc += 1;
            goto load_const;

        case 0x2: // Constant, -8000 to 7FFF. (Two bytes)
            value = (git_sint32) ((git_sint16) memRead16(*pc));
            *pc += 2;
            goto load_const;

        case 0x3: // Constant, any value. (Four bytes)
            value = memRead32(*pc);
            *pc += 4;
            goto load_const;

        case 0x5: // Contents of address 00 to FF. (One byte)
            value = memRead8(*pc);
            *pc += 1;
            goto load_addr;

        case 0x6: // Contents of address 0000 to FFFF. (Two bytes)
            value = memRead16(*pc);
            *pc += 2;
            goto load_addr;

        case 0x7: // Contents of any address. (Four bytes)
            value = memRead32(*pc);
            *pc += 4;
            goto load_addr;

        case 0x8: // Value popped off stack. (Zero bytes)
            goto load_stack;

        case 0x9: // Call frame local at address 00 to FF. (One byte)
            value = memRead8(*pc);
            *pc += 1;
            goto load_local;

        case 0xA: // Call frame local at address 0000 to FFFF. (Two bytes)
            value = memRead16(*pc);
            *pc += 2;
            goto load_local;

        case 0xB: // Call frame local at any address. (Four bytes)
            value = memRead32(*pc);
            *pc += 4;
            goto load_local;

        case 0xD: // Contents of RAM address 00 to FF. (One byte)
            value = memRead8(*pc) + gRamStart;
            *pc += 1;
            goto load_addr;

        case 0xE: // Contents of RAM address 0000 to FFFF. (Two bytes)
            value = memRead16(*pc) + gRamStart;
            *pc += 2;
            goto load_addr;

        case 0xF: // Contents of RAM, any address. (Four bytes)
            value = memRead32(*pc) + gRamStart;
            *pc += 4;
            goto load_addr;

        default: // Illegal addressing mode
            abortCompilation();
            break;

        // ------------------------------------------------------

        load_const:
            if (constVal)
            {
                *constVal = value;
                return 1;
            }
            else
            {
                emitCode (label_L1_const + reg);
                emitData (value);
            }
            break;

        load_stack:
			emitCode (label_L1_stack + reg);
			break;

        load_addr:
            if (value < gRamStart)
            {
                if (size == size32)
                    value = memRead32(value);
                else if (size == size16)
                    value = memRead16(value);
                else
                    value = memRead8(value);
				goto load_const;
            }
			switch (size)
			{
				case size8:
					assert (reg == reg_L1);
					emitCode (label_L1_addr8);
					break;

				case size16:
					assert (reg == reg_L1);
					emitCode (label_L1_addr16);
					break;

				case size32:
					emitCode (label_L1_addr + reg);
					break;
			}
			emitData (value);
			break;

        load_local:
            emitCode (label_L1_local + reg);
            emitData (value / 4); // Convert byte offset to word offset.
            break;
    }

    return 0;
}

void parseStore (git_uint32 * pc, StoreReg reg, int mode, TransferSize size)
{
    git_uint32 value;

    switch (mode)
    {
        case 0x0: // Discard
            break;

        case 0x5: // Contents of address 00 to FF. (One byte)
            value = memRead8(*pc);
            *pc += 1;
            goto store_addr;

        case 0x6: // Contents of address 0000 to FFFF. (Two bytes)
            value = memRead16(*pc);
            *pc += 2;
            goto store_addr;

        case 0x7: // Contents of any address. (Four bytes)
            value = memRead32(*pc);
            *pc += 4;
            goto store_addr;

        case 0x8: // Value popped off stack. (Zero bytes)
            goto store_stack;

        case 0x9: // Call frame local at store_address 00 to FF. (One byte)
            value = memRead8(*pc);
            *pc += 1;
            goto store_local;

        case 0xA: // Call frame local at store_address 0000 to FFFF. (Two bytes)
            value = memRead16(*pc);
            *pc += 2;
            goto store_local;

        case 0xB: // Call frame local at any store_address. (Four bytes)
            value = memRead32(*pc);
            *pc += 4;
            goto store_local;

        case 0xD: // Contents of RAM address 00 to FF. (One byte)
            value = memRead8(*pc) + gRamStart;
            *pc += 1;
            goto store_addr;

        case 0xE: // Contents of RAM address 0000 to FFFF. (Two bytes)
            value = memRead16(*pc) + gRamStart;
            *pc += 2;
            goto store_addr;

        case 0xF: // Contents of RAM, any address. (Four bytes)
            value = memRead32(*pc) + gRamStart;
            *pc += 4;
            goto store_addr;

        // ------------------------------------------------------

        store_stack:
            emitCode (reg == reg_S1 ? label_S1_stack : label_S2_stack);
            break;

        store_addr:
            if (size == size32)
			{
                emitCode (reg == reg_S1 ? label_S1_addr : label_S2_addr);
            }
			else
			{
				assert (reg == reg_S1);
				emitCode (size == size16 ? label_S1_addr16 : label_S1_addr8);
			}
            emitData (value);
            break;

        store_local:
            emitCode (reg == reg_S1 ? label_S1_local : label_S2_local);
            emitData (value / 4); // Convert byte offset to word offset.
            break;
    }
}

static void parseStub (git_uint32 * pc, int mode, Label discardOp)
{
    git_uint32 value;
    switch (mode)
    {
        case 0x0: // Discard
            goto store_discard;
        case 0x5: // Contents of address 00 to FF. (One byte)
            value = memRead8(*pc);
            *pc += 1;
            goto store_addr;
        case 0x6: // Contents of address 0000 to FFFF. (Two bytes)
            value = memRead16(*pc);
            *pc += 2;
            goto store_addr;
        case 0x7: // Contents of any address. (Four bytes)
            value = memRead32(*pc);
            *pc += 4;
            goto store_addr;
        case 0x8: // Value popped off stack. (Zero bytes)
            goto store_stack;
        case 0x9: // Call frame local at store_address 00 to FF. (One byte)
            value = memRead8(*pc);
            *pc += 1;
            goto store_local;
        case 0xA: // Call frame local at store_address 0000 to FFFF. (Two bytes)
            value = memRead16(*pc);
            *pc += 2;
            goto store_local;
        case 0xB: // Call frame local at any store_address. (Four bytes)
            value = memRead32(*pc);
            *pc += 4;
            goto store_local;
        case 0xD: // Contents of RAM address 00 to FF. (One byte)
            value = memRead8(*pc) + gRamStart;
            *pc += 1;
            goto store_addr;
        case 0xE: // Contents of RAM address 0000 to FFFF. (Two bytes)
            value = memRead16(*pc) + gRamStart;
            *pc += 2;
            goto store_addr;
        case 0xF: // Contents of RAM, any address. (Four bytes)
            value = memRead32(*pc) + gRamStart;
            *pc += 4;
            goto store_addr;
        // ------------------------------------------------------
        store_discard:
            emitCode (discardOp);
            break;
        store_stack:
            emitCode (discardOp + (label_call_stub_stack - label_call_stub_discard));
            break;
        store_addr:
            emitCode (discardOp + (label_call_stub_addr - label_call_stub_discard));
            emitData (value);
            break;
        store_local:
            emitCode (discardOp + (label_call_stub_local - label_call_stub_discard));
            emitData (value);
            break;
    }
    
    // Every call stub ends with the glulx return address.
    emitData (*pc);

    // ...which means that every call stub references the next instruction.
    nextInstructionIsReferenced ();
}
void parseCallStub (git_uint32 * pc, int mode)
{
    parseStub (pc, mode, label_call_stub_discard);
}
void parseSaveStub (git_uint32 * pc, int mode)
{
    parseStub (pc, mode, label_save_stub_discard);
}
void parseUndoStub (git_uint32 * pc, int mode)
{
    parseStub (pc, mode, label_undo_stub_discard);
}

void parseCatchStub (git_uint32 * pc, int * modes)
{
    git_uint32 tokenVal;
    git_sint32 branchVal;
    git_uint32 branchConst = 0;
    Block stubCode;

    switch (modes[0])
    {
        case 0x0: // Discard
            goto store_discard;
        case 0x5: // Contents of address 00 to FF. (One byte)
            tokenVal = memRead8(*pc);
            *pc += 1;
            goto store_addr;
        case 0x6: // Contents of address 0000 to FFFF. (Two bytes)
            tokenVal = memRead16(*pc);
            *pc += 2;
            goto store_addr;
        case 0x7: // Contents of any address. (Four bytes)
            tokenVal = memRead32(*pc);
            *pc += 4;
            goto store_addr;
        case 0x8: // Value popped off stack. (Zero bytes)
            goto store_stack;
        case 0x9: // Call frame local at store_address 00 to FF. (One byte)
            tokenVal = memRead8(*pc);
            *pc += 1;
            goto store_local;
        case 0xA: // Call frame local at store_address 0000 to FFFF. (Two bytes)
            tokenVal = memRead16(*pc);
            *pc += 2;
            goto store_local;
        case 0xB: // Call frame local at any store_address. (Four bytes)
            tokenVal = memRead32(*pc);
            *pc += 4;
            goto store_local;
        case 0xD: // Contents of RAM address 00 to FF. (One byte)
            tokenVal = memRead8(*pc) + gRamStart;
            *pc += 1;
            goto store_addr;
        case 0xE: // Contents of RAM address 0000 to FFFF. (Two bytes)
            tokenVal = memRead16(*pc) + gRamStart;
            *pc += 2;
            goto store_addr;
        case 0xF: // Contents of RAM, any address. (Four bytes)
            tokenVal = memRead32(*pc) + gRamStart;
            *pc += 4;
            goto store_addr;
        // ------------------------------------------------------
        store_discard:
            branchConst = parseLoad (pc, reg_L1, modes[1], size32, &branchVal);
            emitCode (label_catch_stub_discard);
            break;
        store_stack:
            branchConst = parseLoad (pc, reg_L1, modes[1], size32, &branchVal);
            emitCode (label_catch_stub_stack);
            break;
        store_addr:
            branchConst = parseLoad (pc, reg_L1, modes[1], size32, &branchVal);
            emitCode (label_catch_stub_addr);
            emitData (tokenVal);
            break;
        store_local:
            branchConst = parseLoad (pc, reg_L1, modes[1], size32, &branchVal);
            emitCode (label_catch_stub_local);
            emitData (tokenVal);
            break;
    }
    
    // The catch stub ends with the address to go to on throw,
    // which is after the branch, so we don't know what it is yet.
    emitData (0);
    stubCode = peekAtEmittedStuff (1);

    // Emit the branch taken after storing the catch token.
    if (branchConst)
    {
        if (branchVal == 0)
            emitCode (label_jump_return0);
        else if (branchVal == 1)
            emitCode (label_jump_return1);
        else
            emitConstBranch (label_jump_const, *pc + branchVal - 2);
    }
    else
    {
        emitCode (label_jump_var);
        emitData (*pc);
    }

    // Fix up the throw return address
    *stubCode = *pc;
    nextInstructionIsReferenced ();
}
