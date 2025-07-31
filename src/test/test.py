import ast

from src.scope_graph import ScopeGraph

if __name__ == "__main__":
    with open("example.py") as f:
        code = f.read()

    tree = ast.parse(code)

    # building scope Graph
    builder = ScopeGraph()
    builder.visit(tree)
    from pprint import pprint

    pprint(builder.get_graph())