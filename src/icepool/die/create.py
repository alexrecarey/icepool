__docformat__ = 'google'

import icepool
from icepool.collections import Counts

from collections import defaultdict
import itertools
import math


def Die(*args,
        weights=None,
        min_outcome=None,
        ndim=None,
        denominator_method='lcm'):
    """Factory for constructing a die.
    
    This is capitalized because it is the preferred way of getting a new instance,
    and so that you can use `from icepool import Die` while leaving the name `die` free.
    The actual class of the result will be one of the subclasses of `BaseDie`.
    
    Don't confuse this with `icepool.d()`:
    
    * `icepool.Die(6)`: A die that always rolls the `int` 6.
    * `icepool.d(6)`: A d6.
    
    Here are some different ways of constructing a d6:
    
    * Just import it: `from icepool import d6`
    * Use the `d()` function: `icepool.d(6)`
    * Use a d6 that you already have: `Die(d6)`
    * Mix a d3 and a d3+3: `Die(d3, d3+3)`
    * Use a dict: `Die({1:1, 2:1, 3:1, 4:1, 5:1, 6:1})`
    * Give the faces as args: `Die(1, 2, 3, 4, 5, 6)`
    
    All weights must be non-negative, though they can be zero.
    
    Args:
        *args: Each of these arguments can be one of the following:
            * A die. The outcomes of the die will be "flattened" into the 
                result; a die object will never contain a die as an outcome.
                `Die()` cannot change the `ndim` of any die not in a tuple.
            * A dict-like that maps outcomes to weights.
                The outcomes of the dict-like will be "flattened" into the result.
                This option will be taken in preference to treating the dict-like 
                itself as an outcome even if the dict-like itself is hashable 
                and comparable.
            * A tuple of outcomes, which produces a joint distribution.
                Any inner nested tuples will be treated as scalar.
                Any arguments that are dice or dicts will expand the tuple
                according to their independent joint distribution.
                For example, (d6, d6) will expand to 36 ordered tuples with 
                weight 1 each. Use this sparingly since it may create a large 
                number of outcomes. Vector dice cannot be nested inside a tuple
                outcome.
            * `icepool.Reroll`, which will drop itself
                and the corresponding element of `weights` from consideration.
            * Anything else will be treated as a single outcome.
                These must be hashable and mutually comparable with all other 
                outcomes (after expansion). The same outcome can appear multiple 
                times, in which case it will be weighted proportionally higher.
        weights: Controls the relative weight of the arguments.
            If an argument expands into multiple outcomes, the weight is shared 
            among those outcomes. If not provided, each argument will end up 
            with the same total weight. For example, `Die(d6, 7)` is the same as 
            `Die(1, 2, 3, 4, 5, 6, 7, 7, 7, 7, 7, 7)`.
        min_outcome: If used, there must be zero `*args`, and `weights` must be 
            provided. The outcomes of the result will be integers starting at 
            `min_outcome`,one per weight in `weights` with that weight.
        ndim: If set to `icepool.Scalar`, the die will be scalar.
            If set to an `int`, the die will have that many dimensions if the 
            outcomes allow, and raise `ValueError` otherwise.
            If `None` (default), the number of dimensions will be automatically 
            detected: If all arguments are `tuple`s of the same length,
            the result will have that many dimensions. Otherwise the result will 
            be scalar. Regardless of `ndim`, any inner nested tuples will be 
            treated as scalar.
        denominator_method: How to determine the denominator of the result
            if the arguments themselves contain weights. This is also used for 
            dict-like arguments. From greatest to least:
            * 'prod': Product of the individual argument denominators, times the 
                total of `weights`. This is like rolling all of the possible 
                dice, and then selecting a result.
            * 'lcm' (default): LCM of the individual argument denominators, 
                times the total of `weights`. This is like rolling `weights` 
                first, then selecting an argument to roll.
            * 'lcm_weighted': LCM of the individual (argument denominators times 
                corresponding element of `weights`). This is like rolling the 
                above, but the specific weight rolled is used to help determine 
                the result of the selected argument.
            * 'reduce': `reduce()` is called at the end.
    Raises:
        `ValueError` if `ndim` is set but is not consistent with `*args`.
            Furthermore, `None` is not a valid outcome for a die.
    """

    # Special case: consecutive outcomes.
    if min_outcome is not None:
        if weights is None:
            raise ValueError(
                'If min_outcome is provided, weights must also be provided.')
        if len(args) > 0:
            raise ValueError(
                'If min_outcome is provided, no *args may be used.')
        if ndim not in [None, icepool.Scalar]:
            raise ValueError(
                'If min_outcome is provided, the result may only be a scalar die.'
            )
        data = Counts(
            {i + min_outcome: weight for i, weight in enumerate(weights)})
        return icepool.ScalarDie(data)

    if weights is not None:
        if len(weights) != len(args):
            raise ValueError(
                'If weights are provided, there must be exactly one weight per argument.'
            )
    else:
        weights = (1,) * len(args)

    # Special cases.
    if len(args) == 0:
        return icepool.EmptyDie()
    elif (len(args) == 1 and _is_die(args[0]) and weights[0] == 1 
          and (ndim is None or ndim == args[0].ndim())):
        # Single unmodified die: just return the existing instance.
        return args[0]

    # Expand data.
    subdatas, die_ndims = zip(*[_expand(arg, denominator_method) for arg in args])
    die_ndim = _merge_die_ndims(die_ndims)
    data = _merge_subdatas(subdatas, weights, denominator_method)

    if len(data) == 0:
        return icepool.EmptyDie()

    # Compute ndim.
    if die_ndim not in [None, icepool.Empty]:
        if ndim is None:
            ndim = die_ndim
        elif ndim != die_ndim:
            raise ValueError(f'Requested ndim {ndim} is incompatible with that of an argument die {die_ndim}')
    
    if ndim is None:
        for outcome in data.keys():
            if _is_tuple(outcome):
                if ndim is None:
                    ndim = len(outcome)
                elif ndim != len(outcome):
                    ndim = icepool.Scalar
                    break
            else:
                ndim = icepool.Scalar
                break
    elif ndim != icepool.Scalar:
        for outcome in data.keys():
            if not _is_tuple(outcome) or len(outcome) != ndim:
                if die_ndim is None:
                    raise ValueError(
                        f'Outcome {outcome} is incompatible with requested ndim {ndim}'
                    )
                else:
                    raise ValueError(
                        f'Outcome {outcome} is incompatible with that of an argument die {die_ndim}'
                    )
                

    if ndim == icepool.Scalar:
        data = Counts(data)
        result = icepool.ScalarDie(data)
    else:
        data = Counts(data)
        result = icepool.VectorDie(data, ndim)

    if denominator_method == 'reduce':
        result = result.reduce()

    return result


def _expand(arg, denominator_method):
    """Expands the argument to a dict mapping outcomes to weights.
    
    Also returns the `ndim` of the dice at this tuple level.
    
    The outcomes are valid outcomes for a die.
    """
    if _is_die(arg):
        return _expand_die(arg)
    elif _is_dict(arg):
        return _expand_dict(arg, denominator_method)
    elif _is_tuple(arg):
        return _expand_tuple(arg, denominator_method)
    else:
        return _expand_scalar(arg)


def _is_die(arg):
    return isinstance(arg, icepool.BaseDie)


def _expand_die(arg):
    return arg._data, arg.ndim()


def _is_dict(arg):
    return hasattr(arg, 'keys') and hasattr(arg, 'values') and hasattr(
        arg, 'items') and hasattr(arg, '__getitem__')


def _expand_dict(arg, denominator_method):
    if len(arg) == 0:
        return {}, None
    subdatas, die_ndims = zip(*[_expand(k, denominator_method) for k, v in arg.items()])
    die_ndim = _merge_die_ndims(die_ndims)
    weights = [x for x in arg.values()]
    return _merge_subdatas(subdatas, weights, denominator_method), die_ndim


def _is_tuple(arg):
    return type(arg) is tuple


def _expand_tuple(arg, denominator_method):
    subdatas, die_ndims = zip(*[_expand(x, denominator_method) for x in arg])
    die_ndim = _merge_die_ndims(die_ndims)
    if isinstance(die_ndim, int):
        raise ValueError('Vector dice cannot be nested inside tuple outcomes.')
    data = defaultdict(int)
    for t in itertools.product(*(subdata.items() for subdata in subdatas)):
        outcomes, weights = zip(*t)
        data[outcomes] += math.prod(weights)
    return data, None


def _expand_scalar(arg):
    if arg is icepool.Reroll:
        return {}, None
    else:
        return {arg: 1}, None


def _merge_subdatas(subdatas, weights, denominator_method):
    if any(x < 0 for x in weights):
        raise ValueError('Weights cannot be negative.')
    subdata_denominators = [sum(subdata.values()) for subdata in subdatas]

    if denominator_method == 'prod':
        denominator_prod = math.prod(d for d in subdata_denominators if d > 0)
    elif denominator_method == 'lcm':
        denominator_prod = math.lcm(*(d for d in subdata_denominators if d > 0))
    elif denominator_method in ['lcm_weighted', 'reduce']:
        denominator_prod = math.lcm(
            *(d // math.gcd(d, w)
              for d, w in zip(subdata_denominators, weights)
              if d > 0))
    else:
        raise ValueError(f'Invalid denominator_method {denominator_method}.')

    data = defaultdict(int)
    for subdata, subdata_denominator, w in zip(subdatas, subdata_denominators,
                                               weights):
        factor = denominator_prod * w // subdata_denominator if subdata_denominator else 0
        for outcome, weight in subdata.items():
            data[outcome] += weight * factor

    return data


def _merge_die_ndims(die_ndims):
    result = None
    for die_ndim in die_ndims:
        if die_ndim in [None, icepool.Empty]:
            pass
        elif result is None:
            result = die_ndim
        elif die_ndim != result:
            raise ValueError('Die() expanded to top-level dice with conflicting ndims.')
    return result


def dice_with_common_ndim(*args, ndim=None):
    """Converts the arguments to dice with a common `ndim`.
    
    Args:
        *args: Args to be converted to dice.
        ndim: The required `ndim` of the results.
    
    Returns:
        dice, ndim: A tuple containing one die per arg, and the common `ndim`,
    
    Raises:
        `ValueError` if the arguments include conflicting `ndim`s.
    """
    if ndim is None:
        if len(args) == 0:
            return (), None
        # First pass: All dice get to be vector if possible.
        first_pass = tuple(Die(arg) for arg in args)
        if all(die.ndim() == first_pass[0].ndim() for die in first_pass):
            # If all dice end up with same ndim, return that.
            return first_pass, first_pass[0].ndim()
        else:
            # Otherwise remake them as scalar.
            return tuple(Die(die, ndim=icepool.Scalar)
                         for die in first_pass), icepool.Scalar
    else:
        return tuple(Die(arg, ndim=ndim) for arg in args), ndim
