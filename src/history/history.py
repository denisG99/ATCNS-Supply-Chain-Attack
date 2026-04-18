import pathlib
import subprocess
import re
import requests
import json

from classes.detector import Detector
from classes.shadowing_history import ShadowingHistoty

UNTIL: str = "2025-12-31"
TEMP_DIR: str = "./tmp"
HISTORY_OUTPUT_DIR: str = "./history_output"
PYPI_API: str = "https://pypi.org/pypi/<package-name>/json"
HEURISTICS_DIR: str = "../classes/heuristics"

def get_owner(pkg_name: str) -> str | None:
    """
    Return the owner of the package

    :param pkg_name: name of the package that we want to get the owner
    :return: owner of the package
    """
    pypi_info = requests.get(PYPI_API.replace("<package-name>", pkg_name)).json()

    for source in ["source", "homepage"]:
        if source in pypi_info["info"]["project_urls"].keys() and re.match(r"^https://github.com/", pypi_info["info"]["project_urls"][source]):
            return pypi_info["info"]["project_urls"][source].split("/")[-2]

def get_repo_url(pkg_name: str) -> str:
    """
    Get the repository url associated to a package

    :param pkg_name: name of the package that we want to get the repository url
    :return: repository url associated to the package
    """
    owner = get_owner(pkg_name)

    return f"https://github.com/{owner}/{pkg_name}.git"

def file_has_shadowing(shadowing_res: dict) -> bool:
    """
    Check if a file has shadowing

    :param shadowing_res: dictionary containing the shadowing results of a file
    :return: True if the file has shadowing, False otherwise
    """
    return len(shadowing_res["shadowing"]) > 0 or len(shadowing_res["yara"]) > 0

if __name__ == '__main__':
    # select packages to analyze, according to some criteria
    pkg_list = ["numpy"] # TODO: cambiare con lista di packages da analizzare

    for pkg in pkg_list:
        repo_url: str = get_repo_url(pkg)
        download_path: str = f"{TEMP_DIR}/{pkg}"
        shadowing_refs_by_file: dict = {}
        history: dict = {}

        # clone repository
        if not pathlib.Path(download_path).exists():
            try:
                subprocess.run(["git", "clone", repo_url, download_path], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Git clone command failed: {e.stderr}")
        else:
            print(f"Repository {download_path} already exists")

        # shadowing results over all files as reference in the current version of the repository
        for py_file in pathlib.Path().glob(f"./tmp/{pkg}/**/*.py"):  # takes only python files in all possible directories
            try:
                detector = Detector(f"{py_file}", heuristic_path=HEURISTICS_DIR)

                if detector.get_builder() is None:
                    shadowing_refs_by_file[py_file] = {"shadowing": [],
                                                       "yara": [],
                                                       "scope_chain_length": 0}
                    continue

                shadowing, yara = detector.shadowing_detection()

                yara_rule_names = [rule.rule for rule in yara]  # list contains the names of the yara rules
                scope_chain_length = detector.get_builder().length_longest_scope_chain()

                shadowing_refs_by_file[str(py_file)] = {"shadowing": shadowing,
                                                        "yara": yara,
                                                        "scope_chain_length": scope_chain_length}
            except Exception as e:
                print(f"Error processing file {py_file}: {e}")
                continue

        # get list of files that has shadowing detected
        files = [file for file in shadowing_refs_by_file.keys() if file_has_shadowing(shadowing_refs_by_file[file])]

        # get git log result for files that has shadowing until December 31, 2025
        for filename in files:
            filename = str(filename).split('/')
            key = "_".join(filename[2: ])

            try:
                git_log = subprocess.run(
                    [
                        "git",
                        "-C", '/'.join(filename[:-1]),
                        "log",
                        "--until", UNTIL,
                        "-p", filename[-1]
                    ],
                    capture_output=True,
                    text=True,
                    check=True
                )

                # build history of shadowing of a given file
                history[key] = ShadowingHistoty(git_log.stdout, "/".join(filename), HEURISTICS_DIR).build_history()

            except subprocess.CalledProcessError as e:
                print(f"Git command failed: {e.stderr}")
                history[key] = {}
                continue

        json.dump(history, open(f"{HISTORY_OUTPUT_DIR}/{pkg}.json", "w"), indent=4)