import json
import os
import re
from traceback import print_exc
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from machine import Machine
from config import INPUT_PATH_ROOT
from decorators import *


@init_path_tree
def main():
    def sort_data(data):
        return {data.pop("machine"): dict(data.items())}

    def clean_dubikat(data_iterator):
        data = list(data_iterator)
        result = {}
        for item in data:
            key = tuple(item.keys())[0]
            value = item[key]
            store = result.get(key, None)
            if store is None:
                store = []
                result[key] = store
            store.append(value)
        for k in result:
            yield {k: result[k]}
    match_objects = scan_folders()
    match_group_dict = map(lambda x: x.groupdict(), match_objects)
    sorted_group = map(lambda s: sort_data(s), match_group_dict)
    cleaned_data = clean_dubikat(sorted_group)
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        while True:
            try:
                data = next(cleaned_data)
            except StopIteration:
                break
            else:
                machine_name = tuple(data.keys())[0]
                if f"{machine_name}.py" not in os.listdir():
                    raise ImportError(f"Нет файла {machine_name}")
                if machine_name not in Machine.CNC_FILE_TYPE.keys():
                    raise ImportError(f"Отсутствует модуль CNC_File для станка {machine_name}")
                #executor.submit(Machine.start, data, machine_name=machine_name)
                Machine.start(data.pop(machine_name), machine_name=machine_name)

def scan_folders():
    def search_valid_folders(reg: re.match, path: str) -> re.match:
        return reg.match(path)
    sep = os.path.sep * 2
    regexp = re.compile(r"(?P<path>[A-Z]:" + sep + "(?:[^\*\.\"\/\\[\]:;\|,]+" + sep + ")*(?P<machine>" +
                        "|".join(MACHINES_INPUT_PATH.keys()) +
                        ")" + sep + "(?:[^\*\.\"\/\\[\]:;\|,]+" + sep +
                        ")*)(?P<name>[A-Z]?\d{2,5}\D?(?:\w+(?:\b)?\d{2,3})?)(?P<frmt>\.[a-z]+)?$")
    available_folders = Path(INPUT_PATH_ROOT).glob("**/*")
    folders = filter(lambda x: x, map(lambda p: search_valid_folders(regexp, str(p)), available_folders))
    return folders


if __name__ == "__main__":
    main()
