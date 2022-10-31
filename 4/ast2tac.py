"""
This file contains the implementation of the classes Prog and Instruction used to converted an AST structure to a TAC representation. 
Prog: Performs maximal munch IR translation. 
Instruction: Represents the TAC instructions. 
"""

import AST as ast
#ast.op_codes_bis
# ================================================================================

"""
Part A of the file: Instruction 
An Instruction object holds three attributes: 
    -> opcode: TAC operation code 
    -> args: either a list containing a single temporary: [%0] or a list of temporaries [%0, %1] (maximum 2)
    -> result: a temporary: %2 where the result of the operation is stored
The class has a property (js_obj) that will be used when creating the json object of TAC representation of the AST. 
For each Instruction we will have obtain we call the property to convert it. 
"""
class Instruction:
  __slots__ = ['opcode', 'args', 'result'] # slots allow us to pre-allocate the memory for each instance of the class we create (makes the compiler more efficient)

  def __init__(self, opcode: str, args: list, result: str):
    self.opcode = opcode
    self.args = args
    self.result = result

  @property
  def js_obj(self):
    return {'opcode': self.opcode,
            'args': self.args,
            'result': self.result}
  
  def __repr__(self):
        return f"{{opcode: {self.opcode}, args: {self.args}, result: {self.result}}}"

# ================================================================================
"""
Part B of the file: Prog 
Prog is the class that performs all the work we need when we call this file. 
It holds seven attriburtes: 
    -> locatemporaries: a list that we use to keep track of all the temporaries that we will create when converting the program.
    -> instrs: a list of all the instruction that we obtain when converting the program.
    -> __tempdict: a dictionary (mapping) to store the correspondance between program variables and temporaries.
    -> __last: an int to serve as a counter when creating new temporaries (avoid create two temporaries with the same name).
    -> __last_label: an int that serves the same purpose as __last, but for programe labels (used for jumps and conditionals...).
    -> _break_stack: a list that is used when entering while loops. It allows us to know where to jump if encountering a break statement.
    -> _continue_stack: a list that serves the same purpose as _break_stack but for continue statements. 
"""

# ================================================================================

class Prog:
  def __init__(self, program: ast.Program, alg: str):
    self.localtemporaries = []
    self.instrs = []
    self.__tempdict = dict()
    self.__last = -1
    self.__last_label = -1
    self._break_stack = []
    self._continue_stack = []

    #Conditional to choose between the two maximal munch algorithms we have
    if alg == 'tmm':
      for stmt in program.lvars:
        self._emit('const', [0], self._lookup(stmt))
      self.tmm_stmt(program.block)
    elif alg == 'bmm':
      for stmt in program.lvars:
        self._emit('const', [0], self._lookup(stmt))
      self.bmm_stmt(program.block)

  @property
  def js_obj(self):
    return [{'proc': '@main',
             'body': [i.js_obj for i in self.instrs]}]

  def _freshtemp(self):
    #Creating a new temporary 
    self.__last += 1
    t = f'%{self.__last}'
    self.localtemporaries.append(t)
    return t

  def _fresh_label(self):
    #Creating a new label 
    self.__last_label += 1
    t = f'%.L{self.__last_label}'
    return t

  def _lookup(self, var: str):
    #Checking if there already exists a temporary for a given var
    t = self.__tempdict.get(var)
    if t is None:
      t = self._freshtemp()
      self.__tempdict[var] = t
    return t

  def _emit(self, opcode: str, args: list, result: str):
    #Create an Instruction instance and add it to the instr list
    self.instrs.append(Instruction(opcode, args, result))

# ================= Maxmimal Munch =================================================

  def tmm_expr(self, expr: ast.Expression, target: str):
    #TMM for expressions 
    if isinstance(expr, ast.ExpressionVar):
      self._emit('copy', [self._lookup(expr.name)], target)
    elif isinstance(expr, ast.ExpressionInt):
      self._emit('const', [expr.value], target)
    elif isinstance(expr, ast.ExpressionUniOp):
      arg_target = self._freshtemp()
      self.tmm_expr(expr.argument, arg_target)
      self._emit(ast.op_codes[expr.operator], [arg_target], target)
    elif isinstance(expr, ast.ExpressionBinOp):
      args = []
      arg_target1 = self._freshtemp()
      self.tmm_expr(expr.left, arg_target1)
      args.append(arg_target1)
      arg_target2 = self._freshtemp()
      self.tmm_expr(expr.right, arg_target2)
      args.append(arg_target2)
      self._emit(ast.op_codes[expr.operator], args, target)
    elif isinstance(expr, ast.Bool):
      self._emit('const', [1 if expr.value else 0], target)
    else:
      raise ValueError(f'In tmm_expr: unknown expression {expr.__class__}')

# ================================================================================

  def tmm_bool_expr(self, boolexpr: ast.Expression, Lt: str, Lf: str):
    #TMM for boolean expressions, the main idea is the following: 
    #jump to Lt if true, to Lf if false
    if isinstance(boolexpr, ast.Bool):
      if boolexpr.value == True:
        self._emit('jmp', [Lt], None)
      elif boolexpr.value == False:
        self._emit('jmp', [Lf], None)
    elif isinstance(boolexpr, ast.ExpressionUniOp):
      if boolexpr.operator == '!':
        self.tmm_bool_expr([boolexpr.argument][0], Lf, Lt)
    elif isinstance(boolexpr, ast.ExpressionBinOp):
      if boolexpr.operator in {'==', '!=', '<', '<=', '>', '>='}:
        largs = []
        arg_target1 = self._freshtemp()
        self.tmm_expr(boolexpr.left, arg_target1)
        largs.append(arg_target1)
        arg_target2 = self._freshtemp()
        self.tmm_expr(boolexpr.right, arg_target2)
        largs.append(arg_target2)
        self._emit('sub', largs, largs[0])
        self._emit(ast.op_codes[boolexpr.operator], [largs[0], Lt], None)
        self._emit('jmp', [Lf], None)
      elif boolexpr.operator == '&&':
        Li = self._fresh_label()
        self.tmm_bool_expr([boolexpr.left][0], Li, Lf)
        self._emit('label', [Li], None)
        self.tmm_bool_expr([boolexpr.right][0], Lt, Lf)
      elif boolexpr.operator == '||':
        Li = self._fresh_label()
        self.tmm_bool_expr([boolexpr.left][0], Lt, Li)
        self._emit('label', [Li], None)
        self.tmm_bool_expr([boolexpr.right][0], Lt, Lf)
    else:
      raise ValueError(
        f'In tmm_expr:unknown expr kind: {boolexpr.__class__}')

# ================================================================================

  def tmm_stmt(self, stmt: ast.Statement):
    #TMM for statements (same as in previous lab with addition of If and While statements)
    if isinstance(stmt, ast.Vardecl):
      target = self._lookup(stmt.var.name)
      self.tmm_expr(stmt.expr, target)
    elif isinstance(stmt, ast.Assign):
      target = self._lookup(stmt.lhs.name)
      self.tmm_expr(stmt.rhs, target)
    elif isinstance(stmt, ast.Print):
      target = self._freshtemp()
      self.tmm_expr(stmt.arg, target)
      self._emit('print', [target], None)
    elif isinstance(stmt, ast.IfElse):
      Lt = self._fresh_label()
      Lf = self._fresh_label()
      Lo = self._fresh_label()
      self.tmm_bool_expr(stmt.condition, Lt, Lf)
      self._emit('label', [Lt], None)
      self.tmm_stmt(stmt.block)
      self._emit('jmp', [Lo], None)
      self._emit('label', [Lf], None)
      self.tmm_stmt(stmt.ifrest)
      self._emit('label', [Lo], None)
    elif isinstance(stmt, ast.Block):
      for stmt in stmt.stmts:
        self.tmm_stmt(stmt)
    elif isinstance(stmt, ast.While):
      Lhead = self._fresh_label()
      Lbody = self._fresh_label()
      Lend = self._fresh_label()
      self._break_stack.append(Lend)
      self._continue_stack.append(Lhead)
      self._emit('label', [Lhead], None)
      self.tmm_bool_expr(stmt.condition, Lbody, Lend)
      self._emit('label', [Lbody], None)
      self.tmm_stmt(stmt.block)
      self._emit('jmp', [Lhead], None)
      self._emit('label', [Lend], None)
      self._break_stack.pop()
      self._continue_stack.pop()
    elif isinstance(stmt, ast.Jump):
      if stmt.operator == 'break':
        if len(self._break_stack) < 1:
          raise ValueError(f'Bad break at line {stmt.sloc}')
        self._emit('jmp', [self._break_stack[-1]], None)
      elif stmt.operator == 'continue':
        if len(self._continue_stack) < 1:
          raise ValueError(f'Bad continue at line {stmt.sloc}')
        self._emit('jmp', [self._continue_stack[-1]], None)
      else:
        print(stmt)
        raise ValueError(f'tmm_stmt: unknown stmt kind: {stmt.__class__}')

# ================================================================================

#DOESN'T WORK YET......
##################
#Driver Code (if you wish to only use the file to retrieve the eg.tac.json file from the eg.ast.json file)

if __name__ == '__main__':
  import sys 
  import json 
  
  def ast_to_tac(ast_name: str):
    with open(ast_name, 'r') as ast_file:
        source = json.read()

    ast_object = ast.Program.json_to_ast(source)
    prog = Prog(ast_object, 'tmm')
    js = prog.js_obj
    dest_name = str(ast_name)[:-8] + 'tac.json'
    with open(dest_name, 'w') as dest_file:
        json.dump(js, dest_file)
    return dest_name

  assert (len(sys.argv) > 1)
  ast_name = sys.argv[1]
  assert ast_name.endswith('.ast.json')
  tac_name = ast_to_tac(ast_name)
  print(ast_name + '->' + tac_name)