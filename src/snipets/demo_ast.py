import ast
import astpretty

if __name__ == "__main__":
    code = """
import ast as ast, base64 as b64
import functools

from functools import reduce
 """

    tree = ast.parse(code)
    astpretty.pprint(tree)