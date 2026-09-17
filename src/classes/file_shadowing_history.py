from subprocess import CompletedProcess

from classes.gitlog_parser import GitLogParser
from classes.detectorv2 import Detector
from classes.lhdiff import LHDiff
from classes.memory import Memory

import subprocess
import os
import json

TEMP_FILE = "./tmp" # path of a temporary file containing the code to analyze

class FileShadowingHistory:
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
        self.__memory: Memory = Memory()

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

    def __parse_result(self, results: list, commit_hash: str, res_type: str) -> None:
        """
        Parses the provided results and updates the internal history data structure with
        the extracted information.

        This method iterates through a list of result objects and adds their data to the
        history dictionary under the specified commit hash and result type. If a result
        name does not exist in the history, it initializes an empty list for that name
        before extending it with the result's lines.

        Parameters:
            :param results (list): A list of result objects, each expected to have methods
                `get_name()` and `get_lines()` for retrieving its name and associated lines.
            :param commit_hash (str): The unique identifier of the commit for which the results
                are being parsed and stored.
            :param res_type (str): The type/category of the results being processed, used to
                separate different result groups in the history.

        Returns:
            None
        """
        for result in results:
            if result.get_name() not in self.__history[commit_hash][res_type].keys():
                self.__history[commit_hash][res_type][result.get_name()] = []

            self.__history[commit_hash][res_type][result.get_name()].extend(result.get_lines())

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

                with open(code_path, "w") as f: # era aperto in append
                    f.write(code.stdout)
            except subprocess.CalledProcessError as e:
                print(f"Git command failed: {e.stderr}")

                self.__history[commit_hash] = {
                    "author": self.__git_log.get_commit_author(commit_hash),
                    "datetime": self.__git_log.get_commit_datetime(commit_hash),
                    "shadowing": str(e),
                    "shadowing_res": {},
                    "yara": {}
                }
                continue

            # shadowing detection
            try:
                shadowing, yara = Detector(code_path, heuristic_path=self.__heuristic_path).shadowing_detection()
            except Exception as e:
                self.__history[commit_hash] = {
                    "author": self.__git_log.get_commit_author(commit_hash),
                    "datetime": self.__git_log.get_commit_datetime(commit_hash),
                    "shadowing": str(e),
                    "shadowing_res": {},
                    "yara": {}
                }
                continue

            self.__history[commit_hash] = {
                "author": self.__git_log.get_commit_author(commit_hash),
                "datetime": self.__git_log.get_commit_datetime(commit_hash),
                "shadowing": "true" if len(shadowing) > 0 or len(yara) > 0 else "false",
                "shadowing_res": {},
                "yara": {}
            }

            self.__parse_result(shadowing, commit_hash, "shadowing_res")
            self.__parse_result(yara, commit_hash, "yara")

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

    def __get_lines_history(self, lines: list[int], res_name: str, data: dict, start_commit: str = None) -> dict:
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
        commits = list(self.__history.keys())[::-1]
        tracker = LHDiff()
        tracker_res = []

        if data is not None:
            if res_name not in data.keys():
                data[res_name] = []

            for i in range(len(commits) - 1):
                try:
                    diff = tracker.diff("/".join(self.__file_path.split("/")[:-1]), commits[i], commits[i + 1], self.__file_path.split('/')[-1], raw=False)
                except Exception as e:
                    print(
                        f"Unable to diff {self.__file_path.split('/')[-1]} "
                        f"between {commits[i]} and {commits[i + 1]}: {e}"
                    )
                    diff = None

                tracker_res.append(diff)

            if len(tracker_res) > 0:
                for line in lines:
                    tracking_str = ""

                    try:
                        i = 0 if start_commit is None else commits.index(start_commit)

                        if i >= len(tracker_res):
                            continue

                        if tracker_res[i] is None:
                            tracking_str += "?"
                            data[res_name].append(tracking_str)
                            continue
                    except ValueError:
                        print("Commit not found, we begin from the first commit")
                        i = 0

                    tracking_str += f"{tracker_res[i][line - 1]['left']}->"
                    next_step = line

                    while i < len(tracker_res):
                        if tracker_res[i] is None:
                            tracking_str += "?"
                            break

                        try:
                            if tracker_res[i][next_step - 1]["right"] is None:
                                # remove no more interesting element from memory (aka shadowing is not longer there)
                                try:
                                    tracking_str += "_"

                                    #self.__memory.add(res_name, tracking_str)
                                    break
                                except ValueError:
                                    pass
                        except TypeError:  # handling the case in which lhdiff gives some error
                            tracking_str += "?"

                            #self.__memory.add(res_name, tracking_str)
                            break

                        next_step = tracker_res[i][next_step - 1]["right"]
                        tracking_str += f"{next_step}->"
                        i += 1

                    if i >= len(tracker_res):
                        tracking_str += f"..." # we reach the end of commit history and shadowing still there

                    #self.__memory.add(res_name, tracking_str)
                    data[res_name].append(tracking_str)

                return data

    def __tracking(self, commit: str, target: str, data: dict) -> dict:
        # based on the fact that the tracking is on contiguous commit, once we add an entry at every successive commit, the lifetime associated with all entry of key decrease
        self.__memory.decrease_lifetime()

        for key in self.__history[commit][target].keys():
            # handle shadowing introduction
            tracking_str = self.__get_lines_history(self.__history[commit][target][key], key, data["tracking_strings"], commit)

            if tracking_str is not None:
                for track in tracking_str[key]:
                    if not self.__memory.is_stored(key, track)[0]:
                        data["what_introduce"].append(key)
                        self.__memory.add(key, track)
            else:
                data["what_introduce"].append(key)

            if not len(data["what_introduce"]) > 0:
                data["tracking_strings"] = tracking_str

        #handle shadowing removal
        to_remove = self.__memory.clean_memory()

        if len(to_remove) > 0:
            for var_id, elem in to_remove:
                if var_id not in data["what_remove"]:
                    data["what_remove"][var_id] = []

                data["what_remove"][var_id].append(elem["line_tracker"])

        return data

    def get_file_history(self) -> dict:
        data_aux = {
            'commits' : {}
        }

        for i, commit_hash in enumerate(list(reversed(self.__history.keys()))[: -1]):
            if self.__history[commit_hash]["shadowing"] == "true":
                #print(f"\tCommit {i + 1}: {commit_hash}")

                data_aux['commits'][commit_hash] = {
                    "who" : self.__history[commit_hash]["author"],
                    "when" : self.__history[commit_hash]["datetime"],
                    "what_introduce":[],
                    "what_remove" : {},
                    "tracking_strings": {}
                }

                # tracking result of algorithm on scope graph
                data_aux['commits'][commit_hash] = self.__tracking(commit_hash, "shadowing_res", data_aux['commits'][commit_hash])
                # tracking YARA results
                data_aux['commits'][commit_hash] = self.__tracking(commit_hash, "yara", data_aux['commits'][commit_hash])

        # handle last hash
        try:
            last_hash = list(reversed(self.__history.keys()))[-1]

            data_aux['commits'][last_hash] = {
                "who": self.__history[last_hash]["author"],
                "when": self.__history[last_hash]["datetime"],
                "what_introduce": [],
                "what_remove": {},
                "tracking_strings": {}
            }

            # tracking result of algorithm on scope graph
            data_aux['commits'][last_hash] = self.__tracking(last_hash, "shadowing_res", data_aux['commits'][last_hash])
            # tracking YARA results
            data_aux['commits'][last_hash] = self.__tracking(last_hash, "yara", data_aux['commits'][last_hash])
        except IndexError:
            # fall in this case if the file history is empty(no commit for the file)
            pass

        return data_aux
