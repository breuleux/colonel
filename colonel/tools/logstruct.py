

def noop(*x, **y):
    pass


def same(x, y):
    if hasattr(x, 'same'):
        return x.same(y)
    else:
        return x == y


class Logged:

    def __init__(self):
        self.__logger__ = noop

    def log(self, *data):
        self.__logger__(self, *data)

    def log_with(self, logger = noop):
        if logger == self.__logger__:
            return False
        self.__logger__ = logger
        return True


class LL(Logged):
    # stands for logged list

    def __init__(self, elements = []):
        self.__logger__ = noop
        self.__elems__ = []
        self.__committer__ = noop
        for element in elements:
            self.append(element)

    def log_ll(self, start, end, elements, commit):
        for child in elements:
            if hasattr(child, 'log_with'):
                child.log_with(self.__logger__)
        return self.log('ll', start, end, elements, commit)

    def log_with(self, logger = noop):
        if super().log_with(logger):
            for child in self[:]:
                if hasattr(child, 'log_with'):
                    child.log_with(logger)

    def __getitem__(self, item):
        return self.__elems__[item]

    def __setitem__(self, item, value):
        done = []
        def commit():
            if not done:
                self.__elems__[item] = value
                done.append(True)
        if isinstance(item, slice):
            assert not item.step
            start = item.start or 0
            stop = item.stop or len(self)
            value = list(value)
            self.log_ll(start, stop, value, commit)
        else:
            self.log_ll(item, item + 1, [value], commit)
        commit()

    def __delitem__(self, item):
        done = []
        def commit():
            if not done:
                del self.__elems__[item]
                done.append(True)
        if isinstance(item, slice):
            assert not item.step
            value = list(value)
            self.log_ll(item.start, item.stop, [], commit)
        else:
            self.log_ll(item, item + 1, [], commit)
        commit()

    def append(self, element):
        elms = self.__elems__
        self[len(elms):] = [element]

    def extend(self, elements):
        elms = self.__elems__
        self[len(elms):] = elements

    def __iadd__(self, elements):
        self.extend(elements)
        return self

    def insert(self, n, value):
        self[n:n] = [value]

    def index(self, value):
        return self.__elems__.index(value)

    def remove(self, value):
        idx = self.index(value)
        self[idx:idx+1] = []

    def pop(self, n = -1):
        val = self[n]
        self[n:n+1] = []
        return val

    def same(self, other):
        return (type(self) == type(other)
                and len(self.__elems__) == len(other.__elems__)
                and all(same(x, y)
                        for x, y in zip(self.__elems__,
                                        other.__elems__)))

    def __len__(self):
        return len(self.__elems__)


class LAD(Logged):
    # stands for logged attribute dictionary

    def __init__(self, attributes = {}, **extra):
        self.__logger__ = noop
        self.__props__ = {}
        self.__committer__ = noop
        for x, y in attributes.items():
            self[x] = y
        for x, y in extra.items():
            self[x] = y

    def log_with(self, logger = noop):
        if super().log_with(logger):
            for name, child in self.items():
                if hasattr(child, 'log_with'):
                    child.log_with(logger)

    def log_lad(self, item, value, old_value, commit):
        if hasattr(value, 'log_with'):
            value.log_with(self.__logger__)
        return self.log('lad', item, value, old_value, commit)


    # Dict behavior
    def __getitem__(self, item):
        if item.endswith("_"):
            item = item[:-1]
        item = item.replace("_", "-")
        return self.__props__[item]

    def __setitem__(self, item, value):
        def commit():
            self.__props__[item] = value
        if item.endswith("_"):
            item = item[:-1]
        item = item.replace("_", "-")
        self.log_lad(item, value, self.__props__.get(item, None), commit)
        commit()

    def __delitem__(self, item):
        done = []
        def commit():
            if not done:
                del self.__props__[item]
                done.append(True)
        self.log_lad(item, None, self.__props__.get(item, None), commit)
        commit()

    def __getattr__(self, attr):
        if attr.startswith("__"):
            return getattr(super(), attr)
        try:
            return self[attr]
        except KeyError as e:
            raise AttributeError(e)

    def __setattr__(self, attr, value):
        if attr.startswith("__"):
            super().__setattr__(attr, value)
        else:
            self[attr] = value

    def __delattr__(self, attr):
        if attr.startswith("__"):
            super().__detattr__(attr)
        else:
            del self[attr]

    def items(self):
        return self.__props__.items()

    def __len__(self):
        return len(self.__props__)

    def same(self, other):
        return (type(self) == type(other)
                and self.__props__.keys() == other.__props__.keys()
                and all(same(v, other[k])
                        for k, v in self.items()))


class LADLL(LAD, LL):

    def __init__(self, attributes = {}, **extra):
        LAD.__init__(self, attributes, **extra)

    def log_with(self, logger = noop):
        super().log_with(logger)
        for child in self[:]:
            if hasattr(child, 'log_with'):
                child.log_with(logger)
        for name, child in self.items():
            if hasattr(child, 'log_with'):
                child.log_with(logger)

    def __getitem__(self, item):
        if isinstance(item, (int, slice)):
            return LL.__getitem__(self, item)
        else:
            return LAD.__getitem__(self, item)

    def __setitem__(self, item, value):
        if isinstance(item, (int, slice)):
            LL.__setitem__(self, item, value)
        else:
            LAD.__setitem__(self, item, value)

    def __delitem__(self, item):
        if isinstance(item, (int, slice)):
            LL.__delitem__(self, item)
        else:
            LAD.__delitem__(self, item)

    def __len__(self):
        return LL.__len__(self) + LAD.__len__(self)

    def same(self, other):
        return LL.same(self, other) and LAD.same(self, other)


