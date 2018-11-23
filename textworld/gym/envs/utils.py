from typing import Iterable, Any

from numpy.random import RandomState


def shuffled_cycle(iterable: Iterable[Any], rng: RandomState, nb_loops: int = -1) -> Iterable[Any]:
    """
    Yield each element of `iterable` one by one, then shuffle the elements
    and start yielding from the start. Stop after `nb_loops` loops.

    Arguments:
        iterable: Iterable containing the elements to yield.
        rng: Random generator used to shuffle the elements after each loop.
        nb_loops: Number of times to go through all the elements. If set to -1,
                  loop an infinite number of times.
    """
    elements = []
    for e in iterable:
        elements.append(e)
        yield e

    cpt = nb_loops
    while cpt != 0:
        cpt -= 1
        rng.shuffle(elements)
        for e in elements:
            yield e
