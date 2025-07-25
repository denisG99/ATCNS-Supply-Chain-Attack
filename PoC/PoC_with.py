import contextlib
import __main__ # we need this because we use functions defines into the main script, but could be any module where the target function is defined

@contextlib.contextmanager
def override_function(target_module, func_name, new_func):
    old_func = getattr(target_module, func_name) # storing temporarily the old function
    setattr(target_module, func_name, new_func) # overwrite the old function with the new one

    try:
        yield
    finally:
        setattr(target_module, func_name, old_func) # restoring old function

def computation(a, b):
    return a ** b


def malicious_computation(a, b):
    print("I'm doing some malicious stuff! I'm so evil!")

    return a ** b

if __name__ == '__main__':
    # this tecnique is often use to mocking, testing and libraries override
    print(f"Benign computation {computation(2, 3)}")

    with override_function(__main__, "computation", malicious_computation):
        print(f"Malicious computation {computation(2, 3)}")

    print(f"Benign computation {computation(2, 3)}")