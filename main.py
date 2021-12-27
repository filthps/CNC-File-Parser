import re
import importlib
import json
from pathlib import Path
from traceback import print_exc
from typing import Iterator

from decorators import *

from config import INPUT_PATH_ROOT, MACHINES_INPUT_PATH


@init_path_tree
def main():
    def iter_data(items: Iterator) -> Iterator:
        """
        Вернуть новый словарь, отсоритрованный по формату:
            "machine": {все имеющиеся пути и имена файлов для станка - 'machine'}

        :param items: итератор словаря
        :return: генератор словаря
        """
        values_dict: dict[list] = {}
        while True:
            try:
                d = next(items)
            except StopIteration:
                return
            machine_name = d.pop("machine")
            machine_value = values_dict.get(machine_name, None)
            if machine_value is None:
                machine_value = []
                values_dict[machine_name] = machine_value
            machine_value.append("".join(d.values()))
            result = {"full": machine_value}
            result.update(d.items())
            yield {machine_name: result}

    match_objects = scan_folders()
    result_dicts = map(lambda x: x.groupdict(), match_objects)
    data_iterator = iter_data(result_dicts)
    for d in data_iterator:
        print(json.dumps(d, indent=4))
    while True:
        try:
            dct = next(data_iterator)
        except StopIteration:
            break
        machine_name, data = dct.keys(), dct.values()
        try:
            module = importlib.import_module(machine_name)
        except ImportError:
            print_exc("Проверь файлы-модули станков, какого-то не хватает")
            return
        func = getattr(module, "main", None)
        if func is None:
            raise SystemError(f"В модуле {machine_name} нету функции main")
        func(data["full"], filename = data["name"], file_format = data["frmt"])


def scan_folders() -> Iterator["re.match"]:
    def search_valid_folders(reg, path):
        return reg.match(str(path))
    sep = os.path.sep
    regexp = re.compile(r"(?P<path>[A-Z]:" + (sep * 2) + "(?:\w+" + (sep * 2) + ")*(?P<machine>" +
                        "|".join(MACHINES_INPUT_PATH.keys()) +
                        ")" + (sep * 2) + "(?:\w+" +
                        (sep * 2) +
                        ")*)(?P<name>[A-Z]?[0-9]{2,5})(?P<frmt>\.\w+)?")
    available_folders = Path(INPUT_PATH_ROOT).glob("**/*.txt")
    folders = map(lambda p: search_valid_folders(regexp, p), available_folders)
    return folders


if __name__ == "__main__":
    main()
