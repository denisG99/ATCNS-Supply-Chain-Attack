# the goal of this code is to evaluate and shows how scope graph and detector work, so it is not intended to be executed
class PoC:
    def g(self, a, b):
        return a ** b

    def f(self):
        original = self.g

        def h(a, b): # doesn't override the original class method
            print("I'm doing some malicious stuff! I'm so evil!")

            return a ** b

        self.g = h # overwritten method
        x = self.g(2, 2)
        self.g = original # restoring the original method

        return 1 + x