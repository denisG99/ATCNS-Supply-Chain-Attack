# the goal of this code is to evaluate and shows how scope graph and detector work, so it is not intended to be executed
def g():
    ...

def f():
    x = "http://xdaforums.com/t/access-adb-without-debug-mode.1283054/"

    def g():
        x  = "http://xdaforums.com/t/access-adb-without-debug-mode.1283054/6"
        #return x + y
        ...

    return g()