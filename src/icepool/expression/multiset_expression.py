__docformat__ = 'google'

import icepool
import icepool.expression
import icepool.evaluator

from icepool.typing import Outcome, SetComparatorStr

from abc import ABC, abstractmethod
from typing import Callable, Collection, Mapping, TypeAlias, TypeVar

T = TypeVar('T', bound=Outcome)
"""Type variable representing an outcome type."""

U = TypeVar('U', bound=Outcome)
"""Type variable representing another outcome type."""


class MultisetExpression(ABC):
    """Abstract base class representing an expression that operates on multisets.

    Use `MultisetVariable` to start an expression.

    Use the provided operators and methods to build up more complicated
    expressions, or to attach a final evaluator.
    """

    @abstractmethod
    def evaluate_counts(self, outcome: Outcome, *counts: int) -> int:
        """Evaluate this expression, producing a single output count.

        You probably won't need to call this yourself.

        Args:
            outcome: The current outcome.
            *counts: The original sequence of counts.
        """

    __call__ = evaluate_counts

    # Binary operators.

    def __add__(self, other: 'MultisetExpression') -> 'MultisetExpression':
        if not isinstance(other, MultisetExpression):
            return NotImplemented
        return icepool.expression.DisjointUnionExpression(self, other)

    def __radd__(self, other: 'MultisetExpression') -> 'MultisetExpression':
        if not isinstance(other, MultisetExpression):
            return NotImplemented
        return icepool.expression.DisjointUnionExpression(other, self)

    def __sub__(self, other: 'MultisetExpression') -> 'MultisetExpression':
        if not isinstance(other, MultisetExpression):
            return NotImplemented
        return icepool.expression.DifferenceExpression(self, other)

    def __rsub__(self, other: 'MultisetExpression') -> 'MultisetExpression':
        if not isinstance(other, MultisetExpression):
            return NotImplemented
        return icepool.expression.DifferenceExpression(other, self)

    def __and__(self, other: 'MultisetExpression') -> 'MultisetExpression':
        if not isinstance(other, MultisetExpression):
            return NotImplemented
        return icepool.expression.IntersectionExpression(self, other)

    def __rand__(self, other: 'MultisetExpression') -> 'MultisetExpression':
        if not isinstance(other, MultisetExpression):
            return NotImplemented
        return icepool.expression.IntersectionExpression(other, self)

    def __or__(self, other: 'MultisetExpression') -> 'MultisetExpression':
        if not isinstance(other, MultisetExpression):
            return NotImplemented
        return icepool.expression.UnionExpression(self, other)

    def __ror__(self, other: 'MultisetExpression') -> 'MultisetExpression':
        if not isinstance(other, MultisetExpression):
            return NotImplemented
        return icepool.expression.UnionExpression(other, self)

    def __xor__(self, other: 'MultisetExpression') -> 'MultisetExpression':
        if not isinstance(other, MultisetExpression):
            return NotImplemented
        return icepool.expression.SymmetricDifferenceExpression(self, other)

    def __rxor__(self, other: 'MultisetExpression') -> 'MultisetExpression':
        if not isinstance(other, MultisetExpression):
            return NotImplemented
        return icepool.expression.SymmetricDifferenceExpression(other, self)

    # Adjust counts.

    def __mul__(self, other: int) -> 'MultisetExpression':
        if not isinstance(other, int):
            return NotImplemented
        return icepool.expression.MultiplyCountsExpression(self, other)

    # Commutable in this case.
    def __rmul__(self, other: int) -> 'MultisetExpression':
        if not isinstance(other, int):
            return NotImplemented
        return icepool.expression.MultiplyCountsExpression(self, other)

    def multiply_counts(self, constant: int, /) -> 'MultisetExpression':
        """Multiplies all counts by a constant.

        Same as `self * constant`.
        """
        return self * constant

    def __floordiv__(self, other: int) -> 'MultisetExpression':
        if not isinstance(other, int):
            return NotImplemented
        return icepool.expression.FloorDivCountsExpression(self, other)

    def divide_counts(self, constant: int, /) -> 'MultisetExpression':
        """Divides all counts by a constant (rounding down).

        Same as `self // constant`.
        """
        return self // constant

    def filter_counts(self, min_count: int) -> 'MultisetExpression':
        """Counts less than `min_count` are treated as zero.

        For example, `generator.filter_counts(2)` would only produce
        pairs and better.
        """
        return icepool.expression.FilterCountsExpression(self, min_count)

    def unique(self, max_count: int = 1) -> 'MultisetExpression':
        """Counts each outcome at most `max_count` times.

        For example, `generator.unique(2)` would count each outcome at most
        twice.
        """
        return icepool.expression.UniqueExpression(self, max_count)

    # Evaluations.

    def evaluator(
        *expressions: 'MultisetExpression',
        evaluator: 'icepool.OutcomeCountEvaluator[T, int, U]'
    ) -> 'icepool.OutcomeCountEvaluator[T, int, U]':
        """Attaches a final `OutcomeCountEvaluator` to this expression.

        The result is an `OutcomeCountEvaluator` that runs the expression
        before sending the result to the provided evaluator.
        """
        return icepool.expression.ExpressionEvaluator(*expressions,
                                                      evaluator=evaluator)

    def expand(self) -> 'icepool.OutcomeCountEvaluator[T, int, tuple[T, ...]]':
        """All possible sorted tuples of outcomes.

        This is expensive and not recommended unless there are few possibilities.
        """
        evaluator = icepool.evaluator.ExpandEvaluator()
        return icepool.expression.ExpressionEvaluator(self, evaluator=evaluator)

    def sum(
        self,
        map: Callable[[T], U] | Mapping[T, U] | None = None
    ) -> 'icepool.OutcomeCountEvaluator[T, int, U]':
        evaluator = icepool.evaluator.FinalOutcomeMapEvaluator(
            icepool.evaluator.sum_evaluator, map)
        return icepool.expression.ExpressionEvaluator(self, evaluator=evaluator)

    def count(self) -> 'icepool.OutcomeCountEvaluator[Outcome, int, int]':
        """The total count over all outcomes.

        This is usually not very interesting unless some other operation is
        performed first. Examples:

        `generator.unique().count()` will count the number of unique outcomes.

        `(generator & [4, 5, 6]).count()` will count up to one each of
        4, 5, and 6.
        """
        evaluator = icepool.evaluator.count_evaluator
        return icepool.expression.ExpressionEvaluator(self, evaluator=evaluator)

    def highest_outcome_and_count(
            self) -> 'icepool.OutcomeCountEvaluator[T, int, tuple[T, int]]':
        """The highest outcome with positive count, along with that count.

        If no outcomes have positive count, an arbitrary outcome will be
        produced with a 0 count.
        """
        evaluator = icepool.evaluator.HighestOutcomeAndCountEvaluator()
        return icepool.expression.ExpressionEvaluator(self, evaluator=evaluator)

    def all_counts(
        self,
        positive_only: bool = True
    ) -> 'icepool.OutcomeCountEvaluator[T, int, tuple[int, ...]]':
        """Produces a tuple of all counts, i.e. the sizes of all matching sets.

        Args:
            positive_only: If `True` (default), negative and zero counts
                will be omitted.
        """
        evaluator = icepool.evaluator.AllCountsEvaluator(
            positive_only=positive_only)
        return icepool.expression.ExpressionEvaluator(self, evaluator=evaluator)

    def largest_count(self) -> 'icepool.OutcomeCountEvaluator[T, int, int]':
        """The size of the largest matching set among the outcomes."""
        evaluator = icepool.evaluator.LargestCountEvaluator()
        return icepool.expression.ExpressionEvaluator(self, evaluator=evaluator)

    def largest_count_and_outcome(
            self) -> 'icepool.OutcomeCountEvaluator[T, int, tuple[int, T]]':
        """The largest matching set among the outcomes and its outcome."""
        evaluator = icepool.evaluator.LargestCountAndOutcomeEvaluator()
        return icepool.expression.ExpressionEvaluator(self, evaluator=evaluator)

    def largest_straight(
            self) -> 'icepool.OutcomeCountEvaluator[int, int, int]':
        """The size of the largest straight among the outcomes.

        Outcomes must be `int`s.
        """
        evaluator = icepool.evaluator.LargestStraightEvaluator()
        return icepool.expression.ExpressionEvaluator(self, evaluator=evaluator)

    def largest_straight_and_outcome(
            self) -> 'icepool.OutcomeCountEvaluator[int, int, tuple[int, int]]':
        """The size of the largest straight among the outcomes and the highest outcome in that straight.

        Outcomes must be `int`s.
        """
        evaluator = icepool.evaluator.LargestStraightAndOutcomeEvaluator()
        return icepool.expression.ExpressionEvaluator(self, evaluator=evaluator)

    # Comparators.

    def compare(self, op_name: SetComparatorStr,
                other: 'MultisetExpression | Mapping[T, int] | Collection[T]',
                /) -> 'icepool.OutcomeCountEvaluator[T, int, bool]':
        """Compares the outcome multiset to another multiset.

        You can also use the symbolic operators directly, e.g.
        `generator <= [1, 2, 2]`.

        If the other argument is a `Mapping` or `Collection`, it
        will be treated as a fixed target.

        Args:
            op_name: One of the following strings:
                `<, <=, >, >=, ==, !=`.
            other: The right-side generator or multiset to compare with.
        """
        if isinstance(other, MultisetExpression):
            evaluator = icepool.evaluator.ComparisonEvaluator.new_by_name(
                op_name)  # type: ignore
            return icepool.expression.ExpressionEvaluator(
                self,
                other,
                evaluator=evaluator,
            )
        elif isinstance(other, (Mapping, Collection)):
            evaluator = icepool.evaluator.ComparisonEvaluator.new_by_name(
                op_name, other)
            return icepool.expression.ExpressionEvaluator(self,
                                                          evaluator=evaluator)
        else:
            return NotImplemented

    def __lt__(self,
               other: 'MultisetExpression | Mapping[T, int] | Collection[T]',
               /) -> 'icepool.OutcomeCountEvaluator[T, int, bool]':
        return self.compare('<', other)

    def __le__(self,
               other: 'MultisetExpression | Mapping[T, int] | Collection[T]',
               /) -> 'icepool.OutcomeCountEvaluator[T, int, bool]':
        return self.compare('<=', other)

    def issubset(self,
                 other: 'MultisetExpression | Mapping[T, int] | Collection[T]',
                 /) -> 'icepool.OutcomeCountEvaluator[T, int, bool]':
        """Whether the outcome multiset is a subset of the other multiset.

        Same as `self <= other`.
        """
        return self <= other

    def __gt__(self,
               other: 'MultisetExpression | Mapping[T, int] | Collection[T]',
               /) -> 'icepool.OutcomeCountEvaluator[T, int, bool]':
        return self.compare('>', other)

    def __ge__(self,
               other: 'MultisetExpression | Mapping[T, int] | Collection[T]',
               /) -> 'icepool.OutcomeCountEvaluator[T, int, bool]':
        return self.compare('>=', other)

    def issuperset(
            self, other: 'MultisetExpression | Mapping[T, int] | Collection[T]',
            /) -> 'icepool.OutcomeCountEvaluator[T, int, bool]':
        """Whether the outcome multiset is a superset of the target multiset.

        Same as `self >= other`.
        """
        return self >= other

    # This does not produce a truth value.
    def __eq__(  # type: ignore
            self, other: 'MultisetExpression | Mapping[T, int] | Collection[T]',
            /) -> 'icepool.OutcomeCountEvaluator[T, int, bool]':
        return self.compare('==', other)

    # This does not produce a truth value.
    def __ne__(  # type: ignore
            self, other: 'MultisetExpression | Mapping[T, int] | Collection[T]',
            /) -> 'icepool.OutcomeCountEvaluator[T, int, bool]':
        return self.compare('!=', other)

    def isdisjoint(
            self, other: 'MultisetExpression | Mapping[T, int] | Collection[T]',
            /) -> 'icepool.OutcomeCountEvaluator[T, int, bool]':
        """Whether the outcome multiset is disjoint from the target multiset."""
        return self.compare('isdisjoint', other)
