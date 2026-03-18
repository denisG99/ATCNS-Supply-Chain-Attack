import re

class GitLogParser:
    def __init__(self, gitlog: str=""):
        if not gitlog == "":
            self.log: dict = self.__parse(gitlog)
        else:
            print("Empty gitlog provided")

    def __parse(self, gitlog: str) -> dict:
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

if __name__ == "__main__":
    gitlog_parser = GitLogParser(open("./gitlog_test.txt", "r").read())