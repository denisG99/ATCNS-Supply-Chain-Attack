from classes.package_shadowing_history import PackageShadowingHistory

import json
import random

from tqdm import tqdm

HISTORY_OUTPUT_DIR = "../../data/history"
NUM_PACKAGES = 400 # for having 95% of confidence level with 5% of error
PACKAGE_LIST_PATH = "../../data/top packages/top50000_2025.json"
FILE_NAME = "400.json"

if __name__ == "__main__":
    package_history:dict = {}

    with open(PACKAGE_LIST_PATH, "r") as f:
        pkgs_list = random.sample(json.load(f), NUM_PACKAGES)

    for pkg_name in tqdm(pkgs_list):
        package_history[pkg_name] = {}

        try:
            package_history[pkg_name] = PackageShadowingHistory(pkg_name, "../classes/heuristics").get_package_history()
        except ValueError as e:
            # handle the case in which the script isn't able to retrieve the repository's URL and so cloning
            print(e)
            continue

    json.dump(package_history, open(f"{HISTORY_OUTPUT_DIR}/{FILE_NAME}", "w"), indent=4)