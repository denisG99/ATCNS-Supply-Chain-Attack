import subprocess

from pathlib import Path
from typing import Any

class LHDiff:
    """
    This class is a wrapper for the LHDiff tool available at https://github.com/SmartBear/lhdiff.

    PREREQUISITE:
        * LHDiff tool installed, preferably download the latest release for your architecture and OS
        * having git installed
        * SUGGESTION: add the command to the PATH environment variable
    """
    def __init__(self, command_path: str="lhdiff"):
        if not (command_path.endswith("lhdiff") or command_path.endswith("lhdiff.exe")):
            raise ValueError("The command path must be the path to the lhdiff executable")

        self.__command_path = command_path

    @staticmethod
    def __parse(output: str) -> list[dict[str, int | None]]:
        """
        Parses a given string into a list of dictionaries, representing mappings.

        Each line in the input string is split by a comma to extract two values. These values
        are converted into integers unless they are underscores ("_"), in which case they
        are replaced with None. The result is a list of dictionaries, each having the keys
        'left' and 'right'.

        Parameters:
        :param output: str
            A string containing mappings, where each line consists of two values separated by a comma.

        :returns: list[dict[str, int | None]]
            A list of dictionaries, where each dictionary maps 'left' and 'right' to either
            an integer value or None if the corresponding input is an underscore.
        """

        mappings = []

        for line in output.strip().splitlines():
            left, right = line.split(",")

            mappings.append({
                "left": None if left == "_" else int(left),
                "right": None if right == "_" else int(right),
            })

        return mappings

    def diff(self, left: str, right: str, raw: bool=True) -> None | list[dict[str, int | None]] | str | Any:
        """
        Generates a diff between two files based on the provided parameters.

        This method utilizes an external command to compute the differences between
        two files specified by their paths. The result can be returned in its raw form
        or as a structured, parsed output depending on the input argument. If any
        errors occur during execution, they are either returned as part of the output
        or printed to the console.

        Parameters:
        :param left: str
            The path to the first file to be compared.
        :param right: str
            The path to the second file to be compared.
        :param raw: bool (Optional)
            A flag to determine whether the result is returned in its raw form. If set to True,
            returns the raw command output as a string. If set to False, the output is parsed.
            Default value is True.

        :returns: None | list[dict[str, int | None]] | str | Any
            Returns a parsed representation of differences between files if raw is False. If raw is True,
            returns the raw text output of the diff command. In case of errors, returns an error message
            as a string.

        Raises:
        subprocess.CalledProcessError
            If the external command fails to execute properly. Errors are printed to the console.
        """
        try:
            result: subprocess.CompletedProcess = subprocess.run([self.__command_path, left, right], capture_output=True, text=True, check=True)

            if result.stderr != "":
                return f"LHDiff command gives the following error: {result.stderr}"
            return result.stdout if raw else self.__parse(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error executing lhdiff: {e.stderr}")

if __name__ == "__main__":
    lhdiff = LHDiff()

    print(lhdiff.diff(str(Path("./test1")), str(Path("./test2")), False))