from aux.benign_func import function

def f(x):
    return x ** 2

if __name__ == "__main__":
    print(f"Before shadowing: {f(2)}")

    f = eval("lambda x: x ** 3")

    print(f"After shadowing: {f(2)}")

    function()

    function = eval("lambda: print('Malicious function')")

    function()

