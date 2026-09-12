class Memory:
    """
    The goal of this class is to helps the tracking of the shadowing occurrences that were deleted based on the line tracker

    OPERATIONS:
    * add a new occurrence of shadowing to the memory
    * search for a shadowing occurrence in the memory
    * decrement the lifetime of a shadowing occurrence
    * remove a shadowing occurrence from the memory and return the elemets with the lifetime equal to zero
    """
    def __init__(self):
        """
        Constructor

        Memory is a dictionary with the following format:
            {"var_name":[{"line_tracker": <str>, "lifetime": <int>},...{...}]}
        where the lifetime field is init to the length of the line tracker and will be decremented every time will
        encounter the correspondent variable
        """
        self.__memory: dict = {}

    def is_stored(self, key: str, tracker: str) -> tuple[bool, int]:
        """
        Checks whether a variable name and its associated tracker are stored in memory.

        The method determines if a specific variable name exists in the internal memory structure
        and whether its associated entry ends with the given tracker value. This can be useful for
        validating the presence of a variable and its tracking metadata.

        Parameters:
            :param var_name: str
                The name of the variable to search for in memory.
            :param tracker: str
                The tracking string to match against the stored entries. Can be the full tracker or may has an arbitrary starting point

        :returns: bool
            True if the variable name exists in memory and has an associated entry that ends with the given tracker string.
            Otherwise, returns False.
            Moreover, get the index where the specific tracker is "stored in"
        """
        if key not in self.__memory:
            return False, -1

        for i, entry in enumerate(self.__memory[key]):
            if entry["line_tracker"].endswith(tracker):
                return True, i
            continue

        return False, -1

    def get_memory(self) -> dict:
        return self.__memory

    def add(self, key: str, tracker: str) -> None:
        # add empty memory entry if it doesn't exist
        if key not in self.__memory:
            self.__memory[key] = []

        if not self.is_stored(key, tracker)[0]:
            self.__memory[key].append({"line_tracker": tracker, "lifetime": len(tracker.split("->"))})

    def decrease_instance_lifetime(self, key: str, tracker: str) -> None:
        exists, idx = self.is_stored(key, tracker)

        if exists:
            self.__memory[key][idx]["lifetime"] -= 1

    def decrease_lifetime(self) -> None:
        for key in self.__memory:
            for entry in self.__memory[key]:
                self.decrease_instance_lifetime(key, entry["line_tracker"])

    def remove_elem(self, key: str, tracker: str) -> dict | None:
        exists, idx = self.is_stored(key, tracker)

        if exists and self.__memory[key][idx]["lifetime"] <= 0:
            return self.__memory[key].pop(idx)
        return None

    def clean_memory(self) -> list:
        to_remove = []

        for key in self.__memory.keys():
            to_remove.extend([(key, entry) for entry in self.__memory[key] if entry["lifetime"] <= 0])

            for elem in to_remove:
                self.remove_elem(key, elem[1]["line_tracker"])

        return to_remove


if __name__ == "__main__":
    memory = Memory()
    memory.add("a", "a->b->c")
    memory.add("a", "1->2->3")
    memory.add("b", "a->b->c")

    print(memory.get_memory())

    memory.decrease_lifetime()
    memory.decrease_lifetime()
    memory.decrease_lifetime()

    print(memory.clean_memory())

    print(memory.get_memory())