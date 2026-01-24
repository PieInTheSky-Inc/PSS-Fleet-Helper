from typing import Iterable as _Iterable

# ---------- Functions ----------


def compare_versions(version_1: str, version_2: str) -> int:
    """Compares two version strings with format x.x.x.x

    Returns:
    -1, if version_1 is higher than version_2
    0, if version_1 is equal to version_2
    1, if version_1 is lower than version_2"""
    if not version_1:
        return 1
    version_1 = version_1.strip("v")
    version_2 = version_2.strip("v")
    version_1_split = version_1.split(".")
    version_2_split = version_2.split(".")
    for i in range(0, len(version_1_split)):
        if version_1_split[i] < version_2_split[i]:
            return 1
        elif version_1_split[i] > version_2_split[i]:
            return -1
    return 0


def intersparse(iterable: _Iterable, delimiter: object):
    it = iter(iterable)
    yield next(it)
    for x in it:
        yield delimiter
        yield x
