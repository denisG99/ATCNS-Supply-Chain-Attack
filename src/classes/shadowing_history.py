from classes.gitlog_parser import GitLogParser
from classes.detector import Detector

import subprocess

TEMP_FILE = "./tmp" # path of a temporary file containing the code to analyze

class ShadowingHistoty:
    """
    Class whose goal is to build the history of shadowing over time of a given file
    """

    def __init__(self, git_log: str, file_path: str):
        """
        :param git_log: git log of the file that we want to build the history
        :param file_path: path of the file that we want to build the history
        """
        self.__git_log = GitLogParser(git_log)
        self.__file_path = file_path

    def build_history(self) -> dict:
        """
        Build the history of shadowing over time of a given file
            * retrieve the file version from the commit hash (git show <commit_hash>:<file>)
            * detect shadowing
            * cycle over all the commits on the specific file

        :return: shadowing history of a file. The result as the following fields:
            * hash: hash of the commit constitutes the key for the dictionary entries
            * author: author of the commit
            * datetime: datetime of the commit
            * shadowing_vars: shadowed variables in the commited file
            * yara: yara rules in the commited file
            * shadowing: "true" if the commited file has shadowing, "false" otherwise
        """
        history = {}

        for hash in self.__git_log.get_commits_hashes():
            code_path = f"{TEMP_FILE}/code/{hash}.py"

            # retrieves file version of the given file associated to hash
            try:
                code = subprocess.run(
                    [
                        "git",
                        "-C", "/".join(self.__file_path.split("/")[:-1]),
                        "show",
                        f"{hash}:{self.__file_path.split('/')[-1]}"
                    ],
                    capture_output=True,
                    text=True,
                    check=True
                )
            except subprocess.CalledProcessError as e:
                print(f"Git command failed: {e.stderr}")
                history[hash] = "error"

            with open(code_path, "w") as f:
                f.write(code.stdout)

            shadowing, yara = Detector(code_path).shadowing_detection()

            history[hash] = {
                "author": self.__git_log.get_commit_author(hash),
                "datetime": self.__git_log.get_commit_datetime(hash),
                "shadowing": "true" if len(shadowing) > 0 or len(yara) > 0 else "false",
                "shadowing_vars": shadowing,
                "yara": yara
            }
        return history