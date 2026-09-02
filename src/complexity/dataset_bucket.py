import json
import os
import subprocess
import sys
import shutil
import pathlib
import pandas as pd
import tokenize

from tqdm import tqdm

from src.utils.utils import get_version

from utils.utils import get_dependencies_infos, get_lloc, get_cyclomatic_complexity, get_max_scope_nesting, remove_package

# CONSTANTS
NUM_CONSIDER_BUCKETS: int = 25
BUCKET_SIZE: int = 500
PACKAGE_RESULTS_PATH: str = "../../data/results/top50000_2025.json"
TMP_ENV: str = "./tmp/" # CHANGE if you want to have different name for environment
PACKAGES_PATH: str = f"{TMP_ENV}/lib/python3.13/site-packages"
OUTPUT_DIR: str = "../../data/complexity"

def get_buckets(data: dict) -> list[list]:
    return [list(data.keys())[i : i + BUCKET_SIZE] for i in range(0, len(data.keys()), BUCKET_SIZE)]

def default_entry(data: dict, pkg: str, id: int) -> dict:
    data["package"].append(pkg)
    data["file"].append(None)
    data["bucket_id"].append(id)
    data["lloc"].append(0)
    data["cyclomatic_complexity"].append(0)
    data["max_scope_nesting_level"].append(0)
    data["total_dependencies"].append(-1)
    data["max_dependencies_depth"].append(-1)

    return data

if __name__ == "__main__":
    packages_data: dict = json.load(open(PACKAGE_RESULTS_PATH, "r"))

    # dataset structure
    data = {
        'package': [],
        'file': [],
        'bucket_id': [],
        'lloc': [],
        'cyclomatic_complexity': [],
        'max_scope_nesting_level': [],
        'total_dependencies': [],
        'max_dependencies_depth': []
    }

    # create temporary environment if needed
    if not os.path.exists(TMP_ENV):
        try:
            subprocess.run(["python3", "-m", "venv", TMP_ENV], check=False)
        except subprocess.CalledProcessError as e:
            print(e)
            sys.exit()  # create temporary environment if needed

    for bucket_id, bucket in enumerate(get_buckets(packages_data)[: NUM_CONSIDER_BUCKETS]):
        for pkg in tqdm(bucket, desc=f"Bucket {bucket_id}"):
            version = get_version(2025, pkg) # here we have fixed year because we are interested only in 2025 results

            # download package
            try:
                # second download of the package in a directory with the same name of the package to cope with the case in which the package has different name inside the environment
                subprocess.run(
                    [sys.executable, "-m", "pip", "install",
                     "-t", f"{PACKAGES_PATH}/{pkg}",
                     "-q",
                     "--no-cache-dir",
                     "--no-deps",
                     "--upgrade",
                     "--disable-pip-version-check",
                     f"{pkg}<={version}"],
                    check=False  # don't rise on failure, your existing try/except handles it
                )
            except (subprocess.CalledProcessError, KeyError, Exception) as e:
                print(f"PIP error: {e}")

                data = default_entry(data, pkg, bucket_id)

                continue
            else:
                deps_num, deptree_depth = get_dependencies_infos(pkg, version, PACKAGES_PATH, TMP_ENV)

                # handles cases in which the package is not available, so pipdeptree fails to build the dependency tree
                if deps_num == -1 and deptree_depth == -1:
                    data = default_entry(data, pkg, bucket_id)

                    continue

                for py_file in pathlib.Path(f"{PACKAGES_PATH}/{pkg}").glob(
                        "**/*.py"):  # takes only python files in all possible directories
                    data["package"].append(pkg)
                    data["file"].append(f"./{'/'.join(str(py_file).split('/')[5:])}")
                    data["bucket_id"].append(bucket_id)
                    data["lloc"].append(get_lloc(tokenize.open(py_file).read()))
                    data["cyclomatic_complexity"].append(get_cyclomatic_complexity(tokenize.open(py_file).read()))
                    data["max_scope_nesting_level"].append(get_max_scope_nesting(tokenize.open(py_file).read()))
                    data["total_dependencies"].append(deps_num)
                    data["max_dependencies_depth"].append(deptree_depth)

                shutil.rmtree(f"{PACKAGES_PATH}/{pkg}", ignore_errors=True)
            finally:
                remove_package(pkg, TMP_ENV)

                # save dataset
            pd.DataFrame(data).to_csv(f"{OUTPUT_DIR}/bucket_complexity.csv", index=False)

            # deletion of temporary environment
            shutil.rmtree(TMP_ENV, ignore_errors=True)