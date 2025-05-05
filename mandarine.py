#!/usr/bin/env python3

import sys
import subprocess
from enum import Enum, auto, Flag
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
    LINUX       = auto()
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
    loc:        tuple[str, int, int]
    name:       str

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
    
def gen_asm_debug(operation: str, register: str, data: str | int, dataType: DT | None, Com_state: ComState = ComState.NONE, ax_used: bool = False, force_value: bool = False) -> tuple[bool, str]:
    
    #if Com_state == ComState.CONDITION:
        #force_value = True

    ret: str = ""
    if isinstance(data, int):
        ax_used = True
        ret = f"\t{operation} {register + 'x, ' if register else ''}{data}\n"
    else:
        match dataType:
            case DT.UINT8:
                if ax_used and register and operation == 'mov':
                    ret = f"\txor {register}x, {register}x\n"
                    ax_used = False
                ret += f"\t{operation} {register + 'l, ' if register else ''}[{data}]\n"
            case DT.UINT16:
                ax_used = True
                ret = f"\t{operation} {register + 'x, ' if register else ''}[{data}]\n"
            case DT.UINT8MEM:
                if force_value:
                    (ax_used, ret) = gen_asm_debug(operation, register, data, DT.UINT8, ax_used)
                else:
                    if ax_used and register and operation == 'mov':
                        ret = f"\txor {register}x, {register}x\n"
                        ax_used = False
                    ret += f"\t{operation} {register + 'x, ' if register else ''}offset {data}\n"
            case DT.UINT16MEM:
                if force_value:
                    (ax_used, ret) = gen_asm_debug(operation, register, data, DT.UINT16, ax_used)
                else:
                    ax_used = True
                    ret = f"\t{operation} {register + 'x, ' if register else ''}offset {data}\n"
            case _:
                print(dataType)
                error(Error.COMPILE, f"Unknown type, {dataType.name}")
    #print((ax_used, ret))
    return (ax_used, ret)

def compile_data(data: list[dict]) -> None:

    if (n:=OP.COUNT.value) != (m:=36):
        error(Error.ENUM, f"{BOLD_}Exhaustive operation parsing protection in {BOLD_}compile_data{BACK_}", expected = (m,n), flags = LogFlag.FAIL | LogFlag.EXPECTED)
    
    heap = bytearray(HEAP_SIZE)
    heap_end = 0
    stack = []
    ip = 0
    state: ComState = ComState.NONE
    temp1: str = ""
    condition: OP
    last_type: DT
    debug_counter = -1
    begin_arith: bool = False
    
    buffor_start: str = ""
    buffor_data: str = ""
    buffor_code: str = ""

    ax_used: bool = False
    
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
            match x.type:
                case OP.NUM:
                    stack.append(int(x.value))
                case OP.STRING:
                    if ComState.VARDEF in state:
                        
                        match data.vars[temp1].type:
                            case DT.UINT8MEM:
                                while (n:=x.value).find('\\n') != -1:
                                    (string_before, string_center, string_after) = x.value.partition('\\n')
                                    x.value = f"{string_before}\", 10,\"{string_after}"
                                buffor_data = buffor_data + f"\t{data.vars[temp1].name} db \"{x.value}$\"\n"
                                #for y in range(len(x.value)):
                                    #heap[heap_end+y] = ord(x.value[y])
                                #heap[heap_end+len(x.value)] = ord('$')
                                #data.vars[temp1].value = bytearray(bfromNum(data.vars[temp1].type, heap_end))
                                #heap_end += len(x.value)+1
                            case DT.UINT16MEM:
                                while (n:=x.value).find('\\n') != -1:
                                    (string_before, string_center, string_after) = x.value.partition('\\n')
                                    x.value = f"{string_before}\", 10,\"{string_after}"
                                buffor_data = buffor_data + f"\t{data.vars[temp1].name} dw \"{x.value}$\"\n"
                                #for y in range(len(x.value)):
                                    #heap[heap_end+y*2] = ord(x.value[y])
                                #heap[heap_end+len(x.value)*2] = ord('$')
                                #data.vars[temp1].value = bytearray(bfromNum(data.vars[temp1].type, heap_end))
                                #heap_end += (len(x.value)+1)*2
                        state = ComState.NONE
                    else:
                        stack.append(data.vars[temp1].name)
                        ###buffor_code += buffor_code + f"\tmov ax, {data.vars[temp1].name}"
                        #for y in range(len(x.value)):
                            #heap[heap_end+y] = ord(x.value[y])
                        #heap[heap_end+len(x.value)] = ord('$')
                        #stack.append(int.from_bytes(bfromNum(data.vars[temp1].type, heap_end)))
                        #heap_end += len(x.value)+1
                case OP.ADD:
                    buffor_code = buffor_code + ";; -- ADD --\n"
                    if begin_arith:
                        a = stack.pop()
                        (ax_used, op) = gen_asm_debug('add', 'a', a, None if isinstance(a, int) else data.vars[a].type, state, ax_used)
                        buffor_code = buffor_code + op
                    else:
                        begin_arith = True
                        a = stack.pop()
                        b = stack.pop()
                        if isinstance(b, int):
                            ax_used = True
                            buffor_code = buffor_code + f"\tmov ax, {b}\n"
                        else:
                            (ax_used, op) = gen_asm_debug('mov', 'a', b, data.vars[b].type, state, ax_used)
                            buffor_code = buffor_code + op
                        if isinstance(a, int):
                            ax_used = True
                            buffor_code = buffor_code + f"\tadd ax, {a}\n"
                        else:
                            (ax_used, op) = gen_asm_debug('add', 'a', a, data.vars[a].type, state, ax_used, force_value=True)
                            buffor_code = buffor_code + op
                        #buffor_code = buffor_code + f"\tadd ax, {a if isinstance(a, int) else f'[{a}]'}\n"
                case OP.SUB:
                    buffor_code = buffor_code + ";; -- SUB --\n"
                    if begin_arith:
                        a = stack.pop()
                        (ax_used, op) = gen_asm_debug('sub', 'a', a, None if isinstance(a, int) else data.vars[a].type, state, ax_used)
                        buffor_code = buffor_code + op
                    else:
                        begin_arith = True
                        a = stack.pop()
                        b = stack.pop()
                        if isinstance(b, int):
                            ax_used = True
                            buffor_code = buffor_code + f"\tmov ax, {b}\n"
                        else:
                            (ax_used, op) = gen_asm_debug('mov', 'a', b, data.vars[b].type, state, ax_used)
                            buffor_code = buffor_code + op
                        if isinstance(a, int):
                            ax_used = True
                            buffor_code = buffor_code + f"\tsub ax, {a}\n"
                        else:
                            (ax_used, op) = gen_asm_debug('sub', 'a', a, data.vars[b].type, state, ax_used, force_value=True)
                            buffor_code = buffor_code + op
                        #buffor_code = buffor_code + f"\tsub ax, {a if isinstance(a, int) else f'[{a}]'}\n"
                case OP.MUL:
                    buffor_code = buffor_code + ";; -- MUL --\n"
                    if begin_arith:
                        a = stack.pop()
                        (ax_used, op) = gen_asm_debug('mul', '', a, None if isinstance(a, int) else data.vars[a].type, state, ax_used)
                        buffor_code = buffor_code + op
                    else:
                        begin_arith = True
                        a = stack.pop()
                        b = stack.pop()
                        if isinstance(b, int):
                            ax_used = True
                            buffor_code = buffor_code + f"\tmov ax, {b}\n"
                        else:
                            (ax_used, op) = gen_asm_debug('mov', 'a', b, data.vars[b].type, state, ax_used)
                            buffor_code = buffor_code + op
                        if isinstance(a, int):
                            ax_used = True
                            buffor_code = buffor_code + f"\tmul {a}\n"
                        else:
                            (ax_used, op) = gen_asm_debug('mul', '', a, data.vars[b].type, state, ax_used, force_value=True)
                            buffor_code = buffor_code + op
                        #buffor_code = buffor_code + f"\tsub ax, {a if isinstance(a, int) else f'[{a}]'}\n"
                case OP.DIV:
                    buffor_code = buffor_code + ";; -- DIV --\n"
                    if begin_arith:
                        a = stack.pop()
                        (ax_used, op) = gen_asm_debug('div', '', a, None if isinstance(a, int) else data.vars[a].type, state, ax_used)
                        buffor_code = buffor_code + op
                    else:
                        begin_arith = True
                        a = stack.pop()
                        b = stack.pop()
                        if isinstance(b, int):
                            ax_used = True
                            buffor_code = buffor_code + f"\tmov ax, {b}\n"
                        else:
                            (ax_used, op) = gen_asm_debug('mov', 'a', b, data.vars[b].type, state, ax_used)
                            buffor_code = buffor_code + op
                        if isinstance(a, int):
                            ax_used = True
                            buffor_code = buffor_code + f"\tmov cx, {a}\n"
                            buffor_code = buffor_code + f"\tdiv cl\n"
                        else:
                            (ax_used, op) = gen_asm_debug('div BYTE', '', a, data.vars[b].type, state, ax_used, force_value=True)
                            buffor_code = buffor_code + op
                        #buffor_code = buffor_code + f"\tdiv BYTE {a if isinstance(a, int) else f'[{a}]'}\n"
                        buffor_code = buffor_code + f"\txor ah, ah\n"
                case OP.MOD:
                    buffor_code = buffor_code + ";; -- MOD --\n"
                    if begin_arith:
                        a = stack.pop()
                        (ax_used, op) = gen_asm_debug('div', '', a, None if isinstance(a, int) else data.vars[a].type, state, ax_used)
                        buffor_code = buffor_code + op
                    else:
                        begin_arith = True
                        a = stack.pop()
                        b = stack.pop()
                        if isinstance(b, int):
                            ax_used = True
                            buffor_code = buffor_code + f"\tmov ax, {b}\n"
                        else:
                            (ax_used, op) = gen_asm_debug('mov', 'a', b, data.vars[b].type, state, ax_used)
                            buffor_code = buffor_code + op
                        if isinstance(a, int):
                            ax_used = True
                            buffor_code = buffor_code + f"\tmov cx, {a}\n"
                            buffor_code = buffor_code + f"\tdiv cl\n"
                        else:
                            (ax_used, op) = gen_asm_debug('div BYTE', '', a, data.vars[b].type, state, ax_used, force_value=True)
                            buffor_code = buffor_code + op
                        #buffor_code = buffor_code + f"\tdiv BYTE {a if isinstance(a, int) else f'[{a}]'}\n"
                        buffor_code = buffor_code + f"\tmov al, ah\n"
                        buffor_code = buffor_code + f"\txor ah, ah\n"
                case OP.SHL:
                    if begin_arith:
                        a = stack.pop()
                        ax_used = True
                        if isinstance(a, int):
                            buffor_code = buffor_code + f"\tshl ax, {a}\n"
                        else:
                            (ax_used, op) = gen_asm_debug('mov', 'c', a, data.vars[b].type, state, ax_used, force_value=True)
                            buffor_code = buffor_code + op
                            buffor_code = buffor_code + f"\tshl ax, cl\n"
                    else:
                        begin_arith = True
                        a = stack.pop()
                        b = stack.pop()
                        ax_used = True
                        if isinstance(b, int):
                            (ax_used, op) = gen_asm_debug('mov', 'a', a, data.vars[b].type, state, ax_used)
                            buffor_code = buffor_code + op
                            buffor_code = buffor_code + f"\tshl ax, {b}\n"
                        else:
                            (ax_used, op) = gen_asm_debug('mov', 'a', a, data.vars[b].type, state, ax_used)
                            buffor_code = buffor_code + op
                            (ax_used, op) = gen_asm_debug('mov', 'c', b, data.vars[b].type, state, ax_used, force_value=True)
                            buffor_code = buffor_code + op
                            buffor_code = buffor_code + f"\tshl ax, cl\n"
                case OP.SHR:
                    if begin_arith:
                        a = stack.pop()
                        ax_used = True
                        if isinstance(a, int):
                            buffor_code = buffor_code + f"\tshr ax, {a}\n"
                        else:
                            (ax_used, op) = gen_asm_debug('mov', 'c', a, data.vars[b].type, state, ax_used, force_value=True)
                            buffor_code = buffor_code + op
                            buffor_code = buffor_code + f"\tshr ax, cl\n"
                    else:
                        begin_arith = True
                        a = stack.pop()
                        b = stack.pop()
                        ax_used = True
                        if isinstance(b, int):
                            (ax_used, op) = gen_asm_debug('mov', 'a', a, data.vars[b].type, state, ax_used)
                            buffor_code = buffor_code + op
                            buffor_code = buffor_code + f"\tshr ax, {b}\n"
                        else:
                            (ax_used, op) = gen_asm_debug('mov', 'a', a, data.vars[b].type, state, ax_used)
                            buffor_code = buffor_code + op
                            (ax_used, op) = gen_asm_debug('mov', 'c', b, data.vars[b].type, state, ax_used, force_value=True)
                            buffor_code = buffor_code + op
                            buffor_code = buffor_code + f"\tshr ax, cl\n"
                case OP.IF:
                    buffor_code = buffor_code + ";; -- IF --\n"
                    state = ComState.CONDITION
                case OP.WHILE:
                    buffor_code = buffor_code + ";; -- WHILE --\n"
                    state = ComState.CONDITION
                case OP.EQUAL:
                    if len(stack) > 0:
                        a = stack.pop()
                        if isinstance(a, int):
                            buffor_code = buffor_code + f"\tmov bx, {a}\n"
                        else:
                            if data.vars[a].type in [DT.UINT8]:
                                buffor_code = buffor_code + f"\tmov bl, [{a}]\n"
                            elif data.vars[a].type in [DT.UINT16]:
                                buffor_code = buffor_code + f"\tmov bx, [{a}]\n"
                            else:
                                error(Error.COMPILE, "unknown type for comparison")
                    else:
                        buffor_code = buffor_code + f"\tmov bx, ax\n"
                    #buffor_code = buffor_code + f"\tmov bx, ax\n"
                    condition = x.type
                    begin_arith = False
                case OP.GREATER:
                    if len(stack) > 0:
                        a = stack.pop()
                        if isinstance(a, int):
                            buffor_code = buffor_code + f"\tmov bx, {a}\n"
                        else:
                            if data.vars[a].type in [DT.UINT8]:
                                buffor_code = buffor_code + f"\txor bx, bx\n"
                                buffor_code = buffor_code + f"\tmov bl, [{a}]\n"
                            elif data.vars[a].type in [DT.UINT16]:
                                buffor_code = buffor_code + f"\tmov bx, [{a}]\n"
                            else:
                                error(Error.COMPILE, "unknown type for comparison")
                    else:
                        buffor_code = buffor_code + f"\tmov bx, ax\n"
                    condition = x.type
                    begin_arith = False
                case OP.LESS:
                    if len(stack) > 0:
                        a = stack.pop()
                        if isinstance(a, int):
                            buffor_code = buffor_code + f"\tmov bx, {a}\n"
                        else:
                            if data.vars[a].type in [DT.UINT8]:
                                buffor_code = buffor_code + f"\tmov bl, [{a}]\n"
                            elif data.vars[a].type in [DT.UINT16]:
                                buffor_code = buffor_code + f"\tmov bx, [{a}]\n"
                            else:
                                error(Error.COMPILE, "unknown type for comparison")
                    else:
                        buffor_code = buffor_code + f"\tmov bx, ax\n"
                    condition = x.type
                    begin_arith = False
                case OP.GE:
                    if len(stack) > 0:
                        a = stack.pop()
                        if isinstance(a, int):
                            buffor_code = buffor_code + f"\tmov bx, {a}\n"
                        else:
                            if data.vars[a].type in [DT.UINT8]:
                                buffor_code = buffor_code + f"\tmov bl, [{a}]\n"
                            elif data.vars[a].type in [DT.UINT16]:
                                buffor_code = buffor_code + f"\tmov bx, [{a}]\n"
                            else:
                                error(Error.COMPILE, "unknown type for comparison")
                    else:
                        buffor_code = buffor_code + f"\tmov bx, ax\n"
                    condition = x.type
                    begin_arith = False
                case OP.LE:
                    if len(stack) > 0:
                        a = stack.pop()
                        if isinstance(a, int):
                            buffor_code = buffor_code + f"\tmov bx, {a}\n"
                        else:
                            if data.vars[a].type in [DT.UINT8]:
                                buffor_code = buffor_code + f"\tmov bl, [{a}]\n"
                            elif data.vars[a].type in [DT.UINT16]:
                                buffor_code = buffor_code + f"\tmov bx, [{a}]\n"
                            else:
                                error(Error.COMPILE, "unknown type for comparison")
                    else:
                        buffor_code = buffor_code + f"\tmov bx, ax\n"
                    condition = x.type
                    begin_arith = False
                case OP.CONJUMP:
                    if len(stack) > 0:
                        a = stack.pop()
                        if isinstance(a, int):
                            buffor_code = buffor_code + f"\tmov ax, {a}\n"
                        else:
                            if data.vars[a].type in [DT.UINT8]:
                                if ax_used:
                                    buffor_code = buffor_code + f"\txor ax, ax\n"
                                    ax_used = False
                                buffor_code = buffor_code + f"\tmov al, [{a}]\n"
                            elif data.vars[a].type in [DT.UINT16]:
                                ax_used = True
                                buffor_code = buffor_code + f"\tmov ax, [{a}]\n"
                            else:
                                error(Error.COMPILE, "unknown type for comparison")
                    else:
                        pass
                    buffor_code = buffor_code + "\tcmp ax, bx\n"
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
                    begin_arith = False
                case OP.JUMP:
                    buffor_code = buffor_code + f"\tjmp {x.value}\n"
                    state = ComState.NONE
                case OP.LABEL:
                    buffor_code = buffor_code + f"{x.value}:\n"
                case OP.COPY:
                    a = stack.pop()
                    stack.append(a)
                    stack.append(a)
                case OP.PRINT:
                    a = stack.pop()
                    #out.write(str(a))
                case OP.PRINT_NL:
                    #out.write('\n')
                    pass
                case OP.PRINT_AND_NL:
                    a = stack.pop()
                    #out.write(str(a))
                    #out.write('\n')
                case OP.PRINT_CHAR:
                    a = stack.pop()
                    #out.write(chr(a))
                case OP.TYPE:
                    pass
                case OP.BUF:
                    if ComState.VARDEF in state:
                        match data.vars[temp1].type:
                            case DT.UINT8MEM:
                                a = stack.pop()
                                buffor_data = buffor_data + f"\t{data.vars[temp1].name} db {a-2},{a-1} dup (0)\n"
                            case DT.UINT16MEM:
                                a = stack.pop()
                                buffor_data = buffor_data + f"\t{data.vars[temp1].name} dw {a-2},{a-1} dup (0)\n"
                        #data.vars[temp1].value
                        state = ComState.NONE
                    else:
                        error(Error.COMPILE, "Buf used in wrong position")
                case OP.VAR:
                    #print(stack, ip, state)
                    if ComState.ARITHMETIC in state or ComState.CONDITION in state:
                        if data.vars[x.value].type in [DT.UINT8, DT.UINT16]:
                            #buffor_code += buffor_code + f"\t{data.vars[x.value].name} dw {a} dup (?)\n"
                            stack.append(data.vars[x.value].name)
                        elif data.vars[x.value].type in [DT.UINT8MEM, DT.UINT16MEM]:
                            stack.append(data.vars[x.value].name)
                        else:
                            error(Error.COMPILE, "Only u8, u16, u8p and u16p are implemented yet")
                    else:
                        temp1 = x.value
                        if not data.vars[x.value].defined:
                            if data.vars[x.value].type in [DT.UINT8]:
                                buffor_data = buffor_data + f"\t{data.vars[temp1].name} db ?\n"
                            elif data.vars[x.value].type in [DT.UINT16]:
                                buffor_data = buffor_data + f"\t{data.vars[temp1].name} dw ?\n"
                            data.vars[x.value].defined = True
                        stack.append(data.vars[x.value].name)
                    last_type = data.vars[x.value].type
                case OP.SET:
                    state = ComState.VARDEF | ComState.ARITHMETIC
                    stack.pop()
                case OP.DOS:
                    a = stack.pop()
                    if a == 9:
                        if len(stack) > 0:
                            b = stack.pop()
                            if isinstance(b, str):
                                buffor_code = buffor_code + f"\tmov dx, offset {b}\n"
                            else:
                                error(Error.COMPILE, "int type in dos call for address")
                        else:
                            buffor_code = buffor_code + f"\tmov dx, ax\n"
                        if ax_used:
                            buffor_code = buffor_code + "\txor ax, ax\n"  
                        ax_used = True
                        buffor_code = buffor_code + "\tmov ah, 9\n"
                        buffor_code = buffor_code + "\tint 21h\n"
                    elif a == 10:
                        if ax_used:
                            buffor_code = buffor_code + "\txor ax, ax\n"
                        ax_used = True
                        buffor_code = buffor_code + "\tmov ah, 10\n"
                        b = stack.pop()
                        if isinstance(b, str):
                            buffor_code = buffor_code + f"\tmov dx, offset {b}\n"
                        else:
                            error(Error.COMPILE, "int type in dos call for address")
                        buffor_code = buffor_code + "\tint 21h\n"
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
                                #out.write(chr(heap[c+x]))
                                pass
                        elif b == 2:
                            for x in range(d):
                                sys.stderr.write(chr(heap[c+x]))
                        else:
                            error(Error.SIMULATE, "other file descriptors than `1` and `2` are not supported yet, skipping...", exitAfter=False)

                case OP.MEMWRITE:
                    buffor_code += ";; -- MEMWRITE --\n"
                    a = stack.pop()
                    if len(stack) > 0:
                        b = stack.pop()
                        if isinstance(b, str):
                            if isinstance(a, str):
                                (_, op) = gen_asm_debug('mov', 'b', a, data.vars[a].type, force_value=True)
                                buffor_code = buffor_code + op
                                buffor_code = buffor_code + f"\tmov si, WORD PTR [{b}]\n"
                                buffor_code = buffor_code + f"\tmov BYTE PTR [si], {'bx' if data.vars[a].type == DT.UINT16MEM else 'bl'}\n"
                            else:
                                buffor_code = buffor_code + f"\tmov si, WORD PTR [{b}]\n"
                                buffor_code = buffor_code + f"\tmov BYTE PTR [si], {a}\n"
                        else:
                            buffor_code = buffor_code + f"\tmov [ax], {b}\n"
                            pass
                            error(Error.COMPILE, "int type in memwrite for address")
                    else:
                        if isinstance(a, str):
                            buffor_code = buffor_code + f"\tmov di, ax\n"
                            buffor_code = buffor_code + f"\tmov BYTE PTR [di], [{a}]\n"
                        else:
                            buffor_code = buffor_code + f"\tmov di, ax\n"
                            buffor_code = buffor_code + f"\tmov BYTE PTR [di], {a}\n"

                    #print(ip, a, data.vars[temp1].type)
                    #match data.vars[temp1].type:
                        #case DT.UINT8MEM:
                            #heap[b] = bfromNum(DT.UINT8, a)[0]
                        #case DT.UINT16MEM:
                            #heap[b:b+2] = bfromNum(DT.UINT16, a)
                        #case _:
                            #error(Error.SIMULATE, "MEM WRITE implemented only to UINT8MEM and UINT16MEM yet!")
                case OP.MEMREAD:
                    # TODO - bx_used
                    buffor_code += ";; -- MEMREAD --\n"
                    if len(stack) > 0:
                        #print(stack)
                        a = stack.pop()
                        if isinstance(a, int):
                            error(Error.COMPILE, "Wrong Type, should be str not int")
                        else:
                            if data.vars[a].type in [DT.UINT8MEM]:
                                if ax_used:
                                    buffor_code = buffor_code + f"\txor ax, ax\n"
                                    ax_used = False
                                buffor_code = buffor_code + f"\tmov al, [{a}]\n"
                            elif data.vars[a].type in [DT.UINT16MEM]:
                                ax_used = True
                                buffor_code = buffor_code + f"\tmov ax, [{a}]\n"
                            else:
                                error(Error.COMPILE, "Wrong Type, should be pointer")
                    else:
                        buffor_code += f"\tmov si, ax\n"
                        (ax_used, op) = gen_asm_debug('mov', 'a', 'si', DT.UINT8, ax_used=ax_used, force_value=True)
                        buffor_code += op
                        ax_used = True
                    begin_arith = True
                        #buffor_code = buffor_code + "\tmov ax, \n"
                    #stack.append(int.from_bytes(data.vars[a].type))
                    #if isinstance(a, str):
                        #buffor_code = buffor_code + f"\tmov ax, [{a}]\n"
                    #else:
                        #buffor_code = buffor_code + f"\tmov ax, {a}\n"
                    #else:
                        #error(Error.COMPILE, "int type in memread for address")
                    #match last_type:
                        #case DT.UINT8MEM:
                            #stack.append(int.from_bytes(heap[a:a+1]))
                        #case DT.UINT16MEM:
                            #stack.append(int.from_bytes(heap[a:a+2]))
                        #case _:
                            #error(Error.SIMULATE, "MEMREAD implemented only to UINT8MEM and UINT16MEM yet!")
                    #print(stack, [x for x in heap[0:100]])

                case OP.COLON:
                    if ComState.VARDEF in state:
                        if len(stack) > 0:
                            a = stack.pop()
                            if isinstance(a, int):
                                buffor_code = buffor_code + f"\tmov [{data.vars[temp1].name}], {a}\n"
                            else:
                                (_, op) = gen_asm_debug('mov', 'b', a, data.vars[a].type, force_value=True)
                                buffor_code = buffor_code + op
                                buffor_code = buffor_code + f"\tmov [{data.vars[temp1].name}], {'bx' if data.vars[temp1].type == DT.UINT16MEM else 'bl'}\n"
                        else:
                            if data.vars[temp1].type in [DT.UINT8]:
                                buffor_code = buffor_code + f"\tmov [{data.vars[temp1].name}], al\n"
                            elif data.vars[temp1].type in [DT.UINT16]:
                                buffor_code = buffor_code + f"\tmov [{data.vars[temp1].name}], ax\n"
                            else:
                                error(Error.COMPILE, "Unknown type")
                            #buffor_code = buffor_code + f"\tmov [{data.vars[temp1].name}], ax\n"
                        #data.vars[temp1].value = bytearray(bfromNum(data.vars[temp1].type, stack[-1]))
                    state = ComState.NONE
                    begin_arith = False
            #print(stack, x)
            #input()
        buffor_code = buffor_code + "\tmov ah, 4Ch\n\tint 21h\nEND start"
        #print(buffor_start, buffor_data, buffor_code)
        return buffor_start + buffor_data + buffor_code

def simulate_data(data: codeBlock, out = sys.stdout):
    
    if (n:=OP.COUNT.value) != (m:=36):
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

    if (n:=OP.COUNT.value) != (m:=36):
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
            case OP.MEMREAD:
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
    
    if (n:=OP.COUNT.value) != (m:=36):
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

    if (n:=OP.COUNT.value) != (m:=36):
        error(Error.ENUM, f"{BOLD_}Exhaustive operation parsing protection in {BOLD_}Secound_token_parse{BACK_}", expected = (m,n), flags = LogFlag.FAIL | LogFlag.EXPECTED)
    if (n:=CB.COUNT.value) != (m:=5):
        error(Error.ENUM, f"{BOLD_}Exhaustive codeBlock parsing protection in {BOLD_}Secound_token_parse{BACK_}", expected = (m,n), flags = LogFlag.FAIL | LogFlag.EXPECTED)
    
    index = 0
    while index < len(data.tokens):
        match data.tokens[index].type:
            case OP.TYPE:
                if index+1 < len(data.tokens):
                    if data.tokens[index+1].type == OP.VAR:
                        if (n:=Var(data.tokens[index].value, (m:=(data.tokens[index+1].value)))) not in data.vars.values():
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
                if (n:=data.tokens[index].value) not in data.vars.keys():
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

    if (n:=OP.COUNT.value) != (m:=36):
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
                codeBlock_stack[-1].tokens.append(OpType(operand_map[data[index].name], index + index_offset, data[index].loc))
            case TOKENS.NAME:
                codeBlock_stack[-1].tokens.append(OpType(OP.VAR, index + index_offset, data[index].loc, data[index].name))
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

def Parse_token(file_path: str, loc: tuple[int, int], data: str) -> list[Token]:

    global Com_Mode

    if (n:=TOKENS.COUNT.value) != (m:=11):
        error(Error.ENUM, f"{BOLD_}Exhaustive operation parsing protection in {BOLD_}Parse_token{BACK_}", expected = (m,n), flags = LogFlag.FAIL | LogFlag.EXPECTED)

    ret: list[Token] = []

    if data in set_token:
        if not loc == (0,len(data)):
            error(Error.PARSE, f"Compilation option token found not on the begining of a file, but on `{bolden(loc)}`!")
        Com_Mode = COMMODE.SET
        ret += [Token(TOKENS.NOTOKEN, (file_path,)+loc, data)]
        data = ""
    elif Com_Mode == COMMODE.SET:
        if data not in option_token:
            error(Error.PARSE, f"Wrong option for `{bolden("#mode")}` probided, found `{bolden(data)}`")
        Com_Mode = option_token[data]
        ret += [Token(TOKENS.NOTOKEN, (file_path,)+loc, data)]
        data = ""
    elif data in alone_token:
        ret += [Token(alone_token[data], (file_path,)+loc, data)]
        data = ""
    elif data in protected_token:
        if data == "dos" and Com_Mode != COMMODE.DOS:
            print(Com_Mode)
            error(Error.PARSE, f"Usage of `{bolden("dos")}` token in non-DOS mode of compilation")
        elif data == "linux" and Com_Mode != COMMODE.LINUX:
            error(Error.PARSE, f"Usage of `{bolden("linux")}` token in non-LINUX mode of compilation")
        ret += [Token(protected_token[data], (file_path,)+loc, data)]
        data = ""
    elif data in indifferent_token:
        ret += [Token(indifferent_token[data], (file_path,)+loc, data)]
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
            ret += [Token(TOKENS.NUM, (file_path,)+loc, data)]
            data = ""
        if data:
            if data[0].isdigit():
                error(Error.TOKENIZE, "name token cannot begin with a number", flags = LogFlag.FAIL)
            ret += [Token(TOKENS.NAME, (file_path,)+loc, 'v'+data)]
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
                    tokens.append(Token(TOKENS.STRING, loc, token))
                    token = ""
                    string_literal = False
                else:
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
