from subprocess import CompletedProcess

from classes.gitlog_parser import GitLogParser
from classes.detectorv2 import Detector
from classes.lhdiff import LHDiff

import subprocess
import os
import json

TEMP_FILE = "./tmp" # path of a temporary file containing the code to analyze

class FileShadowingHistoty:
    """
    Class whose goal is to build the history of shadowing over time of a given file
    """

    def __init__(self, git_log: str, file_path: str, heuristic_path: str) -> None:
        """
        Parameters:
            :param git_log: str
                git log of the file that we want to build the history
            :param file_path: str
                path of the file that we want to build the history
            :param heuristic_path: str
                path containing the heuristics for the detector
        """
        self.__git_log: GitLogParser = GitLogParser(git_log)
        self.__file_path: str = file_path
        self.__heuristic_path: str = heuristic_path
        self.__history: dict = {}
        self.__memory: list = [] #list that works as memory to save the already seen results and to understand when the result doesn't still anymore within the results

    def get_history(self) -> dict:
        return self.__history

    def __get_code_by_hash(self, commit_hash: str) -> CompletedProcess[str]:
        """
        Retrieve the code content of a specific file at a given commit hash from a Git repository.

        This method executes a Git command to fetch the contents of the file specified by
        its path at the specific commit hash. The file path is inferred from the object's
        internal state, omitting any private details. The command output includes the
        desired file's content if successful.

        Parameters:
            commit_hash:
                A string representing the hash of the commit from which the file content should be retrieved.

        Returns:
            CompletedProcess: A subprocess.CompletedProcess instance containing the captured
                              output, with the file's content available in the `stdout` attribute.
        """
        return subprocess.run(
            [
                "git",
                "-C", "/".join(self.__file_path.split("/")[:-1]),
                "show",
                f"{commit_hash}:./{self.__file_path.split('/')[-1]}"
            ],
            capture_output=True,
            text=True,
            check=True
        )

    def build(self, save_commits: bool= False):
        """
        Build the history of shadowing over time of a given file given its git-history
            * retrieve the file version from the commit hash (git show <commit_hash>:<file>)
            * detect shadowing
            * cycle over all the commits on the specific file

        Parameters:
            :param save_commits: bool
                if True, we save the code of the file at each commit. Make sure to have large memory available(memory consuming
                task especially for big repositories).

        :return: shadowing history of a file. The result has the following fields:
            * hash: hash of the commit constitutes the key for the dictionary entries
            * author: author of the commit
            * datetime: datetime of the commit
            * shadowing_vars: shadowed variables in the commited file
            * yara: yara rules in the commited file
            * shadowing: "true" if the commited file has shadowing, "false" otherwise
        """
        if self.__git_log.gitlog_is_empty():
            return

        for commit_hash in self.__git_log.get_commits_hashes():
            if save_commits:
                code_path = f"{TEMP_FILE}/code/{'-'.join(self.__file_path.split("/")[: -1])}/{self.__file_path.split("/")[-1].replace(".py", "")}/{commit_hash}.py"
            else:
                code_path = f"{TEMP_FILE}/code/commit.py"

            # retrieves file version of the given file associated to hash
            try:
                code = self.__get_code_by_hash(commit_hash)

                if not os.path.exists(code_path):
                    os.makedirs(os.path.dirname(code_path), exist_ok=True)

                with open(code_path, "w+") as f:
                    f.write(code.stdout)
            except subprocess.CalledProcessError as e:
                print(f"Git command failed: {e.stderr}")

                self.__history[commit_hash] = "error"

            # shadowing detection
            try:
                shadowing, yara = Detector(code_path, heuristic_path=self.__heuristic_path).shadowing_detection()
            except Exception as e:
                self.__history[commit_hash] = {
                    "author": self.__git_log.get_commit_author(commit_hash),
                    "datetime": self.__git_log.get_commit_datetime(commit_hash),
                    "shadowing": str(e),
                    "shadowing_res": [],
                    "yara": []
                }

                continue

            self.__history[commit_hash] = {
                "author": self.__git_log.get_commit_author(commit_hash),
                "datetime": self.__git_log.get_commit_datetime(commit_hash),
                "shadowing": "true" if len(shadowing) > 0 or len(yara) > 0 else "false",
                "shadowing_res": [{"name": result.get_name(),
                                   "line": result.get_lines()} for result in shadowing],
                "yara": [{"name": match.get_name(),
                          "line": match.get_lines()} for match in yara]
            }

    def dump(self, save_dir: str = "./") -> None:
        """
        Saves the current state of history to a JSON file called 'shadowing_history.json'.

        This method serializes the current state of the internal history and writes
        it to a JSON file located at the specified destination path.

        Parameters:
            :param save_dir: str
                The directory path where the JSON file will be saved. Defaults to "./".
        """
        json.dump(self.__history, open(f"{save_dir}/{self.__file_path.split('/')[-1]}_shadowing_history.json", "w"), indent=4)

    def __get_lines_history(self, lines: list[int], res_name: str, start_commit: str=None):
        """
        Retrieves the history of specified lines in a file, tracking changes across
        commits from the current state to a starting commit if provided.

        Parameters:
            :param lines: list[int]
                A list of line numbers for which the history is to be tracked.
            :param start_commit: str, optional
                The hash of the commit from which the tracking should begin. If not provided, the history is tracked from
                the first available commit.

        :raises: ValueError
            Raised if the provided start_commit is not found in the commit history.

        Notes:
            The function analyzes line changes across commits using a diff tracker
            and prints the history of each line. The history of each line ends when
            the line is deleted, or no further changes are found in subsequent commits.
        """
        commits = list(self.__history.keys())
        tracker = LHDiff()
        tracker_res =[]
        i = len(commits) - 1

        while i > 0:
            diff = tracker.diff("/".join(self.__file_path.split("/")[:-1]), commits[i], commits[i - 1], self.__file_path.split('/')[-1], raw=False)

            tracker_res.append(diff)
            i -= 1

        if len(tracker_res) > 0:
            for line in lines:
                try:
                    i = 0 if start_commit is None else (len(commits) - 1) - commits.index(start_commit)
                except ValueError:
                    print("Commit not found, we begin from the first commit")
                    i = 0

                print(tracker_res[i][line - 1]["left"], end="->")
                next_step = line

                while i < len(tracker_res):
                    if tracker_res[i][next_step - 1]["right"] is None:
                        # remove no more interesting element from memory (aka shadowing is not longer there)
                        try:
                            self.__memory.remove(res_name)
                        except ValueError:
                            pass
                        finally:
                            print("_")
                            break

                    next_step = tracker_res[i][next_step - 1]["right"]
                    i += 1

                    print(next_step, end="->")

                if i >= len(tracker_res):
                    print("...") # we reach the end of commit history and shadowing still there
                    print(f"Shadowing on {res_name} still there\n\n")

    def __memory_remove_elems(self, current_res: list[dict]) -> list[str]:
        """
        Works as a pop, so it removes elements from memory that are no longer needed based on the current result, remove
        them form memory and get them as output.

        Parameters:
            :param current_res: list[dict]
                list containing the result of the detector

        :return: list[str] list of elements that are no longer needed (already removed from the memory). Such results can be
        interpreted as removed shadowing

        """
        if not bool(intesection := set(self.__memory) & set([result["name"] for result in current_res])): # check if the set is empty
            return []

        to_remove = list(set(self.__memory) - intesection)

        # remove elem from memory
        for elem in to_remove:
            self.__memory.remove(elem)

        print(f"memory after remove: {self.__memory}")
        return to_remove

    def __tracking(self, commit: str, target: str):
        # update memory removing the results that are no longer needed
        excluded: list = self.__memory_remove_elems(self.__history[commit][target])

        if len(excluded) != 0:
            for elem in excluded:
                print(f"Shadowing on {elem} was removed on {commit} by {self.__history[commit]['author']} at {self.__history[commit]['datetime']}\n\n")

        for match in self.__history[commit][target]:
            if match["name"] not in self.__memory:
                print(f"Shadowing on {match['name']} was introduced on {commit} by {self.__history[commit]['author']} at {self.__history[commit]['datetime']}")
                # add unseen element to memory
                self.__memory.append(match["name"])

                print(f"\tTracking {match['name']}: ", end="")
                self.__get_lines_history(match["line"], match["name"],commit)

    def get_file_history(self):
        print(f"Tracking history of {self.__file_path} ...")

        # TODO: dataset building (vedi apputi ipad per la struttura)
        # TODO: gestire ultima commit
        # TODO: line tracking as string

        for i, commit_hash in enumerate(list(reversed(self.__history.keys()))[: -1]):
            if self.__history[commit_hash]["shadowing"] == "true":
                print(f"\tCommit {i + 1}: {commit_hash}")

                # tracking result of algorithm on scope graph
                self.__tracking(commit_hash, "shadowing_res")
                # tracking YARA results
                self.__tracking(commit_hash, "yara")

if __name__ == "__main__":
    history = FileShadowingHistoty(open("./test.txt").read(), "./pyjokes/pyjokes/pyjokes.py", "./heuristics")
    history.build()
    history.get_file_history()