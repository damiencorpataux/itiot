"""
State Tailor.

Possible names: tailor, alter, transform, marshal, interface, through
"""

import itiot

class Taylor(itiot.Wheel):
    """
    Abstract.
    I/O state processing unit.
    """
    # FIXME: how do I connect the pipes... look at the examples/tutorial.py
    def iterate(self, iterator):
        """
        Process states yielded from `iterator`.
        """
        for state in iterator: # FIXME: output the processed state
            processed = self.process(state, state['value'])  # helper and unification enforcement
            if processed:
                yield self.state

    def process(self, state, value):
        """
        Process `state` and update `self.state`.
        """
        self.state = state  # neutral taylor

    def states(self):
        """
        Return a generator that yield `self.state`.
        """
        while True:
            yield self.state

# class timer(Taylor):
#     """
#     Iterate with a `machine.Timer`.
#     """
#     def __init__(self, level='info', **kwargs):
#         super().__init__(period=period, **kwargs)
#
#     def process(self, state, value):
#         self.state = state
#         return True

class log(Taylor):
    """
    Log workflow information.
    """
    def __init__(self, level='info', **kwargs):
        super().__init__(level=level, **kwargs)

    def process(self, state, value):
        self.state = state
        return True

class function(Taylor):
    """
    Arbitrary function.
    """
    def __init__(self, f=lambda taylor, state, value: state, **kwargs):
        super().__init__(f=f, **kwargs)

    def process(self, state, value):
        self.state = self.o('f')(self, state, value)  # neutral default function
        return True

class average(Taylor):
    """
    Average of the last `n` values.
    """
    def __init__(self, n=10, **kwargs):
        super().__init__(n=n, **kwargs)
        self.history = []  # FIXME: move to self.state['history']

    def process(self, state, value):  # NOTE: we can avoid having a `values` history
        self.history = [value] + self.history[:self.o('n')-1]  # lifo queue of size n
        if len(self.history) >= self.o('n'):
            self.state = sum(self.history) / len(self.history)
            return True
