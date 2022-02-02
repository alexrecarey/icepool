__docformat__ = 'google'

import hdroller
from hdroller.collections import FrozenSortedWeights
import hdroller.dice.base
import hdroller.dice.multi
import hdroller.dice.single
import hdroller.dice.zero

from collections import defaultdict
import itertools
import math

def die(arg, min_outcome=None, ndim=None, remove_zero_weights=True):
    """ General-purpose constructor for a die.
    
    Don't confuse this with `hdroller.d()`:
    
    * `hdroller.die(6)`: A die that always rolls the integer 6.
    * `hdroller.d(6)`: A d6.
    
    Here are different ways to create a d6:'
    
    * Provide the die itself: `hdroller.die(hdroller.d6)`
    * Provide a mapping from outcomes to weights: `hdroller.die({1:1, 2:1, 3:1, 4:1, 5:1, 6:1})`
    * Provide a sequence of outcomes: `hdroller.die([1, 2, 3, 4, 5, 6])`
    * Provide a consecutive sequence of weights with a minimum outcome: `hdroller.die([1, 1, 1, 1, 1, 1], min_outcome=1)`
    
    Args:
        arg: This can be one of the following, with examples of how to create a d6:
            * A die, which will be returned itself.
            * A mapping from outcomes to weights.
            * A sequence of outcomes. Each outcome will be given weight `1` per time it appears.
            * A sequence of weights, with `min_outcome` set to an `int`. 
                The outcomes will be `int`s starting at `min_outcome`.
            * A single hashable and comparable value.
                There will be a single outcome equal to the argument, with weight `1`.
        ndim: If provided, the die will have the given number of dimensions.
            E.g. for `str` outcomes you may want to set `ndim=1`, which will
            treat e.g. `'abc' + 'def'` as `'abcdef'` rather than `('ad', 'be', 'cf')`.
        remove_zero_weights: If `True`, zero weights will be filtered out.
            This should be left at `True` for most cases.
    """
    data = _make_data(arg, min_outcome, remove_zero_weights)
    
    if len(data) == 0:
        return None
        
    ndim = _calc_ndim(data, ndim)
    
    if ndim == 0:
        return hdroller.dice.zero.ZeroDie(data, 0)
    elif ndim == 1:
        return hdroller.dice.single.SingleDie(data, 1)
    else:
        return hdroller.dice.multi.MultiDie(data, ndim)

def _make_data(arg, min_outcome=None, remove_zero_weights=True):
    """ Creates a `FrozenSortedWeights` from the arguments. """
    if isinstance(arg, hdroller.dice.base.BaseDie):
        data = arg._data
    elif isinstance(arg, FrozenSortedWeights):
        data = arg
    elif min_outcome is not None:
        data = { min_outcome + i : weight for i, weight in enumerate(arg) }
    elif hasattr(arg, 'keys') and hasattr(arg, '__getitem__'):
        data = { k : arg[k] for k in arg.keys() }
    elif hasattr(arg, '__iter__'):
        data = defaultdict(int)
        for v in arg:
            data[v] += 1
    else:
        # Treat arg as the only possible value.
        data = { arg : 1 }
    
    return FrozenSortedWeights(data, remove_zero_weights)
    

def _calc_ndim(data, ndim):
    """Verifies `ndim` if provided, or calculates it if not.
    
    Args:
        data: A `FrozenSortedWeights`.
        ndim: If provided, `ndims` will be set to this value.
        
    Returns:
        An appropriate `ndim` for a die.
        
    Raises:
        `ValueError` if `ndim` is provided but is not consistent with the data.
    """
    if ndim is not None:
        if ndim != 1:
            for outcome in data.keys():
                if len(outcome) != ndim:
                    raise ValueError('Outcomes not consistent with provided ndim.')
        return ndim
    
    if len(data) == 0:
        return None
    
    for outcome in data.keys():
        try:
            if ndim is None:
                ndim = len(outcome)
            elif len(outcome) != ndim:
                # The data has mixed dimensions.
                return 1
        except TypeError:
            # The data contains a scalar.
            return 1
    return ndim

def standard(num_sides):
    """ A standard die.
    
    Specifically, the outcomes are `int`s from `1` to `num_sides` inclusive, with weight 1 each. 
    
    Don't confuse this with `hdroller.die()`:
    
    * `hdroller.die(6)`: A die that always rolls the integer 6.
    * `hdroller.d(6)`: A d6.
    """
    if not isinstance(num_sides, int):
        raise TypeError('Argument to standard() must be an int.')
    elif num_sides < 1:
        raise ValueError('Standard die must have at least one side.')
    return die([1] * num_sides, min_outcome=1)
    
def d(arg):
    """ Converts the argument to a standard die if it is not already a die.
    
    Args:
        arg: Either:
            * An `int`, which produces a standard die.
            * A die, which is returned itself.
    
    Returns:
        A die.
        
    Raises:
        `TypeError` if the argument is not an `int` or a die.
    """
    if isinstance(arg, int):
        return standard(arg)
    elif isinstance(arg, hdroller.dice.base.BaseDie):
        return arg
    else:
        raise TypeError('The argument to d() must be an int or a die.')

def __getattr__(key):
    """ Implements the `dX` syntax, e.g. `hdroller.d6`. """
    if key[0] == 'd':
        try:
            return standard(int(key[1:]))
        except ValueError:
            pass
    raise AttributeError(key)

def bernoulli(n, d):
    """ A die that rolls `True` with chance `n / d`, and `False` otherwise. """
    return die({False : d - n, True : n})

coin = bernoulli

def from_cweights(outcomes, cweights, ndim=None):
    """ Constructs a die from cumulative weights. """
    prev = 0
    d = {}
    for outcome, weight in zip(outcomes, cweights):
        if weight - prev > 0:
            d[outcome] = weight - prev
            prev = weight
    return die(d, ndim=ndim)
    
def from_sweights(outcomes, sweights, ndim=None):
    """ Constructs a die from survival weights. """
    d = {}
    for i, outcome in enumerate(outcomes):
        if i < len(outcomes) - 1:
            weight = sweights[i] - sweights[i+1]
        else:
            weight = sweights[i]
        if weight > 0:
            d[outcome] = weight
    return die(d, ndim=ndim)

def from_rv(rv, outcomes, denominator, **kwargs):
    """ Constructs a die from a rv object (as `scipy.stats`).
    Args:
        rv: A rv object (as `scipy.stats`).
        outcomes: An iterable of `int`s or `float`s that will be the outcomes of the resulting die.
            If the distribution is discrete, outcomes must be `int`s.
        denominator: The total weight of the resulting die will be set to this.
        **kwargs: These will be provided to `rv.cdf()`.
    """
    if hasattr(rv, 'pdf'):
        # Continuous distributions use midpoints.
        midpoints = [(a + b) / 2 for a, b in zip(outcomes[:-1], outcomes[1:])]
        cdf = rv.cdf(midpoints, **kwargs)
        cweights = tuple(int(round(x * denominator)) for x in cdf) + (denominator,)
    else:
        cdf = rv.cdf(outcomes, **kwargs)
        cweights = tuple(int(round(x * denominator)) for x in cdf)
    return from_cweights(outcomes, cweights)

def mix(*dice, mix_weights=None):
    """ Constructs a die from a mixture of the input dice.
    
    This is equivalent to rolling a die and then choosing one of the input dice
    based on the resulting outcome rolled.
    
    Args:
        *dice: The dice to mix.
        mix_weights: An iterable of one `int` per input die.
            If not provided, all dice are mixed uniformly.
    """
    dice = hdroller.dice.base._align(*dice)
    ndim = None
    for d in dice:
        if ndim is None:
            ndim = d.ndim()
        elif d.ndim() != ndim:
            ndim = 1
    
    weight_product = math.prod(d.total_weight() for d in dice)
    
    if mix_weights is None:
        mix_weights = (1,) * len(dice)
    
    data = defaultdict(int)
    for d, mix_weight in zip(dice, mix_weights):
        factor = mix_weight * weight_product // d.total_weight()
        for outcome, weight in zip(d.outcomes(), d.weights()):
            data[outcome] += weight * factor
    return die(data, ndim=ndim)

def apply(func, *dice, ndim=None):
    """ Applies `func(outcome_of_die_0, outcome_of_die_1, ...)` for all possible outcomes of the dice.
    
    This is flexible but not very efficient for large numbers of dice.
    In particular, for pools use `hdroller.pool` and `hdroller.PoolEval` instead if possible.
    
    Args:
        func: A function that takes one argument per input die and returns a new outcome.
        ndim: If supplied, the result will have this many dimensions.
    
    Returns:
        A die constructed from the outputs of `func` and the product of the weights of the dice.
    """
    dice = [die(d) for d in dice]
    data = defaultdict(int)
    for t in itertools.product(*(d.items() for d in dice)):
        outcomes, weights = zip(*t)
        data[func(*outcomes)] += math.prod(weights)
    
    return die(data, ndim=ndim)
