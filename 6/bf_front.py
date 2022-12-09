def parse(program: str, leniant: bool = True):
    stack = [[]]

    for c in program:
        if c == '+':
            stack[-1].append('inc')
        elif c == '-':
            stack[-1].append('dec')
        elif c == '>':
            stack[-1].append('forw')
        elif c == '<':
            stack[-1].append('bckw')
        elif c == '.':
            stack[-1].append('print')
        elif c == ',':
            stack[-1].append('input')
        elif c == '[':
            stack.append([])
        elif c == ']':
            if len(stack) < 2:
                raise BFError
            stack[-2].append(stack.pop())
        elif not (c.isspace() or leniant):
            raise BFError

    if len(stack) != 1:
        raise BFError

    return stack.pop()


class BFError(Exception):
    pass


def main(filename):
    with open(filename) as filein:
        program = filein.read()
    return parse(program)
