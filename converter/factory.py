

class CNCFileFactory:
    FILE_TYPE = None

    @classmethod
    def create(cls, item):
        return cls.FILE_TYPE(**item)
