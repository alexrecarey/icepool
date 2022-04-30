__docformat__ = 'google'

import icepool
import icepool.die.base
import icepool.die.vector

import bisect
from collections import defaultdict
import itertools
import math

class ScalarDie(icepool.die.base.BaseDie):
    """ Univariate die.
    
    Outcomes are scalars and operations are performed directly on the outcomes.
    """
    
    def ndim(self):
        return icepool.Scalar
    
    def __init__(self, data):
        """ Constructor.
        
        Dice should not be constructed directly;
        instead, use one of the methods defined in `icepool.die.func` 
        (which are imported into the top-level `icepool` module).
        
        Args:
            data: A `Counts` mapping outcomes to weights.
        """
        self._data = data
    
    def _unary_op(self, op, *args, **kwargs):
        """ Returns a die representing the effect of performing the operation on the outcomes. """
        data = defaultdict(int)
        for outcome, weight in self.items():
            data[op(outcome, *args, **kwargs)] += weight
        return icepool.Die(data, ndim=icepool.Scalar)
    
    def _binary_op(self, other, op, *args, **kwargs):
        """ Returns a die representing the effect of performing the operation on pairs of outcomes from the two dice. """
        data = defaultdict(int)
        for (outcome_self, weight_self), (outcome_other, weight_other) in itertools.product(self.items(), other.items()):
            data[op(outcome_self, outcome_other, *args, **kwargs)] += weight_self * weight_other
        return icepool.Die(data, ndim=icepool.Scalar)
    
    def _wrap_unpack(self, func):
        return func
    
    # Special operators.
    
    def d(self, other, *, ndim=None):
        """ Roll the left die, then roll the right die that many times and sum the outcomes. 
        
        If an `int` is provided for the right side, it becomes a standard die with that many faces.
        Otherwise it is cast to a die.
        """
        if isinstance(other, int):
            other = icepool.standard(other)
        else:
            other = icepool.Die(other, ndim=ndim)
        
        data = defaultdict(int)
        
        max_abs_die_count = max(abs(self.min_outcome()), abs(self.max_outcome()))
        for die_count, die_count_weight in self.items():
            factor = other.denominator() ** (max_abs_die_count - abs(die_count))
            subresult = other.repeat_and_sum(die_count)
            for outcome, subresult_weight in subresult.items():
                data[outcome] += subresult_weight * die_count_weight * factor
            
        return icepool.Die(data, ndim=other.ndim())
    
    def __matmul__(self, other):
        """ Roll the left die, then roll the right die that many times and sum the outcomes. 
        
        Unlike other operators, this does not work for built-in types on the right side.
        For example, `1 @ 6` does not work, nor does `d(6) @ 6`. But `1 @ d(6)` works.
        
        This is because all other operators convert their right side to a die using die,
        so `6` would become a constant 6, while  `d()` converts `int`s to a standard die with that many sides,
        so `6` would become a d6. Thus the right-side conversion of `@` would be ambiguous.
        """
        if not isinstance(other, icepool.die.base.BaseDie):
            raise TypeError(f'The @ operator will not automatically convert the right side of type {type(other).__qualname__} to a die.')
        return self.d(other)
    
    def if_else(self, outcome_if_true, outcome_if_false, /, *, ndim=None, denominator_method='lcm'):
        """ Ternary conditional operator.
        
        This replaces truthy outcomes with the first argument and falsy outcomes with the second argument.
        """
        return self.bool().sub(lambda x: outcome_if_true if x else outcome_if_false, ndim=ndim, denominator_method=denominator_method)
    
    # Statistics.
    
    def median_left(self):
        """ Returns the median.
        
        If the median lies between two outcomes, returns the lower of the two. """
        return self.ppf_left(1, 2)
    
    def median_right(self):
        """ Returns the median.
        
        If the median lies between two outcomes, returns the higher of the two. """
        return self.ppf_right(1, 2)
    
    def median(self):
        """ Returns the median.
        
        If the median lies between two outcomes, returns the mean of the two.
        This will fail if the outcomes do not support division;
        in this case, use `median_left` or `median_right` instead.
        """
        return self.ppf(1, 2)
    
    def ppf_left(self, n, d=100):
        """ Returns a quantile, `n / d` of the way through the cdf.
        
        If the result lies between two outcomes, returns the lower of the two.
        """
        index = bisect.bisect_left(self.cweights(), (n * self.denominator() + d - 1) // d)
        if index >= self.num_outcomes(): return self.max_outcome()
        return self.outcomes()[index]
    
    def ppf_right(self, n, d=100):
        """ Returns a quantile, `n / d` of the way through the cdf.
        
        If the result lies between two outcomes, returns the higher of the two.
        """
        index = bisect.bisect_right(self.cweights(), n * self.denominator() // d)
        if index >= self.num_outcomes(): return self.max_outcome()
        return self.outcomes()[index]
    
    def ppf(self, n, d=100):
        """ Returns a quantile, `n / d` of the way through the cdf.
        
        If the result lies between two outcomes, returns the mean of the two.
        This will fail if the outcomes do not support division;
        in this case, use `ppf_left` or `ppf_right` instead.
        """
        return (self.ppf_left(n, d) + self.ppf_right(n, d)) / 2
    
    def mean(self):
        return sum(outcome * p for outcome, p in zip(self.outcomes(), self.pmf()))
    
    def variance(self):
        mean = self.mean()
        mean_of_squares = sum(p * outcome ** 2 for outcome, p in zip(self.outcomes(), self.pmf()))
        return mean_of_squares - mean * mean
    
    def standard_deviation(self):
        return math.sqrt(self.variance())
    
    sd = standard_deviation
    
    def standardized_moment(self, k):
        sd = self.standard_deviation()
        mean = self.mean()
        ev = sum(p * (outcome - mean) ** k for outcome, p in zip(self.outcomes(), self.pmf()))
        return ev / (sd ** k)
    
    def skewness(self):
        return self.standardized_moment(3.0)
    
    def excess_kurtosis(self):
        return self.standardized_moment(4.0) - 3.0
    
    def __repr__(self):
        return type(self).__qualname__ + f'({self._data.__repr__()})'
    
    def markdown(self, include_weights=True):
        outcome_length = max(tuple(len(str(outcome)) for outcome in self.outcomes()) + (len('Outcome'),))
        result = ''
        result += f'Denominator: {self.denominator()}\n\n'
        result +=  '| ' + ' ' * (outcome_length - len('Outcome')) + 'Outcome |'
        if include_weights:
            weight_length = max(tuple(len(str(weight)) for weight in self.weights()) + (len('Weight'),))
            result +=   ' ' + ' ' * (weight_length - len('Weight'))   +  'Weight |'
        if self.denominator() > 0:
            result += ' Probability |'
        result += '\n'
        result += '|-' + '-' * outcome_length + ':|'
        if include_weights:
            result += '-' + '-' * weight_length + ':|'
        if self.denominator() > 0:
            result += '------------:|'
        result += '\n'
        for outcome, weight, p in zip(self.outcomes(), self.weights(), self.pmf()):
            result += f'| {str(outcome):>{outcome_length}} |'
            if include_weights:
                result += f' {weight:>{weight_length}} |'
            if self.denominator() > 0:
                result += f' {p:11.6%} |'
            result += '\n'
        return result