import ast

from src.scope_graph import ScopeGraph

if __name__ == "__main__":
    code = """
x = 1
def f(y):
    z = 2
    def g():
        print(y)
 """

    tree = ast.parse(code)

    # building scope Graph
    builder = ScopeGraph()
    builder.visit(tree)
    from pprint import pprint

    pprint(builder.get_graph())
