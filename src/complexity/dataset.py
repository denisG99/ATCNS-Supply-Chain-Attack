import os
import pathlib
import random
import re
import shutil
import subprocess
import sys
import json
import ast
import requests
import pandas as pd

from tqdm import tqdm

from radon.raw import analyze
from radon.complexity import cc_visit
from radon.visitors import Function, Class

from classes.scope_graphv2 import ScopeGraph

OUTPUT_DIR: str = "../../data/complexity"
TMP_ENV: str = "./tmp/" # CHANGE if you want to have different name for environment
PACKAGES_PATH: str = f"{TMP_ENV}/lib/python3.13/site-packages"
TOP_PKGS_PATH: str = "../../data/results"
#NUM_PKGS: int = 400 # for having 95% of confidence level with 5% of error
NUM_PKGS: int = 1 # for having 95% of confidence level with 5% of error
PYPI_API: str = "https://pypi.org/pypi/<package-name>/json"

def get_dependencies_infos(pkg_name: str, pkg_version: str) -> tuple[int, int]:
    # downloading wanted package
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install",
             "-t", PACKAGES_PATH,
             "-q",
             "--no-cache-dir",
             f"{pkg_name}<={pkg_version}"],
            check=False  # don't raise on failure, your existing try/except handles it
        )
    except subprocess.CalledProcessError as e:
        print(e)

        return -1, -1

    # dependencies tree summary
    try:
        deptree_summary = json.loads(subprocess.run(
            [
                "pipdeptree",
                 "--python", f"{TMP_ENV}bin/python3",
                 "--packages", pkg_name,
                 "--summary",
                 "-o", "json"],
            check=False,
            capture_output = True,
            text = True
        ).stdout)

        return deptree_summary["total_packages"], deptree_summary["max_depth"]
    except (subprocess.CalledProcessError, json.decoder.JSONDecodeError) as e:
        print(e)

        return -1, -1

def get_loc(code: str) -> int:
    return analyze(code).loc # TODO: valutare lloc (da effettive linee di codice contenti istruzioni) vs loc (number of line of code (istruzioni + commenti))

def get_cyclomatic_complexity(code: str) -> int:
    try:
        cc_results = cc_visit(code)
        code_cc_complexity = 0 # accumulator for cyclomatic complexity

        if len(cc_results) == 0:
            return -1

        for res in cc_results:
            if isinstance(res, Function):
                code_cc_complexity += res.complexity

            if isinstance(res, Class):
                code_cc_complexity += res.real_complexity

        return code_cc_complexity
    except SyntaxError as e:
        print(e)

        return -1

def get_max_scope_nesting(code: str) -> int:
    try:
        tree = ast.parse(code)

        # building scope graph
        scope_graph = ScopeGraph()
        scope_graph.visit(tree)

        return scope_graph.length_longest_scope_chain()
    except Exception as e:
        print(f"Error parsing the code: {e}")
        return -1

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
    # dataset structure
    data = {
        'package': [],
        'file': [],
        'year': [],
        'loc': [],
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
            sys.exit()

    for file in os.listdir(TOP_PKGS_PATH):
        res = json.load(open(f"{TOP_PKGS_PATH}/{file}"))

        pkgs_list = random.sample([key for key in res.keys() if not res[key] == "unavailable"], NUM_PKGS)
        year = int(file.split("_")[-1][: -5])

        del res

        for pkg in tqdm(pkgs_list, desc=f"Packages analysis({file})"):
            deps_num, deptree_depth = get_dependencies_infos(pkg, get_version(year, pkg))

            for py_file in pathlib.Path(f"{PACKAGES_PATH}/{pkg}").glob("**/*.py"):  # takes only python files in all possible directories
                data["package"].append(pkg)
                data["file"].append(f"./{'/'.join(str(py_file).split('/')[4:])}")
                data["year"].append(year)
                data["loc"].append(get_loc(open(py_file).read()))
                data["cyclomatic_complexity"].append(get_cyclomatic_complexity(open(py_file).read()))
                data["max_scope_nesting_level"].append(get_max_scope_nesting(open(py_file).read()))
                data["total_dependencies"].append(deps_num)
                data["max_dependencies_depth"].append(deptree_depth)

    # save dataset
    pd.DataFrame(data).to_csv(f"{OUTPUT_DIR}/complexity.csv", index=False)

    # deletion of temporary environment
    shutil.rmtree(TMP_ENV, ignore_errors=True)