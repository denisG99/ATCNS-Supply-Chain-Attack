# the goal of this code is to evaluate and shows how scope graph and detector work, so it is not intended to be executed
def g():
    ...

def f():
    x = 1

    def g():
        x  = 4
        #return x + y
        ...

    return g()