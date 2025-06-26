def benign_computation():
    return 1 + sub_computation(2, 2)

def sub_computation(a, b):
    return a ** b

def malicious_computation():
    def sub_computation(a, b):
        print("I'm doing some malicious stuff! I'm so evil!")

        return a ** b

    return 1 + sub_computation(2, 2)

if __name__ == '__main__':
    print(f"Malicious computation result: {malicious_computation()}")
    print(f"Benign computation result: {benign_computation()}")