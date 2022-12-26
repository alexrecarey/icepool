__docformat__ = 'google'

import icepool
from icepool.counts import Counts
from icepool.die.die import Die
from icepool.typing import Outcome

from functools import cached_property
import warnings

from typing import Callable, Hashable, TypeVar

T = TypeVar('T', bound=Outcome)
"""Type variable representing the outcome type."""


class DieWithTruth(Die[T]):
    """A `Die` with a truth value.

    Additionally, the data is evaluated lazily since the caller may only be
    interested in the truth value.
    """
    _used_callback: bool
    """Whether either of the callbacks has been used."""
    _data_callback: Callable[[], Counts[T]]
    _truth_value_callback: Callable[[], bool]

    def __new__(cls, data_callback: Callable[[], Counts[T]],
                truth_value_callback: Callable[[], bool]) -> 'DieWithTruth[T]':
        """This class does not need to be constructed publically.

        Args:
            data_callback: Called with no arguments to populate _data if
                requested.
            truth_value: The truth value of this die.
        """
        # Skip Die.__new__.
        self = super(Die, cls).__new__(cls)
        self._used_callback = False
        self._data_callback = data_callback  # type: ignore
        self._truth_value_callback = truth_value_callback  # type: ignore
        return self

    @cached_property
    def _data(self) -> Counts[T]:  # type: ignore
        if self._used_callback:
            warnings.warn(
                'Both the Die result and the truth value of a comparator were used. This is likely to be unintentional.',
                category=RuntimeWarning,
                stacklevel=3)
        self._used_callback = True
        return self._data_callback()  # type: ignore

    @cached_property
    def _truth_value(self) -> bool:
        if self._used_callback:
            warnings.warn(
                'Both the Die result and the truth value of a comparator were used. This is likely to be unintentional.',
                category=RuntimeWarning,
                stacklevel=4)
        self._used_callback = True
        return self._truth_value_callback()  # type: ignore

    def __bool__(self) -> bool:
        return self._truth_value
