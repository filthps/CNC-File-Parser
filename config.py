import os

THREADS = 3
PROJECT_PATH: str = os.getcwd()
INPUT_PATH_NAME: str = "files"
OUTPUT_PATH_NAME: str = "converted"
INPUT_PATH_ROOT: str = os.path.normpath(os.path.join(PROJECT_PATH, INPUT_PATH_NAME))
OUTPUT_PATH_ROOT: str = os.path.normpath(os.path.join(PROJECT_PATH, OUTPUT_PATH_NAME))
MACHINES_INPUT_PATH: dict = {"heller": os.path.normpath(os.path.join(INPUT_PATH_ROOT, "heller")),
                 "fidia": os.path.normpath(os.path.join(INPUT_PATH_ROOT, "fidia")),
                 "rambaudi": os.path.normpath(os.path.join(INPUT_PATH_ROOT, "rambaudi"))}
INVALID_SYMBOLS = "[=/:;]"  # Строки, содержащие один из символов внутри [], будут удалены
