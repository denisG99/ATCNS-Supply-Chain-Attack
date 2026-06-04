class Result:
    def __init__(self, name: str, lines: list[int]):
        self.__name: str = name
        self.__lines: list[int] = lines

    def __str__(self) -> str:
        return f"Result(name={self.__name}, lines={self.__lines})"

    def __repr__(self) -> str:
        return self.__str__()

    def get_name(self) -> str:
        return self.__name

    def get_lines(self) -> list[int]:
        return self.__lines

    def set_name(self, name: str) -> None:
        self.__name = name

    def set_lines(self, lines: list[int]) -> None:
        self.__lines = lines
