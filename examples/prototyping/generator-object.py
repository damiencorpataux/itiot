class Average(object):
    def __init__(self, g, size=10, values=[]):
        self.g = g
        self.size = size
        self.values = values

    def __iter__(self):
        return self.generator()

    def generator(self):
        for value in self.g:
            self.values = [value] + self.values[:self.size-1]  # prepend value and trim to first n elements
            print(len(self.values), self.values)
            if len(self.values) >= self.size:
                yield sum(self.values) / len(self.values)

class Changed(object):
    def __init__(self, g, last=None):
        self.g = g
        self.last = last

    def __iter__(self):
        return self.generator()

    def generator(self):
        for value in self.g:
            if value != self.last:
                self.last = value
                yield value

for i in Changed(g=[1,1,2,2,3,3]):
    print(i)
