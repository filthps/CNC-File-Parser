"""
Данный модуль содержит класс QThreadInstance, который нужно применять как декоратор к методам класса в UI,
в которах происходит взаимодействие как с UI, так и с внешними интерфейсами инфрастуктуры приложения.
"""
import dill
from typing import Callable, Any, Optional
from PySide2.QtCore import QObject, Signal, QThreadPool, QRunnable


class TaskConnection(QObject):
    data_transmission_signal = Signal(tuple)
    empty_signal = Signal(None)


class Task(QRunnable):

    def __init__(self, func: Callable, *args, **kwargs):
        super().__init__()
        self.connection = TaskConnection()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        result: Any = self.func(*self.args, **self.kwargs)
        if result is None:
            self.connection.empty_signal.emit()
            return
        if not isinstance(result, tuple):
            result = (result,)
        try:
            tuple_ = dill.dumps(result, dill.HIGHEST_PROTOCOL)
        except dill.PicklingError as err:
            print("Не удалось вернуть данные главному потоку!")
        self.connection.data_transmission_signal.emit(tuple_)


class QThreadInstanceDecorator:
    threadpool = QThreadPool()
    threadpool.setMaxThreadCount(32)
    threadpool.setExpiryTimeout(5000)

    def __init__(self, result_callback: Optional[Callable] = None, in_new_qthread: bool = True):
        if result_callback is not None:
            if not callable(result_callback):
                raise TypeError
        if not isinstance(in_new_qthread, bool):
            raise TypeError
        self.task = None
        self.end_f = result_callback
        self.create_new_task = in_new_qthread

    def __call__(self, call_f):
        def outer(*a, create_thread: bool = True, **k):
            if type(create_thread) is not bool:
                raise TypeError
            self.create_new_task = create_thread if create_thread is not None else self.create_new_task
            if self.create_new_task:
                self.task = Task(call_f, *a, **k)
                if self.end_f is not None:
                    def callback(serialized_data):
                        deserialized = dill.loads(serialized_data)
                        if not deserialized:
                            self.end_f()
                        if isinstance(deserialized, tuple):
                            self.end_f(*deserialized)
                            return
                        self.end_f(deserialized)
                    self.task.connection.data_transmission_signal.connect(lambda stringify_data: callback(stringify_data))
                    self.task.connection.empty_signal.connect(self.end_f)
                self.threadpool.start(self.task)
                return
            result = call_f(*a, **k)
            if result is None:
                if self.end_f:
                    return self.end_f()
            if type(result) is tuple:
                self.end_f(*result)
                return
            if self.end_f:
                self.end_f(result)
        return outer
