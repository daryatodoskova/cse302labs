import sys
import bf_optimizer as opt

ptr_reg = '%r12'


def a(instr):
    return '\t' + instr + '\n'


class Program:
    def __init__(self, prog):
        self.prog = prog
        self.label_count = 0

    def tox64(self):
        asm = ''
        asm += a('.bss')
        asm += 'buffer:\n'
        asm += a('.zero 30000\n')
        asm += a('.text')
        asm += a('.globl main')
        asm += 'main:\n'
        asm += a('pushq %rbp')
        asm += a('movq %rsp, %rbp')
        asm += a(f'leaq buffer(%rip), {ptr_reg}')

        for instr in self.prog:
            asm += self.instrtox64(instr)

        asm += a('xorq %rax, %rax')
        asm += a('movq %rbp, %rsp')
        asm += a('popq %rbp')
        asm += a('retq')

        return asm

    def instrtox64(self, instr):
        asm = ''
        if isinstance(instr, opt.Modify):
            offset = str(instr.offset) if instr.offset != 0 else ''
            asm += a(f'addb ${instr.n}, {offset}({ptr_reg})')
        elif isinstance(instr, opt.Move):
            asm += a(f'addq ${instr.n}, {ptr_reg}')
        elif isinstance(instr, opt.Print):
            asm += a(f'movb ({ptr_reg}), %dil')
            asm += a('callq putchar')
        elif isinstance(instr, opt.Input):
            asm += a('callq getchar')
            asm += a(f'movb %al, ({ptr_reg})')
        elif isinstance(instr, opt.ScanLoop):
            asm += a(f'leaq buffer(%rip), %r8')
            asm += a(f'movq {ptr_reg}, %r9')
            asm += a(f'movq %r8, %r10')
            asm += a(f'addq $30000, %r10')
            if instr.forward:
                asm += a(f'movq %r10, %r11')
                asm += a(f'subq %r9, %r11')
                asm += a(f'addq $1, %r11')
                asm += a(f'movq %r9, %rdi')
                asm += a(f'movb $0, %sil')
                asm += a(f'movq %r11, %rdx')
                asm += a(f'callq memchr')
            else:
                asm += a(f'movq %r9, %r11')
                asm += a(f'subq %r8, %r11')
                asm += a(f'addq $1, %r11')
                asm += a(f'movq %r8, %rdi')
                asm += a(f'movb $0, %sil')
                asm += a(f'movq %r11, %rdx')
                asm += a(f'callq memrchr')
            asm += a(f'movq %rax, {ptr_reg}')
        elif isinstance(instr, opt.SetLoop):
            asm += a(f'movb ({ptr_reg}), %r13b')
        elif isinstance(instr, opt.LoopModify):
            asm += a(f'movb ${instr.n}, %r14b')
            asm += a(f'imulq %r13, %r14')
            offset = str(instr.offset) if instr.offset != 0 else ''
            asm += a(f'addb %r14b, {offset}({ptr_reg})')
        elif isinstance(instr, list):
            lab_num = self.label_count
            self.label_count += 1
            asm += f'.L{lab_num}b:\n'
            asm += a(f'cmpb $0, ({ptr_reg})')
            asm += a(f'je .L{lab_num}e')
            for sub_instr in instr:
                asm += self.instrtox64(sub_instr)
            asm += a(f'jmp .L{lab_num}b')
            asm += f'.L{lab_num}e:\n'

        return asm


if __name__ == '__main__':
    argc = len(sys.argv)
    if argc == 1:
        raise ValueError("No Input File")
    elif argc == 2:
        stdout = True
        filein = sys.argv[1]
    elif argc == 4:
        if sys.argv[1] != '-o':
            raise ValueError('Expected -o flag')
        stdout = False
        filein = sys.argv[3]
        fileout = sys.argv[2]
    else:
        raise ValueError("Incorrect Number of Arguments")

    prog = opt.main(filein)
    asmx64 = Program(prog).tox64()

    if stdout:
        print(asmx64)
    else:
        with open(fileout, 'w') as file:
            file.write(asmx64)
