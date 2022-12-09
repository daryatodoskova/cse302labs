import bf_front


class Modify:
    def __init__(self, n, offset=0):
        self.n = n
        self.offset = offset


class Move:
    def __init__(self, n):
        self.n = n


class Print:
    pass


class Input:
    pass


class ScanLoop:
    def __init__(self, forward):
        self.forward = forward


class SetLoop:
    pass


class LoopModify:
    def __init__(self, n, offset=0):
        self.n = n
        self.offset = offset


# --------------------------------------------------------------------


def convert(program):
    prog = []
    for bf_instr in program:
        if isinstance(bf_instr, str):
            if bf_instr == 'inc':
                prog.append(Modify(1))
            if bf_instr == 'dec':
                prog.append(Modify(-1))
            if bf_instr == 'forw':
                prog.append(Move(1))
            if bf_instr == 'bckw':
                prog.append(Move(-1))
            if bf_instr == 'print':
                prog.append(Print())
            if bf_instr == 'input':
                prog.append(Input())
        elif isinstance(bf_instr, list):
            prog.append(convert(bf_instr))
    return prog


def opt_inc_dec(prog):
    res = []
    i = 0
    while i < len(prog):
        instr = prog[i]
        if isinstance(instr, Modify):
            modify = 0
            while i < len(prog) and isinstance(prog[i], Modify):
                modify += prog[i].n
                i += 1
            if modify != 0:
                res.append(Modify(modify))
            continue
        if isinstance(instr, list):
            res.append(opt_inc_dec(instr))
        else:
            res.append(instr)
        i += 1
    return res


def opt_forw_bckw(prog):
    res = []
    i = 0
    while i < len(prog):
        instr = prog[i]
        if isinstance(instr, Move):
            move = 0
            while i < len(prog) and isinstance(prog[i], Move):
                move += prog[i].n
                i += 1
            if move != 0:
                res.append(Move(move))
            continue
        if isinstance(instr, list):
            res.append(opt_forw_bckw(instr))
        else:
            res.append(instr)
        i += 1
    return res


def opt_fixed_offset(prog):
    res = []
    i = 0
    while i < len(prog):
        instr = prog[i]
        if isinstance(instr, Modify):
            if 0 < i < len(prog) - 1:
                instr_left = prog[i - 1]
                instr_right = prog[i + 1]
                if isinstance(instr_left, Move) and isinstance(instr_right, Move):
                    if instr_left.n * instr_right.n < 0:
                        res[-1].n = instr_left.n + instr_right.n
                        if res[-1].n == 0:
                            res.pop()
                        res.append(Modify(instr.n, -instr_right.n))
                        instr_right.n = 0
                        i += 2
                        continue
        if isinstance(instr, list):
            res.append(opt_fixed_offset(instr))
        else:
            res.append(instr)
        i += 1
    return res


def opt_post_mov(prog):
    res = []
    i = 0
    while i < len(prog):
        instr = prog[i]
        if isinstance(instr, Move):
            offset = 0
            while i < len(prog):
                curr = prog[i]
                if isinstance(curr, Move):
                    offset += curr.n
                elif isinstance(curr, Modify):
                    res.append(Modify(curr.n, curr.offset + offset))
                else:
                    break
                i += 1
            if offset != 0:
                res.append(Move(offset))
            continue
        if isinstance(instr, list):
            res.append(opt_post_mov(instr))
        else:
            res.append(instr)
        i += 1
    return res


def opt_assign_cancel(prog):
    res = []
    i = 0
    while i < len(prog):
        instr = prog[i]
        if isinstance(instr, Modify):
            modify = 0
            while i < len(prog) and isinstance(prog[i], Modify) and instr.offset == prog[i].offset:
                modify += prog[i].n
                i += 1
            if modify != 0:
                res.append(Modify(modify, instr.offset))
            continue
        if isinstance(instr, list):
            res.append(opt_assign_cancel(instr))
        else:
            res.append(instr)
        i += 1
    return res


def opt_scan_loop(prog):
    res = []
    i = 0
    while i < len(prog):
        instr = prog[i]
        if isinstance(instr, list) and len(instr) == 1 and isinstance(instr[0], Move):
            if instr[0].n == 1:
                res.append(ScanLoop(True))
                i += 1
                continue
            elif instr[0].n == -1:
                res.append(ScanLoop(False))
                i += 1
                continue
        if isinstance(instr, list):
            res.append(opt_scan_loop(instr))
        else:
            res.append(instr)
        i += 1
    return res


def opt_cpy_mul_loop(prog):
    res = []
    i = 0
    while i < len(prog):
        instr = prog[i]
        if isinstance(instr, list):
            valid = True
            for sub_instr in instr:
                if isinstance(sub_instr, list) or isinstance(sub_instr, Print) or isinstance(sub_instr, Input):
                    valid = False
                    break
            offset = 0
            for sub_instr in instr:
                if isinstance(sub_instr, Move):
                    offset += sub_instr.n
            decr = 0
            for sub_instr in instr:
                if isinstance(sub_instr, Modify):
                    if sub_instr.offset == 0:
                        decr += sub_instr.n
            if valid and offset == 0 and decr == -1:
                res.append(SetLoop())
                for sub_instr in instr:
                    if isinstance(sub_instr, Modify):
                        res.append(LoopModify(sub_instr.n, sub_instr.offset))
                    else:
                        res.append(sub_instr)
                i += 1
                continue
        if isinstance(instr, list):
            res.append(opt_cpy_mul_loop(instr))
        else:
            res.append(instr)
        i += 1
    return res


# --------------------------------------------------------------------


def main(filename):
    program = bf_front.main(filename)

    prog = convert(program)

    # Contraction of increments/decrements
    prog = opt_inc_dec(prog)

    # Contraction of data pointer movements
    prog = opt_forw_bckw(prog)

    # Increments/decrements at a fixed offset
    prog = opt_fixed_offset(prog)

    # Postponing movements
    prog = opt_post_mov(prog)

    # Assignments cancellation
    prog = opt_assign_cancel(prog)

    # Scan loop simplification
    prog = opt_scan_loop(prog)

    # Copy/multiply loop simplification
    prog = opt_cpy_mul_loop(prog)

    return prog
