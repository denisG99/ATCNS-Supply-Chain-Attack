import ast
import astpretty

if __name__ == "__main__":
    code = """x = 1
def f(y):
    z = 2
    def g():
        print(y)
 """

    tree = ast.parse(code)
    astpretty.pprint(tree)