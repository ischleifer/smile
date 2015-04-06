import threading

class RegisteredContextClass(type):
    def __init__(cls, name, bases, dct):
        super(RegisteredContextClass).__init__(name, bases, dct)
        cls.__local = threading.local()
        cls.__local.stack = []

    @property
    def context(cls):
        try:
            return cls.__local.stack[-1]
        except IndexError:
            return None

    @staticmethod
    def push_context(obj):
        for cls in type(obj).mro():
            if isinstance(cls, RegisteredContextClass):
                cls.__local.stack.append(obj)

    @staticmethod
    def pop_context(obj):
        for cls in type(obj).mro():
            if isinstance(cls, RegisteredContextClass):
                del cls.__local.stack[-1]
    

class RegisteredContext(object):
    __metaclass__ = RegisteredContextClass

    def __enter__(self):
        RegisteredContextClass.push_context(self)
        return self

    def __exit__(self, type, value, traceback):
        RegisteredContextClass.pop_context(self)
