from gitlog_parser import GitLogParser
from detector import Detector

import re

TEMP_FILE = "./tmp/tmp.py" # path of a temporary file containing the code to analyze

class ShadowingHistoty:
    """
    Class whose goal is to build the history of shadowing over time of a given file
    """

    def __init__(self, gitlog_output: str, detector_results: tuple):
        """
        :param gitlog_output: git log output
        :param detector_results: result of the detector, gives the expected results (ideally should be the results of the most recent version pf the package)
        """
        self.__file_history: GitLogParser = GitLogParser(gitlog_output)
        self.__shadowing, self.__yara = detector_results

    def get_file_history(self) -> GitLogParser:
        return self.__file_history

    def build_history(self) -> dict:
        """
        Build the history of shadowing over time of a given file

        :return: shadowing history of a file. The result as the following fields:
            * author: author of the commit
            * datetime: datetime of the commit
            * ref_shadowed_vars: reference result for shadowed variables
            * shadowed_vars: shadowed variables in the commited file
            * ref_yara: reference result for yara rules
            * yara: yara rules in the commited file
            * shadowing: "true" if the commited file has shadowing, "false" otherwise
        """
        history = {}

        for hash in self.__file_history.get_commits_hash():
            diff = self.__clean_diff(self.file_history.get_commit_diffs(hash))

            with open(TEMP_FILE, 'w') as f:
                f.write(diff)

            detector = Detector(TEMP_FILE)
            shadowing, yara = detector.shadowing_detection()

            hystory[hash] = {"author": self.__file_history.get_commit_author(hash),
                             "datetime": self.__file_history.get_commit_datetime(hash),
                             "ref_shadowed_vars": self.__shadowing,
                             "shadowed_vars": shadowing,
                             "ref_yara": self.__yara,
                             "yara": yara,
                             "shadowing": "true" if len(shadowing) > 0 or len(yara) > 0 else "false"}

        return history

    def __clean_diff(self, diff: str) -> str:
        """
        Clean up the diffs result from deletion keeping only teh addition in order to have the committed version of the file.
        It performs the following operations to clean the string:
            * remove character '+' ad the beginning of the line
            * remove lines of code beginning with '-'

        :param diff: diffs sting
        :return: actual committed code as string
        """

        addition_regex = r'^\+'
        deletion_regex = r'^\-.*'

        diff = re.sub(addition_regex, " ", diff, flags=re.MULTILINE)
        diff = re.sub(deletion_regex, "", diff, flags=re.MULTILINE)

        return diff

if __name__ == '__main__':
    shadowing_history = ShadowingHistoty(open("./test.txt", 'r').read(), ([], []))

    for commit in shadowing_history.get_file_history().get_commits_hashes():
        history = shadowing_history.build_history()

    print(history)