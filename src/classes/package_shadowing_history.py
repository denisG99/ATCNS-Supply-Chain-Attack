import pathlib
import shutil
import requests
import subprocess
import re

from classes.file_shadowing_history import FileShadowingHistoty

PYPI_API: str = "https://pypi.org/pypi/<package-name>/json"
TEMP_PATH: str = "./tmp"

class PackageShadowingHistory:
    def __init__(self, pck_name: str, heuristic_path: str="./heuristics") -> None:
        self.__pck_name: str = pck_name
        self.__heuristic_path: str = heuristic_path

        download_path = f"{TEMP_PATH}/{self.__pck_name}"
        try:
            subprocess.run(["git", "clone", self.__get_repo_url(), download_path], check=True)
        except AttributeError:
            # handle the case in which PyPI API doesn't the owner or the package isn't published on PyPI
            repo_url = input("Enter the repository url: ")

            subprocess.run(["git", "clone", repo_url, download_path], check=True)

    def __get_owner(self) -> str | None:
        """
        Return the owner of the package

        :param pkg_name: name of the package that we want to get the owner
        :return: owner of the package
        """
        pypi_info = requests.get(PYPI_API.replace("<package-name>", self.__pck_name)).json()

        for source in ["source", "homepage"]:
            if source in pypi_info["info"]["project_urls"].keys() and re.match(r"^https://github.com/", pypi_info["info"]["project_urls"][source]):
                return pypi_info["info"]["project_urls"][source].split("/")[-2]

    def __get_repo_url(self) -> str:
        """
        Get the repository url associated to a package

        :param pkg_name: name of the package that we want to get the repository url
        :return: repository url associated to the package
        """
        owner = self.__get_owner()

        return f"https://github.com/{owner}/{self.__pck_name}.git"

    def __get_gitlog(self, filename: str, until: str) -> str:
        filename: list[str] = filename.split("/")

        git_log = subprocess.run(
            [
                "git",
                "-C", '/'.join(filename[:-1]),
                "log",
                "--until", until,
                "-p", filename[-1]
            ],
            capture_output=True,
            text=True,
            check=True
        )

        return git_log.stdout

    def __file_history(self, filename: str, until: str) -> dict:
        self.__get_gitlog(filename, until)

        file_history = FileShadowingHistoty(self.__get_gitlog(filename, until), filename, self.__heuristic_path)
        file_history.build()

        return file_history.get_file_history()

    def get_package_history(self) -> dict:
        history = {
            "package": self.__pck_name,
            "files" : {}
        }

        for py_file in pathlib.Path().glob(f"./tmp/{self.__pck_name}/**/*.py"): # considers only python files in all possible directories
            key = f"./{'/'.join(str(py_file).split('/')[2:])}" # relative path of the file (wrt repository root)

            history["files"][key] = self.__file_history(str(py_file), "2025-12-31")

        shutil.rmtree(TEMP_PATH, ignore_errors=True)

        return history
