#!/usr/bin/env python3

"""
Darya TODOSKOVA

This is a x64 assembly to TAC pass. 

Usage: python3 ast2tac.py astfile.json
Produces: astfile.s (assembly) and astfile.exe (executable)
Requires: a working gcc
"""

import json
import sys
import os
from pathlib import Path

op_codes = {'addition': 'add', 
            'substraction': 'sub', 
            'multiplication': 'mul', 
            'division': 'div', 
            'modulus': 'mod', 
            'bitwise-xor': 'xor', 
            'bitwise-or': 'or', 
            'bitwise-and': 'and',
            'opposite': 'not', 
            'bitwise-negation': 'neg',
            'logical-shift-left':'shl', 
            'logical-shift-right':'shr'}


class Expression: 

    @staticmethod
    def load(js_obj):
        if not isinstance(js_obj, list): 
          return None
        if js_obj[0] == '<expression:var>':
          return ExpressionVar(js_obj[1]['name'][1]['value']) 
        elif js_obj[0] == '<lvalue:var>':
          return ExpressionVar(js_obj[1]['name'][1]['value'])
        elif js_obj[0] =='<expression:call>':
          return Expression.load(js_obj[1]['arguments'][0])
        elif js_obj[0] == '<expression:int>':
          return ExpressionInt(js_obj[1]['value']) 
        elif js_obj[0] == '<expression:uniop>':
          operator = js_obj[1]['operator'][1]['value']
          argument = Expression.load(js_obj[1]['argument']) 
          return ExpressionUniOp(operator, argument)
        elif js_obj[0] == '<expression:binop>':
          operator = js_obj[1]['operator'][1]['value']
          left = Expression.load(js_obj[1]['left'])
          right = Expression.load(js_obj[1]['right'])
          return ExpressionBinOp(operator, left, right)
        else:
          return None


class ExpressionVar(Expression): 
    def __init__(self, name:str):
        self.name = name

    @property
    def js_obj(self):
        return {'tag': 'Variable', 'name': self.name}

class ExpressionInt(Expression): 
    def __init__(self, value):
        self.value = value

    @property
    def js_obj(self):
        return {'tag': 'Integer', 'value': str(self.value)}
                
class ExpressionUniOp(Expression):
    def __init__(self, operator:str, argument):
        self.operator = operator
        self.argument = argument

    @property
    def js_obj(self):
        return {'tag': 'UniOp',
                'op': self.operator,
                'arg': self.argument}

class ExpressionBinOp(Expression): 
    def __init__(self, operator:str, left, right):
        self.operator = operator
        self.left = left
        self.right = right
        
      
    @property
    def js_obj(self):
        return {'tag': 'BinOp',
                'op': self.operator,
                'larg': self.left,
                'rarg': self.right,
                }




class Statement:

    @staticmethod
    def load(js_obj):
        if not isinstance(js_obj, list): 
            return None
        if js_obj[0] == '<statement:assign>':
            return Assign(Expression.load(js_obj[1]['lvalue']), Expression.load(js_obj[1]['rvalue']))
        elif js_obj[0] == '<statement:eval>':
            js_obj = js_obj[1]['expression']
            return Print(Expression.load(js_obj))
        else:
            return None

class Assign(Statement):

    def __init__(self, lhs :ExpressionVar, rhs :Expression):
        self.lhs = lhs
        self.rhs = rhs

    @property
    def js_obj(self):
        return {'tag': 'Assign', 'lhs': self.lhs.js_obj, 'rhs': self.rhs.js_obj}

class Print(Statement):
    def __init__(self, arg :Expression):
        self.arg = arg

    @property
    def js_obj(self):
        return {'tag': 'Print', 'arg': self.arg.js_obj}




class Program:
  def __init__(self, lvars, stmts):
    self.lvars = lvars
    self.stmts = stmts


  @staticmethod
  def load(js_obj):
    assert isinstance(js_obj, list)
    js_obj = js_obj[0]
    assert len(js_obj) == 2
    js_obj = js_obj[1]
    assert len(js_obj) == 5  
    section = js_obj['body'][:]
    lvars = []
    while len(section) > 0:
      if section[0][0] != '<statement:vardecl>': 
          break
      var, section = section[0], section[1:]
      lvars.append(var[1]['name'][1]['value'])
    stmts = []
    while len(section) > 0:
      stmtt, section = section[0], section[1:]
      stmt = Statement.load(stmtt)
      stmts.append(stmt)
    return Program(lvars, stmts)

  @property
  def js_obj(self):
    return {'tag': 'Program',
            'vars': self.vars,
            'stmts': [stmt.js_obj for stmt in self.stmts]}




class Instruction:
  __slots__ = ['opcode', 'args', 'result']

  def __init__(self, opcode, args, result):
    self.opcode = opcode
    self.args = args
    self.result = result

  @property
  def js_obj(self):
    return {'opcode': self.opcode,
            'args': self.args,
            'result': self.result}


class Programm:
  def __init__(self, program : Program, alg):
    self.localtemporaries = []
    self.instrs = []
    self.__tempdict = dict()
    self.__last = -1
    for i in program.lvars:
      self._emit('const', [0], self._lookup(i))
    if alg == 'tmm':
      for stmt in program.stmts: 
        self.tmm_stmt(stmt)
    elif alg == 'bmm':
      for stmt in program.stmts: 
        self.bmm_stmt(stmt)

  @property
  def js_obj(self):
    return [{'proc': '@main',
             'body': [i.js_obj for i in self.instrs]}]

  def _freshtemp(self):
    self.__last += 1
    t = f'%{self.__last}'
    self.localtemporaries.append(t)
    return t

  def _lookup(self, var):
    t = self.__tempdict.get(var)
    if t is None:
      t = self._freshtemp()
      self.__tempdict[var] = t
    return t

  def _emit(self, opcode, args, result):
    self.instrs.append(Instruction(opcode, args, result))

  def tmm_expr(self, expr, target):
    if isinstance(expr, ExpressionVar):
      self._emit('copy', [self._lookup(expr.name)], target)
    elif isinstance(expr, ExpressionInt):
      self._emit('const', [expr.value], target)
    elif isinstance(expr, ExpressionUniOp):
      arg_target = self._freshtemp()
      self.tmm_expr(expr.argument, arg_target)
      self._emit(op_codes[expr.operator], [arg_target], target)
    elif isinstance(expr, ExpressionBinOp):
      args = []
      arg_target1 = self._freshtemp()
      self.tmm_expr(expr.left, arg_target1)
      args.append(arg_target1)
      arg_target2 = self._freshtemp()
      self.tmm_expr(expr.right, arg_target2)
      args.append(arg_target2)
      self._emit(op_codes[expr.operator], args, target)

  def tmm_stmt(self, stmt):
    if isinstance(stmt, Assign):
      lhss = self._lookup(stmt.lhs.name)
      self.tmm_expr(stmt.rhs, lhss)
    elif isinstance(stmt, Print):
      temp = self._freshtemp()
      self.tmm_expr(stmt.arg, temp)
      self._emit('print', [temp], None)


  def bmm_expr(self, expr):
    if isinstance(expr, ExpressionVar):
      return self._lookup(expr.name)
    elif isinstance(expr, ExpressionInt):
      target = self._freshtemp()
      self._emit('const', [expr.value], target)
      return target
    elif isinstance(expr, ExpressionBinOp):
      args = []
      rarg = self.bmm_expr(expr.right)
      target1 = self._freshtemp()
      self._emit(op_codes[expr.operator], rarg, target1)
      args.append(target1)
      larg = self.bmm_expr(expr.left)
      target2 = self._freshtemp()
      self._emit(op_codes[expr.operator], larg, target2)
      args.append(target2)
      return args
    elif isinstance(expr, ExpressionUniOp):
      arg = self.bmm_expr(expr.argument) 
      target = self._freshtemp()
      self._emit(op_codes[expr.operator], arg, target)
      return target
  


  def bmm_stmt(self, stmt):
    if isinstance(stmt, Assign):
      lhss = self._lookup(stmt.lhs.name)
      lhss = self.bmm_expr(stmt.rhs)
      self._emit('copy', [lhss], lhss)
    elif isinstance(stmt, Print):
      temp = self.bmm_expr(stmt.arg)
      self._emit('print', [temp], None)


#---------------------------------------------------------------------------------------

""" def newtmp():
    if 'tmp_counter' in locals():       #check if global variable already exists in local symbol table
        return tmp_counter
    else:
        global tmp_counter              #if not, create a global variable
        tmp_counter += 1
        return tmp_counter

    #Whenever a tmp variable is used as an operand (appeared on the RHS), decrement tmp_counter by one, 
    #because each temporary name will be assigned and used exactly once, 
    #which is true in the majority of cases. """

import json

def compile_ast(fname, alg):
  assert fname.endswith('.json')
  with open(fname, 'rb') as fp:
    js_obj = json.load(fp)
    program = Program.load(js_obj['ast'])
  tac_prog = Programm(program, alg)
  tac = fname[:-5] + '.tac.json'
  with open(tac, 'w') as fp:
    json.dump(tac_prog.js_obj, fp)
  print(f'{fname} -> {tac}')
  return tac

if __name__ == '__main__':
  import sys, argparse
  parser = argparse.ArgumentParser()
  parser.add_argument('--bmm', dest='bmm', action='store_true', default=False)
  parser.add_argument('--tmm', dest='tmm', action='store_true', default=False)
  parser.add_argument('fname', metavar='FILE', type=str, nargs=1)
  opts = parser.parse_args(sys.argv[1:])
  mm = 'tmm' if opts.tmm or not opts.bmm else 'bmm'
  tac = compile_ast(opts.fname[0], mm)

