"""
This file contains the implementation of the Reader class. 
The Reader is composed of a lexer and a parser (from the PLY library). 
It takes as input a source file (.bx) and generates the corresponding ast in json format (json can be dumped in a file)
"""
from lex_pars import Lexer, Parser

"""
Part A of the file: Reader 
The Reader classe encapsulates the Lexer and the Parser. 
Thanks to this we only need to class the read(self) method in order to obtain the first node of the AST object. 
"""
# ================================================================================

class Reader:
    def __init__(self, source_name: str, data: str):
        self.lexer = Lexer(source_name, data)
        self.parser = Parser(self.lexer)

    def read(self):
        return self.parser.parse()


    def write_out(self, source_name: str, source: str, ast_obj):
        """
        Function used to write the json representation of the ast in a file
        """
        dest_name = source_name[:-2] + 'ast.json'
        js = {
            "provenance": source_name, 
            "source": source,
            "ast": ast_obj.prog_to_json
        }
        with open(dest_name, 'w') as dest_file:
            json.dump(js, dest_file)
        print(source_name + '->' + dest_name)

# ================================================================================


##################
#Driver Code (if you wish to only use the reader and retrieve the eg.ast.json file)
if __name__ == '__main__':
    import sys
    import json

    def write_out(source_name: str, source: str, ast_obj):
        """
        Function used to write the json representation of the ast in a file
        """
        dest_name = source_name[:-2] + 'ast.json'
        js = {
            "provenance": source_name, 
            "source": source,
            "ast": ast_obj.prog_to_json
        }
        with open(dest_name, 'w') as dest_file:
            json.dump(js, dest_file)
        print(source_name + '->' + dest_name)

    assert (len(sys.argv) > 1)
    source_name = sys.argv[1]
    assert source_name.endswith('.bx')
    with open(source_name, 'r') as bx_file:
        source = bx_file.read()
    reader = Reader(source_name, source)
    ast_obj = reader.read()
    print("Sucess in lexing/parsing. Ast object created:", ast_obj)
    write_out(source_name, source, ast_obj)
