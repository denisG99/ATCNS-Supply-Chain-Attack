class PoC:
    def benign_computation(self):
        return 1 + self._sub_computation(2, 2)

    def _sub_computation(self, a, b):
        return a ** b

    def malicious_computation(self):
        original_sub_computation = self._sub_computation

        def _sub_computation(a, b): # doesn't override the original class method
            print("I'm doing some malicious stuff! I'm so evil!")

            return a ** b

        self._sub_computation = _sub_computation # overwritten method
        sub_computation = self._sub_computation(2, 2)
        self._sub_computation = original_sub_computation # restoring the original method

        return 1 + sub_computation

if __name__ == '__main__':
    poc = PoC()

    print(f"Malicious computation result: {poc.malicious_computation()}")
    print(f"Benign computation result: {poc.benign_computation()}")