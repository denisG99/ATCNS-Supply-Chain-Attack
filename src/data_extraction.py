import pathlib
import shutil
import json
import os
import pandas as pd

from detector import Detector
from tqdm import tqdm

# constants
TEMP_DIR = "./tmp" # path to the temporary directory where the packages will be downloaded
PKGS_DATA = "../data/top50000_Dec2k25.json" # path to the json file containing the top n packages names
RESULT_PATH = "./res_test.json"
SAVE_FREQUENCY = 10 # how many packages will be analyzed before saving the results

def get_checkpoint(json: dict) -> int:
    """
    Restore the index of the last analyzed package in order to have a checkpoint mechanism

    :json: dictionary containing the statistics gathered so far
    :return: index of the last package that has been analyzed
    """
    return len(json.keys())

if __name__ == "__main__":
    if not os.path.exists(PKGS_DATA):
        print("Files containing packages doesn't exists!")

    statistics = {}# dictionary to store the gathered statistics for each package under analysis
    start_idx = 0
    analyzed_pkgs_count = 0

    if os.path.exists(RESULT_PATH):
        statistics = json.load(open(RESULT_PATH))
        start_idx = get_checkpoint(statistics)
        analyzed_pkgs_count = start_idx

    df_pkgs = pd.read_json(PKGS_DATA)[0][start_idx:]

    try:
        for pkg_name in tqdm(df_pkgs, desc=f"Packages analysis"):
            local_import = []
            inner_function = []
            total_scopes = 0
            download_path = os.path.join(TEMP_DIR, pkg_name)

            # downloading package
            os.system(f"pip3 install -t {download_path} -q --upgrade --no-deps --no-cache-dir {pkg_name}")

            #print(f"Analyzing {pkg_name}...")
            for py_file in pathlib.Path(download_path).glob("**/*.py"): # takes only python files in all possible directories
                detector = Detector(f"{py_file}")
                shadowing, yara = detector.shadowing_detection()

                yara_rule_names = [rule.rule for rule in yara] # list contains the names of the yara rules

                if detector.get_builder() is not None:
                    # features extraction
                    local_import = detector.local_import_detection()
                    inner_function, scopes_number = detector.inner_function_detection()
                    scope_chain_length = detector.get_builder().length_longest_scope_chain()
                    total_scopes += scopes_number

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

            #print(f"Analysis complete")

            analyzed_pkgs_count += 1

            if analyzed_pkgs_count % SAVE_FREQUENCY == 0:
                json.dump(statistics, open(RESULT_PATH, "w"), indent=4)

            # removing temp directory, even if isn't empty
            shutil.rmtree(download_path, ignore_errors=True)

    except Exception as e:
        json.dump(statistics, open(RESULT_PATH, "w"), indent=4)
    finally:
        json.dump(statistics, open(RESULT_PATH, "w"), indent=4)