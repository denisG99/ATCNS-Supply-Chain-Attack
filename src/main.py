import os
import pathlib
import shutil

import git
import pandas as pd

if __name__ == "__main__":
    pkgs_path = "../top_100_python_packages.csv"
    temp_dir_path = "./tmp"

    df_pkgs = pd.read_csv(pkgs_path, index_col=0)

    for pkg_name, link in zip(df_pkgs["Package"], df_pkgs["GitHub Link"]):
        print(f"Downloading {pkg_name}...")

        git.Repo.clone_from(link, temp_dir_path)
        print("Download complete.")

        print(f"Analyzing {pkg_name}...")
        for py_file in pathlib.Path(temp_dir_path).glob("**/*.py"): # takes only python files in all possible directories
            #TODO: source code analysis to find shadowing occurrences
            ...
        print(f"Analysis complete")

        # removing temp directory, even if isn't empty
        shutil.rmtree(temp_dir_path, ignore_errors=True)

        print("\n", end="")