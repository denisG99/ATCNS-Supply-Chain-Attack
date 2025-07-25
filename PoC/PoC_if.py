def computation():
    return 1 + sub_computation(2, 2)

def sub_computation(a, b):
    return a ** b

if __name__ == '__main__':
    print(f"Benign computation result: {computation()}")

    if True:
        def sub_computation(a, b):
            print("I'm doing some malicious stuff! I'm so evil!")

            return a ** b

        print(f"Malicious computation result: {computation()}")

    print(f"Benign computation result: {computation()}")