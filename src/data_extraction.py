import pathlib
import shutil
import json
import os
import pandas as pd
import sys
import requests
import re

from detector import Detector
from tqdm import tqdm

# constants
TEMP_DIR = "./tmp" # path to the temporary directory where the packages will be downloaded
PKGS_DATA_DIR = "../data/top packages"  # path to the directory containing the top n packages names for each year
RESULT_PATH_DIR = "../data/results"
SAVE_FREQUENCY = 10 # how many packages will be analyzed before saving the results
PYPI_API: str = "https://pypi.org/pypi/<package-name>/json"

sys.setrecursionlimit(3000) # increase recursion limit (NOTE: change with caution)

def get_checkpoint(json: dict) -> int:
    """
    Restore the index of the last analyzed package in order to have a checkpoint mechanism

    :json: dictionary containing the statistics gathered so far
    :return: index of the last package that has been analyzed
    """
    return len(json.keys())

def is_later_version(v1: str, v2: str) -> int:
    """
    :v1: first version to compare
    :v2: second version to compare
    :return: 1 if v1 is later than v2, -1 if v2 is later than v1, 0 if they are equal
    """
    # This will split both the versions by '.'
    arr1 = v1.split(".")
    arr2 = v2.split(".")
    n = len(arr1)
    m = len(arr2)

    # converts to integer from string
    arr1 = [int(i) for i in arr1]
    arr2 = [int(i) for i in arr2]

    # compares which list is bigger and fills
    # smaller list with zero (for unequal delimiters)
    if n > m:
        for i in range(m, n):
            arr2.append(0)
    elif m > n:
        for i in range(n, m):
            arr1.append(0)

    # returns 1 if version 1 is bigger and -1 if
    # version 2 is bigger and 0 if equal
    for i in range(len(arr1)):
        if arr1[i] > arr2[i]:
            return 1
        elif arr2[i] > arr1[i]:
            return -1
    return 0

def get_version(year: int, pkg: str) -> str:
    """
    Get the last version of a given year for a package

    :year: year of interest
    :pkg: package name
    :return: version of the package for the given year
    """
    # retrive info about all package's releases for a specific package
    releases: dict = requests.get(PYPI_API.replace("<package-name>", pkg)).json()["releases"]
    last_version: str = "0.0.0"

    for version in releases.keys():
        try:
            if bool(re.fullmatch(r"^\d+(?:\.\d+)*$", version)) and releases[version][0]["upload_time"].startswith(str(year)) and is_later_version(version, last_version) == 1:
                last_version = version
        except (IndexError, KeyError):
            pass

    if not last_version == "0.0.0":
        return last_version
    else:
        return get_version(year - 1, pkg)

if __name__ == "__main__":
    for json_file in os.listdir(PKGS_DATA_DIR):
        statistics = {}# dictionary to store the gathered statistics for each package under analysis
        start_idx = 0
        analyzed_pkgs_count = 0
        year = int(json_file.split("_")[-1][: -5])

        if os.path.exists(f"{RESULT_PATH_DIR}/{json_file}"):
            statistics = json.load(open(f"{RESULT_PATH_DIR}/{json_file}"))
            start_idx = get_checkpoint(statistics)
            analyzed_pkgs_count = start_idx

        df_pkgs = pd.read_json(f"{PKGS_DATA_DIR}/{json_file}")[0][start_idx:]

        try:
            for pkg_name in tqdm(df_pkgs, desc=f"Packages analysis({json_file})"):
                local_import = []
                inner_function = []
                total_scopes = 0
                download_path = os.path.join(TEMP_DIR, pkg_name)
                version = get_version(year, pkg_name)

                # downloading package (we use <= just in case the version, for some reason, is not available)
                os.system(f"pip3 install -t {download_path} -q --upgrade --no-deps --no-cache-dir '{pkg_name}<={version}'")

                for py_file in pathlib.Path(download_path).glob("**/*.py"): # takes only python files in all possible directories
                    try:
                        detector = Detector(f"{py_file}")
                        shadowing, yara = detector.shadowing_detection()

                        yara_rule_names = [rule.rule for rule in yara] # list contains the names of the yara rules

                        if detector.get_builder() is not None:
                            # features extraction
                            local_import = detector.local_import_detection()
                            inner_function, scopes_number = detector.inner_function_detection()
                            scope_chain_length = detector.get_builder().length_longest_scope_chain()
                            total_scopes += scopes_number
                    except Exception as e:
                        print(f"Error processing file {py_file}: {e}")
                        continue

                statistics[pkg_name] = {"local_import": local_import,
                                        "inner_function": inner_function,
                                        "number_of_scopes": total_scopes,
                                        "scope_chain_length": scope_chain_length,
                                        "shadowing": "true" if len(shadowing) > 0 or len(yara) > 0 else "false",
                                        "patch_decorator_import": "true" if "patch_decorator_import" in yara_rule_names else "false",
                                        "patch_decorator_usage": "true" if "patch_decorator_usage" in yara_rule_names else "false",
                                        "contextmanager_import": "true" if "contextmanager_import" in yara_rule_names else "false",
                                        "contextmanager_usage": "true" if "contextmanager_usage" in yara_rule_names else "false",
                                        "with_statement": "true" if "with_statement" in yara_rule_names else "false",
                                        "overwrite_method_class": "true" if "overwrite_method_class" in yara_rule_names else "false"}

                analyzed_pkgs_count += 1

                if analyzed_pkgs_count % SAVE_FREQUENCY == 0:
                    json.dump(statistics, open(f"{RESULT_PATH_DIR}/{json_file}", "w"), indent=4)

                # removing temp directory, even if isn't empty
                shutil.rmtree(download_path, ignore_errors=True)
        except Exception as e:
            print(f"Error processing {pkg_name}: {e}")
            json.dump(statistics, open(f"{RESULT_PATH_DIR}/{json_file}", "w"), indent=4)
        finally:
            json.dump(statistics, open(f"{RESULT_PATH_DIR}/{json_file}", "w"), indent=4)