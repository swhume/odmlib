

class Descriptor:
    def __init__(self, name=None, required=False, element_class=None, valid_values=[], namespace="odm"):
        self.name = name
        self.required = required
        self.element_class = element_class
        self.valid_values = valid_values
        self.namespace = namespace

    def __get__(self, instance, cls):
        if instance is None:
            return self
        elif (self.name not in instance.__dict__) and (self.name != self.__dict__["name"]):
            raise ValueError(f"Missing attribute or element {self.name} in {cls.__name__}")
        else:
            if self.name not in instance.__dict__:
                if isinstance(self, list):
                    self.__set__(instance, [])
                else:
                    if self.element_class is None:
                        instance.__dict__[self.name] = self.element_class
                    else:
                        try:
                            instance.__dict__[self.name] = self.element_class()
                        except ValueError:
                            instance.__dict__[self.name] = None
            return instance.__dict__[self.name]

    def __set__(self, instance, value):
        instance.__dict__[self.name] = value

    def __delete__(self, instance):
        del instance.__dict__[self.name]
