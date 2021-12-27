import os

PROJECT_PATH: str = os.getcwd()
INPUT_PATH_NAME: str = "files"
OUTPUT_PATH_NAME: str = "converted"
INPUT_PATH_ROOT: str = os.path.normpath(os.path.join(PROJECT_PATH, INPUT_PATH_NAME))
OUTPUT_PATH_ROOT: str = os.path.normpath(os.path.join(PROJECT_PATH, OUTPUT_PATH_NAME))
MACHINES_INPUT_PATH: dict = {"Heller": os.path.normpath(os.path.join(INPUT_PATH_ROOT, "Heller")),
                 "Fidia": os.path.normpath(os.path.join(INPUT_PATH_ROOT, "Fidia")),
                 "Rambaudi": os.path.normpath(os.path.join(INPUT_PATH_ROOT, "Rambaudi"))}
INVALID_SYMBOLS = "[=/:;]"  # Строки, содержащие один из символов внутри [], будут удалены
