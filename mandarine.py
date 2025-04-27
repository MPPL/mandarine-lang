#!/usr/bin/env python3

import sys
import subprocess
from enum import Enum, auto, Flag
import types
import typing
import os
import glob
from dataclasses import dataclass, field

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
    COUNT       = auto()
    MODE        = auto()

class OP(Enum):
    NUM         = auto()
    SET         = auto()
    ADD         = auto()
    SUB         = auto()
    MUL         = auto()
    SHL         = auto()
    SHR         = auto()
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
    COPY        = auto()
    PRINT       = auto()
    PRINT_NL    = auto()
    PRINT_AND_NL= auto()
    PRINT_CHAR  = auto()
    BUF         = auto()
    MEMWRITE    = auto()
    MEMREAD     = auto()
    DOS         = auto()
    MODE        = auto()
    VAR         = auto()
    TYPE        = auto()
    COLON       = auto()
    COUNT       = auto()

class DT(Enum):
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
@dataclass
class Token:
    type:       TOKENS
    name:       str

@dataclass
class Var:
    type: DT
    name: str
    value: bytearray = field(default_factory=bytearray)
class codeBlock:
    id:         int = -1
    type:       CB = CB.COMPILETIME
    tokens:     list[Token | typing.Self] = []
    vars:       dict[str,Var]

    def __init__(self, id = -1, tokens = [], vars = {}):
        self.id = id
        self.tokens = tokens
        self.vars = vars
    
    def __repr__(self) -> str:
        return f"(codeBlock > id = {self.id} | type = {self.type})"

@dataclass
class OpType:
    type:       OP
    loc:        int
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

    outfun(out)

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

    if (n:=OP.COUNT.value) != (m:=32):
        error(Error.ENUM, f"{BOLD_}Exhaustive operation protection in {bolden("bfromNum")}", expected = (m,n), flags = LogFlag.FAIL | LogFlag.EXPECTED)
    if (n:=DT.COUNT.value) != (m:=5):
        error(Error.ENUM, f"{BOLD_}Exhaustive datatype protection in {bolden("bfromNum")}", expected = (m,n), flags = LogFlag.FAIL | LogFlag.EXPECTED)

    match type:
        case DT.UINT8:
            return bytearray([value % 256])
        case DT.UINT16:
            return bytearray([(value // 256) % 256, value % 256])
        case DT.UINT8MEM:
            return bytearray([value % (1<<8)])
        case DT.UINT16MEM:
            return bytearray([value % (1<<8)])
        case _:
            pass
            


def compile_data(data: list[dict]):
    assert False, "not implemented yet"

    if (n:=OP.COUNT.value) != (m:=32):
        error(Error.ENUM, f"{BOLD_}Exhaustive operation parsing protection in {BOLD_}simulate_data{BACK_}", expected = (m,n), flags = LogFlag.FAIL | LogFlag.EXPECTED)
    
    heap = bytearray(HEAP_SIZE)
    heap_end = 0
    stack = []
    ip = 0
    state: ComState = ComState.NONE
    temp1: str = ""
    condition: OP
    last_type: DT
    debug_counter = -1

def simulate_data(data: codeBlock, out = sys.stdout):
    
    if (n:=OP.COUNT.value) != (m:=32):
        error(Error.ENUM, f"{BOLD_}Exhaustive operation parsing protection in {BOLD_}simulate_data{BACK_}", expected = (m,n), flags = LogFlag.FAIL | LogFlag.EXPECTED)
    
    heap = bytearray(HEAP_SIZE)
    heap_end = 0
    stack = []
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
                match condition:
                    case OP.EQUAL:
                        if not b == a:
                            ip = int(x.value[5:])
                            continue
                    case OP.GREATER:
                        if not b > a:
                            ip = int(x.value[5:])
                            continue
                    case OP.LESS:
                        if not b < a:
                            ip = int(x.value[5:])
                            continue
                    case OP.GE:
                        if not b >= a:
                            ip = int(x.value[5:])
                            continue
                    case OP.LE:
                        if not b <= a:
                            ip = int(x.value[5:])
                            continue
            case OP.JUMP:
                ip = int(x.value[5:])
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
                out.write(chr(int(a)))
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
                    heap_end += a
                    data.vars[temp1].value
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
                    for x in range(1<<10):
                        c = chr(heap[b+x])
                        if c == '$':
                            break
                        else:
                            out.write(c)
                elif a == 10:
                    b = stack.pop()
                    c = input()[:256]
                    for x in range(min(int.from_bytes(heap[b]),len(c))):
                        heap[b+2+x] = c[x]
                    heap[b+1] = bytes(len(c))
                else:
                    error(Error.SIMULATE, "only 9 and 10 dos calls are implemented yet")
            case OP.MEMWRITE:
                a = stack.pop()
                b = stack.pop()
                #print(ip, a, data.vars[temp1].type)
                match data.vars[temp1].type:
                    case DT.UINT8MEM:
                        heap[b] = bfromNum(DT.UINT8, a)[0]
                    case DT.UINT16MEM:
                        heap[b:b+2] = bfromNum(DT.UINT16, a)
                    case _:
                        error(Error.SIMULATE, "MEM WRITE implemented only to UINT8MEM and UINT16MEM yet!")
            case OP.MEMREAD:
                a = stack.pop()
                match last_type:
                    case DT.UINT8MEM:
                        stack.append(int.from_bytes(heap[a]))
                    case DT.UINT16MEM:
                        stack.append(int.from_bytes(heap[a:a+2]))
                    case _:
                        error(Error.SIMULATE, "MEMREAD implemented only to UINT8MEM and UINT16MEM yet!")
                #print(stack, [x for x in heap[0:100]])

            case OP.COLON:
                #print(state)
                if ComState.VARDEF in state:
                    data.vars[temp1].value = bytearray(bfromNum(data.vars[temp1].type, stack.pop()))
                state = ComState.NONE
        #print(data.tokens[ip])
        ip += 1
        #print(stack, heap[0:5], ip, x)
        #input()

def unpack(arr: list) -> tuple[typing.Any, list]:
    if len(argv) < 1:
        error(Error.CMD, "Not enough arguments!", LogFlag.WARNING)
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

option_token: dict[str, TOKENS] = {
    "dos"   : COMMODE.DOS,
}

protected_token: dict[str, TOKENS] = {
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
    "*"     : TOKENS.OPERAND,
    "{"     : TOKENS.CODEOPEN,
    "("     : TOKENS.CODEOPEN,
    "}"     : TOKENS.CODECLOSE,
    ")"     : TOKENS.CODECLOSE,
    ";"     : TOKENS.WORD,
}

operand_map: dict[str, OP] = {
    "while" : OP.WHILE,
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
    "*"     : OP.MUL,
    ";"     : OP.COLON,
}

arithmetic_ops: tuple[OP] = (
    OP.ADD,
    OP.SUB,
    OP.MUL,
    OP.SHL,
    OP.SHR,
)

condition_ops: tuple[OP] = (
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

unprotected_static_token = {
}

def Switch_Ops(data: codeBlock, index1: int, index2: int) -> codeBlock:

    tmp = data.tokens[index1]
    data.tokens[index1] = data.tokens[index2]
    data.tokens[index1].loc = tmp.loc
    tmp2 = data.tokens[index2]
    data.tokens[index2] = tmp
    data.tokens[index2].loc = tmp2.loc

    return data

def Shift_listOps(data: list[OpType], shift: int) -> list[OpType]:
    
    index = 0
    while index < len(data):
        if data[index].type in OP:
            data[index].loc += shift
        elif data[index].type in CB:
            Shift_codeBlock(data[index], shift)
        index += 1
    
    return data

def Shift_codeBlock(data: codeBlock, shift: int) -> codeBlock:
    
    index = 0
    while index < len(data.tokens):
        if data.tokens[index].type in OP:
            data.tokens[index].loc += shift
        elif data.tokens[index].type in CB:
            Shift_codeBlock(data.tokens[index], shift)
        index += 1
    
    return data

def Parse_condition_block(data: codeBlock, type: OP) -> list[OpType]:

    if (n:=OP.COUNT.value) != (m:=32):
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
                    if len(left) > 0 and left[-1].type in arithmetic_ops:
                        error(Error.PARSE, f"Wrong position of token `{bolden(data.tokens[index].type.name)}`, maybe you forgot some opperand? {WARN_}loc = {data.tokens[index].loc}{BACK_}", flags = LogFlag.FAIL)
                    left.append(data.tokens[index])
                    l_count += 1
                else:
                    if len(right) > 0 and right[-1].type in arithmetic_ops:
                        error(Error.PARSE, f"Wrong position of token `{bolden(data.tokens[index].type.name)}`, maybe you forgot some opperand? {WARN_}loc = {data.tokens[index].loc}{BACK_}", flags = LogFlag.FAIL)
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
                    error(Error.PARSE, f"multiple conditions in condition codeBlock are not supported yet", flags = LogFlag.FAIL)
                condition = data.tokens[index]
                left_or_right = False
            case _:
                error(Error.PARSE, f"token `{bolden(data.tokens[index].type.name)}` is disallowed in condition codeBlock")
        index += 1
    
    if not len(right) or r_count*2-1 != len(right):
        error(Error.PARSE, f"Empty {bolden("right-side")} of condition! {WARN_}loc = {data.tokens[index].loc}{BACK_}", flags = LogFlag.FAIL)
    if not len(left) or l_count*2-1 != len(left):
        error(Error.PARSE, f"condidion codeBlock is empty!", flags = LogFlag.FAIL)
    if condition == None:
        error(Error.PARSE, f"No condition token found", flags = LogFlag.FAIL)
    if type == OP.WHILE:
        return [OpType(OP.LABEL, (loc:=left[0].loc), f"label{loc}")] + Shift_listOps(left + [condition] + right + [OpType(OP.CONJUMP, right[-1].loc+1)], 1)
    return left + [condition] + right + [OpType(OP.CONJUMP, right[-1].loc+1)]

def Third_token_parse(data: codeBlock) -> codeBlock:
    
    if (n:=OP.COUNT.value) != (m:=32):
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
                    error()
                if data.tokens[index+1].type != CB.CONDITION:
                    error()
                # Update Parse_condition_block to
                # 
                # return list of tokens
                # append to list of tokens a conditional jump and (if 'while') label
                con_token_list: list[OpType] = []
                con_token_list = Parse_condition_block(data.tokens[index+1], OP.IF)
                index_offset += 1

                if data.tokens[index+2].type != CB.CODE:
                    error()
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
                data.tokens[index+2] = Shift_codeBlock(data.tokens[index+2], index_offset)
                if is_else:
                    data.tokens[index+2].tokens.append(OpType(OP.JUMP, data.tokens[index+2].tokens[-1].loc+1, f"label{data.tokens[index+4].tokens[-1].loc+2+index_offset}"))
                data.tokens[index+2].tokens.append(OpType(OP.LABEL, (loc:=data.tokens[index+2].tokens[-1].loc+1), f"label{loc}"))
                code_token_list += data.tokens[index+2].tokens
                index_offset += 1

                data.tokens[index+4] = Shift_codeBlock(data.tokens[index+4], index_offset)
                data.tokens[index+4].tokens.append(OpType(OP.LABEL, (loc:=data.tokens[index+4].tokens[-1].loc+1), f"label{loc}"))
                code_token_list += data.tokens[index+4].tokens
                index_offset += 1
                #for i, x in enumerate(code_token_list):
                    #print("code > >", x, index + len(con_token_list)+1 + i)
                
                data.tokens.pop(index+1)
                data.tokens.pop(index+1)
                if is_else:
                    data.tokens.pop(index+1)
                    data.tokens.pop(index+1)
                data.tokens[index+1:] = Shift_listOps(data.tokens[index+1:], index_offset)
                for i, x in enumerate(con_token_list + code_token_list):
                    data.tokens.insert(index+1+i, x)
                
            case OP.WHILE:
                if index+2 >= len(data.tokens):
                    error()
                if data.tokens[index+1].type != CB.CONDITION:
                    for x in data.tokens:
                        print("???",x)
                    error(Error.PARSE, f"Non Condition codeBlock after While at `{index}`")
                # Update Parse_condition_block to
                # 
                # return list of tokens
                # append to list of tokens a conditional jump and (if 'while') label
                con_token_list: list[OpType] = []
                con_token_list = Parse_condition_block(data.tokens[index+1], OP.WHILE)
                index_offset += 2

                if data.tokens[index+2].type != CB.CODE:
                    error()
                con_token_list[-1].value = f"label{data.tokens[index+2].tokens[-1].loc+2+index_offset}"
                #for i, x in enumerate(con_token_list):
                    #print("con > >", x, index + index_offset + i)
                code_token_list: list[OpType] = []
                data.tokens[index+2] = Shift_codeBlock(data.tokens[index+2], index_offset)
                data.tokens[index+2].tokens.append(OpType(OP.JUMP, data.tokens[index+2].tokens[-1].loc+1, f"label{con_token_list[0].loc}"))
                data.tokens[index+2].tokens.append(OpType(OP.LABEL, (loc:=data.tokens[index+2].tokens[-1].loc+1), f"label{loc}"))
                code_token_list += data.tokens[index+2].tokens
                index_offset += 2
                #for i, x in enumerate(code_token_list):
                    #print("code > >", x, index + len(con_token_list)+1 + i)
                
                data.tokens.pop(index+1)
                data.tokens.pop(index+1)
                data.tokens[index+1:] = Shift_listOps(data.tokens[index+1:], index_offset)
                for i, x in enumerate(con_token_list + code_token_list):
                    data.tokens.insert(index+1+i, x)
                data = Switch_Ops(data, index, index+1)
                index += 1
        index += 1
    return data

def Secound_token_parse(data: codeBlock, index_offset: int = 0) -> codeBlock:

    if (n:=OP.COUNT.value) != (m:=32):
        error(Error.ENUM, f"{BOLD_}Exhaustive operation parsing protection in {BOLD_}Secound_token_parse{BACK_}", expected = (m,n), flags = LogFlag.FAIL | LogFlag.EXPECTED)
    if (n:=CB.COUNT.value) != (m:=5):
        error(Error.ENUM, f"{BOLD_}Exhaustive codeBlock parsing protection in {BOLD_}Secound_token_parse{BACK_}", expected = (m,n), flags = LogFlag.FAIL | LogFlag.EXPECTED)
    
    index = 0
    while index < len(data.tokens):
        match data.tokens[index].type:
            case OP.TYPE:
                if index+1 < len(data.tokens):
                    if data.tokens[index+1].type == OP.VAR:
                        if not (n:=Var(data.tokens[index].value, (m:=data.tokens[index+1].value))) in data.vars.values():
                            data.vars[m] = n
                            data.tokens.pop(index)
                            index_offset -= 1
                        else:
                            error(Error.PARSE, f"var already stated", flags = LogFlag.FAIL)
                    else:
                        error(Error.PARSE, f"no var token after type", flags = LogFlag.FAIL)
                else:
                    error(Error.PARSE, f"type at the end of file", flags = LogFlag.FAIL)
            case OP.VAR:
                if not (n:=data.tokens[index].value) in data.vars.keys():
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

    if (n:=OP.COUNT.value) != (m:=32):
        error(Error.ENUM, f"{BOLD_}Exhaustive operation parsing protection in {BOLD_}First_token_parse{BACK_}", expected = (m,n), flags = LogFlag.FAIL | LogFlag.EXPECTED)


    ret: codeBlock = codeBlock(0)

    codeBlock_stack: list[codeBlock] = [ret]
    
    codeblock_id_index = 1

    index_offset = 0
    index = 0
    while index < len(data):
        match data[index].type:
            case TOKENS.NOTOKEN:
                index_offset -= 1
            case TOKENS.WORD | TOKENS.OPERAND:
                codeBlock_stack[-1].tokens.append(OpType(operand_map[data[index].name], index + index_offset))
            case TOKENS.NAME:
                codeBlock_stack[-1].tokens.append(OpType(OP.VAR, index + index_offset, data[index].name))
            case TOKENS.NUM:
                codeBlock_stack[-1].tokens.append(OpType(OP.NUM, index + index_offset, int(data[index].name)))
            case TOKENS.TYPE:
                codeBlock_stack[-1].tokens.append(OpType(OP.TYPE, index + index_offset, type_map[data[index].name]))
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
                            error(Error.PARSE, f"Found wrong codeBlock closing!", expected = (')',data[index].name), flags = LogFlag.FAIL | LogFlag.EXPECTED)
                    case "{":
                        if codeBlock_stack[-1].type != CB.CODE:
                            error(Error.PARSE, f"Found wrong codeBlock closing!", expected = ('}',data[index].name), flags = LogFlag.FAIL | LogFlag.EXPECTED)
                codeBlock_stack[-2].tokens.append(codeBlock_stack.pop())
                index_offset -= 1
            case _:
                error(Error.PARSE, "unreachable!", flags = LogFlag.FAIL)
        index += 1
    return codeBlock_stack[-1]

def Parse_token(file_path: str, loc: tuple[int, int], data: str) -> list[Token]:
    global Com_Mode

    if (n:=TOKENS.COUNT.value) != (m:=9):
        error(Error.ENUM, f"{BOLD_}Exhaustive operation parsing protection in {BOLD_}Parse_token{BACK_}", expected = (m,n), flags = LogFlag.FAIL | LogFlag.EXPECTED)

    ret: list[Token] = []

    if data in set_token:
        if not loc == (0,len(data)+1) :
            error(Error.PARSE, f"Compilation option token found not on the begining of a file, but on `{bolden(loc)}`!")
        Com_Mode = COMMODE.SET
        ret += [Token(TOKENS.NOTOKEN, data)]
        data = ""
    elif Com_Mode == COMMODE.SET:
        if not data in option_token:
            error(Error.PARSE, f"Wrong option for `{bolden("#mode")}` probided, found `{bolden(data)}`")
        Com_Mode = option_token[data]
        ret += [Token(TOKENS.NOTOKEN, data)]
        data = ""
    elif data in alone_token:
        ret += [Token(alone_token[data], data)]
        data = ""
    elif data in protected_token:
        if data == "dos" and Com_Mode != COMMODE.DOS:
            error(Error.PARSE, f"Usage of `{bolden("dos")}` token in non-DOS mode of compilation")
        ret += [Token(protected_token[data], data)]
        data = ""
    elif data in indifferent_token:
        ret += [Token(indifferent_token[data], data)]
        data = ""
    else:
        for x in list(alone_token.keys()):
            if data.startswith(x) or data.endswith(x):
                error(Error.TOKENIZE, f"at {file_path}:{loc[0]+1}:{loc[1]-len(data)} keyword starts with disallowed token `{BOLD_}{x}{BACK_}` in `{BOLD_}{data}{BACK_}`", flags = LogFlag.FAIL)
        for x in indifferent_token.keys():
            if data.find(x) != -1:
                (before, token, after) = data.partition(x)
                if before:
                    ret += Parse_token(file_path, loc, before)
                ret += Parse_token(file_path, loc, token)
                ret += Parse_token(file_path, loc, after)
                data = ""
                break

        if data.isnumeric():
            ret += [Token(TOKENS.NUM, data)]
            data = ""
        if data:
            if data[0].isdigit():
                error(Error.TOKENIZE, f"name token cannot begin with a number", flags = LogFlag.FAIL)
            ret += [Token(TOKENS.NAME, data)]
            #assert False, "unknown keyword %s" % (data)

    return ret

def Parse_line(file_path: str, line: int, data: str) -> list:
    ret = []
    t = ""
    index = 0
    if data.find("//") != -1:
        (before, _, after) = data.partition("//")
        data = before
    while index < len(data):
        if data[index].isspace():
            ret += Parse_token(file_path, (line, index+1), t)
            t = ""
        else:
            t = t + data[index]
        index += 1
    if t:
        ret += Parse_token(file_path, (line, index+1), t)
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

def Parse_file(input: str) -> list:
    data = []
    with open(input, 'r') as f:
        data = f.readlines()
    #for x in [op for row, line in enumerate(data) for op in Parse_line(input, row, line)]:
        #print(x)
    ops: list[OpType] = Third_token_parse(Secound_token_parse(First_token_parse([op for row, line in enumerate(data) for op in Parse_line(input, row, line)])))
    #Print_codeBlock_ops(ops)
    return ops
    #return Parse_jump(resolve_names([op for row, line in enumerate(data) for op in Parse_line(input, row, line)]))

# ------------------------------------------------------
# -------------------- TEST SECTION --------------------
# ------------------------------------------------------
class dataHolder:
    data: str = ""
    def write(self, string):
        self.data = self.data + string
    
    def compare_with_file(self, file_path):
        data: str = ""
        with open(file_path, 'r') as f:
            data = f.read()
        return data == self.data

def record_test():
    for x in glob.glob("./tests/*.mand"):
        with open(x[:-5]+".txt", "w") as f:
            print(x)
            simulate_data(Parse_file(x), out = f)

def compare_test():
    for x in glob.glob("./tests/*.mand"):
        dh: dataHolder = dataHolder()
        print(x)
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
                error(Error.CMD, f"Wrong file provided, compiller couldn't find file at a `%s` location" % (input_file), flags = LogFlag.WARNING)
            data = Parse_file(input_file)
            
            compile_data(data)
        case '-s':
            input_file, argv = unpack(argv)

            if not os.path.isfile(input_file):
                error(Error.CMD, f"Wrong file provided, compiller couldn't find file at a `{input_file}` location", flags = LogFlag.WARNING)
            data = Parse_file(input_file)
            
            simulate_data(data)
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
