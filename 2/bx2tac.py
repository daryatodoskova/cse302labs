#!/usr/bin/env python3
"""
Reads the BX source file specified in the command line
and outputs a TAC program in JSON format.
"""

import json
import scanner
import parser
import bx_ast as ast

def bx_to_tac(fname, alg):
  assert fname.endswith('.bx')
  ast_prog = parser.load_bx(fname)
  tac_prog = ast.Programm(ast_prog, alg)
  tacname = fname[:-3] + '.tac.json'
  with open(tacname, 'w') as fp:
    json.dump(tac_prog.js_obj, fp)
  print(f'{fname} -> {tacname}')
  return tacname

if __name__ == '__main__':
  import sys, argparse
  ap = argparse.ArgumentParser()
  ap.add_argument('--bmm', dest='bmm', action='store_true', default=False)
  ap.add_argument('--tmm', dest='tmm', action='store_true', default=False)
  ap.add_argument('fname', metavar='FILE', type=str, nargs=1)
  opts = ap.parse_args(sys.argv[1:])
  if opts.tmm or not opts.bmm:
      alg = 'tmm'
  else:
      alg = 'bmm'
  tacname = bx_to_tac(opts.fname[0], alg)
