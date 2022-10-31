"""
Going from .bx to x64 (currently stops at tac...)
"""
import argparse
import json
import os
from pathlib import Path
from bx2ast import Reader
from ast2tac import Prog
import tac2x64 as x64
import sys 

#We use this function to translate from bx to a Prog object (implemented in ast2tac.py)
def bx_to_tac(source_name: str, source: str, opts=None):
    reader = Reader(source_name, source) # Creating the reader object
    ast_object = reader.read() #Calling the read method of the reader object
    if not ast_object:
        raise RuntimeError(f'Error parsing {source_name}')
    if opts.keep_ast:
        js_ast = ast_object.prog_to_json
        dest_name = source_name[:-3] + '.ast.json'
        with open(dest_name, 'w') as dest_file:
            json.dump(js_ast, dest_file, indent=2)
        print(f'{source_name} -> {dest_name}')
    prog = Prog(ast_object, 'tmm')
    if opts.keep_tac:
        js_tac = prog.js_obj
        dest_name = source_name[:-3] + '.tac.json'
        with open(dest_name, 'w') as dest_file:
            json.dump(js_tac, dest_file, indent=2)
        print(f'{source_name} -> {dest_name}')
    return prog

# We use this function that takes as input a tac.json file 
def accept_tac(tac_filename: str, opt=None):
    asm_filename = tac_filename[:-9] + '.s'
    filename = tac_filename[:-9]
    with open(tac_filename, 'r') as tac_file:
        tac = json.load(tac_file)
        asm = x64.compile_tac(tac)
        with open (asm_filename, 'w') as asm_file:
            print(*asm, file=asm_file, sep='\n')
        print(f'{tac_filename} -> {asm_filename}')
        if opt.stop_asm:
            sys.exit(0)
        shell_command = f"gcc -o {filename} {asm_filename} bx_runtime.c"
        gcc_stat = os.system(shell_command)
        if not (os.WIFEXITED(gcc_stat) and os.WEXITSTATUS(gcc_stat) == 0):
          print(f'gcc exited abnormally')
        print(f"{tac_filename} -> {filename}")
    

def main(options):
    bx_filename = options.fname[0]
    if options.accept_tac_json:
        accept_tac(bx_filename, options)
        sys.exit(0)
    if not bx_filename.endswith('.bx'):
        print(f'File {bx_filename} does not have .bx extension')
        sys.exit(1)
    filename = bx_filename[:-3]
    asm_filename = f'{filename}.s'
    with open(bx_filename, 'r') as bx_file:
        source = bx_file.read()
        tac = bx_to_tac(bx_filename, source, options)
        if options.stop_tac: 
            sys.exit(0)
        asm = x64.compile_tac(tac.js_obj)

        with open (asm_filename, 'w') as asm_file:
            print(*asm, file=asm_file, sep='\n')
        print(f'{bx_filename} -> {asm_filename}')


        if options.stop_asm:
            sys.exit(0)
        #shell_command to compile the .s file to an executable
        shell_command = f"gcc -o {filename} {asm_filename} bx_runtime.c"
        gcc_stat = os.system(shell_command)
        if not (os.WIFEXITED(gcc_stat) and os.WEXITSTATUS(gcc_stat) == 0):
          print(f'gcc exited abnormally')
        if not options.keep_asm:
            shell_command_2 = f"rm {asm_filename}"
            os.system(shell_command_2)
        print(f"{bx_filename} -> {filename}")
    
if __name__ == '__main__':
    #Adding command line arguments
    ap = argparse.ArgumentParser()
    ap.add_argument('--keep_ast', dest = 'keep_ast', action='store_true', default=False, help= 'Keep the ast.json file')
    ap.add_argument('--keep_tac', dest = 'keep_tac', action='store_true', default=False, help= 'Keep the tac.json file')
    ap.add_argument('--keep_asm', dest = 'keep_asm', action='store_true', default=False, help= 'Keep the .s file')
    ap.add_argument('--stop_tac', dest = 'stop_tac', action='store_true', default=False, help= 'Stop at the tac.json file')
    ap.add_argument('--stop_asm', dest = 'stop_asm', action='store_true', default=False, help= 'Stop at the .s file')
    ap.add_argument('--accept.tac.json', dest = 'accept_tac_json', action='store_true', default=False, help='Accept the tac.json file')
    ap.add_argument('fname',metavar='FILE', type=str, nargs=1, help='The BX file to compile, if accept.tac.json is not set')

    options = ap.parse_args(sys.argv[1:])
    main(options)

