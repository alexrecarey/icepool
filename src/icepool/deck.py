__docformat__ = 'google'

import icepool
import icepool.math
import icepool.creation_args
from icepool.counts import Counts, CountsKeysView, CountsValuesView, CountsItemsView
from icepool.population import Population

from collections import defaultdict
from functools import cached_property
import operator

from typing import Any, Callable, Iterator
from collections.abc import Mapping, MutableMapping, Sequence


class Deck(Population):
    """EXPERIMENTAL: Sampling without replacement.

    API and naming WIP.
    """

    _data: Counts
    _deal: int

    def __new__(cls,
                outcomes: Mapping[Any, int] | Sequence,
                times: Sequence[int] | int = 1) -> 'Deck':
        """Constructor for a deck.

        Args:
            outcomes: The cards of the deck. This can be one of the following:
                * A `Mapping` from outcomes to dups.
                * A sequence of outcomes.

                Note that `Die` and `Deck` both count as `Mapping`s.

                Each card may be one of the following:
                * A `Mapping` from outcomes to dups.
                    The outcomes of the `Mapping` will be "flattened" into the
                    result. This option will be taken in preference to treating
                    the `Mapping` itself as an outcome even if the `Mapping`
                    itself is hashable and totally orderable. This means that
                    `Die` and `Deck` will never be outcomes.
                * A tuple of outcomes.
                    Any tuple elements that are `Mapping`s will expand the
                    tuple according to their independent joint distribution.
                    For example, `(d6, d6)` will expand to 36 ordered tuples
                    with dup 1 each. Use this carefully since it may create a
                    large number of outcomes.
                * Anything else will be treated as a single outcome.
                    Each outcome must be hashable, and the
                    set of outcomes must be totally orderable (after expansion).
                    The same outcome can appear multiple times, in which case
                    the corresponding dups will be accumulated.
            times: Multiplies the number of times each element of `outcomes`
                will be put into the deck.
                `times` can either be a sequence of the same length as
                `outcomes` or a single `int` to apply to all elements of
                `outcomes`.
        """
        if isinstance(outcomes, Deck):
            if times == 1:
                return outcomes
            else:
                outcomes = outcomes._data

        outcomes, times = icepool.creation_args.itemize(outcomes, times)

        if len(outcomes) == 1 and times[0] == 1 and isinstance(
                outcomes[0], Deck):
            return outcomes[0]

        data = icepool.creation_args.expand_args_for_deck(outcomes, times)
        return Deck._new_deck(data)

    def unary_op_non_elementwise(self, op: Callable, *args, **kwargs) -> 'Deck':
        """As `unary_op()`, but not elementwise.

        This is used for `marginals()`.
        """
        data: MutableMapping[Any, int] = defaultdict(int)
        for outcome, quantity in self.items():
            new_outcome = op(outcome, *args, **kwargs)
            data[new_outcome] += quantity
        return Deck(data)

    @classmethod
    def _new_deck(cls, data: Counts) -> 'Deck':
        """Creates a new deck using already-processed arguments.

        Args:
            data: At this point, this is a Counts.
        """
        self = super(Deck, cls).__new__(cls)
        self._data = data
        return self

    def keys(self) -> CountsKeysView:
        """The outcomes of the deck in sorted order.

        These are also the `keys` of the deck as a `Mapping`.
        Prefer to use the name `outcomes`.
        """
        return self._data.keys()

    def values(self) -> CountsValuesView:
        """The dups of the deck in outcome order.

        These are also the `values` of the deck as a `Mapping`.
        Prefer to use the name `dups`.
        """
        return self._data.values()

    def items(self) -> CountsItemsView:
        return self._data.items()

    def __getitem__(self, outcome) -> int:
        return self._data[outcome]

    def __iter__(self) -> Iterator:
        return iter(self.keys())

    def __len__(self) -> int:
        return len(self._data)

    size = icepool.Population.denominator

    @cached_property
    def _popped_min(self) -> tuple['Deck', int]:
        return self._new_deck(self._data.remove_min()), self.quantities()[0]

    def _pop_min(self) -> tuple['Deck', int]:
        """Returns a deck with the min outcome removed."""
        return self._popped_min

    @cached_property
    def _popped_max(self) -> tuple['Deck', int]:
        return self._new_deck(self._data.remove_max()), self.quantities()[-1]

    def _pop_max(self) -> tuple['Deck', int]:
        """Returns a deck with the max outcome removed."""
        return self._popped_max

    def deal(self, *hand_sizes: int) -> 'icepool.Deal':
        """Creates a `Deal` object from this deck.

        See `Deal()` for details.
        """
        return icepool.Deal(self, *hand_sizes)

    class Marginals():
        """Helper class for implementing marginals()."""

        _deck: 'Deck'

        def __init__(self, deck: 'Deck', /):
            self._deck = deck

        def __getitem__(self, dims, /) -> 'Deck':

            return self._deck.unary_op_non_elementwise(operator.getitem, dims)

    @property
    def marginals(self):
        """A property that applies the `[]` operator to outcomes.

        This is not performed elementwise on tuples, so that this can be used
        to slice tuples. For example, `deck.marginals[:2]` will marginalize the
        first two elements of tuples.
        """
        return Deck.Marginals(self)

    @cached_property
    def _key_tuple(self) -> tuple:
        return Deck, tuple(self.items())

    def __eq__(self, other) -> bool:
        if not isinstance(other, Deck):
            return False
        return self._key_tuple == other._key_tuple

    @cached_property
    def _hash(self) -> int:
        return hash(self._key_tuple)

    def __hash__(self) -> int:
        return self._hash

    def __repr__(self) -> str:
        inner = ', '.join(
            f'{outcome}: {quantity}' for outcome, quantity in self.items())
        return type(self).__qualname__ + '({' + inner + '})'
