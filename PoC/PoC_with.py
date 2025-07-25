def computation(a, b):
    return a ** b

if __name__ == '__main__':
    print(f"Benign computation {computation(2, 3)}")

    with open("aux/aux.txt") as _:
        def computation(a, b):
            print("I'm doing some malicious stuff! I'm so evil!")

            return a ** b


        print(f"Malicious computation {computation(2, 3)}")

    print(f"Benign computation {computation(2, 3)}")