import ast
import astpretty

if __name__ == "__main__":
    '''    
    code = """x = 1
def f(y):
    z = 2
    def g():
        print(y)
 """
'''
    code = """
import asyncio

async def func():
    print("Hello!")
    await asyncio.sleep(2)  # Pause for 2 second without blocking
    print("Geeks for Geeks")  #

asyncio.run(func())
"""
    tree = ast.parse(code)
    astpretty.pprint(tree)