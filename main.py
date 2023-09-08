import runner, lexer, prsr
import os

while True:
    s = input(">> ")
    f = open(s)
    runner.project_path = os.path.dirname(s)
    tokens = lexer.Lexer(f.read().replace("\n", " ")).lex()
    parser = prsr.Parser(tokens)
    ast = parser.expression()
    # print(ast)
    runner.Runner(ast).run()
    runner.modules = {}
