from classes.package_shadowing_history import PackageShadowingHistory

import json
import random
import os

from tqdm import tqdm

HISTORY_OUTPUT_DIR = "../../data/history"
NUM_PACKAGES = 1 # for having 95% of confidence level with 5% of error (400 pkgs)
PACKAGE_LIST_PATH = "../../data/top packages/top50000_2025.json"
FILE_NAME = "samples.json"
SAVE_FREQUENCY = 10 # how many packages will be analyzed before saving the results
UNTIL = "2025-12-31"

def get_checkpoint(json: dict) -> int:
    """
    Restore the index of the last analyzed package in order to have a checkpoint mechanism

    :json: dictionary containing the statistics gathered so far
    :return: index of the last package that has been analyzed
    """
    return len(json.keys())

if __name__ == "__main__":
    package_history:dict = {}

    # check if we sampled packages to analyze
    if not os.path.exists(f"{HISTORY_OUTPUT_DIR}/packages/rnd_{NUM_PACKAGES}_pkgs.json"):
        with open(PACKAGE_LIST_PATH, "r") as f:
            pkgs_list = random.sample(json.load(f), NUM_PACKAGES)
        json.dump(pkgs_list, open(f"{HISTORY_OUTPUT_DIR}/packages/rnd_{NUM_PACKAGES}_pkgs.json", "w"))
    else:
        pkgs_list = json.load(open(f"{HISTORY_OUTPUT_DIR}/packages/rnd_{NUM_PACKAGES}_pkgs.json", "r"))

    if os.path.exists(f"{HISTORY_OUTPUT_DIR}/{FILE_NAME}"):
        package_history = json.load(open(f"{HISTORY_OUTPUT_DIR}/{FILE_NAME}"))
        start_idx = get_checkpoint(package_history)

    pkg_count = len(package_history.keys())

    for pkg_name in tqdm(pkgs_list[pkg_count:]):
        package_history[pkg_name] = {}

        try:
            package_history[pkg_name] = PackageShadowingHistory(pkg_name, "../classes/heuristics").get_package_history(UNTIL)

            if pkg_count % SAVE_FREQUENCY == 0:
                json.dump(package_history, open(f"{HISTORY_OUTPUT_DIR}/{FILE_NAME}", "w"), indent=4)
        except ValueError as e:
            # handle the case in which the script isn't able to retrieve the repository's URL and so cloning
            print(e)

            json.dump(package_history, open(f"{HISTORY_OUTPUT_DIR}/{FILE_NAME}", "w"), indent=4)
            continue

    json.dump(package_history, open(f"{HISTORY_OUTPUT_DIR}/{FILE_NAME}", "w"), indent=4)