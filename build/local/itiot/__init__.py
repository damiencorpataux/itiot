"""
Abstract stateful generator/iterator structure.

WARNING! Python Generators on Steroids ahead.
WARNING! Itergenerateous people out there.

It's all a `Wheel`, and we keep reinvent it.
Now let's iterate IoT, chain iterators and build data flows.
                                                                      - an itiot
"""

import ulogging

class Wheel(object):
    """
    Abstract.
    It's an iterator and also a generator, designed to bind things toghether
    and make them run.
    """
    state = {'value': None}  # state MUST have a 'value' key

    def __init__(self, _state={}, _debug=False, **options):
        self.log = ulogging.getLogger('.'.join((self.__module__, self.__class__.__name__)))
        self.options = dict({}, **options)  # FIXME: use deepcopy, but it fails on micropython
        self.state = dict(dict({}, **Wheel.state), **_state)
        self.debug = _debug

    def iterate(self, iterator):  # FIXME: rename to `subscribe`
        """
        Process `state` yielded from `iterator`.
        """
        # TODO: implement __iter__ etc.
        for state in iterator:
            self.commit(state)

    def commit(self, state):  # FIXME: this method could be called `process`
        """
        Process `state` and apply result to `state`.
        """
        raise NotImplementedError()

    def states(self):  # FIXME: rename to `publish`
        """
        Return a generator that yield processed `state`.
        """
        while True:
            yield self.state

    @property
    def o(self):
        """
        Shorthand for `self.options.get`. Example: `self.o('pin', 1)`.
        """
        return self.options.get

    @property
    def value(self):
        """
        Read-only.
        Shorthand for `self.state['value']`. Example: `self.value == 1`.
        """
        return self.state['value']

    def __str__(self):
        debug = ' '.join((
            ', '.join('%s=%s'%o for o in self.options.items()),
            str(self.state)))
        return ('<%s=%s%s>'%(self.__class__.__name__, self.value, ' '+debug if self.debug else ''))
