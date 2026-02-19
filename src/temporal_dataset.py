"""
The goal of this file is to create a dataset containing additional information about top 50k packages:
    * author -> PyPI API (https://pypi.org/pypi/<package-name>/json)
    * owner -> PyPI API (https://pypi.org/pypi/<package-name>/json)
    * contributors -> Github API (https://api.github.com/repos/<owner>/<repo>/contributors)
    * categories -> Github API (https://api.github.com/repos/<owner>/<repo>/topics)
"""
import requests
import os
import re

import pandas as pd
import numpy as np

PYPI_API: str = "https://pypi.org/pypi/<package-name>/json"
GITHUB_API_CONTRIBUTORS: str = "https://api.github.com/repos/<owner>/<repo>/contributors"
GITHUB_API_TOPICS: str = "https://api.github.com/repos/<owner>/<repo>/topics"
PKGS_DATA_DIR: str = "../data/top packages" # path to the json file containing the top n packages names
CSV_DIR_PATH: str = "../data/pkgs info"

if __name__ == "__main__":
    for file in os.listdir(PKGS_DATA_DIR):
        lst_pkgs: list = pd.read_json(f"{PKGS_DATA_DIR}/{file}")[0]

        df_info: pd.DataFrame = pd.DataFrame(data={"pkg_name": lst_pkgs,
                                                   "author": np.empty(len(lst_pkgs), dtype=str),
                                                   "owner": np.empty(len(lst_pkgs), dtype=str),
                                                   "contributors": np.empty(len(lst_pkgs), dtype=str),
                                                   "categories": np.empty(len(lst_pkgs), dtype=str)})
        df_info.set_index("pkg_name", inplace=True)

        for pkg in lst_pkgs:
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
            contributors: str = ""

            if not owner ==  "Unknown":
                git_response: dict = requests.get(GITHUB_API_CONTRIBUTORS.replace("<owner>", owner).replace("<repo>", repo)).json()

                contributors = ",".join([str((contributor["login"], contributor["contributions"])) for contributor in git_response])

            df_info.loc[pkg, "contributors"] = contributors

            # infos about categories from Github API
            categories: str = ""

            if not owner ==  "Unknown":
                categories = ",".join(requests.get(GITHUB_API_TOPICS.replace("<owner>", owner).replace("<repo>", repo)).json()["names"])

            df_info.loc[pkg, "categories"] = categories

        # save dataframe in CSV format
        df_info.to_csv(f"{CSV_DIR_PATH}/{file.replace('.json', '.csv')}")