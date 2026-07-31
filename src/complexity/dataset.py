import os
import pathlib
import random
import shutil
import subprocess
import sys
import json
import ast
import pandas as pd
import tokenize # use it to respect PEP 263 encoding declaration and handle non-UTF-8 files robustly

from tqdm import tqdm

from radon.raw import analyze
from radon.complexity import cc_visit
from radon.visitors import Function, Class

from classes.scope_graphv2 import ScopeGraph

from utils.utils import get_version

OUTPUT_DIR: str = "../../data/complexity"
TMP_ENV: str = "./tmp/" # CHANGE if you want to have different name for environment
PACKAGES_PATH: str = f"{TMP_ENV}/lib/python3.13/site-packages"
TOP_PKGS_PATH: str = "../../data/results"
NUM_PKGS: int = 400 # for having 95% of confidence level with 5% of error

# NOTE: we need to download the package twice: when we want to analyze its dependencies and from the other case because there is some case where the package has different name inside the environment and the script doesn't find it

def get_dependencies_infos(pkg_name: str, version: int) -> tuple[int, int]:
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install",
             "-t", f"{PACKAGES_PATH}",
             "-q",
             "--no-cache-dir",
             "--upgrade",
             "--disable-pip-version-check",
             f"{pkg}<={version}"],
            check=False  # don't rise on failure, your existing try/except handles it
        )
    except (subprocess.CalledProcessError, KeyError, Exception) as e:
        print(f"PIP error: {e}")

        return -1, -1

    # dependency tree summary
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
        print(f"pipdeptree error: {e}")

        return -1, -1

def get_lloc(code: str) -> int:
    try:
        return analyze(code).lloc
    except Exception as e:
        print(f"LOC error: {e}")

        return 0

def get_cyclomatic_complexity(code: str) -> int:
    try:
        cc_results = cc_visit(code)
        code_cc_complexity = 0 # accumulator for cyclomatic complexity

        if len(cc_results) == 0:
            return 0

        for res in cc_results:
            if isinstance(res, Function):
                code_cc_complexity += res.complexity

            if isinstance(res, Class):
                code_cc_complexity += res.real_complexity

        return code_cc_complexity
    except SyntaxError as e:
        print(f"Cyclomatic complexity error: {e}")

        return 0

def get_max_scope_nesting(code: str) -> int:
    try:
        tree = ast.parse(code)

        # building scope graph
        scope_graph = ScopeGraph()
        scope_graph.visit(tree)

        return scope_graph.length_longest_scope_chain()
    except Exception as e:
        print(f"Error parsing the code: {e}")

        return 0

def default_entry(data: dict, pkg: str, year: int) -> dict:
    data["package"].append(pkg)
    data["file"].append(None)
    data["year"].append(year)
    data["lloc"].append(0)
    data["cyclomatic_complexity"].append(0)
    data["max_scope_nesting_level"].append(0)
    data["total_dependencies"].append(-1)
    data["max_dependencies_depth"].append(-1)

    return data


if __name__ == "__main__":
    # dataset structure
    data = {
        'package': [],
        'file': [],
        'year': [],
        'lloc': [],
        'cyclomatic_complexity': [],
        'max_scope_nesting_level': [],
        'total_dependencies': [],
        'max_dependencies_depth': []
    }

    for file in os.listdir(TOP_PKGS_PATH):
        # create temporary environment if needed
        if not os.path.exists(TMP_ENV):
            try:
                subprocess.run(["python3", "-m", "venv", TMP_ENV], check=False)
            except subprocess.CalledProcessError as e:
                print(e)
                sys.exit()# create temporary environment if needed

        res = json.load(open(f"{TOP_PKGS_PATH}/{file}"))

        pkgs_list = random.sample([key for key in res.keys() if not res[key] == "unavailable"], NUM_PKGS)
        year = int(file.split("_")[-1][: -5])

        del res

        for pkg in tqdm(pkgs_list, desc=f"Packages analysis({file})"):
            #print(f"Package: {pkg}")
            version = get_version(year, pkg)

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
                     f"{pkg}<={year}"],
                    check=False  # don't rise on failure, your existing try/except handles it
                )
            except (subprocess.CalledProcessError, KeyError, Exception) as e:
                print(f"PIP error: {e}")

                data = default_entry(data, pkg, year)

                continue
            else:
                deps_num, deptree_depth = get_dependencies_infos(pkg, year)

                # handles cases in which the package is not available, so pipdeptree fails to build the dependency tree
                if deps_num == -1 and deptree_depth == -1:
                    data = default_entry(data, pkg, year)

                    continue

                for py_file in pathlib.Path(f"{PACKAGES_PATH}/{pkg}").glob("**/*.py"):  # takes only python files in all possible directories
                    data["package"].append(pkg)
                    data["file"].append(f"./{'/'.join(str(py_file).split('/')[5:])}")
                    data["year"].append(year)
                    data["lloc"].append(get_lloc(tokenize.open(py_file).read()))
                    data["cyclomatic_complexity"].append(get_cyclomatic_complexity(tokenize.open(py_file).read()))
                    data["max_scope_nesting_level"].append(get_max_scope_nesting(tokenize.open(py_file).read()))
                    data["total_dependencies"].append(deps_num)
                    data["max_dependencies_depth"].append(deptree_depth)

                shutil.rmtree(f"{PACKAGES_PATH}/{pkg}", ignore_errors=True)

        # save dataset
        pd.DataFrame(data).to_csv(f"{OUTPUT_DIR}/complexity.csv", index=False)

        # deletion of temporary environment
        shutil.rmtree(TMP_ENV, ignore_errors=True)
