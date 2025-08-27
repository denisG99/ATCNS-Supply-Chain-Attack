import pathlib
import shutil
import json
import os

import pandas as pd

from detector import Detector

if __name__ == "__main__":
    pkgs_path = "../top10000_pkgs_names.json"
    temp_dir_path = "./tmp"
    #fields = ["id", "name", "repository_url"]

    if not os.path.exists(pkgs_path):
        print("Files containing packages doesn't exists!")

    df_pkgs = pd.read_json(pkgs_path)[0]

    statistics = {} # dictionary to store the gathered statistics for each package under analysis in the top 100
    local_import = []
    inner_function = []

    for pkg_name in df_pkgs:
        local_import = []
        inner_function = []
        total_scopes = 0
        download_path = os.path.join(temp_dir_path, pkg_name)

        # downloading package
        os.system(f"pip install -t {download_path} --no-deps --no-cache-dir {pkg_name}")

        print(f"Analyzing {pkg_name}...")
        for py_file in pathlib.Path(download_path).glob("**/*.py"): # takes only python files in all possible directories
            detector = Detector(f"{py_file}")

            if detector.get_builder() is not None:
                local_import = detector.local_import_detection()
                inner_function, scopes_number = detector.inner_function_detection()
                scope_chain_length = detector.get_builder().length_longest_scope_chain()
                total_scopes += scopes_number

        statistics[pkg_name] = {"local_import": local_import,
                                "inner_function": inner_function,
                                "number_of_scopes": total_scopes,
                                "scope_chain_length": scope_chain_length}
        print(f"Analysis complete")

        # removing temp directory, even if isn't empty
        shutil.rmtree(download_path, ignore_errors=True)

        print("\n", end="")

    json.dump(statistics, open("statistics.json", "w"), indent=4)