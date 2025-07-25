def computation(a, b):
    return a ** b

if __name__ == '__main__':
    i = 0

    while i < 2:
        print(f"Benign computation {computation(2, i)}")
        i += 1

    i = 0

    while i < 2:
        def computation(a, b):
            print("I'm doing some malicious stuff! I'm so evil!")

            return a ** b

        print(f"Malicious computation {computation(2, i)}")
        i += 1

    i = 0

    while i < 2:
        print(f"Benign computation {computation(2, i)}")
        i += 1