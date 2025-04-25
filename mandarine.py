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

class TOKENS(Enum):
    WORD        = auto()
    OPERAND     = auto()
    NAME        = auto()
    TYPE        = auto()
    CODEOPEN    = auto()
    CODECLOSE   = auto()
    NUM         = auto()
    COUNT       = auto()

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
    WHILE       = auto()
    JUMP        = auto()
    COPY        = auto()
    PRINT       = auto()
    PRINT_NL    = auto()
    PRINT_AND_NL= auto()
    PRINT_CHAR  = auto()
    VAR         = auto()
    TYPE        = auto()
    COUNT       = auto()

class DT(Enum):
    UINT8       = auto()
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
    startvalue: bytearray = field(default_factory=bytearray)
class codeBlock:
    id:         int = -1
    type:       CB = CB.COMPILETIME
    tokens:     list[Token | typing.Self] = []
    vars:       list[Var]

    def __init__(self, id = -1, tokens = [], vars = []):
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
    jmp:        int = -1
    codeblock:  codeBlock = codeBlock()

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

def compile_data(data: list[dict]):
    assert False, "not implemented yet"

def simulate_data(data: list[dict], out = sys.stdout):
    assert OP.COUNT.value == 16, "Exhaustive token counter protection"
    heap = bytearray(HEAP_SIZE)
    stack = []
    overjump = False
    ip = 0
    while ip < len(data):
        x = data[ip]
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
            case OP.IF:
                a = stack.pop()
                if not a:
                    ip = x.jmp
                    continue
            case OP.WHILE:
                pass
            case OP.DIACRITIC:
                a = stack.pop()
                if not a:
                    ip = x.jmp
                    overjump = True
                    continue
            case OP.END:
                if x.jmp != -1 and not overjump:
                    ip = x.jmp
                    continue
                overjump = False
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
            case OP.VAR | OP.SET | OP.UINT8:
                assert False, "unreachable %s | ip -> %d" % (x.type.name, ip)
            case _:
                assert False, "unreachable %s | ip -> %d" % (x.type.name, ip)
        ip += 1

def unpack(arr: list) -> tuple[typing.Any, list]:
    if len(argv) < 1:
        error(Error.CMD, "Not enough arguments!", LogFlag.WARNING)
    return (arr[0], arr[1:])

alone_token: dict[str, TOKENS] = {
    "."     : TOKENS.WORD,
    ".n"    : TOKENS.WORD,
    "..n"   : TOKENS.WORD,
    ".c"    : TOKENS.WORD,
}

protected_token: dict[str, TOKENS] = {
    "if"    : TOKENS.WORD,
    "while" : TOKENS.WORD,
    "copy"  : TOKENS.WORD,
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
}

operand_map: dict[str, OP] = {
    "while" : OP.WHILE,
    "copy"  : OP.COPY,
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
}

boolean_ops: tuple[OP] = (
    OP.ADD,
    OP.SUB,
    OP.MUL,
    OP.SHL,
    OP.SHR,
    OP.EQUAL,
    OP.GREATER,
    OP.LESS,
    OP.GE,
    OP.LE,
)

type_map: dict[str, DT] = {
    "u8"    : DT.UINT8
}

unprotected_static_token = {
}

def resolve_structures(data: list[OpType]) -> list[OpType]:
    ret = []

    index = 0
    while index < len(data):
        pass
    
    return ret

def resolve_names(data: list[OpType]) -> list[OpType]:
    index = 0
    tmp: OpType
    num: OpType
    while index < len(data):
        if data[index].type == OP.SET:
            if 0 >= index >= len(data)-1:
                error(Error.PARSE, f"Wrong usage of `{BOLD_}={BACK_}`, found at the end or begining of file", flags = LogFlag.FAIL)
            if data[index-1].type != OP.NUM or data[index+1].type != OP.VAR:
                error(Error.PARSE, f"Wrong usage of `{BOLD_}={BACK_}`, couldn't find number or/and var name at either side\n {BOLD_}ip-1 > {data[index-1].type.name}{BACK_} | {BOLD_}ip+1 > {data[index+1].type.name}{BACK_}", flags = LogFlag.FAIL)
            index -= 1
            data.pop(index+1)
            num = data[index].value
            tmp = data.pop(index+1)
            secIndex = index
            while secIndex < len(data):
                if data[secIndex].type == OP.SET:
                    if 0 >= secIndex >= len(data)-1:
                        error(Error.PARSE, f"Wrong usage of `{BOLD_}={BACK_}` during reassigment", flags = LogFlag.FAIL)
                    if data[secIndex+1].type != OP.VAR or data[secIndex+1].value != tmp.value or data[secIndex-1].type != OP.NUM:
                        error(Error.PARSE, f"Wrong usage of `{BOLD_}={BACK_}` during reassigment, couldn't find number ", flags = LogFlag.FAIL)
                    secIndex -= 1
                    data.pop(secIndex+1)
                    data.pop(secIndex+1)
                    num = data[secIndex].value
                    secIndex -= 3
                if data[secIndex].type == OP.VAR and data[secIndex].value == tmp.value:
                    data[secIndex].type = OP.NUM
                    data[secIndex].value = num
                secIndex += 1
        index += 1
    return data

def Parse_jump(data: list[OpType]) -> list[OpType]:
    assert OP.COUNT.value == 16, "Exhaustive token jump parsing protection"
    end_stack = []
    index = 0
    while index < len(data):
        if data[index].type == OP.IF:
            end_stack.append(index)
        if data[index].type == OP.WHILE:
            end_stack.append(index)
        if data[index].type == OP.DIACRITIC:
            pass
            end_stack.append(index)
        if data[index].type == OP.END:
            if len(end_stack):
                x = end_stack.pop()
                match data[x].type:
                    case OP.IF:
                        data[x].jmp = index
                    case OP.WHILE:
                        error(Error.PARSE, f"`{BOLD_}end{BACK_}` after while without `{BOLD_}:{BACK_}` symbol!", flags = LogFlag.FAIL)
                    case OP.DIACRITIC:
                        if len(end_stack):
                            y = end_stack.pop()
                            if data[y].type != OP.WHILE:
                                error(Error.PARSE, "use of `:` without `while` beforehand!", flags = LogFlag.FAIL)
                            data[x].jmp = index
                            data[index].jmp = y
                    case _:
                        error(Error.TOKENIZE, "unreachable or not implemented", flags = LogFlag.FAIL)
        index += 1
    return data

#  IF codeBlock == CB.CONDITION
#  MUST BE ONLY BOOLEAN AND MATH OPERATIONS WITH REASULT ON STACK (temporary)
#

def Parse_condition_block(data: codeBlock) -> codeBlock:

    if (n:=OP.COUNT.value) != (m:=23):
        error(Error.ENUM, f"{BOLD_}Exhaustive operation parsing protection in {BOLD_}Parse_condition_block{BACK_}", expected = (m,n), flags = LogFlag.FAIL | LogFlag.EXPECTED)
    if data.type != CB.CONDITION:
        error(Error.PARSE, f"Passed non-condition type codeblock to {BOLD_}Parse_condition_block{BACK_}", flags = LogFlag.FAIL)

    left: list[OpType] = []
    right: list[OpType] = []

    # left : right -> True : False
    left_or_right: bool = True

    index = 0
    while index < len(data):
        pass
        

def Third_token_parse(data: codeBlock) -> codeBlock:
    
    if (n:=OP.COUNT.value) != (m:=23):
        error(Error.ENUM, f"{BOLD_}Exhaustive operation parsing protection in {BOLD_}Third_token_parse{BACK_}", expected = (m,n), flags = LogFlag.FAIL | LogFlag.EXPECTED)
    if (n:=CB.COUNT.value) != (m:=5):
        error(Error.ENUM, f"{BOLD_}Exhaustive codeBlock parsing protection in {BOLD_}Third_token_parse{BACK_}", expected = (m,n), flags = LogFlag.FAIL | LogFlag.EXPECTED)
    if data.type == CB.COMPILETIME:
        index = 0
        index_offset = 0
        while index < len(data.tokens):
            match data.tokens[index].type:
                case OP.IF:
                    if index+2 >= len(data.tokens):
                        error()
                    if data.tokens[index+1].type != CB.CONDITION:
                        error()
                    data.tokens[index+1] = Third_token_parse(data.tokens[index+1])
                    if data.tokens[index+2].type != CB.CODE:
                        error()
                    index_offset += 1
                    data.tokens[index+2].tokens.append(OpType(OP.LABEL, index+index_offset, f"label{index+index_offset}"))
                case OP.WHILE:
                    if index+2 >= len(data.tokens):
                        error()
                    if data.tokens[index+1].type != CB.CONDITION:
                        error()
                    data.tokens[index+1] = Third_token_parse(data.tokens[index+1])
                    if data.tokens[index+2].type != CB.CODE:
                        error()
                    index_offset += 1
                    data.tokens[index+2].tokens.append(OpType(OP.LABEL, index+index_offset, f"label{index+index_offset}"))


def Secound_token_parse(data: codeBlock, index_offset: int = 0) -> codeBlock:

    if (n:=OP.COUNT.value) != (m:=23):
        error(Error.ENUM, f"{BOLD_}Exhaustive operation parsing protection in {BOLD_}Secound_token_parse{BACK_}", expected = (m,n), flags = LogFlag.FAIL | LogFlag.EXPECTED)
    if (n:=CB.COUNT.value) != (m:=5):
        error(Error.ENUM, f"{BOLD_}Exhaustive codeBlock parsing protection in {BOLD_}Secound_token_parse{BACK_}", expected = (m,n), flags = LogFlag.FAIL | LogFlag.EXPECTED)
    
    index = 0
    while index < len(data.tokens):
        match data.tokens[index].type:
            case OP.TYPE:
                if index+1 < len(data.tokens):
                    if data.tokens[index+1].type == OP.VAR:
                        if not (n:=Var(data.tokens[index].value, data.tokens[index+1].value)) in data.vars:
                            data.vars.append(n)
                            data.tokens.pop(index)
                            index += 1
                        else:
                            error(Error.PARSE, f"var already stated", flags = LogFlag.FAIL)
                    else:
                        error(Error.PARSE, f"no var token after type", flags = LogFlag.FAIL)
                else:
                    error(Error.PARSE, f"type at the end of file", flags = LogFlag.FAIL)
            case OP.VAR:
                if not (n:=data.tokens[index].value) in [x.name for x in data.vars]:
                    error(Error.PARSE, f"Variable `{BOLD_}{n}{BACK_}` stated without assigment!", flags = LogFlag.FAIL)

            case CB.CODE | CB.CONDITION | CB.RESOLVE:
                data.tokens[index].vars = data.vars.copy()
                data.tokens[index] = Secound_token_parse(data.tokens[index], index)
        index += 1
    return data
        
def First_token_parse(data: list[Token]) -> codeBlock:

    if (n:=OP.COUNT.value) != (m:=23):
        error(Error.ENUM, f"{BOLD_}Exhaustive operation parsing protection in {BOLD_}First_token_parse{BACK_}", expected = (m,n), flags = LogFlag.FAIL | LogFlag.EXPECTED)


    ret: codeBlock = codeBlock(0)

    codeBlock_stack: list[codeBlock] = [ret]
    
    codeblock_id_index = 1

    index_offset = 0
    index = 0
    while index < len(data):
        match data[index].type:
            case TOKENS.WORD | TOKENS.OPERAND:
                codeBlock_stack[-1].tokens.append(OpType(operand_map[data[index].name], index + index_offset))
            case TOKENS.NAME:
                codeBlock_stack[-1].tokens.append(OpType(OP.VAR, index + index_offset, data[index].name))
            case TOKENS.NUM:
                codeBlock_stack[-1].tokens.append(OpType(OP.NUM, index + index_offset, int(data[index].name)))
            case TOKENS.TYPE:
                codeBlock_stack[-1].tokens.append(OpType(OP.TYPE, index + index_offset, type_map[data[index].name]))
            case TOKENS.CODEOPEN:
                codeBlock_stack.append(codeBlock(codeblock_id_index, [], []))
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
    if (n:=TOKENS.COUNT.value) != (m:=8):
        error(Error.ENUM, f"{BOLD_}Exhaustive operation parsing protection in {BOLD_}Parse_token{BACK_}", expected = (m,n), flags = LogFlag.FAIL | LogFlag.EXPECTED)

    ret: list[Token] = []
    if data in alone_token:
        ret += [Token(alone_token[data], data)]
        data = ""
    elif data in protected_token:
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
                data = after

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
def Print_codeBlock_ops(data: codeBlock, suffix="") -> None:
    color: tuple[LogFlag, LogFlag] = (LogFlag.GOOD,LogFlag.WARNING)
    for x in data.tokens:
        if x.type in CB:
            Print_codeBlock_ops(x, suffix = f"in {data.id} > ")
        else:
            error(Error.TEST, f"{suffix}in {data.id} > {x}\n", flags = color[data.id % len(color)], exitAfter = False)

def Parse_file(input: str) -> list:
    data = []
    with open(input, 'r') as f:
        data = f.readlines()
    for x in [op for row, line in enumerate(data) for op in Parse_line(input, row, line)]:
        print(x)
    Print_codeBlock_ops(Secound_token_parse(First_token_parse([op for row, line in enumerate(data) for op in Parse_line(input, row, line)])))
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
                error(Error.CMD, f"Wrong file provided, compiller couldn't find file at a `%s` location" % (input_file), flags = LogFlag.WARNING)
            data = Parse_file(input_file)
            
            compile_data(data)
        case '-s':
            input_file, argv = unpack(argv)

            if not os.path.isfile(input_file):
                error(Error.CMD, f"Wrong file provided, compiller couldn't find file at a `{input_file}` location", flags = LogFlag.WARNING)
            data = Parse_file(input_file)
            
            #simulate_data(data)
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
