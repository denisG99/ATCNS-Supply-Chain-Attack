from unittest.mock import patch
from contextlib import contextmanager

import os

@patch("os.listdir")
def test():
    assert "test1" == os.listdir()


@contextmanager
def ContextManager():
    # Before yield as the enter method
    print("Enter method called")
    yield

    # After yield as the exit method
    print("Exit method called")

if __name__ == "__main__":
    with ContextManager() as ctx:
        ...