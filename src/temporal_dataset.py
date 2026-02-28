"""
The goal of this file is to create a dataset containing additional information about top 50k packages:
    * author -> PyPI API (https://pypi.org/pypi/<package-name>/json)
    * owner -> PyPI API (https://pypi.org/pypi/<package-name>/json)
    * contributors -> Github log command
    * categories -> Github API (https://api.github.com/repos/<owner>/<repo>/topics)
"""
from collections import Counter
from pathlib import Path

import subprocess
import requests
import os
import re
import json

import pandas as pd
import numpy as np

PYPI_API: str = "https://pypi.org/pypi/<package-name>/json"
GITHUB_API_CONTRIBUTORS: str = "https://api.github.com/repos/<owner>/<repo>/contributors"
GITHUB_API_TOPICS: str = "https://api.github.com/repos/<owner>/<repo>/topics"
RESULTS_DATA_DIR: str = "../data/results" # path to the json files containing the information about shadowing of top n packages
CSV_DIR_PATH: str = "../data/pkgs info"
TMP_DIR_PATH: str = "./temp"

def get_year_contributors(repo_url: str, year: int) -> Counter:
    """
    Function get the contributor until a given year cloning the repository and then extract the contributor using 'git log' command,
    giving all commit

    :param repo_url: repository link to clone
    :param year: year to analyze

    :return: dictionary contains the contributors and the number of their contribution made until the given year
    """

    clone_dir = Path(TMP_DIR_PATH)
    clone_dir.mkdir(exist_ok=True)

    repo_name = repo_url.split("/")[-1].replace(".git", "")
    repo_path = clone_dir / repo_name

    # Clone if not exists
    if not repo_path.exists():
        subprocess.run(["git", "clone", repo_url, str(repo_path)], check=True)

    # Pull latest changes
    subprocess.run(["git", "-C", str(repo_path), "pull"], check=True)

    until = f"{year}-12-31"

    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo_path),
            "log",
            "--until", until,
            "--pretty=%an"
        ],
        capture_output=True,
        text=True,
        check=True
    )

    authors = result.stdout.strip().split("\n")
    counter = Counter(authors)

    return counter

if __name__ == "__main__":
   for file in os.listdir(RESULTS_DATA_DIR):
        year = int(file.split("_")[-1].replace(".json", ""))

        with open(f"{RESULTS_DATA_DIR}/{file}", "r") as f:
            pkgs: dict = json.load(f)
            df_info: pd.DataFrame = pd.DataFrame(data={"pkg_name": pkgs,
                                                       "author": np.empty(len(pkgs), dtype=str),
                                                       "owner": np.empty(len(pkgs), dtype=str),
                                                       "contributors": np.empty(len(pkgs), dtype=str),
                                                       "categories": np.empty(len(pkgs), dtype=str)})
            df_info.set_index("pkg_name", inplace=True)

            for pkg in pkgs.keys():
                if pkgs[pkg]["shadowing"] == "true":
                    pypi_info: dict = requests.get(PYPI_API.replace("<package-name>", pkg)).json()

                    # infos about package author and owner from PyPI API
                    try:
                        author: str = pypi_info["info"]["author"]
                    except KeyError:
                        author = "Unknown"

                    owner: str = "Unknown"

                    for source in ["Source", "Homepage"]:
                        if source in pypi_info["info"]["project_urls"].keys() and re.match(r"^https://github.com/", pypi_info["info"]["project_urls"][source]):
                            owner = pypi_info["info"]["project_urls"][source].split("/")[-2]
                            repo: str = pypi_info["info"]["project_urls"][source].split("/")[-1]


                    df_info.loc[pkg, "author"] = author
                    df_info.loc[pkg, "owner"] = owner

                    #  infos about contributors from Github API
                    contributors: str = str(list(get_year_contributors(f"https://github.com/{owner}/{pkg}.git", year)))

                    df_info.loc[pkg, "contributors"] = contributors

                    # infos about categories from Github API
                    categories: str = ""

                    if not owner ==  "Unknown":
                        categories = ",".join(requests.get(GITHUB_API_TOPICS.replace("<owner>", owner).replace("<repo>", repo)).json()["names"])

                    df_info.loc[pkg, "categories"] = categories

        # save dataframe in CSV format
        df_info.to_csv(f"{CSV_DIR_PATH}/{file.replace('.json', '.csv')}")