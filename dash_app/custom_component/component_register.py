COMPONENT_CLASS = {}

def component_register(cls):
    COMPONENT_CLASS[cls.__name__] = cls
    return cls