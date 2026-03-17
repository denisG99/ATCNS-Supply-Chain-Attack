import subprocess

UNTIL = "2025-12-31"

if __name__ == '__main__':
    filename = "../main.py"
    try:
        result = subprocess.run(
            [
                "git",
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