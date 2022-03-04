import json
import re
import importlib
from traceback import print_exc
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from decorators import *
from config import INPUT_PATH_ROOT, MACHINES_INPUT_PATH


@init_path_tree
def main():
    def sort_data(data):
        while True:
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
    #with ThreadPoolExecutor(max_workers=THREADS) as executor:
    while True:
        try:
            data = next(cleaned_data)
        except StopIteration:
            break
        else:
            machine_name = tuple(data.keys())[0]
            module_name = machine_name.capitalize()
            try:
                module = importlib.import_module(module_name)
            except ImportError:
                msg = f"Нет файла {module_name}! Отмена {len(data)} операций, связанных с ним."
                raise ImportError(msg)
            else:
                cls = getattr(module, module_name, None)
                if cls is None:
                    raise ImportError(f"В модуле {module_name} отсутствует класс {module_name}!"
                                      f"Отмена {len(data)} операций, связанных с ним.")
                func = getattr(cls, "start", None)
                if func is None:
                    raise ImportError(f"В модуле {module_name}, в классе {module_name} отсутствует функция 'start'!"
                                      f"Отмена {len(data)} операций, связанных с ним.")
                #executor.submit(func, data[machine_name])
                func(data[machine_name])


def scan_folders():
    def search_valid_folders(reg: re.match, path: str) -> re.match:
        return reg.match(path)
    sep = os.path.sep * 2
    regexp = re.compile(r"(?P<path>[A-Z]:" + sep + "(?:[^\*\.\"\/\\[\]:;\|,]+" + sep + ")*(?P<machine>" +
                        "|".join(MACHINES_INPUT_PATH.keys()) +
                        ")" + sep + "(?:[^\*\.\"\/\\[\]:;\|,]+" + sep +
                        ")*)(?P<name>[A-Z]?\d{2,5}\b?(?:\w+\b?\d{2,3})?)(?P<frmt>\.[a-z]+)?$")
    available_folders = Path(INPUT_PATH_ROOT).glob("**/*")
    folders = filter(lambda x: x, map(lambda p: search_valid_folders(regexp, str(p)), available_folders))
    #print(json.dumps(list(map(lambda x: x.group(), folders)), indent=4, ensure_ascii=False))
    return folders


if __name__ == "__main__":
    main()
