import subprocess
import tempfile
import os

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

    def diff(self, repo_path: str, commit_left: str, commit_right: str, file_path: str, raw: bool=True) -> None | list[dict[str, int | None]] | str | Any:
        """
        Executes the lhdiff tool on a file across two commits and optionally parses the output.

        This method compares the specified file across two git commits using the lhdiff tool.
        Temporary files are created to store the file contents at each commit, which are then
        passed as input to the lhdiff tool. The method returns a parsed representation of the
        output if not in raw mode.

        Parameters:
            :param repo_path: str
                The path to the git repository.
            :param commit_left: str
                The identifier of the earlier or left commit (e.g., commit hash).
            :param commit_right: str
                The identifier of the later or right commit (e.g., commit hash).
            :param file_path: str
                The relative path to the file to be compared.
            :param raw: bool, optional
                A flag indicating whether to return the raw output of lhdiff. Defaults to True.


        :returns: None | list[dict[str, int | None]] | str | Any
            Returns `None` if there is an issue preventing the command from running.
            If `raw` is True, the raw output of the lhdiff tool is returned as a string.
            Otherwise, returns the parsed output of the lhdiff command as a data structure.

        :raises: subprocess.CalledProcessError
            If any subprocess command fails during execution.
        """
        def git_show(commit: str, path: str) -> str:
            """Extract file content at a given commit."""
            result = subprocess.run(
                ["git", "-C", repo_path, "show", f"{commit}:./{path}"],
                capture_output=True,
                text=True,
                check=True,
            )

            return result.stdout

        # Get file contents at each commit
        left_content = git_show(commit_left, file_path)
        right_content = git_show(commit_right, file_path)

        # Write to temp files and call lhdiff
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as left_tmp, \
                tempfile.NamedTemporaryFile(mode="w+", delete=False) as right_tmp:
            try:
                left_tmp.write(left_content)
                left_tmp.flush()
                right_tmp.write(right_content)
                right_tmp.flush()

                cmd = ["lhdiff"]
                cmd += [left_tmp.name, right_tmp.name]

                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                return result.stdout if raw else self.__parse(result.stdout)

            except subprocess.CalledProcessError as e:
                print(f"Error executing lhdiff: {e.stderr}")

            finally:
                # erase temp files
                os.unlink(left_tmp.name)
                os.unlink(right_tmp.name)