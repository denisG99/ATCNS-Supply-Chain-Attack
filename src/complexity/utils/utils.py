import subprocess
import sys
import json
import ast

from radon.raw import analyze
from radon.complexity import cc_visit
from radon.visitors import Function, Class

from classes.scope_graphv2 import ScopeGraph

def get_dependencies_infos(pkg_name: str, version: int, packages_path: str, env_path: str) -> tuple[int, int]:
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install",
             "-t", f"{packages_path}",
             "-q",
             "--no-cache-dir",
             "--upgrade",
             "--disable-pip-version-check",
             f"{pkg_name}<={version}"],
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
                 "--python", f"{env_path}bin/python3",
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

def remove_package(pkg_name: str, env_path: str) -> None:
    # retrive all dependencies of a given package
    try:
        dependencies_tree = json.loads(subprocess.run(
            [
                "pipdeptree",
                "--python", f"{env_path}bin/python3",
                "--packages", pkg_name,
                "-o", "json"],
            check=False,
            capture_output=True,
            text=True
        ).stdout)

        to_remove = [pkg_name]

        for deps in dependencies_tree:
            if len(deps["dependencies"]) == 0:
                continue

            for dep in deps["dependencies"]:
                to_remove.append(dep["package_name"])

        subprocess.run(
            [
                f"pip",
                "--python", f"{env_path}bin/python3",
                "uninstall",
                "-y",
                "--no-cache-dir",
                *to_remove
            ],
            check=False,
            capture_output=True
        )
    except Exception as e:
        print(f"Error removing package {pkg_name}: {e}")