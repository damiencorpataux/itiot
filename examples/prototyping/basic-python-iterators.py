"""
Plain python examples of generator constructs,
a selection usable with micropython `machine` module.
The goal is to build pipes.
"""

import itertools
import time
import sys

def t(title):
    print("\n", title, "\n")

def source(generator=range(5), name='source'):
    # A simple wrapper around range(5), printing a line on each yield
    for i in generator:
        print('<- %s yielded %s' % (name, i))
        yield i

def section():
    t("1:1 pipe straight - modify and filter value: quick and dirty")
    g = source()
    for value in g:
        sys.stdout.write('Pipe 1:1 - Generator value -> %s' % value)
        value /= 10  # modify
        sys.stdout.write(' modify -> %s' % (value))
        if 0.2 <= value <= 0.3:  # filter
            sys.stdout.write(' filter -> %s' % (value))
        sys.stdout.write('\n')

    t("1:1 pipe straight - same as before, with a generators chain: simplest form")
    for _ in (print(value) for value in (value for value in (value/10 for value in source()) if 0.2 <= value <= 0.3)):
        pass

    t("1:1 pipe straight - same as before, with generator functions")
    modify = lambda g: (value / 10 for value in g)
    filter = lambda g: (value for value in g if 0.2 <= value <= 0.3)
    display = lambda g: (print(value) for value in g)
    pipe = lambda g: display(filter(modify(g)))
    g = source()
    for _ in pipe(g):
        pass
section()

def section():
    t("n:1 pipe roundrobin - roundrobin-join 2 generators")
    g1 = source(range(5), name='source1')
    g2 = source(range(10, 15), name='source2')
    generators = (g1, g2)
    try:
        while True:
            # micropython doesn't support: for value in itertools.chain.from_iterable(zip(*generators)):
            # because itertools.chain.from_iterable is not implemented
            for g in generators:
                value = next(g)
                print('Pipe n:1 - Roundrobin-joined pipe output value %s' % (value))
    except StopIteration:
        pass

    t("n:1 pipe roundrobin - same as before, with a generators chain")
    print("Actually, this is not possible with a one-line: we need a `while True` and a `except StopIteration`")
    # g1 = (i for i in source())
    # g2 = (i+10 for i in source())
    # generators = (g1, g2)
    # for value in (print(next(g)) for i in range(1000000) for g in generators):
    #     pass

    t("n:1 pipe zip - zip-join 2 generators")
    g1 = source(range(5), name='source1')
    g2 = source(range(10, 15), name='source2')
    generators = (g1, g2)
    for values in zip(*generators):
        value = sum(values) / len(values)
        print('Averaged value of from 2 generators values %s: %s' % (values, value))

    t("n:1 pipe zip - same as before, with a generator chain")
    g1 = source(range(5), name='source1')
    g2 = source(range(10, 15), name='source2')
    generators = (g1, g2)
    for _ in (print(sum(values)/len(values)) for values in (values for values in zip(*generators))):
        pass
section()

def section():
    t("1:n pipe - split 1 generator")
    # - this is not possible: iteration can be done by only 1 consumer
    # - so we created class Consumer - see blow
    consumer1 = lambda v: print('1:n pipe - Consumer 1 value %s' % value)
    consumer2 = lambda v: print('1:n pipe - Consumer 2 value %s' % value)
    consumers = (consumer1, consumer2)
    g = source()
    for value in g:
        for consumer in consumers:
            consumer(value)
    print("\n#FIXME: Shouldn't it work ?")
    for _ in (consumer(value) for consumer in consumers for value in source()):
        pass
section()

def section():
    t("Pipe consumption timing - consumer gives tempo")
    g = source()
    for value in g:
        time.sleep(3/100)
        print('Consumed value at %.1f after sleeping: %s' % (time.time(), value))

    t("Pipe consumption timing - producer gives tempo")
    def g():
        for i in source():
            time.sleep(3/100)
            yield i
    for value in g():
        print('Consumed value at %.1f after waiting on producer: %s' % (time.time(), value))

    t("Pipe consumption timing - middle pipe element gives tempo")
    g = source()
    def middle(g):
        for value in g:
            time.sleep(3/100)
            yield value
    for value in middle(g):
        print('Consumed value at %.1f after waiting on middle pipe element: %s' % (time.time(), value))
section()

def section():
    t("\n*** Pipe advanced: 1:n pipes and join pipes with different iteration rates ***")
    try:
        import machine
    except:
        # not running on MCU
        print('This example can only run on MCU, not in plain python because it uses machine.Timer')
        # FIXME: emulate a periodic timer emulation ala machine.timer using eg. module `threading`
        # so that we can run the framework in plain python
        machine = None

    if machine:
        class Consumer(object):
            """
            This class acts like a reservoir. It will store the last received value
            (ie. the last value iterated on self.generator)
            and yield it either:
                - by iterating the method `self.values` generator that yield value only once when received
                - by iterating `self` generator that yield the last received value (with duplicates and pseudo-infinitely)

            The behavior when iterating `self` differs slightly compared to a traditional generator because it can yield duplicates.
            It can be used to create:
                - 1:n pipes (it can be iterated by multiple consumers seamlessly)
                - join pipes with different iteration rates
                  (it can "pad" "missing" generator yield by yielding duplicates)
            Note that `self` is a pseudo-infinite generator because it will raise StopIteration
            when the iterated generator raises StopIteration. It makes no sense to continues because
            the iterated generator will never start again.

            # FIXME: Consumer starts iterating at construction time,
            # we may need a way to delay it, for building pipes without starting iterating right away:
            # fix is easy: use a method `start` or `iterate`.
            """
            timer_id = -1

            def __init__(self, g, period=1):
                self.generator = g
                self.value = None
                self.value_consumed = False
                self.stop_iteration = False
                if period:
                    self.consume(g, period)  # then, use Consumer object.next() to iterate the given generator `g`.

            def consume(self, g, period):
                self.timer = machine.Timer(Consumer.timer_id)  # FIXME: creating timer object in function = exception OSError: 261
                Consumer.timer_id -= 1
                self.timer.init(period=int(period*1000), callback=lambda t: self.next())
                self.next()  # start periodic task immediately, don't wait for `period`
                             # this also has the advantage of raising StopIteration immediately

            def next(self):
                try:
                    self.value = next(self.generator)
                    self.value_consumed = False
                except StopIteration:
                    self.stop_iteration = True
                    self.timer.deinit()

            def __iter__(self):
                return self
            def __next__(self):
                # Return a generator that yield the stored value
                if self.stop_iteration:
                    # FIXME: shall we StopIteration on the infinite generator ?
                    # Let's call it a pseudo-infinite generator and StopIteration:
                    # because the consumed generated will never start again,
                    # it makes no sense to not StopIteration here.
                    raise StopIteration()
                return self.value
            def values(self):
                # Return a generator that yield value only once when received
                # but then you should use a plain generator function, no need of Consumer
                for i in self:
                    if not self.value_consumed:
                        self.value_consumed = True
                        yield self.value

        t("Pipe split 1:1 - split a fast pipe and a slow pipe (the slow pipe will miss values: it is intended that the slow consumer doesn't slow down the fast pipe)")
        # Consumer object <- display-line <- slow-pipe <- Consumer object <- display-dot <- fast-pipe
        def display(prefix, g):
            for value in g:
                print(prefix, 'iterated', value, '<-')
                yield value
        Consumer(period=1, g=display('Slow pipe', g=(Consumer(period=5/10, g=display('Fast pipe', g=(source()))))))
        time.sleep(3)  # wait for non-blocking example to finish before displaying prompt

        t("Pipe split 1:n - multiple consumers (and implied yield-chain decoupling), NON BLOCKING !)")
        # The big picture:
        #                            pipeA <-+- pipe
        #                            pipeB <-+
        #
        # The details:
        # (pipe could go further <-) Consumer object <- displayA <- pipeA <-+- Consumer object <- pipe <- source
        # (pipe could go further <-) Consumer object <- displayB <- pipeB <-+
        pipe = source()
        split = Consumer(period=1, g=pipe)
        pipeA = display(prefix='pipeA', g=split)
        pipeB = display(prefix='pipeB', g=split)
        Consumer(period=1, g=pipeA)
        Consumer(period=5/10, g=pipeB)
        time.sleep(6)  # wait for non-blocking example to finish before displaying prompt
section()

def section():
    t("\n*** A more readable way to express pipes  #TODO ***")

    print("""
    We'll need to have generators as class rather than function (for this and eg. average history, etc)
    Let's keep this for the next prototyping step in file: examples/prototyping/machine-iterators.py

    How about this:

        pipe = Poll(pin).bind(Average(size=5).bind(Print(prefix='Value')))

    or

        pipe = Pipe(
            Poll(pin),
            Display(prefix='Reading'),
            Average(size=5),
            Display(prefix='Average'),
            Boolean()
            Display(prefix='Boolean'),
            Update(led))

        consumer = pipe.consume(period=1)  # equals to: Consumer(period=1, g=pipe)
    """.lstrip())

    # class Pipe(object):
    #     def __init__(self, *generators):
    #         self.pipe = generators.pop(0)
    #         for generator in generators:
    #             self.pipe.bind(generator)
    #     def consume(self, period=1):
    #         return Consume(period=period, g=self.pipe)
    #     def __iter__(self):
    #         return self
    #     def __next__(self):
    #         while True:
    #             yield self.pipe
    #
    # class Element(object):
    #     def __init__(self):
    #         pass  # FIXME: maybe use the **options argument system to free subclasses from having to declare __init__ with their specific args
    #     def bind(self, g):
    #         self.g = g
    #     def bind(self, value):
    #         return value  # neutral processing, subclass extend this method
    #     def __iter__(self):
    #         return self
    #     def __next__(self):
    #         for value in self.g:
    #             self.process(value)
    #             yield value
    #
    # pipe = Pipe(
    #     (i for i in range(5)),
    #     Element(),
    #     # TODO: allow plain generator functions ()
    #     # lambda g: (value/10 for value in g),
    #     # lambda g: display(g, prefix='Pipe plain generator function')
    # )
    # consumer = pipe.consume(period=1)  # equals to: Consumer(period=1, g=pipe)
section()

t("Thank you for watching, enjoy !")
