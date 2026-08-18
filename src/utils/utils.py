import requests

from functools import lru_cache

from packaging.version import InvalidVersion, Version

PYPI_API: str = "https://pypi.org/pypi/<package-name>/json"
REQUEST_TIMEOUT_SECONDS: int = 20

def get_pypi_releases(pkg: str) -> dict:
    """
    Retrieve all PyPI releases for a package.

    Results are cached so the same package is not downloaded repeatedly.
    """
    url = PYPI_API.replace("<package-name>", pkg)

    try:
        response = requests.get(url)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as e:
        print(f"PyPI request error for {pkg}: {e}")
        return {}
    except ValueError as e:
        print(f"Invalid JSON from PyPI for {pkg}: {e}")
        return {}

    releases = payload.get("releases", {})

    if not isinstance(releases, dict):
        return {}

    return releases


def get_version(year: int, pkg: str) -> str | None:
    """
    Get the latest package version released in or before a given year.

    :year: year of interest
    :pkg: package name
    :return: version of the package for the given year, or None if no valid release exists
    """
    releases = get_pypi_releases(pkg)

    if not releases:
        return None

    best_version: str | None = None

    for version, release_files in releases.items():
        if not release_files:
            continue

        try:
            parsed_version = Version(version)
        except InvalidVersion:
            continue

        upload_years = []

        for release_file in release_files:
            upload_time = release_file.get("upload_time")
            if not upload_time:
                continue

            try:
                upload_years.append(int(upload_time[:4]))
            except ValueError:
                continue

        if not upload_years:
            continue

        first_upload_year = min(upload_years)

        if first_upload_year > year:
            continue

        if best_version is None or parsed_version > Version(best_version):
            best_version = version

    return best_version