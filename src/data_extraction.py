import pathlib
import shutil
import json
import os
import pandas as pd
import sys
import requests
import re
import subprocess

from tqdm import tqdm

from classes.detector import Detector

from utils.utils import get_version

TEMP_DIR = "./tmp" # path to the temporary directory where the packages will be downloaded
PKGS_DATA_DIR = "../data/top packages"  # path to the directory containing the top n packages names for each year
RESULT_PATH_DIR = "../data/results"
SAVE_FREQUENCY = 10 # how many packages will be analyzed before saving the results
PYPI_API: str = "https://pypi.org/pypi/<package-name>/json"
HEURISTICS_DIR: str = "./classes/heuristics"

sys.setrecursionlimit(3000) # increase recursion limit (NOTE: change with caution)

def get_checkpoint(json: dict) -> int:
    """
    Restore the index of the last analyzed package in order to have a checkpoint mechanism

    :json: dictionary containing the statistics gathered so far
    :return: index of the last package that has been analyzed
    """
    return len(json.keys())

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
                try:
                    local_import = []
                    inner_function = []
                    total_scopes = 0
                    download_path = os.path.join(TEMP_DIR, pkg_name)
                    version = get_version(year, pkg_name)

                    # downloading package (we use <= just in case the version, for some reason, is not available)
                    #os.system(f"pip3 install -t {download_path} -q --no-deps --no-cache-dir '{pkg_name}<={version}'")
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install",
                         "-t", download_path,
                         "-q",
                         "--no-deps",
                         "--no-cache-dir",
                         f"{pkg_name}<={version}"],
                        check=False  # don't raise on failure, your existing try/except handles it
                    )

                    for py_file in pathlib.Path(download_path).glob("**/*.py"): # takes only python files in all possible directories
                        try:
                            detector = Detector(f"{py_file}", heuristic_path=HEURISTICS_DIR)
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
                    statistics[pkg_name] = "unavailable"
                    continue
        except Exception as e:
            json.dump(statistics, open(f"{RESULT_PATH_DIR}/{json_file}", "w"), indent=4)
        finally:
            json.dump(statistics, open(f"{RESULT_PATH_DIR}/{json_file}", "w"), indent=4)