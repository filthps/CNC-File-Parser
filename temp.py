import tempfile
from abstractions import AbstractTemp


class Temp(AbstractTemp):

    def __int__(self):
        self.__temp = tempfile.TemporaryFile(mode="w+t")

    def write(self, line):
        if line.endswith("\n"):
            self.__temp.write(line)
        self.__temp.write(f"{line}\n")

    def clone(self):
        self.__temp.seek(0)
        val = self.__temp.read()
        self.close()
        return val

    def close(self):
        self.__temp.close()
