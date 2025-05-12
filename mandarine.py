#!/usr/bin/env python3

import sys
import subprocess
from enum import Enum, IntEnum, auto, Flag, IntFlag
import types
import typing
import os
import glob
from dataclasses import dataclass, field
from functools import lru_cache


HEAP_SIZE = 64 * 1<<10

# for future use. To throw as much errors to cmdline before exiting
#GLOBAL_ERROR_COUNT = 0

__HELP_STR__ ='''
commandline usage: mandarin.py <[-c <input_file> <c_options>]|[-S <input_file> <s_options>]|[-t <t_options>]>

<input_file> -> *.mand

<c_options> -> [-o <output_file>]

!not implemented yet! <s_options> -> [-s <output_file>]

<t_options> -> [record | compare]
    record -> record output of tests
    compare (default) -> compares output of tests to recorded data

    -o -> specify output file for compilation
    -S -> specify output file for outputting of simulation data output
    
'''
GOOD_ = '\033[92m'
OKAY_ = '\033[96m'
OK_ = '\033[94m'
WARN_ = '\033[93m'
FAIL_ = '\033[91m'
BOLD_ = '\033[1m'
LINE_ = '\033[4m'
END_ = '\033[0m'
BACK_ = '{0}'

class COMMODE(Enum):
    STANDARD    = auto()
    SET         = auto()
    DOS         = auto()
    LINUX       = auto()

Com_Mode: COMMODE = COMMODE.STANDARD

class TOKENS(Enum):
    NOTOKEN     = auto()
    WORD        = auto()
    OPERAND     = auto()
    NAME        = auto()
    TYPE        = auto()
    CODEOPEN    = auto()
    CODECLOSE   = auto()
    NUM         = auto()
    STRING      = auto()
    MODE        = auto()
    COUNT       = auto()

class OP(Enum):
    NUM         = auto()
    STRING      = auto()
    SET         = auto()
    ADD         = auto()
    SUB         = auto()
    MUL         = auto()
    DIV         = auto()
    MOD         = auto()
    SHL         = auto()
    SHR         = auto()
    PTR         = auto()
    EQUAL       = auto()
    GREATER     = auto()
    LESS        = auto()
    GE          = auto()
    LE          = auto()
    IF          = auto()
    ELSE        = auto()
    WHILE       = auto()
    CONJUMP     = auto()
    JUMP        = auto()
    LABEL       = auto()
    COPY        = auto() # currently unsupported for a moment
    PRINT       = auto() # currently unsupported for a moment
    PRINT_NL    = auto() # currently unsupported for a moment
    PRINT_AND_NL= auto() # currently unsupported for a moment
    PRINT_CHAR  = auto() # currently unsupported for a moment
    BUF         = auto()
    MEMWRITE    = auto()
    MEMREAD     = auto()
    DOS         = auto()
    LINUX       = auto()
    MODE        = auto()
    VAR         = auto()
    TYPE        = auto()
    COLON       = auto()
    COUNT       = auto()

class DT(Enum):
    REGISTER    = auto()
    REGISTERMEM = auto()
    IMMEDIATE   = auto()
    UINT8       = auto()
    UINT16      = auto()
    UINT8MEM    = auto()
    UINT16MEM   = auto()
    COUNT       = auto()

class CB(Enum):
    COMPILETIME = auto()
    CONDITION   = auto()
    RESOLVE     = auto()
    CODE        = auto()
    COUNT       = auto()

class Sticky(IntFlag):
    LEFT    = auto()
    RIGHT   = auto()

@dataclass
class Token:
    type:       TOKENS
    loc:        tuple[str, int, int]
    name:       str
    flags:      Sticky

@dataclass
class Var:
    type: DT
    name: str
    value: bytearray = field(default_factory=bytearray)
    defined: bool = field(default=False)
class codeBlock:
    id:         int = -1
    type:       CB = CB.COMPILETIME
    tokens:     list[Token | typing.Self] = []
    vars:       dict[str,Var]

    def __init__(self: typing.Self, id: int = -1, tokens: list[Token] = [], vars: dict[str, Var] = {}):
        self.id = id
        self.tokens = tokens
        self.vars = vars
    
    def __repr__(self) -> str:
        return f"(codeBlock > id = {self.id} | type = {self.type})"

@dataclass
class OpType:
    type:       OP
    loc:        int
    file_loc:   tuple[str, int, int]
    value:      typing.Any = None

class Error(Enum):
    CMD         = auto()
    ENUM        = auto()
    PARSE       = auto()
    TOKENIZE    = auto()
    COMPILE     = auto()
    SIMULATE    = auto()
    TEST        = auto()
    SELF        = auto()

class LogFlag(Flag):
    DEFAULT     = 0
    FAIL        = auto()
    WARNING     = auto()
    INFO        = auto()
    GOOD        = auto()
    EXPECTED    = auto()

b8tuplel = ('al', 'bl', 'cl', 'dl', 'bpl', 'spl', 'di', 'si')
b8tupleh = ('ah', 'bh', 'ch', 'dh', 'bpl', 'spl', 'di', 'si')
b16tuple = ('ax', 'bx', 'cx', 'dx', 'bp', 'sp', 'di', 'si')
b32tuple = ('eax', 'ebx', 'ecx', 'edx', 'ebp', 'esp', 'edi', 'esi')
b64tuple = ('rax', 'rbx', 'rcx', 'rdx', 'rbp', 'rsp', 'rdi', 'rsi')

regToId: dict[str, int] = {
    'ax' : 0,
    'al' : 0,
    'ah' : 0,
    'bx' : 1,
    'bl' : 1,
    'bh' : 1,
    'cx' : 2,
    'cl' : 2,
    'ch' : 2,
    'dx' : 3,
    'dl' : 3,
    'dh' : 3,
    'di' : 6,
    'si' : 7,
}

DTtoV: dict[DT, DT] = {
    DT.UINT16 : DT.UINT16,
    DT.UINT8 : DT.UINT8,
    DT.UINT16MEM : DT.UINT16,
    DT.UINT8MEM : DT.UINT8,
}
DTtoP: dict[DT, DT] = {
    DT.UINT16 : DT.UINT16MEM,
    DT.UINT8 : DT.UINT8MEM,
    DT.UINT16MEM : DT.UINT16MEM,
    DT.UINT8MEM : DT.UINT8MEM,
}

def bolden(string: str) -> str:
    return f"{BOLD_}{string}{BACK_}"

def error(errorType: Error, errorStr: str, expected: tuple[typing.Any, typing.Any] = (None,None), flags: LogFlag = LogFlag(0), exitAfter: bool = True):
    
    if not errorStr:
        error(Error.SELF, f"{BOLD_}errorStr{BACK_} is empty for error() call!!!")

    out: str = f"{LINE_}{OKAY_}Error.{errorType.name}{END_} "
    outfun: callable

    if LogFlag.FAIL in flags:
        errorStr = errorStr.format(FAIL_)
        out = out + f"{FAIL_}{errorStr}{END_}"
        outfun = sys.stderr.write
    elif LogFlag.WARNING in flags:
        errorStr = errorStr.format(WARN_)
        out = out + f"{WARN_}{errorStr}{END_}"
        outfun = sys.stderr.write
    elif LogFlag.INFO in flags:
        errorStr = errorStr.format(OK_)
        out = out + f"{OK_}{errorStr}{END_}"
        outfun = sys.stdout.write
    elif LogFlag.GOOD in flags:
        errorStr = errorStr.format(GOOD_)
        out = out + f"{GOOD_}{errorStr}{END_}"
        outfun = sys.stdout.write
    else:
        errorStr = errorStr.format(OKAY_)
        out = out + f"{OKAY_}{errorStr}{END_}"
        outfun = sys.stdout.write
    
    if LogFlag.EXPECTED in flags:
        if expected[0] == None:
            error(Error.SELF, f"no `{BOLD_}expected{BACK_}` string for error message with {BOLD_}EXPECTED{BACK_} Flag\n Error message passed > {errorStr}")
        out = out + f"{OKAY_} >>> Expected `{GOOD_}{expected[0]}{OKAY_}` found `{FAIL_}{expected[1]}{OKAY_}`{END_}"

    outfun(out + '\n')

    if(errorType == Error.CMD):
        sys.stdout.write(__HELP_STR__ + f"{END_}\n")
    if exitAfter:
        exit(1)

class ComState(Flag):
    NONE            = auto()
    CONDITION       = auto()
    ARITHMETIC      = auto()
    VARDEF          = auto()

def bfromNum(type: DT, value: int) -> bytearray:

    #if (n:=OP.COUNT.value) != (m:=33):
        #error(Error.ENUM, f"{BOLD_}Exhaustive operation protection in {bolden("bfromNum")}", expected = (m,n), flags = LogFlag.FAIL | LogFlag.EXPECTED)
    if (n:=DT.COUNT.value) != (m:=5):
        error(Error.ENUM, f"{BOLD_}Exhaustive datatype protection in {bolden("bfromNum")}", expected = (m,n), flags = LogFlag.FAIL | LogFlag.EXPECTED)

    match type:
        case DT.UINT8:
            return bytearray([value % 256])
        case DT.UINT16:
            return bytearray([(value // 256) % 256, value % 256])
        case DT.UINT8MEM:
            return bytearray([(value // 256) % 256, value % 256])
        case DT.UINT16MEM:
            return bytearray([(value // 256) % 256, value % 256])
        case _:
            return bytearray([0])

#regTuple: types.GenericAlias = types.GenericAlias(tuple, (bool,bool,bool,bool,bool,bool,bool,bool))

class BITS(IntEnum):
    B8  = 8
    B16 = 16
    B32 = 32
    B64 = 64
    MAX = (1<<64)-1

@lru_cache
def bitRange(data: int) -> BITS:
    if data < 1<<BITS.B8.value:
        return BITS.B8
    elif data < 1<<BITS.B16.value:
        return BITS.B16
    elif data < 1<<BITS.B32.value:
        return BITS.B32
    elif data < 1<<BITS.B64.value:
        return BITS.B64
    else:
        return BITS.MAX

@lru_cache
def cutNumToBit(data: int, bits: BITS) -> int:
    match bits:
        case BITS.B8:
            if data >= (1<<8):
                error(Error.COMPILE, f"Got immediate value beyound 8 bit limit, using modulo to cut it to 8 bits | value = {data} | result = {data % (1<<8)}", flags = LogFlag.WARNING, exitAfter = False)
            return data % (1<<8)
        case BITS.B16:
            if data >= (1<<16):
                error(Error.COMPILE, f"Got immediate value beyound 16 bit limit, using modulo to cut it to 16 bits | value = {data} | result = {data % (1<<16)}", flags = LogFlag.WARNING, exitAfter = False)
            return data % (1<<16)
        case BITS.B32:
            if data >= (1<<32):
                error(Error.COMPILE, f"Got immediate value beyound 32 bit limit, using modulo to cut it to 32 bits | value = {data} | result = {data % (1<<32)}", flags = LogFlag.WARNING, exitAfter = False)
            return data % (1<<32)
        case BITS.B64:
            if data >= (1<<64):
                error(Error.COMPILE, f"Got immediate value beyound 64 bit limit, using modulo to cut it to 64 bits | value = {data} | result = {data % (1<<64)}", flags = LogFlag.WARNING, exitAfter = False)
            return data % (1<<64)
        case _:
            return data

class GENASMF(IntFlag):
    FV  = auto()    # Force Value # Is it needed???
    SV  = auto()    # Single Value operation
    FH  = auto()    # Force High register in 8 bit mode
    B8  = auto()    # Force 8Bits
    B16 = auto()    # Force 16Bits 
    PD  = auto()    # Preserve Dx  
    CD  = auto()    # Clear Destination (xor or mov 0)

dosDTS: dict[DT, BITS] = {
    DT.UINT8:       BITS.B8,
    DT.UINT8MEM:    BITS.B16,
    DT.UINT16:      BITS.B16,
    DT.UINT16MEM:   BITS.B16,
    DT.IMMEDIATE:   BITS.B16,
    DT.REGISTER:    BITS.B16,
    DT.REGISTERMEM: BITS.B16,
}

dosDTSex: dict[DT, BITS] = {
    DT.UINT8:       BITS.B8,
    DT.UINT8MEM:    BITS.B8,
    DT.UINT16:      BITS.B16,
    DT.UINT16MEM:   BITS.B16,
    DT.IMMEDIATE:   BITS.B16,
    DT.REGISTER:    BITS.B16,
    DT.REGISTERMEM: BITS.B16,
}
@dataclass
class Reg:
    used: bool = field(default = False)
    DType: DT = field(default = DT.IMMEDIATE)
    refCount: int = field(default = 0)
@dataclass
class asmData:
    data: str | int
    datatype: DT
    bits: BITS
    refCount: int = field(default = 0)
    isReg: bool = field(default = False)

def resAD(src: asmData, flags: GENASMF = GENASMF(0), forceSelf = False, forceB16 = False) -> str:
    if src.data in regToId.keys():
        src.data = regToId[src.data]
        n = dosDTSex[src.datatype] if not forceB16 else 16
        match n:
            case 8:
                return b8tupleh[src.data] if GENASMF.FH in flags else b8tuplel[src.data]
            case 16:
                return b16tuple[src.data]
            case _:
                error(Error.COMPILE, "resAD, unimplemented BITS WIDTH")
    if src.isReg:
        n = dosDTSex[src.datatype] if not forceB16 else 16
        match n:
            case 8:
                return b8tupleh[src.data] if GENASMF.FH in flags else b8tuplel[src.data]
            case 16:
                return b16tuple[src.data]
            case _:
                error(Error.COMPILE, "resAD, unimplemented BITS WIDTH")
    return f'[{src.data}]' if not forceSelf else src.data

def deref(regs: tuple[Reg,Reg,Reg,Reg,Reg,Reg,Reg,Reg], src: asmData) -> tuple[tuple[Reg,Reg,Reg,Reg,Reg,Reg,Reg,Reg], str, asmData]:
    
    ret: str = ''
    if src.refCount == 0:
        return (regs, ret, src)
    if src.refCount == -1 and not src.isReg:
        return (regs, ret, src)
    if src.refCount < 0:
        ret += f"\tmov si, {resAD(src, forceB16 = True)}\n"
        regs[7].DType = src.datatype
        regs[7].used = True
        src = asmData(7, src.datatype, src.bits, src.refCount+1, isReg = True)
        if src.refCount != 0:
            (regs, rett, src) = deref(regs, src)
            ret += rett
        return (regs, ret, src)
    else:
        ret += f"\tmov si, offset {resAD(src, forceSelf = True)}\n"
        regs[7].DType = src.datatype
        regs[7].used = True
        src = asmData(7, src.datatype, src.bits, src.refCount-1, isReg = True)
        if src.refCount != 0:
            (regs, rett, src) = deref(regs, src)
            ret += rett
        return (regs, ret, src)

def genAsm(op: str, regs: tuple[Reg,Reg,Reg,Reg,Reg,Reg,Reg,Reg], dest: asmData | None, src: asmData, flags: GENASMF = GENASMF(0)) -> tuple[tuple[Reg,Reg,Reg,Reg,Reg,Reg,Reg,Reg], str]:
    ret: str = ""
    if GENASMF.SV in flags:
        if GENASMF.B8 in flags:
            if GENASMF.PD in flags or True: # Currently unused flag (have to think about it more)
                match src.datatype:
                    case DT.UINT8 | DT.UINT16:
                        (regs, rett, src) = deref(regs, src)
                        ret += rett
                        ret += f"\t{op} byte {resAD(src)}\n"
                    case DT.UINT8MEM | DT.UINT16MEM:
                        (regs, rett, src) = deref(regs, src)
                        ret += rett
                        if not src.isReg:
                            ret += f"\tmov {b16tuple[7]}, offset {resAD(src)}\n"
                            ret += f"\t{op} byte [{b16tuple[7]}]\n"
                        else:
                            ret += f"\t{op} byte {resAD(src)}\n"
                        regs[7].used = True
                    case DT.IMMEDIATE:
                        ret += f"\tmov {b8tuplel[3]}, {cutNumToBit(src.data, BITS.B8)}\n"
                        ret += f"\t{op} {b8tuplel[3]}\n"
                    case DT.REGISTER:
                        ret += f"\t{op} {b8tupleh[src.data] if GENASMF.FH in flags else b8tuplel[src.data]}\n"
                    case DT.REGISTERMEM:
                        if not src.data == 7:
                            #error(Error.COMPILE, f"Writing `si` register into `si` register", flags = LogFlag.WARNING)
                            ret += f"\tmov {b16tuple[7]}, {b16tuple[src.data]}\n"
                        ret += f"\t{op} byte [{b16tuple[7]}]\n"
                        regs[7].used = True
                    case _:
                        error(Error.COMPILE, f"Unknown datatype for generating assembly", flags = LogFlag.FAIL)
        elif GENASMF.B16 in flags:
            if GENASMF.PD in flags or True: # Currently unused flag (have to think about it more)
                match src.datatype:
                    case DT.UINT8 | DT.UINT16:
                        (regs, rett, src) = deref(regs, src)
                        ret += rett
                        ret += f"\t{op} word {resAD(src)}\n"
                    case DT.UINT8MEM | DT.UINT16MEM:
                        (regs, rett, src) = deref(regs, src)
                        ret += rett
                        if not src.isReg:
                            ret += f"\tmov {b16tuple[7]}, offset {resAD(src)}\n"
                            ret += f"\t{op} word [{b16tuple[7]}]\n"
                        else:
                            ret += f"\t{op} word {resAD(src)}\n"
                        regs[7].used = True
                    case DT.IMMEDIATE:
                        ret += f"\tmov {b16tuple[3]}, {cutNumToBit(src.data, BITS.B16)}\n"
                        ret += f"\t{op} word {b16tuple[3]}\n"
                        regs[3].used = True
                    case DT.REGISTER:
                        ret += f"\t{op} {b16tuple[src.data]}\n"
                    case DT.REGISTERMEM:
                        if not src.data == 7:
                            #error(Error.COMPILE, f"Writing `si` register into `si` register", flags = LogFlag.WARNING)
                            ret += f"\tmov {b16tuple[7]}, {b16tuple[src.data]}\n"
                        ret += f"\t{op} word [{b16tuple[7]}]\n"
                        regs[7].used = True
        else:
            if GENASMF.PD in flags or True: # Currently unused flag (have to think about it more)
                match src.datatype:
                    case DT.UINT8 | DT.UINT8MEM | DT.UINT16 | DT.UINT16MEM:
                        (regs, rett, src) = deref(regs, src)
                        ret += rett
                        ret += f"\t{op} {resAD(src)}\n"
                    case DT.IMMEDIATE:
                        ret += f"\tmov {b16tuple[3]}, {src.data}\n"
                        ret += f"\t{op} {b16tuple[3]}\n"
                        regs[3].used = True
                    case DT.REGISTER:
                        ret += f"\t{op} {b16tuple[src.data]}\n"
                    case DT.REGISTERMEM:
                        if not src.data == 7:
                            #error(Error.COMPILE, f"Writing `si` register into `si` register", flags = LogFlag.WARNING)
                            ret += f"\tmov {b16tuple[7]}, {b16tuple[src.data]}\n"
                        ret += f"\t{op} [{b16tuple[7]}]\n"
                        regs[7].used = True
    else:
        if dest.datatype == DT.IMMEDIATE:
            error(Error.COMPILE, f"Immediate value as destination! | dest = {dest} | src = {src}", flags = LogFlag.FAIL)
        if GENASMF.CD in flags:
            match dest.datatype:
                case DT.UINT8 | DT.UINT8MEM | DT.UINT16 | DT.UINT16MEM:
                    ret += f"\tmov [{dest.data}], 0\n"
                case DT.REGISTER:
                    ret += f"\txor {b16tuple[dest.data]}, {b16tuple[dest.data]}\n"
                case DT.REGISTERMEM:
                    ret += f"\tmov {b16tuple[6]}, {b16tuple[dest.data]}\n"
                    ret += f"\tmov [{b16tuple[6]}], 0"

        if GENASMF.B8 in flags:
            if GENASMF.PD in flags or True: # Currently unused flag (have to think about it more)
                match src.datatype:
                    case DT.UINT8 | DT.UINT16 | DT.UINT8MEM | DT.UINT16MEM:
                        (regs, rett, src) = deref(regs, src)
                        ret += rett
                        match dest.datatype:
                            case DT.UINT8 | DT.UINT16 | DT.UINT8MEM | DT.UINT16MEM:
                                ret += f"\t{op} {b16tuple[6]}, offset {dest.data}\n"
                                if not src.isReg:
                                    ret += f"\t{op} {b16tuple[7]}, offset {src.data}\n"
                                else:
                                    pass
                                if op == 'mov':
                                    ret += "\tmovs\n"
                                else:
                                    ret += f"\t{op} byte [{b16tuple[6]}], byte [{b16tuple[7]}]\n"
                            case DT.REGISTER:
                                ret += f"\t{op} {b8tupleh[dest.data] if GENASMF.FH in flags else b8tuplel[dest.data]}, byte [{resAD(src)}]\n"
                                regs[dest.data].DType = src.datatype
                                regs[dest.data].used = GENASMF.FH in flags
                            case DT.REGISTERMEM:
                                if dest.data != 6:
                                    ret += f"\tmov {b16tuple[6]}, {b16tuple[dest.data]}\n"
                                ret += f"\tmov {b16tuple[7]}, offset {src.data}\n"
                                ret += f"\t{op} byte [{b16tuple[6]}], byte [{b16tuple[7]}]\n"
                    case DT.IMMEDIATE:
                        match dest.datatype:
                            case DT.UINT8 | DT.UINT16 | DT.UINT8MEM | DT.UINT16MEM:
                                ret += f"\t{op} {b16tuple[6]}, offset {dest.data}\n"
                                ret += f"\t{op} byte [{b16tuple[6]}], {cutNumToBit(src.data, BITS.B8)}\n"
                            case DT.REGISTER:
                                ret += f"\t{op} {b8tupleh[dest.data] if GENASMF.FH in flags else b8tuplel[dest.data]}, {cutNumToBit(src.data, BITS.B8)}\n"
                                regs[dest.data].DType = src.datatype
                                regs[dest.data].used = GENASMF.FH in flags
                            case DT.REGISTERMEM:
                                if dest.data != 6:
                                    ret += f"\tmov {b16tuple[6]}, {b16tuple[dest.data]}\n"
                                ret += f"\t{op} byte [{b16tuple[6]}], {cutNumToBit(src.data, BITS.B8)}\n"
                    case DT.REGISTER:
                        match dest.datatype:
                            case DT.UINT8 | DT.UINT16 | DT.UINT8MEM | DT.UINT16MEM:
                                ret += f"\t{op} {b16tuple[6]}, offset {dest.data}\n"
                                ret += f"\t{op} byte [{b16tuple[6]}], {b8tupleh[src.data] if GENASMF.FH in flags else b8tuplel[src.data]}\n"
                            case DT.REGISTER:
                                ret += f"\t{op} {b8tupleh[dest.data] if GENASMF.FH in flags else b8tuplel[dest.data]}, {b8tupleh[dest.data] if GENASMF.FH in flags else b8tuplel[dest.data]}\n"
                                regs[dest.data].DType = src.datatype
                                regs[dest.data].used = GENASMF.FH in flags
                            case DT.REGISTERMEM:
                                if dest.data != 6:
                                    ret += f"\tmov {b16tuple[6]}, {b16tuple[dest.data]}\n"
                                ret += f"\t{op} byte [{b16tuple[6]}], {b8tupleh[dest.data] if GENASMF.FH in flags else b8tuplel[dest.data]}\n"
                    case DT.REGISTERMEM:
                        match dest.datatype:
                            case DT.UINT8 | DT.UINT16 | DT.UINT8MEM | DT.UINT16MEM:
                                if src.data != 7:
                                    ret += f"\tmov {b16tuple[7]}, {b16tuple[src.data]}\n"
                                ret += f"\t{op} {b16tuple[6]}, offset {dest.data}\n"
                                ret += f"\t{op} byte [{b16tuple[6]}], byte [{b16tuple[7]}]\n"
                            case DT.REGISTER:
                                if src.data != 7:
                                    ret += f"\tmov {b16tuple[7]}, {b16tuple[src.data]}\n"
                                ret += f"\t{op} {b8tupleh[dest.data] if GENASMF.FH in flags else b8tuplel[dest.data]}, byte [{b16tuple[7]}]\n"
                                regs[dest.data].DType = src.datatype
                                regs[dest.data].used = GENASMF.FH in flags
                            case DT.REGISTERMEM:
                                if src.data != 7:
                                    ret += f"\tmov {b16tuple[7]}, {b16tuple[src.data]}\n"
                                if dest.data != 6:
                                    ret += f"\tmov {b16tuple[6]}, {b16tuple[dest.data]}\n"
                                ret += f"\t{op} byte [{b16tuple[6]}], byte [{b16tuple[7]}]\n"
                    case _:
                        error(Error.COMPILE, f"Unknown datatype for generating assembly", flags = LogFlag.FAIL)
        elif GENASMF.B16 in flags:
            if GENASMF.PD in flags or True: # Currently unused flag (have to think about it more)
                match src.datatype:
                    case DT.UINT8 | DT.UINT8MEM:
                        (regs, rett, src) = deref(regs, src)
                        ret += rett
                        match dest.datatype:
                            case DT.UINT8 | DT.UINT8MEM:
                                ret += f"\t{op} {b16tuple[6]}, offset {dest.data}\n"
                                if not src.isReg:
                                    ret += f"\t{op} {b16tuple[7]}, offset {src.data}\n"
                                else:
                                    pass
                                if op == 'mov':
                                    ret += "\tmovsb\n"
                                else:
                                    ret += f"\t{op} byte [{b16tuple[6]}], byte [{b16tuple[7]}]\n"
                            case DT.UINT16 | DT.UINT16MEM:
                                ret += f"\t{op} {b16tuple[6]}, offset {dest.data}\n"
                                if not src.isReg:
                                    ret += f"\t{op} {b16tuple[7]}, offset {src.data}\n"
                                else:
                                    pass
                                ret += f"\t{op} {b16tuple[7]}, offset {src.data}\n"
                                if op == 'mov':
                                    ret += "\tmovsb\n"
                                else:
                                    ret += f"\t{op} word [{b16tuple[6]}], byte [{b16tuple[7]}]\n"
                            case DT.REGISTER:
                                ret += f"\t{op} {b16tuple[dest.data]}, byte [{resAD(src)}]\n"
                                regs[dest.data].DType = src.datatype
                                regs[dest.data].used = True
                            case DT.REGISTERMEM:
                                if dest.data != 6:
                                    ret += f"\tmov {b16tuple[6]}, {b16tuple[dest.data]}\n"
                                ret += f"\tmov {b16tuple[7]}, offset {src.data}\n"
                                ret += f"\t{op} word [{b16tuple[6]}], byte [{b16tuple[7]}]\n"
                    case DT.UINT16 | DT.UINT16MEM:
                        match dest.datatype:
                            case DT.UINT8 | DT.UINT8MEM:
                                ret += f"\t{op} {b16tuple[6]}, offset {dest.data}\n"
                                if not src.isReg:
                                    ret += f"\t{op} {b16tuple[7]}, offset {src.data}\n"
                                else:
                                    pass
                                ret += f"\t{op} {b16tuple[7]}, offset {src.data}\n"
                                if op == 'mov':
                                    ret += "\tmovsb\n"
                                else:
                                    ret += f"\t{op} byte [{b16tuple[6]}], byte [{b16tuple[7]}]\n"
                            case DT.UINT16 | DT.UINT16MEM:
                                ret += f"\t{op} {b16tuple[6]}, offset {dest.data}\n"
                                if not src.isReg:
                                    ret += f"\t{op} {b16tuple[7]}, offset {src.data}\n"
                                else:
                                    pass
                                ret += f"\t{op} {b16tuple[7]}, offset {src.data}\n"
                                if op == 'mov':
                                    ret += "\tmovsw\n"
                                else:
                                    ret += f"\t{op} word [{b16tuple[6]}], word [{b16tuple[7]}]\n"
                            case DT.REGISTER:
                                ret += f"\t{op} {b16tuple[dest.data]}, word [{resAD(src)}]\n"
                                regs[dest.data].DType = src.datatype
                                regs[dest.data].used = True
                            case DT.REGISTERMEM:
                                if dest.data != 6:
                                    ret += f"\tmov {b16tuple[6]}, {b16tuple[dest.data]}\n"
                                ret += f"\tmov {b16tuple[7]}, offset {src.data}\n"
                                ret += f"\t{op} word [{b16tuple[6]}], word [{b16tuple[7]}]\n"
                    case DT.IMMEDIATE:
                        match dest.datatype:
                            case DT.UINT8 | DT.UINT8MEM:
                                ret += f"\t{op} byte [{dest.data}], {cutNumToBit(src.data, BITS.B8)}\n"
                            case DT.UINT16 | DT.UINT16MEM:
                                    ret += f"\t{op} word [{dest.data}], {cutNumToBit(src.data, BITS.B16)}\n"
                            case DT.REGISTER:
                                ret += f"\t{op} {b16tuple[dest.data]}, {cutNumToBit(src.data, BITS.B16)}\n"
                                regs[dest.data].used = True
                            case DT.REGISTERMEM:
                                if dest.data != 6:
                                    ret += f"\tmov {b16tuple[6]}, {b16tuple[dest.data]}\n"
                                ret += f"\t{op} word [{b16tuple[6]}], {cutNumToBit(src.data, BITS.B16)}\n"
                    case DT.REGISTER:
                        match dest.datatype:
                            case DT.UINT8 | DT.UINT8MEM:
                                ret += f"\t{op} byte [{dest.data}], {b16tuple[src.data]}\n"
                            case DT.UINT16 | DT.UINT16MEM:
                                    ret += f"\t{op} word [{dest.data}], {b16tuple[src.data]}\n"
                            case DT.REGISTER:
                                ret += f"\t{op} {b16tuple[dest.data]}, {b16tuple[src.data]}\n"
                                regs[dest.data].DType = src.datatype
                                regs[dest.data].used = True
                            case DT.REGISTERMEM:
                                if dest.data != 6:
                                    ret += f"\tmov {b16tuple[6]}, {b16tuple[dest.data]}\n"
                                ret += f"\t{op} word [{b16tuple[6]}], {b16tuple[src.data]}\n"
                    case DT.REGISTERMEM:
                        match dest.datatype:
                            case DT.UINT8 | DT.UINT8MEM:
                                ret += f"\t{op} {b16tuple[6]}, offset {dest.data}\n"
                                ret += f"\t{op} {b16tuple[7]}, {b16tuple[src.data]}\n"
                                if op == 'mov':
                                    ret += "\tmovsb\n"
                                else:
                                    ret += f"\t{op} byte [{b16tuple[6]}], byte [{b16tuple[7]}]\n"
                            case DT.UINT16 | DT.UINT16MEM:
                                ret += f"\t{op} {b16tuple[6]}, offset {dest.data}\n"
                                ret += f"\t{op} {b16tuple[7]}, {b16tuple[src.data]}\n"
                                if op == 'mov':
                                    ret += "\tmovsb\n"
                                else:
                                    ret += f"\t{op} word [{b16tuple[6]}], word [{b16tuple[7]}]\n"
                            case DT.REGISTER:
                                ret += f"\t{op} {b16tuple[7]}, {b16tuple[src.data]}\n"
                                ret += f"\t{op} {b16tuple[dest.data]}, word [{b16tuple[7]}]\n"
                                regs[dest.data].DType = src.datatype
                                regs[dest.data].used = True
                            case DT.REGISTERMEM:
                                if src.data != 7:
                                    ret += f"\tmov {b16tuple[7]}, {b16tuple[src.data]}\n"
                                if dest.data != 6:
                                    ret += f"\tmov {b16tuple[6]}, {b16tuple[dest.data]}\n"
                                ret += f"\t{op} word [{b16tuple[6]}], word [{b16tuple[7]}]\n"
                    case _:
                        error(Error.COMPILE, f"Unknown datatype for generating assembly", flags = LogFlag.FAIL)
        else:
            if GENASMF.PD in flags or True: # Currently unused flag (have to think about it more)
                match src.datatype:
                    case DT.UINT8:
                        (regs, rett, src) = deref(regs, src)
                        ret += rett
                        match dest.datatype:
                            case DT.UINT8 | DT.UINT8MEM:
                                ret += f"\t{op} {b16tuple[6]}, offset {dest.data}\n"
                                if not src.isReg:
                                    ret += f"\t{op} {b16tuple[7]}, offset {src.data}\n"
                                else:
                                    pass
                                if op == 'mov':
                                    ret += "\tmovsb\n"
                                else:
                                    ret += f"\t{op} byte [{b16tuple[6]}], byte [{b16tuple[7]}]\n"
                            case DT.UINT16 | DT.UINT16MEM:
                                if dest.refCount != 0:
                                    ret += f"\t{op} {b16tuple[6]}, word [{dest.data}]\n"
                                else:
                                    ret += f"\t{op} {b16tuple[6]}, offset {dest.data}\n"
                                if not src.isReg:
                                    ret += f"\t{op} {b16tuple[7]}, offset {src.data}\n"
                                else:
                                    pass
                                ret += f"\t{op} {b16tuple[7]}, offset {src.data}\n"
                                if op == 'mov':
                                    ret += "\tmovsb\n"
                                else:
                                    ret += f"\t{op} word [{b16tuple[6]}], byte [{b16tuple[7]}]\n"
                            case DT.REGISTER:
                                #if regs[dest.data].used:
                                    #ret += f"\txor {b16tuple[dest.data]}, {b16tuple[dest.data]}\n"
                                if src.isReg:
                                    ret += f"\t{op} {b8tuplel[dest.data]}, {resAD(src)}\n"
                                else:
                                    ret += f"\t{op} {b8tuplel[dest.data]}, byte {resAD(src)}\n"
                                regs[dest.data].DType = src.datatype
                                regs[dest.data].used = True
                            case DT.REGISTERMEM:
                                if dest.data != 6:
                                    ret += f"\tmov {b16tuple[6]}, {b16tuple[dest.data]}\n"
                                ret += f"\tmov {b16tuple[7]}, offset {src.data}\n"
                                ret += f"\t{op} {'word' if dest.bits > 8 else 'byte'} [{b16tuple[6]}], byte [{b16tuple[7]}]\n"
                    case DT.UINT8MEM:
                        (regs, rett, src) = deref(regs, src)
                        ret += rett
                        match dest.datatype:
                            case DT.UINT8 | DT.UINT8MEM:
                                ret += f"\t{op} {b16tuple[6]}, offset {dest.data}\n"
                                if not src.isReg:
                                    ret += f"\t{op} {b16tuple[7]}, offset {src.data}\n"
                                else:
                                    pass
                                if op == 'mov':
                                    ret += "\tmovsb\n"
                                else:
                                    ret += f"\t{op} byte [{b16tuple[6]}], byte [{b16tuple[7]}]\n"
                            case DT.UINT16 | DT.UINT16MEM:
                                ret += f"\t{op} {b16tuple[6]}, offset {dest.data}\n"
                                if not src.isReg:
                                    ret += f"\t{op} {b16tuple[7]}, offset {src.data}\n"
                                else:
                                    pass
                                ret += f"\t{op} word [{b16tuple[6]}], {b16tuple[7]}\n"
                            case DT.REGISTER:
                                if not src.isReg:
                                    ret += f"\t{op} {b16tuple[dest.data]}, offset {src.data}\n"
                                else:
                                    ret += f"\t{op} {b16tuple[dest.data]}, {resAD(src)}\n"
                                regs[dest.data].DType = src.datatype
                                regs[dest.data].used = True
                            case DT.REGISTERMEM:
                                if dest.data != 6:
                                    ret += f"\tmov {b16tuple[6]}, {b16tuple[dest.data]}\n"
                                ret += f"\tmov {b16tuple[7]}, offset {src.data}\n"
                                ret += f"\t{op} {'word' if dest.bits > 8 else 'byte'} [{b16tuple[6]}], {b16tuple[7]}\n"
                    case DT.UINT16:
                        (regs, rett, src) = deref(regs, src)
                        ret += rett
                        match dest.datatype:
                            case DT.UINT8 | DT.UINT8MEM:
                                ret += f"\t{op} {b16tuple[6]}, offset {dest.data}\n"
                                if not src.isReg:
                                    ret += f"\t{op} {b16tuple[7]}, offset {src.data}\n"
                                else:
                                    pass
                                if op == 'mov':
                                    ret += "\tmovsb\n"
                                else:
                                    ret += f"\t{op} byte [{b16tuple[6]}], byte [{b16tuple[7]}]\n"
                            case DT.UINT16 | DT.UINT16MEM:
                                ret += f"\t{op} {b16tuple[6]}, offset {dest.data}\n"
                                if not src.isReg:
                                    ret += f"\t{op} {b16tuple[7]}, offset {src.data}\n"
                                else:
                                    pass
                                ret += f"\t{op} word [{b16tuple[6]}], {b16tuple[7]}\n"
                            case DT.REGISTER:
                                print(src.data)
                                if src.isReg:
                                    ret += f"\t{op} {b16tuple[dest.data]}, {resAD(src)}\n"
                                else:
                                    ret += f"\t{op} {b16tuple[dest.data]}, word {resAD(src)}\n"
                                regs[dest.data].DType = src.datatype
                                regs[dest.data].used = True
                            case DT.REGISTERMEM:
                                if dest.data != 6:
                                    ret += f"\tmov {b16tuple[6]}, {b16tuple[dest.data]}\n"
                                ret += f"\tmov {b16tuple[7]}, offset {src.data}\n"
                                ret += f"\t{op} {'word' if dest.bits > 8 else 'byte'} [{b16tuple[6]}], [{b16tuple[7]}]\n"
                    case DT.UINT16MEM:
                        (regs, rett, src) = deref(regs, src)
                        ret += rett
                        match dest.datatype:
                            case DT.UINT8 | DT.UINT8MEM:
                                ret += f"\t{op} {b16tuple[6]}, offset {dest.data}\n"
                                if not src.isReg:
                                    ret += f"\t{op} {b16tuple[7]}, offset {src.data}\n"
                                else:
                                    pass
                                if op == 'mov':
                                    ret += "\tmovsb\n"
                                else:
                                    ret += f"\t{op} byte [{b16tuple[6]}], byte [{b16tuple[7]}]\n"
                            case DT.UINT16 | DT.UINT16MEM:
                                ret += f"\t{op} {b16tuple[6]}, offset {dest.data}\n"
                                if not src.isReg:
                                    ret += f"\t{op} {b16tuple[7]}, offset {src.data}\n"
                                else:
                                    pass
                                ret += f"\t{op} word [{b16tuple[6]}], word {b16tuple[7]}\n"
                            case DT.REGISTER:
                                if not src.isReg:
                                    ret += f"\t{op} {b16tuple[dest.data]}, offset {src.data}\n"
                                else:
                                    ret += f"\t{op} {b16tuple[dest.data]}, word [{resAD(src)}]\n"
                                regs[dest.data].DType = src.datatype
                                regs[dest.data].used = True
                            case DT.REGISTERMEM:
                                if dest.data != 6:
                                    ret += f"\tmov {b16tuple[6]}, {b16tuple[dest.data]}\n"
                                ret += f"\tmov {b16tuple[7]}, offset {src.data}\n"
                                ret += f"\t{op} {'word' if dest.bits > 8 else 'byte'} [{b16tuple[6]}], {b16tuple[7]}\n"
                    case DT.IMMEDIATE:
                        match dest.datatype:
                            case DT.UINT8 | DT.UINT8MEM:
                                ret += f"\t{op} byte [{dest.data}], {cutNumToBit(src.data, BITS.B8)}\n"
                            case DT.UINT16 | DT.UINT16MEM:
                                if dest.refCount != 0:
                                    ret += f"\t{op} {b16tuple[6]}, [{dest.data}]\n"
                                else:
                                    ret += f"\t{op} {b16tuple[6]}, offset {dest.data}\n"
                                ret += f"\t{op} word ptr [{b16tuple[6]}], {cutNumToBit(src.data, BITS.B16)}\n"
                            case DT.REGISTER:
                                ret += f"\t{op} {b16tuple[dest.data]}, {cutNumToBit(src.data, BITS.B16)}\n"
                                regs[dest.data].DType = src.datatype
                                regs[dest.data].used = True
                            case DT.REGISTERMEM:
                                if dest.data != 6:
                                    ret += f"\tmov {b16tuple[6]}, {b16tuple[dest.data]}\n"
                                ret += f"\t{op} {'word' if dest.bits > 8 else 'byte'} [{b16tuple[6]}], {cutNumToBit(src.data, BITS.B16 if dest.bits > 8 else BITS.B8)}\n"
                    case DT.REGISTER:
                        srcVar = b16tuple[src.data] if src.bits == BITS.B16 else b8tupleh[src.data] if GENASMF.FH in flags else b8tuplel[src.data]
                        (regs, rett, src) = deref(regs, asmData(srcVar, regs[src.data].DType, src.bits, src.refCount, src.isReg))
                        print(src, srcVar)
                        ret += rett
                        match dest.datatype:
                            case DT.UINT8 | DT.UINT8MEM:
                                ret += f"\t{op} byte [{dest.data}], {b8tuplel[regToId[src.data]]}\n"
                            case DT.UINT16 | DT.UINT16MEM:
                                    ret += f"\t{op} word [{dest.data}], {b16tuple[regToId[src.data]]}\n"
                            case DT.REGISTER:
                                destVar = b16tuple[dest.data] if (dosDTSex[src.datatype] == BITS.B16) else b8tupleh[dest.data] if GENASMF.FH in flags else b8tuplel[dest.data]
                                #(regs, retd, ndest) = deref(regs, asmData(destVar, regs[dest.data].DType, dosDTSex[regs[regToId[resAD(src)]].DType], regs[dest.data].refCount))
                                #ret += retd
                                if rett:
                                    ret += f"\t{op} {destVar},{'' if dosDTS[regs[regToId[resAD(src)]].DType] > 8 else ' byte'} [{resAD(src)}]\n"
                                else:
                                    ret += f"\t{op} {destVar}, {resAD(src)}\n"
                                regs[regToId[destVar]].DType = src.datatype
                                regs[regToId[destVar]].used = True
                            case DT.REGISTERMEM:
                                if dest.data != 6:
                                    ret += f"\tmov {b16tuple[6]}, {resAD(src)}\n"
                                ret += f"\t{op} {'word' if dest.bits > 8 else 'byte'} [{b16tuple[6]}], {resAD(src)}\n"
                    case DT.REGISTERMEM:
                        match dest.datatype:
                            case DT.UINT8 | DT.UINT8MEM:
                                ret += f"\t{op} {b16tuple[6]}, offset {dest.data}\n"
                                ret += f"\t{op} {b16tuple[7]}, {b16tuple[src.data]}\n"
                                if op == 'mov':
                                    ret += "\tmovsb\n"
                                else:
                                    ret += f"\t{op} byte [{b16tuple[6]}], byte [{b16tuple[7]}]\n"
                            case DT.UINT16 | DT.UINT16MEM:
                                ret += f"\t{op} {b16tuple[6]}, offset {dest.data}\n"
                                ret += f"\t{op} {b16tuple[7]}, {b16tuple[src.data]}\n"
                                ret += f"\t{op} word [{b16tuple[6]}], {b16tuple[7]}\n"
                            case DT.REGISTER:
                                ret += f"\t{op} {b16tuple[7]}, {b16tuple[src.data]}\n"
                                ret += f"\t{op} {b16tuple[dest.data]}, byte [{b16tuple[7]}]\n"
                                regs[dest.data].DType = src.datatype
                                regs[dest.data].used = True
                            case DT.REGISTERMEM:
                                if src.data != 7:
                                    ret += f"\tmov {b16tuple[7]}, {b16tuple[src.data]}\n"
                                if dest.data != 6:
                                    ret += f"\tmov {b16tuple[6]}, {b16tuple[dest.data]}\n"
                                ret += f"\t{op} {'word' if dest.bits > 8 else 'byte'} [{b16tuple[6]}], {b16tuple[7]}\n"
                    case _:
                        error(Error.COMPILE, f"Unknown datatype for generating assembly", flags = LogFlag.FAIL)
    return (regs, ret)

def compile_data(data: list[dict]) -> None:

    if (n:=OP.COUNT.value) != (m:=37):
        error(Error.ENUM, f"{BOLD_}Exhaustive operation parsing protection in {BOLD_}compile_data{BACK_}", expected = (m,n), flags = LogFlag.FAIL | LogFlag.EXPECTED)
    
    stack: list[asmData] = []
    ip = 0
    state: ComState = ComState.NONE
    temp1: str = ""
    condition: OP
    
    buffor_start: str = ""
    buffor_data: str = ""
    buffor_code: str = ""

    ax: Reg = Reg()
    bx: Reg = Reg()
    cx: Reg = Reg()
    dx: Reg = Reg()
    di: Reg = Reg()
    si: Reg = Reg()
    bp: Reg = Reg()
    sp: Reg = Reg()
    
    ar_len: int = 0
    
    if Com_Mode == COMMODE.LINUX:
        buffor_start = buffor_start + "format ELF64 executable 3\nsegment readable executable\n"
        buffor_code = buffor_code + "entry main\nmain\n"
        for x in data:
            match x.type:
                case OP.NUM:
                    stack.append(int(x.value))
                case OP.ADD:
                    pass
                case OP.COLON:
                    pass
    elif Com_Mode == COMMODE.DOS:
        buffor_start = buffor_start + ".MODEL SMALL\n.STACK 100h\n"
        buffor_data = buffor_data + ".DATA\n"
        buffor_code = buffor_code + ".CODE\nstart:\n\tmov ax, @data\n\tmov ds, ax\n"

        for ip, x in enumerate(data.tokens):
            regs = (ax, bx, cx, dx, di, si, bp, sp)
            match x.type:
                case OP.NUM:
                    stack.append(asmData(int(x.value), DT.IMMEDIATE, BITS.B16))
                case OP.STRING:
                    if ComState.VARDEF in state:
                        
                        match data.vars[temp1].type:
                            case DT.UINT8MEM:
                                while (n:=x.value).find('\n') != -1:
                                    (string_before, string_center, string_after) = x.value.partition('\n')
                                    x.value = f"{string_before}\", 10,\"{string_after}"
                                buffor_data = buffor_data + f"\t{data.vars[temp1].name} db \"{x.value}$\"\n"
                            case DT.UINT16MEM:
                                while (n:=x.value).find('\n') != -1:
                                    (string_before, string_center, string_after) = x.value.partition('\n')
                                    x.value = f"{string_before}\", 10,\"{string_after}"
                                buffor_data = buffor_data + f"\t{data.vars[temp1].name} dw \"{x.value}$\"\n"
                        state = ComState.NONE
                    else:
                        stack.append(asmData(data.vars[temp1].name, (n:=data.vars[temp1].type), dosDTS[n]))
                case OP.ADD:
                    buffor_code = buffor_code + ";; -- ADD --\n"
                    if len(stack) > 0:
                        a = stack.pop()
                        if not ax.used:
                            b = stack.pop()
                            (regs, op) = genAsm('mov', regs, asmData(0, DT.REGISTER, BITS.B16), b)
                            buffor_code += op
                        (regs, op) = genAsm('add', regs, asmData(0, DT.REGISTER, BITS.B16), a)
                        buffor_code += op
                    else:
                        error(Error.COMPILE, "Not enough arguments in arithmetics", flags = LogFlag.FAIL)
                case OP.SUB:
                    buffor_code = buffor_code + ";; -- SUB --\n"
                    if len(stack) > 0:
                        a = stack.pop()
                        if not ax.used:
                            b = stack.pop()
                            (regs, op) = genAsm('mov', regs, asmData(0, DT.REGISTER, BITS.B16), b)
                            buffor_code += op
                        (regs, op) = genAsm('sub', regs, asmData(0, DT.REGISTER, BITS.B16), a)
                        buffor_code += op
                    else:
                        error(Error.COMPILE, "Not enough arguments in arithmetics", flags = LogFlag.FAIL)
                case OP.MUL:
                    buffor_code = buffor_code + ";; -- MUL --\n"
                    if len(stack) > 0:
                        a = stack.pop()
                        if not ax.used:
                            b = stack.pop()
                            (regs, op) = genAsm('mov', regs, asmData(0, DT.REGISTER, BITS.B16), b)
                            buffor_code += op
                        (regs, op) = genAsm('mul', regs, asmData(0, DT.REGISTER, BITS.B16), a, flags = GENASMF.SV | GENASMF.B8)
                        buffor_code += op
                    else:
                        error(Error.COMPILE, "Not enough arguments in arithmetics", flags = LogFlag.FAIL)
                case OP.DIV:
                    buffor_code = buffor_code + ";; -- DIV --\n"
                    if len(stack) > 0:
                        a = stack.pop()
                        if not ax.used:
                            b = stack.pop()
                            (regs, op) = genAsm('mov', regs, asmData(0, DT.REGISTER, BITS.B16), b)
                            buffor_code += op
                        (regs, op) = genAsm('div', regs, asmData(0, DT.REGISTER, BITS.B16), a, flags = GENASMF.SV | GENASMF.B8)
                        buffor_code += op
                        buffor_code += f"\txor ah, ah\n"
                    else:
                        error(Error.COMPILE, "Not enough arguments in arithmetics", flags = LogFlag.FAIL)
                case OP.MOD:
                    buffor_code = buffor_code + ";; -- MOD --\n"
                    if len(stack) > 0:
                        a = stack.pop()
                        if not ax.used:
                            b = stack.pop()
                            (regs, op) = genAsm('mov', regs, asmData(0, DT.REGISTER, BITS.B16), b)
                            buffor_code += op
                        (regs, op) = genAsm('div', regs, asmData(0, DT.REGISTER, BITS.B16), a, flags = GENASMF.SV | GENASMF.B8)
                        buffor_code += op
                        buffor_code = buffor_code + f"\tmov al, ah\n"
                        buffor_code = buffor_code + f"\txor ah, ah\n"
                    else:
                        error(Error.COMPILE, "Not enough arguments in arithmetics", flags = LogFlag.FAIL)
                case OP.SHL:
                    buffor_code = buffor_code + ";; -- SHL --\n"
                    if len(stack) > 0:
                        a = stack.pop()
                        if not ax.used:
                            b = stack.pop()
                            (regs, op) = genAsm('mov', regs, asmData(0, DT.REGISTER, BITS.B16), b)
                            buffor_code += op
                        if isinstance(a[0], str):
                            (regs, op) = genAsm('mov', regs, asmData(2, DT.REGISTER, BITS.B16), a, flags = GENASMF.B8)
                            buffor_code += op
                            (regs, op) = genAsm('shl', regs, asmData(0, DT.REGISTER, BITS.B16), asmData(2, DT.REGISTER, BITS.B8))
                            buffor_code += op
                        else:
                            (regs, op) = genAsm('shl', regs, asmData(0, DT.REGISTER, BITS.B16), asmData(a.data, a.datatype, BITS.B8, a.refCount))
                            buffor_code += op
                    else:
                        error(Error.COMPILE, "Not enough arguments in arithmetics", flags = LogFlag.FAIL)
                case OP.SHR:
                    buffor_code = buffor_code + ";; -- SHL --\n"
                    if len(stack) > 0:
                        a = stack.pop()
                        if not ax.used:
                            b = stack.pop()
                            (regs, op) = genAsm('mov', regs, asmData(0, DT.REGISTER, BITS.B16), b)
                            buffor_code += op
                        if isinstance(a[0], str):
                            (regs, op) = genAsm('mov', regs, asmData(2, DT.REGISTER, BITS.B16), a, flags = GENASMF.B8)
                            buffor_code += op
                            (regs, op) = genAsm('shr', regs, asmData(0, DT.REGISTER, BITS.B16), asmData(2, DT.REGISTER, BITS.B8))
                            buffor_code += op
                        else:
                            (regs, op) = genAsm('shr', regs, asmData(0, DT.REGISTER, BITS.B16), asmData(a.data, a.datatype, BITS.B8, a.refCount))
                            buffor_code += op
                    else:
                        error(Error.COMPILE, "Not enough arguments in arithmetics", flags = LogFlag.FAIL)
                case OP.PTR:
                    error(Error.COMPILE, "not implemented yet!")
                case OP.IF:
                    buffor_code = buffor_code + ";; -- IF --\n"
                    state = ComState.CONDITION
                case OP.WHILE:
                    buffor_code = buffor_code + ";; -- WHILE --\n"
                    state = ComState.CONDITION
                case OP.EQUAL | OP.GREATER | OP.LESS | OP.GE | OP.LE:
                    if len(stack) == 1:
                        a = stack.pop()
                        (regs, op) = genAsm('mov', regs, asmData(1, DT.REGISTER, dosDTS[a.datatype]), a)
                        buffor_code += op
                    elif len(stack) == 0:
                        (regs, op) = genAsm('mov', regs, asmData(1, DT.REGISTER, BITS.B16), asmData(0, DT.REGISTER, BITS.B16))
                        buffor_code += op
                    else:
                        error(Error.COMPILE, "Unused value or variable in arithmetics", flags = LogFlag.WARNING, exitAfter = False)
                    condition = x.type
                case OP.CONJUMP:
                    if len(stack) == 1:
                        a = stack.pop()
                        (regs, op) = genAsm('mov', regs, asmData(0, DT.REGISTER, BITS.B16), a)
                        buffor_code += op
                    elif len(stack) == 0:
                        pass
                    else:
                        error(Error.COMPILE, "Unfinished arithmetics before conditional jump", flags = LogFlag.WARNING)
                    (regs, op) = genAsm('cmp', regs, asmData(1, DT.REGISTER, BITS.B16, isReg = True), asmData(0, DT.REGISTER, BITS.B16, isReg = True))
                    buffor_code += op
                    state = ComState.NONE
                    match condition:
                        case OP.EQUAL:
                            if ip - int(x.value[5:]) < -30:
                                buffor_code = buffor_code + f"\tje bar{ip}\n"
                                buffor_code = buffor_code + f"\tjmp {x.value}\n"
                                buffor_code = buffor_code + f"bar{ip}:\n"
                            else:
                                buffor_code = buffor_code + f"\tjne {x.value}\n"
                        case OP.GREATER:
                            if ip - int(x.value[5:]) < -30:
                                buffor_code = buffor_code + f"\tjg bar{ip}\n"
                                buffor_code = buffor_code + f"\tjmp {x.value}\n"
                                buffor_code = buffor_code + f"bar{ip}:\n"
                            else:
                                buffor_code = buffor_code + f"\tjle {x.value}\n"
                        case OP.LESS:
                            if ip - int(x.value[5:]) < -30:
                                buffor_code = buffor_code + f"\tjl bar{ip}\n"
                                buffor_code = buffor_code + f"\tjmp {x.value}\n"
                                buffor_code = buffor_code + f"bar{ip}:\n"
                            else:
                                buffor_code = buffor_code + f"\tjge {x.value}\n"
                        case OP.GE:
                            if ip - int(x.value[5:]) < -30:
                                buffor_code = buffor_code + f"\tjge bar{ip}\n"
                                buffor_code = buffor_code + f"\tjmp {x.value}\n"
                                buffor_code = buffor_code + f"bar{ip}:\n"
                            else:
                                buffor_code = buffor_code + f"\tjl {x.value}\n"
                        case OP.LE:
                            if ip - int(x.value[5:]) < -30:
                                buffor_code = buffor_code + f"\tle bar{ip}\n"
                                buffor_code = buffor_code + f"\tjmp {x.value}\n"
                                buffor_code = buffor_code + f"bar{ip}:\n"
                            else:
                                buffor_code = buffor_code + f"\tjg {x.value}\n"
                    for x in range(len(regs)):
                        regs[x].used = False
                        regs[x].DType = DT.IMMEDIATE
                        regs[x].refCount = 0
                case OP.JUMP:
                    buffor_code += f"\tjmp {x.value}\n"
                    state = ComState.NONE
                    for x in range(len(regs)):
                        regs[x].used = False
                        regs[x].DType = DT.IMMEDIATE
                        regs[x].refCount = 0
                case OP.LABEL:
                    buffor_code += f"{x.value}:\n"
                case OP.COPY:
                    error(Error.COMPILE, "COPY: Currently Unsupported!")
                case OP.PRINT:
                    error(Error.COMPILE, "PRINT: Currently Unsupported!")
                case OP.PRINT_NL:
                    error(Error.COMPILE, "PRINT_NL: Currently Unsupported!")
                case OP.PRINT_AND_NL:
                    error(Error.COMPILE, "PRINT_AND_NL: Currently Unsupported!")
                case OP.PRINT_CHAR:
                    error(Error.COMPILE, "PRINT_CHAR: Currently Unsupported!")
                case OP.TYPE:
                    pass
                case OP.BUF:
                    if ComState.VARDEF in state:
                        match data.vars[temp1].type:
                            case DT.UINT8MEM:
                                a = stack.pop()
                                buffor_data = buffor_data + f"\t{data.vars[temp1].name} db {a.data-2},{a.data-1} dup (0)\n"
                            case DT.UINT16MEM:
                                a = stack.pop()
                                buffor_data = buffor_data + f"\t{data.vars[temp1].name} dw {a.data-2},{a.data-1} dup (0)\n"
                        #data.vars[temp1].value
                        state = ComState.NONE
                    else:
                        error(Error.COMPILE, "Buf used in wrong position")
                case OP.VAR:
                    if ComState.ARITHMETIC not in state and ComState.CONDITION not in state:
                        temp1 = x.value[0]
                        if not data.vars[x.value[0]].defined:
                            if x.value[1] != 0:
                                error(Error.COMPILE, "dereferencing or referencing variable in definition", flags = LogFlag.WARNING, exitAfter = False)
                            if data.vars[x.value[0]].type in [DT.UINT8]:
                                buffor_data = buffor_data + f"\t{data.vars[temp1].name} db ?\n"
                            elif data.vars[x.value[0]].type in [DT.UINT16]:
                                buffor_data = buffor_data + f"\t{data.vars[temp1].name} dw ?\n"
                            data.vars[x.value[0]].defined = True
                    stack.append(asmData(data.vars[x.value[0]].name, (n:=data.vars[x.value[0]].type), dosDTS[n], x.value[1]))
                case OP.SET:
                    state = ComState.VARDEF | ComState.ARITHMETIC
                    stack.pop()
                case OP.DOS:
                    a = stack.pop().data
                    if a == 9:
                        buffor_code += ";; -- DOS -- 9 --\n"
                        if len(stack) > 0:
                            b = stack.pop()
                            if isinstance(b.data, str):
                                (regs, op) = genAsm('mov', regs, asmData(3, DT.REGISTER, BITS.B16), b)
                                buffor_code += op
                            else:
                                error(Error.COMPILE, "int type in dos call for address")
                        else:
                            (regs, op) = genAsm('mov', regs, asmData(3, DT.REGISTER, BITS.B16, isReg = True), asmData(0, DT.REGISTER, BITS.B16, isReg = True))
                            buffor_code += op
                        (regs, op) = genAsm('mov', regs, asmData(0, DT.REGISTER, BITS.B8), asmData(9, DT.IMMEDIATE, BITS.B8), flags = GENASMF.FH | GENASMF.B8)
                        buffor_code += op
                        buffor_code += "\tint 21h\n"
                    elif a == 10:
                        buffor_code += ";; -- DOS -- 10 --\n"
                        if len(stack) > 0:
                            b = stack.pop()
                            if isinstance(b.data, str):
                                (regs, op) = genAsm('mov', regs, asmData(3, DT.REGISTER, BITS.B16), b)
                                buffor_code += op
                            else:
                                error(Error.COMPILE, "int type in dos call for address")
                        else:
                            (regs, op) = genAsm('mov', regs, asmData(3, DT.REGISTER, BITS.B16), asmData(0, DT.REGISTER, BITS.B16))
                            buffor_code += op
                        (regs, op) = genAsm('mov', regs, asmData(0, DT.REGISTER, BITS.B8), asmData(10, DT.IMMEDIATE, BITS.B8), flags = GENASMF.FH | GENASMF.B8)
                        buffor_code += op
                        buffor_code += "\tint 21h\n"
                    else:
                        error(Error.SIMULATE, "only 9 and 10 dos calls are implemented yet")
                case OP.MEMWRITE:
                    buffor_code += ";; -- MEMWRITE --\n"
                    if len(stack) == 1:
                        a = stack.pop()
                        (regs, op) = genAsm('mov', regs, asmData(0, DT.REGISTERMEM, BITS.B8), a)
                        buffor_code += op
                    elif len(stack) == 2:
                        a = stack.pop()
                        b = stack.pop()
                        (regs, op) = genAsm('mov', regs, b, a)
                        buffor_code += op
                case OP.MEMREAD:
                    buffor_code += ";; -- MEMREAD --\n"
                    if ax.used:
                        (regs, op) = genAsm('mov', regs, asmData(0, DT.REGISTER, BITS.B16, isReg = True), asmData(0, DT.REGISTER, BITS.B16, refCount = -1, isReg = True))
                        buffor_code += op
                        print(op)
                    elif len(stack) > 0:
                        a = stack.pop()
                        if a.datatype != DT.UINT16MEM and a.datatype != DT.UINT8MEM:
                            error(Error.COMPILE, "Reading from non memory variable")
                        (regs, op) = genAsm('mov', regs, asmData(0, DT.REGISTER, BITS.B16), a)
                        print(op)
                        buffor_code += op
                    else:
                        error(Error.COMPILE, "MEMREAD DEBUG ERROR, UNKNOWN CAUSE")
                        #(regs, op) = genAsm('mov', regs, asmData(0, DT.REGISTER, BITS.B16), asmData(0, DT.REGISTER, BITS.B16))
                        #buffor_code += op
                case OP.COLON:
                    if ComState.VARDEF in state:
                        if len(stack) > 0:
                            a = stack.pop()
                            (regs, op) = genAsm('mov', regs, asmData(data.vars[temp1].name, data.vars[temp1].type, dosDTS[data.vars[temp1].type]), a)
                            buffor_code += op
                        else:
                            (regs, op) = genAsm('mov', regs, asmData(data.vars[temp1].name, data.vars[temp1].type, dosDTS[data.vars[temp1].type]), asmData(0, DT.REGISTER, dosDTS[data.vars[temp1].type]))
                            buffor_code += op
                    state = ComState.NONE
                    for x in range(len(regs)):
                        regs[x].used = False
                        regs[x].DType = DT.IMMEDIATE
                        regs[x].refCount = 0
            (ax, bx, cx, dx, bp, sp, di, si) = regs
            #print(stack, x)
            #print(regs)
            #print(" | ".join([str(x.used) for x in regs]))
            #input()
        buffor_code = buffor_code + "\tmov ah, 4Ch\n\tint 21h\nEND start"
        #print(buffor_start, buffor_data, buffor_code)
        return buffor_start + buffor_data + buffor_code

def simulate_data(data: codeBlock, out = sys.stdout):
    
    if (n:=OP.COUNT.value) != (m:=37):
        error(Error.ENUM, f"{BOLD_}Exhaustive operation parsing protection in {BOLD_}simulate_data{BACK_}", expected = (m,n), flags = LogFlag.FAIL | LogFlag.EXPECTED)
    
    heap = bytearray(HEAP_SIZE)
    heap_end = 0
    stack: list[int] = []
    ip = 0
    state: ComState = ComState.NONE
    temp1: str = ""
    condition: OP
    last_type: DT
    debug_counter = -1
    while ip < len(data.tokens):
        debug_counter += 1
        x = data.tokens[ip]
        match x.type:
            case OP.NUM:
                stack.append(int(x.value))
            case OP.STRING:
                if ComState.VARDEF in state:
                    match data.vars[temp1].type:
                        case DT.UINT8MEM:
                            for y in range(len(x.value)):
                                heap[heap_end+y] = ord(x.value[y])
                            heap[heap_end+len(x.value)] = ord('$')
                            data.vars[temp1].value = bytearray(bfromNum(data.vars[temp1].type, heap_end))
                            heap_end += len(x.value)+1
                        case DT.UINT16MEM:
                            for y in range(len(x.value)):
                                heap[heap_end+y*2] = ord(x.value[y])
                            heap[heap_end+len(x.value)*2] = ord('$')
                            data.vars[temp1].value = bytearray(bfromNum(data.vars[temp1].type, heap_end))
                            heap_end += (len(x.value)+1)*2
                    state = ComState.NONE
                else:
                    for y in range(len(x.value)):
                        heap[heap_end+y] = ord(x.value[y])
                    heap[heap_end+len(x.value)] = ord('$')
                    stack.append(int.from_bytes(bfromNum(data.vars[temp1].type, heap_end)))
                    heap_end += len(x.value)+1
            case OP.ADD:
                a = stack.pop()
                b = stack.pop()
                stack.append(b+a)
            case OP.SUB:
                a = stack.pop()
                b = stack.pop()
                stack.append(b-a)
            case OP.MUL:
                a = stack.pop()
                b = stack.pop()
                stack.append(b*a)
            case OP.DIV:
                a = stack.pop()
                b = stack.pop()
                stack.append(b // a)
            case OP.MOD:
                a = stack.pop()
                b = stack.pop()
                stack.append(b%a)
            case OP.SHL:
                a = stack.pop()
                b = stack.pop()
                stack.append(b<<a)
            case OP.SHR:
                a = stack.pop()
                b = stack.pop()
                stack.append(b>>a)
            case OP.IF:
                state = ComState.CONDITION
            case OP.WHILE:
                state = ComState.CONDITION
            case OP.EQUAL:
                condition = x.type
            case OP.GREATER:
                condition = x.type
            case OP.LESS:
                condition = x.type
            case OP.GE:
                condition = x.type
            case OP.LE:
                condition = x.type
            case OP.CONJUMP:
                a = stack.pop()
                b = stack.pop()
                state = ComState.NONE
                match condition:
                    case OP.EQUAL:
                        if not b == a:
                            ipx = ip
                            while ipx < len(data.tokens):
                                if (n:=data.tokens[ipx]).type == OP.LABEL and n.value[5:] == x.value[5:]:
                                    ip = ipx
                                    break
                                ipx += 1
                            continue
                    case OP.GREATER:
                        if not b > a:
                            ipx = ip
                            while ipx < len(data.tokens):
                                if (n:=data.tokens[ipx]).type == OP.LABEL and n.value[5:] == x.value[5:]:
                                    ip = ipx
                                    break
                                ipx += 1
                            continue
                    case OP.LESS:
                        if not b < a:
                            ipx = ip
                            while ipx < len(data.tokens):
                                if (n:=data.tokens[ipx]).type == OP.LABEL and n.value[5:] == x.value[5:]:
                                    ip = ipx
                                    break
                                ipx += 1
                            continue
                    case OP.GE:
                        if not b >= a:
                            ipx = ip
                            while ipx < len(data.tokens):
                                if (n:=data.tokens[ipx]).type == OP.LABEL and n.value[5:] == x.value[5:]:
                                    ip = ipx
                                    break
                                ipx += 1
                            continue
                    case OP.LE:
                        if not b <= a:
                            ipx = ip
                            while ipx < len(data.tokens):
                                if (n:=data.tokens[ipx]).type == OP.LABEL and n.value[5:] == x.value[5:]:
                                    ip = ipx
                                    break
                                ipx += 1
                            continue
            case OP.JUMP:
                ip = int(x.value[5:])
                state = ComState.NONE
                continue
            case OP.COPY:
                a = stack.pop()
                stack.append(a)
                stack.append(a)
            case OP.PRINT:
                a = stack.pop()
                out.write(str(a))
            case OP.PRINT_NL:
                out.write('\n')
            case OP.PRINT_AND_NL:
                a = stack.pop()
                out.write(str(a))
                out.write('\n')
            case OP.PRINT_CHAR:
                a = stack.pop()
                out.write(chr(a))
            case OP.TYPE:
                pass
            case OP.BUF:
                if ComState.VARDEF in state:
                    
                    match data.vars[temp1].type:
                        case DT.UINT8MEM:
                            a = stack.pop()
                        case DT.UINT16MEM:
                            a = stack.pop() * 2
                    data.vars[temp1].value = bytearray(bfromNum(data.vars[temp1].type, heap_end))
                    heap[heap_end] = a-2
                    heap_end += a
                    #data.vars[temp1].value
                    state = ComState.NONE
                else:
                    error(Error.SIMULATE, "Buf used in wrong position")
            case OP.VAR:
                #print(stack, ip, state)
                if ComState.ARITHMETIC in state or ComState.CONDITION in state:
                    if data.vars[x.value].type in [DT.UINT8, DT.UINT16]:
                        stack.append(int.from_bytes(data.vars[x.value].value))
                    elif data.vars[x.value].type in [DT.UINT8MEM, DT.UINT16MEM]:
                        stack.append(int.from_bytes(data.vars[x.value].value))
                    else:
                        error(Error.SIMULATE, "Other types than UINT8 are not implemented yet")
                else:
                    temp1 = x.value
                    stack.append(int.from_bytes(data.vars[x.value].value))
                last_type = data.vars[x.value].type
            case OP.SET:
                state = ComState.VARDEF | ComState.ARITHMETIC
                stack.pop()
            case OP.DOS:
                a = stack.pop()
                if a == 9:
                    b = stack.pop()
                    for x in range(1<<8):
                        c = chr(heap[b+x])
                        if c == '$':
                            break
                        else:
                            out.write(c)
                elif a == 10:
                    b = stack.pop()
                    c = input("> ")[:256]
                    for x in range(min(int(heap[b]),len(c))):
                        heap[b+2+x] = ord(c[x])
                        #print(ord(c[x]), end=" ")
                    heap[b+1] = len(c)
                else:
                    error(Error.SIMULATE, "only 9 and 10 dos calls are implemented yet")
            case OP.LINUX:
                a = stack.pop()
                if a == 1:
                    b = stack.pop()
                    c = stack.pop()
                    d = stack.pop()
                    if b == 1:
                        for x in range(d):
                            out.write(chr(heap[c+x]))
                    elif b == 2:
                        for x in range(d):
                            sys.stderr.write(chr(heap[c+x]))
                    else:
                        error(Error.SIMULATE, "other file descriptors than `1` and `2` are not supported yet, skipping...", exitAfter=False)

            case OP.MEMWRITE:
                a = stack.pop()
                b = stack.pop()
                #print(ip, a, data.vars[temp1].type)
                match data.vars[temp1].type:
                    case DT.UINT8MEM | DT.UINT8:
                        heap[b] = bfromNum(DT.UINT8, a)[0]
                    case DT.UINT16MEM | DT.UINT16:
                        heap[b:b+2] = bfromNum(DT.UINT16, a)
                    case _:
                        error(Error.SIMULATE, "MEM WRITE implemented only to UINT8MEM and UINT16MEM yet!")
            case OP.MEMREAD:
                a = stack.pop()
                match last_type:
                    case DT.UINT8MEM | DT.UINT8:
                        stack.append(int.from_bytes(heap[a:a+1]))
                    case DT.UINT16MEM | DT.UINT16:
                        stack.append(int.from_bytes(heap[a:a+2]))
                    case _:
                        error(Error.SIMULATE, "MEMREAD implemented only to UINT8MEM and UINT16MEM yet!")
                #print(stack, [x for x in heap[0:100]])

            case OP.COLON:
                if ComState.VARDEF in state:
                    data.vars[temp1].value = bytearray(bfromNum(data.vars[temp1].type, stack.pop()))
                state = ComState.NONE
        ip += 1
        '''print(stack)
        

        print(ip, heap_end, x)
        w = input()
        if w in data.vars.keys():
            print(data.vars[w])'''
    print()
    for z in range(10):
        print(f"{z*100:>4}:", end=" ")
        for y in range(100):
            print(f"{chr(n) if (n:=heap[z*100+y]) != 10 and n != 0 else 'n' if n != 0 else " ":>1}", end=" ")
        print()
    #print(heap[:15])

def unpack(arr: list) -> tuple[typing.Any, list]:
    if len(arr) < 1:
        error(Error.CMD, "Not enough arguments!", flags = LogFlag.WARNING)
    return (arr[0], arr[1:])

alone_token: dict[str, TOKENS] = {
    ".mem"  : TOKENS.WORD,
    ",mem"  : TOKENS.WORD,
    "..n"   : TOKENS.WORD,
    ".n"    : TOKENS.WORD,
    ".c"    : TOKENS.WORD,
    "."     : TOKENS.WORD,
}

set_token: dict[str, TOKENS] = {
    "#mode" : TOKENS.MODE,
}

option_token: dict[str, COMMODE] = {
    "linux" : COMMODE.LINUX,
    "dos"   : COMMODE.DOS,
}

protected_token: dict[str, TOKENS] = {
    "linux" : TOKENS.WORD,
    "while" : TOKENS.WORD,
    "copy"  : TOKENS.WORD,
    "else"  : TOKENS.WORD,
    "u16p"  : TOKENS.TYPE,
    "u8p"   : TOKENS.TYPE,
    "u16"   : TOKENS.TYPE,
    "buf"   : TOKENS.WORD,
    "dos"   : TOKENS.WORD,
    "if"    : TOKENS.WORD,
    "u8"    : TOKENS.TYPE,
}

indifferent_token: dict[str, TOKENS] = {
    "=="    : TOKENS.OPERAND,
    "<<"    : TOKENS.OPERAND,
    ">>"    : TOKENS.OPERAND,
    "<="    : TOKENS.OPERAND,
    ">="    : TOKENS.OPERAND,
    "<"     : TOKENS.OPERAND,
    ">"     : TOKENS.OPERAND,
    "="     : TOKENS.OPERAND,
    "+"     : TOKENS.OPERAND,
    "-"     : TOKENS.OPERAND,
    "/"     : TOKENS.OPERAND,
    "%"     : TOKENS.OPERAND,
    "*"     : TOKENS.OPERAND,
    "&"     : TOKENS.WORD,
    "{"     : TOKENS.CODEOPEN,
    "("     : TOKENS.CODEOPEN,
    "}"     : TOKENS.CODECLOSE,
    ")"     : TOKENS.CODECLOSE,
    ";"     : TOKENS.WORD,
}

operand_map: dict[str, OP] = {
    "while" : OP.WHILE,
    "linux" : OP.LINUX,
    "copy"  : OP.COPY,
    "else"  : OP.ELSE,
    ".mem"  : OP.MEMWRITE,
    ",mem"  : OP.MEMREAD,
    "dos"   : OP.DOS,
    "buf"   : OP.BUF,
    "..n"   : OP.PRINT_AND_NL,
    ".n"    : OP.PRINT_NL,
    ".c"    : OP.PRINT_CHAR,
    "if"    : OP.IF,
    "=="    : OP.EQUAL,
    "<<"    : OP.SHL,
    ">>"    : OP.SHR,
    "<="    : OP.LE,
    ">="    : OP.GE,
    "<"     : OP.LESS,
    ">"     : OP.GREATER,
    "."     : OP.PRINT,
    "="     : OP.SET,
    "+"     : OP.ADD,
    "-"     : OP.SUB,
    "/"     : OP.DIV,
    "%"     : OP.MOD,
    "*"     : OP.MUL,
    "&"     : OP.PTR,
    ";"     : OP.COLON,
}

arithmetic_ops: tuple[OP,...] = (
    OP.ADD,
    OP.SUB,
    OP.MUL,
    OP.SHL,
    OP.SHR,
)

condition_ops: tuple[OP,...] = (
    OP.EQUAL,
    OP.GREATER,
    OP.LESS,
    OP.GE,
    OP.LE,
)

type_map: dict[str, DT] = {
    "u16p"  : DT.UINT16MEM,
    "u8p"   : DT.UINT8MEM,
    "u16"   : DT.UINT16,
    "u8"    : DT.UINT8
}

unprotected_static_token: dict[str, Token] = {
}

def Switch_Ops(data: codeBlock, index1: int, index2: int) -> codeBlock:

    tmp = data.tokens[index1]
    data.tokens[index1] = data.tokens[index2]
    #data.tokens[index1].loc = tmp.loc
    #tmp2 = data.tokens[index2]
    data.tokens[index2] = tmp
    #data.tokens[index2].loc = tmp2.loc

    return data

def Shift_listOps(data: list[OpType | codeBlock], since: int, shift: int) -> list[OpType]:
    
    index = since
    while index < len(data):
        if data[index].type in OP:
            if data[index].type == OP.LABEL:
                x = data[index].value[:5] + str(int(data[index].value[5:]) + shift)
                indexx = since
                while indexx > -1:
                    if data[indexx].type == OP.CONJUMP and data[indexx].value == data[index].value:
                        data[indexx].value = x
                        break
                    indexx -= 1
                data[index].value = x
            data[index].loc += shift
        elif data[index].type in CB:
            Shift_codeBlock(data[index], 0, shift)
        index += 1
    
    return data

def Shift_codeBlock(data: codeBlock, since: int, shift: int) -> codeBlock:
    
    index = since
    while index < len(data.tokens):
        if data.tokens[index].type in OP:
            if data.tokens[index].type == OP.LABEL:
                x = data.tokens[index].value[:5] + str(int(data.tokens[index].value[5:]) + shift)
                indexx = since
                while indexx > -1:
                    if data.tokens[indexx].type == OP.CONJUMP and data.tokens[indexx].value == data.tokens[index].value:
                        data.tokens[indexx].value = x
                        break
                    indexx -= 1
                data[index].value = x
            data.tokens[index].loc += shift
        elif data.tokens[index].type in CB:
            Shift_codeBlock(data.tokens[index], 0, shift)
        index += 1
    
    return data

def Parse_condition_block(data: codeBlock, typeof: OP) -> list[OpType]:

    # FIX LABELS WHEN TESTING? (idk why the problem is here)

    if (n:=OP.COUNT.value) != (m:=37):
        error(Error.ENUM, f"{BOLD_}Exhaustive operation parsing protection in {BOLD_}Parse_condition_block{BACK_}", expected = (m,n), flags = LogFlag.FAIL | LogFlag.EXPECTED)
    if data.type != CB.CONDITION:
        error(Error.PARSE, f"Passed non-condition type codeblock to {BOLD_}Parse_condition_block{BACK_}", flags = LogFlag.FAIL)

    left: list[OpType] = []
    right: list[OpType] = []
    condition: OpType = None
    # left : right -> True : False
    left_or_right: bool = True

    index = 0
    l_count = 0
    r_count = 0
    while index < len(data.tokens):
        match data.tokens[index].type:
            case x if x in [OP.VAR, OP.NUM]:
                if left_or_right:
                    #if len(left) > 0 and left[-1].type in arithmetic_ops:
                        #error(Error.PARSE, f"Wrong position of token `{bolden(data.tokens[index].type.name)}`, maybe you forgot some opperand? {WARN_}loc = {data.tokens[index].loc}{BACK_}", flags = LogFlag.FAIL)
                    left.append(data.tokens[index])
                    l_count += 1
                else:
                    #if len(right) > 0 and right[-1].type in arithmetic_ops:
                        #error(Error.PARSE, f"Wrong position of token `{bolden(data.tokens[index].type.name)}`, maybe you forgot some opperand? {WARN_}loc = {data.tokens[index].loc}{BACK_}", flags = LogFlag.FAIL)
                    right.append(data.tokens[index])
                    r_count += 1
            case x if x in arithmetic_ops:
                if left_or_right:
                    #if len(left) > 0 and left[-1].type in [OP.VAR, OP.NUM]:
                    #    error(Error.PARSE, f"Wrong position of token `{bolden(data.tokens[index].type.name)}`, maybe you forgot some opperand? {WARN_}loc = {data.tokens[index].loc}{BACK_}", flags = LogFlag.FAIL)
                    left.append(data.tokens[index])
                else:
                    #if len(right) > 0 and right[-1].type in [OP.VAR, OP.NUM]:
                    #    error(Error.PARSE, f"Wrong position of token `{bolden(data.tokens[index].type.name)}`, maybe you forgot some opperand? {WARN_}loc = {data.tokens[index].loc}{BACK_}", flags = LogFlag.FAIL)
                    right.append(data.tokens[index])
            case x if x in condition_ops:
                if not len(left):
                    error(Error.PARSE, f"Empty {bolden("left-side")} of condition! {WARN_}loc = {data.tokens[index].loc}{BACK_}", flags = LogFlag.FAIL)
                if not left_or_right:
                    error(Error.PARSE, "multiple conditions in condition codeBlock are not supported yet", flags = LogFlag.FAIL)
                condition = data.tokens[index]
                left_or_right = False
            case OP.MEMREAD | OP.PTR:
                if left_or_right:
                    left.append(data.tokens[index])
                    #l_count += 1
                else:
                    right.append(data.tokens[index])
                    #r_count += 1
            case _:
                error(Error.PARSE, f"token `{bolden(data.tokens[index].type.name)}` is disallowed in condition codeBlock")
        index += 1
    
    if sum([1 for x in left if x.type in [OP.NUM, OP.VAR]]) != sum([1 for x in left if x.type in arithmetic_ops])+1:
        print(sum([1 for x in left if x.type in [OP.NUM, OP.VAR]]), sum([1 for x in left if x.type in arithmetic_ops])+1)
        error(Error.PARSE, "Wrong layout of arithmetics in condition block", flags = LogFlag.FAIL)
    if sum([1 for x in right if x.type in [OP.NUM, OP.VAR]]) != sum([1 for x in right if x.type in arithmetic_ops])+1:
        error(Error.PARSE, "Wrong layout of arithmetics in condition block", flags = LogFlag.FAIL)

    #if not len(right) or r_count*2-1 != len(right):
        #error(Error.PARSE, f"Empty {bolden("right-side")} of condition! {WARN_}loc = {data.tokens[index].loc}{BACK_}", flags = LogFlag.FAIL)
    #if not len(left) or l_count*2-1 != len(left):
        #error(Error.PARSE, "condidion codeBlock is empty!", flags = LogFlag.FAIL)
    if condition is None:
        error(Error.PARSE, "No condition token found", flags = LogFlag.FAIL)
    if typeof == OP.WHILE:
        return [OpType(OP.LABEL, (loc:=left[0].loc), ("",-1,-1), f"label{loc}")] + Shift_listOps(left + [condition] + right + [OpType(OP.CONJUMP, right[-1].loc+1, ("",-1,-1))], 0, 1)
    return left + [condition] + right + [OpType(OP.CONJUMP, right[-1].loc+1, ("",-1,-1))]

def Third_token_parse(data: codeBlock) -> codeBlock:
    
    if (n:=OP.COUNT.value) != (m:=37):
        error(Error.ENUM, f"{BOLD_}Exhaustive operation parsing protection in {BOLD_}Third_token_parse{BACK_}", expected = (m,n), flags = LogFlag.FAIL | LogFlag.EXPECTED)
    if (n:=CB.COUNT.value) != (m:=5):
        error(Error.ENUM, f"{BOLD_}Exhaustive codeBlock parsing protection in {BOLD_}Third_token_parse{BACK_}", expected = (m,n), flags = LogFlag.FAIL | LogFlag.EXPECTED)
    index = 0
    index_offset = 0
    # DEBUG, I was using it while having a lot of problems with wrong OpType.loc after merging codeBlocks
    #off = 0
    #for i, x in enumerate(data.tokens):
    #    if x.type in OP:
    #        print(x.loc, i+off, x)
    #    else:
    #        off += len(x.tokens)-1
    #        print(len(x.tokens), i+off, x)
    while index < len(data.tokens):
        match data.tokens[index].type:
            case OP.IF:
                if index+2 >= len(data.tokens):
                    error(Error.PARSE, "If keyword at the end of file")
                if data.tokens[index+1].type != CB.CONDITION:
                    error(Error.PARSE, "codeBlock not a type of condition after If keyword")
                # Update Parse_condition_block to
                # 
                # return list of tokens
                # append to list of tokens a conditional jump and (if 'while') label
                con_token_list: list[OpType] = []
                con_token_list = Parse_condition_block(data.tokens[index+1], OP.IF)
                index_offset += 1

                if data.tokens[index+2].type != CB.CODE:
                    error(Error.PARSE, "codeBlock not a type of code after If keyword")
                is_else: bool = False
                if index+4 < len(data.tokens):
                    if data.tokens[index+3].type == OP.ELSE:
                        if data.tokens[index+4].type != CB.CODE:
                            error(Error.PARSE, "ELSE - NO CODEBLOCK", flags = LogFlag.FAIL)
                        is_else = True
                con_token_list[-1].loc = con_token_list[-2].loc+1
                con_token_list[-1].value = f"label{data.tokens[index+2].tokens[-1].loc+1+index_offset+int(is_else)}"
                #for i, x in enumerate(con_token_list):
                    #print("con > >", x, index + index_offset + i)
                code_token_list: list[OpType] = []
                data.tokens = Shift_codeBlock(data.tokens, index+1, index_offset)
                if is_else:
                    data.tokens[index+2].tokens.append(OpType(OP.JUMP, data.tokens[index+2].tokens[-1].loc+1, ("",-1,-1), f"label{data.tokens[index+4].tokens[-1].loc+2+index_offset}"))
                data.tokens[index+2].tokens.append(OpType(OP.LABEL, (loc:=data.tokens[index+2].tokens[-1].loc+1), ("",-1,-1), f"label{loc}"))
                code_token_list += data.tokens[index+2].tokens
                index_offset += 1
                if is_else:
                    data.tokens = Shift_codeBlock(data.tokens, index+3, index_offset)
                    data.tokens[index+4].tokens.append(OpType(OP.LABEL, (loc:=data.tokens[index+4].tokens[-1].loc+1), ("",-1,-1), f"label{loc}"))
                    code_token_list += data.tokens[index+4].tokens
                    index_offset += 1
                #for i, x in enumerate(code_token_list):
                    #print("code > >", x, index + len(con_token_list)+1 + i)
                
                data.tokens.pop(index+1)
                data.tokens.pop(index+1)
                if is_else:
                    data.tokens.pop(index+1)
                    data.tokens.pop(index+1)
                data.tokens = Shift_listOps(data.tokens, index, index_offset)
                for i, x in enumerate(con_token_list + code_token_list):
                    data.tokens.insert(index+1+i, x)
                
            case OP.WHILE:
                if index+2 >= len(data.tokens):
                    error(Error.PARSE, "While keyword at the end of file")
                if data.tokens[index+1].type != CB.CONDITION:
                    error(Error.PARSE, f"Non Condition codeBlock after While at `{index}`")
                # Update Parse_condition_block to
                # 
                # return list of tokens
                # append to list of tokens a conditional jump and (if 'while') label
                con_token_list: list[OpType] = []
                con_token_list = Parse_condition_block(data.tokens[index+1], OP.WHILE)
                index_offset += 2

                if data.tokens[index+2].type != CB.CODE:
                    error(Error.PARSE, "codeBlock not a type of code after While keyword")
                con_token_list[-1].value = f"label{data.tokens[index+2].tokens[-1].loc+2+index_offset}"
                #for i, x in enumerate(con_token_list):
                    #print("con > >", x, index + index_offset + i)
                code_token_list: list[OpType] = []
                data.tokens = Shift_listOps(data.tokens, index+1, index_offset)
                data.tokens[index+2].tokens.append(OpType(OP.JUMP, data.tokens[index+2].tokens[-1].loc+1, ("",-1,-1), f"label{con_token_list[0].loc}"))
                data.tokens[index+2].tokens.append(OpType(OP.LABEL, (loc:=data.tokens[index+2].tokens[-1].loc+1), ("",-1,-1), f"label{loc}"))
                code_token_list += data.tokens[index+2].tokens
                index_offset += 2
                #for i, x in enumerate(code_token_list):
                    #print("code > >", x, index + len(con_token_list)+1 + i)
                
                data.tokens.pop(index+1)
                data.tokens.pop(index+1)
                data.tokens = Shift_listOps(data.tokens, index, index_offset)
                for i, x in enumerate(con_token_list + code_token_list):
                    data.tokens.insert(index+1+i, x)
                data = Switch_Ops(data, index, index+1)
                index += 1
        index += 1
    return data

def Secound_token_parse(data: codeBlock, index_offset: int = 0) -> codeBlock:

    if (n:=OP.COUNT.value) != (m:=37):
        error(Error.ENUM, f"{BOLD_}Exhaustive operation parsing protection in {BOLD_}Secound_token_parse{BACK_}", expected = (m,n), flags = LogFlag.FAIL | LogFlag.EXPECTED)
    if (n:=CB.COUNT.value) != (m:=5):
        error(Error.ENUM, f"{BOLD_}Exhaustive codeBlock parsing protection in {BOLD_}Secound_token_parse{BACK_}", expected = (m,n), flags = LogFlag.FAIL | LogFlag.EXPECTED)
    
    index = 0
    while index < len(data.tokens):
        match data.tokens[index].type:
            case OP.TYPE:
                if index+1 < len(data.tokens):
                    if data.tokens[index+1].type == OP.VAR:
                        if (n:=Var(data.tokens[index].value, (m:=(data.tokens[index+1].value[0])))) not in data.vars.values():
                            data.vars[m] = n
                            data.tokens.pop(index)
                            index_offset -= 1
                        else:
                            error(Error.PARSE, "var already stated", flags = LogFlag.FAIL)
                    else:
                        error(Error.PARSE, "no var token after type", flags = LogFlag.FAIL)
                else:
                    error(Error.PARSE, "type at the end of file", flags = LogFlag.FAIL)
            case OP.VAR:
                if (n:=data.tokens[index].value[0]) not in data.vars.keys():
                    error(Error.PARSE, f"Variable `{BOLD_}{n}{BACK_}` stated without assigment!", flags = LogFlag.FAIL)
            case CB.CODE | CB.CONDITION | CB.RESOLVE:
                data.tokens[index].vars = data.vars.copy()
                data.tokens[index] = Secound_token_parse(data.tokens[index], index_offset)
        if data.tokens[index].type in OP:
            #print(data.tokens[index].loc, index_offset, data.tokens[index])
            data.tokens[index].loc += index_offset
        index += 1
    return data
        
def First_token_parse(data: list[Token]) -> codeBlock:

    if (n:=OP.COUNT.value) != (m:=37):
        error(Error.ENUM, f"{BOLD_}Exhaustive operation parsing protection in {BOLD_}First_token_parse{BACK_}", expected = (m,n), flags = LogFlag.FAIL | LogFlag.EXPECTED)

    # ret: codeBlock = codeBlock(0) this line was bugging tests, actually stupid bug
    ret: codeBlock = codeBlock(0, [], {})

    codeBlock_stack: list[codeBlock] = [ret]
    
    codeblock_id_index = 1

    index_offset = 0
    index = 0
    while index < len(data):
        match data[index].type:
            case TOKENS.NOTOKEN:
                index_offset -= 1
            case TOKENS.WORD | TOKENS.OPERAND:
                match data[index].name:
                    case '*':
                        broke = False
                        c = 1
                        if index+1 < len(data) and Sticky.RIGHT in data[index].flags:
                            while True:
                                if data[index+c].type == TOKENS.NAME and Sticky.LEFT in data[index+c].flags:
                                    codeBlock_stack[-1].tokens.append(OpType(OP.VAR, index + index_offset, data[index].loc, (data[index+c].name, -c)))
                                    index += c
                                    index_offset -= c
                                    break
                                c += 1
                                if index+c < len(data) and Sticky.RIGHT in data[index+c-1].flags and data[index+c-1].name == '*':
                                    pass
                                else:
                                    broke = True
                                    break
                        else:
                            broke = True
                        if broke:
                            codeBlock_stack[-1].tokens.append(OpType(operand_map[data[index].name], index + index_offset, data[index].loc))
                    case '&':
                        broke = False
                        c = 1
                        while True:
                            if index+c < len(data) and Sticky.RIGHT in data[index+c-1].flags:
                                if data[index+1].type == TOKENS.NAME and Sticky.LEFT in data[index+1].flags:
                                    codeBlock_stack[-1].tokens.append(OpType(OP.VAR, index + index_offset, data[index].loc, (data[index+1].name, c)))
                                    index += c
                                    index_offset -= c
                                    break
                                c += 1
                                if index+c < len(data) and Sticky.RIGHT in data[index+c-1].flags and data[index+c-1].name == '&':
                                    pass
                                else:
                                    broke = True
                                    break
                        if broke:
                            error(Error.PARSE, "Found `&` not used with variable")
                    case _:
                        codeBlock_stack[-1].tokens.append(OpType(operand_map[data[index].name], index + index_offset, data[index].loc))
            case TOKENS.NAME:
                codeBlock_stack[-1].tokens.append(OpType(OP.VAR, index + index_offset, data[index].loc, (data[index].name, 0)))
            case TOKENS.NUM:
                codeBlock_stack[-1].tokens.append(OpType(OP.NUM, index + index_offset, data[index].loc, int(data[index].name)))
            case TOKENS.STRING:
                codeBlock_stack[-1].tokens.append(OpType(OP.STRING, index + index_offset, data[index].loc, data[index].name))
            case TOKENS.TYPE:
                codeBlock_stack[-1].tokens.append(OpType(OP.TYPE, index + index_offset, data[index].loc, type_map[data[index].name]))
            case TOKENS.CODEOPEN:
                codeBlock_stack.append(codeBlock(codeblock_id_index, [], {}))
                match data[index].name:
                    case "(":
                        codeBlock_stack[-1].type = CB.CONDITION
                    case "{":
                        codeBlock_stack[-1].type = CB.CODE
                codeblock_id_index += 1
                index_offset -= 1
            case TOKENS.CODECLOSE:
                match data[index].name:
                    case ")":
                        if codeBlock_stack[-1].type != CB.CONDITION:
                            error(Error.PARSE, "Found wrong codeBlock closing!", expected = (')',data[index].name), flags = LogFlag.FAIL | LogFlag.EXPECTED)
                    case "{":
                        if codeBlock_stack[-1].type != CB.CODE:
                            error(Error.PARSE, "Found wrong codeBlock closing!", expected = ('}',data[index].name), flags = LogFlag.FAIL | LogFlag.EXPECTED)
                codeBlock_stack[-2].tokens.append(codeBlock_stack.pop())
                index_offset -= 1
            case _:
                error(Error.PARSE, "unreachable!", flags = LogFlag.FAIL)
        index += 1
    return codeBlock_stack[-1]

def Parse_token(file_path: str, loc: tuple[int, int], data: str, sticky: Sticky = Sticky(0)) -> list[Token]:

    global Com_Mode

    if (n:=TOKENS.COUNT.value) != (m:=11):
        error(Error.ENUM, f"{BOLD_}Exhaustive operation parsing protection in {BOLD_}Parse_token{BACK_}", expected = (m,n), flags = LogFlag.FAIL | LogFlag.EXPECTED)

    ret: list[Token] = []

    if data in set_token:
        if not loc == (0,len(data)):
            error(Error.PARSE, f"Compilation option token found not on the begining of a file, but on `{bolden(loc)}`!")
        Com_Mode = COMMODE.SET
        ret += [Token(TOKENS.NOTOKEN, (file_path,)+loc, data, sticky)]
        data = ""
    elif Com_Mode == COMMODE.SET:
        if data not in option_token:
            error(Error.PARSE, f"Wrong option for `{bolden("#mode")}` probided, found `{bolden(data)}`")
        Com_Mode = option_token[data]
        ret += [Token(TOKENS.NOTOKEN, (file_path,)+loc, data, sticky)]
        data = ""
    elif data in alone_token:
        ret += [Token(alone_token[data], (file_path,)+loc, data, sticky)]
        data = ""
    elif data in protected_token:
        if data == "dos" and Com_Mode != COMMODE.DOS:
            print(Com_Mode)
            error(Error.PARSE, f"Usage of `{bolden("dos")}` token in non-DOS mode of compilation")
        elif data == "linux" and Com_Mode != COMMODE.LINUX:
            error(Error.PARSE, f"Usage of `{bolden("linux")}` token in non-LINUX mode of compilation")
        ret += [Token(protected_token[data], (file_path,)+loc, data, sticky)]
        data = ""
    elif data in indifferent_token:
        ret += [Token(indifferent_token[data], (file_path,)+loc, data, sticky)]
        data = ""
    else:
        for x in list(alone_token.keys()):
            if data.startswith(x) or data.endswith(x):
                error(Error.TOKENIZE, f"at {file_path}:{loc[0]+1}:{loc[1]-len(data)} keyword starts with disallowed token `{BOLD_}{x}{BACK_}` in `{BOLD_}{data}{BACK_}`", flags = LogFlag.FAIL)
        for x in indifferent_token.keys():
            if data.find(x) != -1:
                (before, token, after) = data.partition(x)
                if before:
                    ret += Parse_token(file_path, loc, before, Sticky.RIGHT | sticky)
                ret += Parse_token(file_path, loc, token, (Sticky.LEFT if before else Sticky(0)) | sticky | (Sticky.RIGHT if after else Sticky(0)))
                if after:
                    ret += Parse_token(file_path, loc, after, Sticky.LEFT | sticky)
                data = ""
                break

        if data.isnumeric():
            ret += [Token(TOKENS.NUM, (file_path,)+loc, data, sticky)]
            data = ""
        if data:
            if data[0].isdigit():
                error(Error.TOKENIZE, "name token cannot begin with a number", flags = LogFlag.FAIL)
            ret += [Token(TOKENS.NAME, (file_path,)+loc, 'v'+data, sticky)]
            #assert False, "unknown keyword %s" % (data)

    return ret

# debug
def Print_codeBlock_ops(data: codeBlock, suffix="", color_offset = 0) -> None:
    color: tuple[LogFlag, LogFlag, LogFlag] = (LogFlag.GOOD,LogFlag.WARNING, LogFlag.INFO)
    for i, x in enumerate(data.tokens):
        if x.type in CB:
            color_offset += Print_codeBlock_ops(x, suffix = f"in {data.id} > ", color_offset=i+color_offset)
        else:
            error(Error.TEST, f"{suffix}in {data.id} > {x}\n", flags = color[(i+color_offset) // 5 % len(color)], exitAfter = False)
    return len(data.tokens)

def Parse_file(in_path: str) -> list:
    data = []
    with open(in_path, 'rt', encoding='utf-8') as f:
        data = f.read()
    
    tokens: list[TOKENS] = []

    token: str = ""
    index: int = 0
    slash_before: bool = False
    string_literal: bool = False
    loc: tuple[int, int] = (0,0)
    while index < len(data):
        match data[index]:
            case '\\':
                if slash_before and not string_literal:
                    tokens += Parse_token(in_path, loc, token)
                    index = data[index:].find("\n")+index
                    if not index:
                        break
                    continue
                else:
                    slash_before = True
            case '"':
                if slash_before:
                    token = token + data[index]
                elif string_literal:
                    tokens.append(Token(TOKENS.STRING, loc, token, flags = Sticky(0)))
                    token = ""
                    string_literal = False
                else:
                    tokens += Parse_token(in_path, loc, token)
                    token = ""
                    string_literal = True
            case '\n':
                tokens += Parse_token(in_path, loc, token)
                token = ""
                slash_before = False
                loc = (loc[0]+1, 0)
            case ' ':
                if not string_literal:
                    tokens += Parse_token(in_path, loc, token)
                    token = ""
                else:
                    token = token + data[index]
                slash_before = False
            case x if isinstance(x, str):
                #if slash_before:
                    #token = token + '\\'
                    #slash_before = False
                if slash_before and string_literal:
                    match data[index]:
                        case 'n':
                            token = token + '\n'
                        case _:
                            token = token + data[index]
                            token = token.encode("utf-8").decode("unicode_escape")
                    slash_before = False
                else:
                    token = token + data[index]
            case _:
                error(Error.TOKENIZE, f"{in_path}:{loc[0]}:{loc[1]} Error while tokenizing file, incorrect character?", expected = ("any character",data[index]), flags = LogFlag.FAIL | LogFlag.EXPECTED)
        index += 1
        loc = (loc[0], loc[1]+1)
    tokens += Parse_token(in_path, loc, token)
    token = ""

    #for x in [op for row, line in enumerate(data) for op in Parse_line(in_path, row, line)]:
        #print(x)
    return Third_token_parse(Secound_token_parse(First_token_parse([tok for tok in tokens])))
    #Print_codeBlock_ops(ops)
    #return Parse_jump(resolve_names([op for row, line in enumerate(data) for op in Parse_line(in_path, row, line)]))

# ------------------------------------------------------
# -------------------- TEST SECTION --------------------
# ------------------------------------------------------
class dataHolder:
    data: str = ""
    def write(self, string):
        self.data = self.data + string
    
    def compare_with_file(self, file_path):
        data: str = ""
        with open(file_path, 'rt', encoding='utf-8') as f:
            data = f.read()
        return data == self.data

def record_test():
    for x in glob.glob("./tests/*.mand"):
        with open(x[:-5]+".txt", "wt", encoding='utf-8') as f:
            simulate_data(Parse_file(x), out = f)

def compare_test():
    for x in glob.glob("./tests/*.mand"):
        dh: dataHolder = dataHolder()
        simulate_data(Parse_file(x), out = dh)
        if not dh.compare_with_file(x[:-5]+".txt"):
            error(Error.TEST, f"{BOLD_}{x}{BACK_} Test Failed\n", flags = LogFlag.WARNING, exitAfter = False)
        else:
            error(Error.TEST, f"{BOLD_}{x}{BACK_} Passed\n", flags = LogFlag.GOOD, exitAfter = False)

# CMD LINE

if __name__ == "__main__":
    argv: list[str] = sys.argv[1:]
    if len(argv) < 1:
        error(Error.CMD, "No Commandline options provided", flags = LogFlag.WARNING)
    option, argv = unpack(argv)

    match option:
        case '-c':
            input_file, argv = unpack(argv)

            if not os.path.isfile(input_file):
                error(Error.CMD, f"Wrong file provided, compiller couldn't find file at a `{input_file}` location", flags = LogFlag.WARNING)
            parsed = Parse_file(input_file)
            
            output_string = compile_data(parsed)
            if len(argv) > 0:
                option, argv = unpack(argv)
            if option == '-o':
                if argv[0]:
                    with open(argv[0], 'wt', encoding="utf-8") as f:
                        f.write(output_string)
            else:
                with open(input_file[:input_file.rfind('.')] + ".asm", 'wt', encoding="utf-8") as f:
                    f.write(output_string)
        case '-s':
            input_file, argv = unpack(argv)

            if not os.path.isfile(input_file):
                error(Error.CMD, f"Wrong file provided, compiller couldn't find file at a `{input_file}` location", flags = LogFlag.WARNING)
            parsed = Parse_file(input_file)
            
            simulate_data(parsed)
        case '-t':
            test_type: str

            if len(argv) > 0:
                test_type, argv = unpack(argv)
            else:
                test_type = "compare"

            match test_type:
                case "record":
                    record_test()
                case "compare":
                    compare_test()
                case _:
                    error(Error.CMD, f"Wrong test type provided, expected `record` or `compare`, got `{test_type}`!", flags = LogFlag.WARNING) 
        case _:
            error(Error.CMD, f"Wrong mode provided, expected `-c` | `-s` | `-t`, got `{option}`!", flags = LogFlag.WARNING)
