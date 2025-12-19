import pathlib
import shutil
import json
import os

import pandas as pd

from detector import Detector

# constants
TEMP_DIR = "./tmp" # path to the temporary directory where the packages will be downloaded
PKGS_DATA = "../data/test.json" # path to the json file containing the top n packages names
RESULT_PATH = "./res_test.json"

if __name__ == "__main__":
    if not os.path.exists(PKGS_DATA):
        print("Files containing packages doesn't exists!")

    df_pkgs = pd.read_json(PKGS_DATA)[0]

    statistics = {} # dictionary to store the gathered statistics for each package under analysis in the top 100
    #local_import = []
    #inner_function = []

    for pkg_name in df_pkgs:
        local_import = []
        inner_function = []
        total_scopes = 0
        download_path = os.path.join(TEMP_DIR, pkg_name)

        # downloading package
        os.system(f"pip3 install -t {download_path} -q --no-deps --no-cache-dir {pkg_name}")

        print(f"Analyzing {pkg_name}...")
        for py_file in pathlib.Path(download_path).glob("**/*.py"): # takes only python files in all possible directories
            detector = Detector(f"{py_file}")
            shadowing, yara = detector.shadowing_detection()

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
                                "shadowing": "true" if len(shadowing) > 0 else "false",
                                "patch_decorator_import": "true" if "patch_decorator_import" in yara else "false",
                                "patch_decorator_usage": "true" if "patch_decorator_usage" in yara else "false",
                                "contextmanager_import": "true" if "contextmanager_import" in yara else "false",
                                "contextmanager_usage": "true" if "contextmanager_usage" in yara else "false",
                                "with_statement": "true" if "with_statement" in yara else "false",
                                "overwrite_method_class": "true" if "overwrite_method_class" in yara else "false"}

        print(f"Analysis complete")

        # removing temp directory, even if isn't empty
        shutil.rmtree(download_path, ignore_errors=True)

        print("\n", end="")

    json.dump(statistics, open(RESULT_PATH, "w"), indent=4)