import os
import re

THREADS = 3
PROJECT_PATH: str = os.getcwd()
INPUT_PATH_NAME: str = "files"
OUTPUT_PATH_NAME: str = "converted"
HELLER: str = "heller"
FIDIA: str = "fidia"
RAMBAUDI: str = "rambaudi"
_65A90: str = "_65A90"
sep = os.path.sep
INPUT_PATH_ROOT: str = os.path.normpath(os.path.join(PROJECT_PATH, INPUT_PATH_NAME))
OUTPUT_PATH_ROOT: str = os.path.normpath(os.path.join(PROJECT_PATH, OUTPUT_PATH_NAME))
MACHINES_INPUT_PATH: dict = {
    HELLER: os.path.normpath(os.path.join(INPUT_PATH_ROOT, HELLER)),
    FIDIA: os.path.normpath(os.path.join(INPUT_PATH_ROOT, FIDIA)),
    RAMBAUDI: os.path.normpath(os.path.join(INPUT_PATH_ROOT, RAMBAUDI)),
    _65A90: os.path.normpath(os.path.join(INPUT_PATH_ROOT, _65A90))
}
MACHINES_OUTPUT_PATH: dict = {
    HELLER: os.path.normpath(os.path.join(OUTPUT_PATH_ROOT, HELLER)),
    FIDIA: os.path.normpath(os.path.join(OUTPUT_PATH_ROOT, FIDIA)),
    RAMBAUDI: os.path.normpath(os.path.join(OUTPUT_PATH_ROOT, RAMBAUDI)),
    _65A90: os.path.normpath(os.path.join(OUTPUT_PATH_ROOT, _65A90))
}
HEAD_TEMPLATES = {
        "65A90": re.compile(r";"
                            r"\(UAO,(?P<binding>[0-9])\)\n"
                            r"G27\n"
                            r".*NC NAME: (?P<name>[a-zA-Z0-9]+).*\n"
                            r".*Date - (?P<time>(?P<day>[0-9]{,2}) \.(?P<month>[0-9]{,2}) \.(?P<year>[0-9]{2}))"
                            r" -(?P<hour>[0-9]{2} \:(?P<minute>[0-9]{2}) \:(?P<second>[0-9]{2}))\n")
    }
LOG_PATH = os.path.join(PROJECT_PATH, "log.log")
TOOLS = {
    "TIPRADIUSED": {
        ("tor",): (12, 20, 30, 66, 80, 160)},
    "ENDMILL": {
        ("end",): (2, 3, 4, 5, 8, 10, 12, 16, 20)
    }
}

