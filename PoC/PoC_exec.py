from auxiliary.benign_func import function

def f(x):
    return x ** 2

if __name__ == "__main__":
    print(f"Before shadowing: {f(2)}")

    exec("""def f(x):
    return x ** 3""")

    print(f"After shadowing: {f(2)}")

    function()

    exec("""def function():
    print('Malicious function')""")

    function()