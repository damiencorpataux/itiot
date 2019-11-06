class Mock(object):
    static = {
    }
    def __getattr__(self, name):
        return Ubique()
    def __setattr__(self, name, value):
        return setattr(self, name, value)
    def __call__(self, *args, **kwargs):
        return Ubique()
    def __iter__(self):
        return self
    def __next__(self):
        return Ubique()
    def test(self):
        print('test')

machine = Mock()
