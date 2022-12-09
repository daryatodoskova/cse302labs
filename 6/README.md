# An Optimizing Brainfuck Compiler

* `bf_front.py` parses a brainfuck program
* `bf_optimizer.py` converts into a convenient structure and runs optimizations
* `bf2x64.py` generates x64 assembly

To compile a brainfuck program run:

* Print: `python3 bf2x64.py example.bf`
* Output to a file: `python3 bf2x64.py -o example.s example.bf`
* Generate an executable: `gcc -g -o example.exe example.s`
