class GitLogParser:
    def parse(self, gitlog: str) -> dict:
        print(gitlog)

if __name__ == "__main__":
    print(GitLogParser().parse(open("./gitlog_test.txt").read()))