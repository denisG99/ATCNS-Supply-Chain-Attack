import re

class GitLogParser:
    """
    Class that parse the git log command output into dictionary
    """
    def __init__(self, gitlog: str=""):
        """
        Constructor

        :param gitlog: output of git log command
        """
        if not gitlog == "":
            self.log: dict = self.__parse(gitlog)
        else:
            print("Empty gitlog provided")

    def __parse(self, gitlog: str) -> dict:
        """
        Execute the actual parsing of the git log

        :param gitlog: output of git log command
        :return: git log output parsed
        """
        # split git log by commits
        commits = re.split(r'(?=^commit\s+[0-9a-f]{40}\n)', gitlog, flags=re.MULTILINE)[1:]

        commits_info = {}

        # gather info about each commit: hash is the index of our dictionary
        for commit in commits:
            hash = re.search(r'commit\s+([0-9a-f]{40})', commit).group(1)
            author, mail = (aux := re.search(r'Author:\s+(.+)', commit).group(1).split(" "))[0], aux[1].replace("<", "").replace(">", "")
            datetime = re.search(r'Date:\s+(\w{3}\s+\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s+\d{4})', commit).group(1)
            description = re.search(r'\n\n\s*(.+)\n\n', commit).group(1)
            diffs = re.split(r'@@\s+-\d+(?:,\d+)?\s+\+\d+(?:,\d+)?\s+@@', commit)[1:]

            commits_info[hash] = {"author": author,
                                  "mail": mail,
                                  "datetime": datetime,
                                  "description": description,
                                  "diffs": diffs}

        return commits_info

    def get_commits_hashes(self) -> list:
        return list(self.log.keys())

    def get_commit_by_hash(self, hash: str) -> dict:
        return self.log[hash]

    def get_commit_author(self, hash: str) -> str:
        return self.log[hash]["author"]

    def get_commit_mail(self, hash: str) -> str:
        return self.log[hash]["mail"]

    def get_commit_datetime(self, hash: str) -> str:
        return self.log[hash]["datetime"]

    def get_commit_description(self, hash: str) -> str:
        return self.log[hash]["description"]

    def get_commit_diffs(self, hash: str) -> str:
        return self.log[hash]["diffs"]