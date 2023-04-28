"""
Данный модуль содержит класс QThreadInstance, который нужно применять как декоратор к методам класса в UI,
в которах происходит взаимодействие как с UI, так и с внешними интерфейсами инфрастуктуры приложения.
"""
from typing import Callable, Any, Optional
import dill
from PySide2.QtCore import QObject, Signal, QThreadPool, QRunnable


class TaskConnection(QObject):
    callback_signal = Signal(tuple)


class Task(QRunnable):

    def __init__(self, func: Callable, *args, **kwargs):
        super().__init__()
        self.connection = TaskConnection()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        result: Any = self.func(*self.args, **self.kwargs)
        if type(result) is not tuple:
            tuple_ = (result,)
        try:
            tuple_ = dill.dumps(result)
        except dill.PicklingError as err:
            print("Не удалось вернуть данные главному потоку!")
            tuple_ = (None,)
        self.connection.callback_signal.emit(tuple_)


class QThreadInstanceDecorator:
    threadpool = QThreadPool()

    def __init__(self, result_callback=None, in_new_qthread=True):
        self.task = None
        self.end_f = result_callback
        self.create_new_task = in_new_qthread

    def __call__(self, call_f):
        def outer(*a, **k):
            self.create_new_task = k.pop("create_thread", self.create_new_task)
            if self.create_new_task:
                self.task = Task(call_f, *a, **k)
                if self.end_f is not None:
                    def callback(serialized_data: Optional[tuple]):
                        deserialized = dill.loads(serialized_data)
                        if deserialized is None:
                            self.end_f()
                            return
                        self.end_f(*deserialized)
                    self.task.connection.callback_signal.connect(lambda x: callback(x))
                self.threadpool.globalInstance().start(self.task)
                return
            result = call_f(*a, **k)
            self.end_f(result)
        return outer
