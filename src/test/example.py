"""
This code has only a test purpose, so it doesn't write to be executed
"""
import sys, ast

if __name__ == '__main__':
    x = 1

    def regular_function(a, b):
        c = a + b
        l = lambda x: x * 2  # Lambda
        return l(c)

    class MyClass:  # ClassDef
        def method(self):
            import ast

            data = [i for i in range(10) if i % 2 == 0]  # ListComp
            return data

    try:
        result = regular_function(1, 2)
    except Exception as e:  # ExceptHandler
        print("Errore:", e)

    async def async_function():  # AsyncFunctionDef
        def regular_function(a, b):
            pass
