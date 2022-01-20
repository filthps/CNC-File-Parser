import re
import math
import importlib
from typing import Iterator, Generator
from traceback import print_exc
from pathlib import Path
from threading import Thread

from decorators import *
from config import INPUT_PATH_ROOT, MACHINES_INPUT_PATH


@init_path_tree
def main():
    def launch_task(machine: str, task: list):
        try:
            module = importlib.import_module(machine)
        except ImportError:
            print_exc("Проверь файлы-модули станков, какого-то не хватает")
            return
        func = getattr(module, machine, None)
        if func is None:
            raise SystemError(f"В модуле {machine} нету функции {machine}")
        func(task)

    def sort_data(data):
        while True:
            return {data.pop("machine"): dict(data.items())}

    def clean_dubikat(data_iterator):
        data = list(data_iterator)
        result = {}
        stats = {}
        for item in data:
            key = tuple(item.keys())[0]
            value = item[key]
            store = result.get(key, None)
            if store is None:
                store = []
                result[key] = store
            store.append(value)
            task_size =  len(value)
            stats.update({key: task_size})
        for k in result:
            yield {k: result[k], "stats": stats}
    match_objects = scan_folders()
    match_group_dict = map(lambda x: x.groupdict(), match_objects)
    sorted_group = map(lambda s: sort_data(s), match_group_dict)
    cleaned_data = clean_dubikat(sorted_group)
    init_args = map(lambda task: sort_by_tasks(task), cleaned_data)
    init_threads = map(lambda y: Thread(target=launch_task, args=y), init_args)
    for thread in init_threads:
        thread.start()

def scan_folders():
    def search_valid_folders(reg: re.match, path: str) -> re.match:
        return reg.match(path)
    sep = os.path.sep
    regexp = re.compile(r"(?P<path>[A-Z]:" + (sep * 2) + "(?:\w+" + (sep * 2) + ")*(?P<machine>" +
                        "|".join(MACHINES_INPUT_PATH.keys()) +
                        ")" + (sep * 2) + "(?:\w+" +
                        (sep * 2) +
                        ")*)(?P<name>[A-Z]?[0-9]{2,5})(?P<frmt>\.\w+)?")
    available_folders = Path(INPUT_PATH_ROOT).glob("**/*.txt")
    folders = filter(lambda x: x, map(lambda p: search_valid_folders(regexp, str(p)), available_folders))
    return folders


@sort
@slice
def sort_by_tasks(task) -> tuple[list, int]:
    stats = task.pop("stats")
    return task, stats


if __name__ == "__main__":
    main()
