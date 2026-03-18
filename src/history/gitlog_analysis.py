import subprocess

UNTIL = "2025-12-31"
TEMP_DIR = "./tmp"

def get_repo_url(pkg_name: str) -> str:
    ...

if __name__ == '__main__':
    filename = "../main.py"


    # clone repository
    subprocess.run(["git", "clone", repo_url, str(repo_path)], check=True)

    # get git log result
    try:
        result = subprocess.run(
            [
                "git",
                "-C", TEMP_DIR,
                "log",
                "--until", UNTIL,
                "-p", filename
            ],
            capture_output=True,
            text=True,
            check=True
        )

        print(result)
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {e.stderr}")